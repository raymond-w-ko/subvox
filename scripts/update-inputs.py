#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = [
#   "textual==8.2.8",
# ]
# ///

"""Safely update selected flake inputs through a candidate lock file."""

from __future__ import annotations

import argparse
import asyncio
import hashlib
import json
import os
import shlex
import shutil
import tempfile
from pathlib import Path
from typing import Any

from rich.text import Text
from textual.app import App, ComposeResult
from textual.containers import Horizontal, Vertical
from textual.widgets import Button, Checkbox, Footer, Header, Label, RichLog, Static

HIGH_FREQUENCY = ("neru", "claude-code", "codex-cli-nix")
CORE = ("nixpkgs", "nix-darwin", "home-manager", "nixos-wsl", "rust-overlay")
ALL_INPUTS = HIGH_FREQUENCY + CORE
GROUPS = {
    "high": HIGH_FREQUENCY,
    "core": CORE,
    "all": ALL_INPUTS,
}


def parse_initial_selection(arguments: list[str]) -> set[str]:
    """Resolve group names and individual inputs from command-line arguments."""
    if not arguments:
        return set(HIGH_FREQUENCY)

    selected: set[str] = set()
    for argument in arguments:
        if argument in GROUPS:
            selected.update(GROUPS[argument])
        elif argument in ALL_INPUTS:
            selected.add(argument)
        else:
            choices = ", ".join((*GROUPS, *ALL_INPUTS))
            raise ValueError(
                f"unknown group or input {argument!r}; choose from: {choices}"
            )
    return selected


def lock_digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_lock(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


def direct_node(lock: dict[str, Any], input_name: str) -> dict[str, Any]:
    root_inputs = lock["nodes"]["root"]["inputs"]
    reference = root_inputs[input_name]
    if not isinstance(reference, str):
        return {}
    return lock["nodes"].get(reference, {})


def locked_summary(node: dict[str, Any]) -> str:
    locked = node.get("locked", {})
    revision = locked.get("rev")
    if revision:
        return str(revision)[:12]
    return str(locked.get("ref") or locked.get("path") or "unlocked")


def describe_lock_changes(old_path: Path, new_path: Path) -> list[str]:
    """Describe direct input changes plus changed transitive lock nodes."""
    old = load_lock(old_path)
    new = load_lock(new_path)
    lines = ["Direct inputs:"]

    direct_changes = 0
    for input_name in ALL_INPUTS:
        old_summary = locked_summary(direct_node(old, input_name))
        new_summary = locked_summary(direct_node(new, input_name))
        if old_summary != new_summary:
            direct_changes += 1
            lines.append(f"  {input_name}: {old_summary} -> {new_summary}")
    if direct_changes == 0:
        lines.append("  no direct revision changes")

    old_nodes = old.get("nodes", {})
    new_nodes = new.get("nodes", {})
    changed_nodes: list[str] = []
    for node_name in sorted(set(old_nodes) | set(new_nodes)):
        old_locked = old_nodes.get(node_name, {}).get("locked")
        new_locked = new_nodes.get(node_name, {}).get("locked")
        if old_locked == new_locked:
            continue
        if old_locked is None:
            changed_nodes.append(
                f"  + {node_name}: {locked_summary(new_nodes[node_name])}"
            )
        elif new_locked is None:
            changed_nodes.append(
                f"  - {node_name}: {locked_summary(old_nodes[node_name])}"
            )
        else:
            changed_nodes.append(
                f"  {node_name}: {locked_summary(old_nodes[node_name])}"
                f" -> {locked_summary(new_nodes[node_name])}"
            )

    lines.append("All changed lock nodes:")
    lines.extend(changed_nodes or ["  none"])
    return lines


class UpdateInputsApp(App[None]):
    TITLE = "Subvox flake input updater"
    SUB_TITLE = "candidate first, validate before apply"

    CSS = """
    Screen {
      layout: vertical;
    }

    #content {
      height: 1fr;
    }

    #inputs {
      width: 38;
      min-width: 32;
      padding: 1 2;
      border: round $accent;
    }

    #inputs Label {
      margin-top: 1;
      text-style: bold;
    }

    #status {
      margin-top: 1;
      padding: 1;
      border: round $primary;
    }

    #log {
      width: 1fr;
      border: round $primary;
      padding: 0 1;
    }

    #actions {
      height: auto;
      padding: 1;
      align-horizontal: center;
    }

    #actions Button {
      margin: 0 1;
    }
    """

    BINDINGS = [
        ("q", "quit", "Quit"),
        ("g", "generate", "Generate"),
        ("v", "validate", "Validate"),
    ]

    def __init__(self, initial_selection: set[str]) -> None:
        super().__init__()
        self.initial_selection = initial_selection
        self.repo = Path(__file__).resolve().parent.parent
        self.lock_file = self.repo / "flake.lock"
        self.candidate: Path | None = None
        self.source_digest: str | None = None
        self.candidate_inputs: tuple[str, ...] = ()
        self.validated = False
        self.applied = False
        self.busy = False

    def compose(self) -> ComposeResult:
        yield Header()
        with Horizontal(id="content"):
            with Vertical(id="inputs"):
                yield Label("High frequency")
                for input_name in HIGH_FREQUENCY:
                    yield Checkbox(
                        input_name,
                        value=input_name in self.initial_selection,
                        id=f"input-{input_name}",
                    )
                yield Label("Core / manual")
                for input_name in CORE:
                    yield Checkbox(
                        input_name,
                        value=input_name in self.initial_selection,
                        id=f"input-{input_name}",
                    )
                yield Static("Ready", id="status")
            yield RichLog(id="log", wrap=True, highlight=True, markup=False)
        with Horizontal(id="actions"):
            yield Button("Generate candidate", id="generate", variant="primary")
            yield Button("Validate + build", id="validate", disabled=True)
            yield Button(
                "Apply validated lock", id="apply", variant="success", disabled=True
            )
            yield Button("Commit lock", id="commit", disabled=True)
        yield Footer()

    def on_mount(self) -> None:
        self.write_log("Tracked flake.lock remains untouched until Apply.")
        self.write_log(f"Repository: {self.repo}")

    def selected_inputs(self) -> tuple[str, ...]:
        return tuple(
            input_name
            for input_name in ALL_INPUTS
            if self.query_one(f"#input-{input_name}", Checkbox).value
        )

    def write_log(self, message: str) -> None:
        self.query_one("#log", RichLog).write(Text(message))

    def set_status(self, message: str) -> None:
        self.query_one("#status", Static).update(message)

    def set_busy(self, busy: bool) -> None:
        self.busy = busy
        self.query_one("#generate", Button).disabled = busy
        self.query_one("#validate", Button).disabled = busy or self.candidate is None
        self.query_one("#apply", Button).disabled = busy or not self.validated
        self.query_one("#commit", Button).disabled = busy or not self.applied
        for checkbox in self.query(Checkbox):
            checkbox.disabled = busy

    def invalidate_candidate(self) -> None:
        self.candidate = None
        self.source_digest = None
        self.candidate_inputs = ()
        self.validated = False
        self.applied = False
        self.query_one("#validate", Button).disabled = True
        self.query_one("#apply", Button).disabled = True
        self.query_one("#commit", Button).disabled = True
        self.set_status("Selection changed; generate a new candidate")

    async def run_command(self, command: list[str]) -> int:
        self.write_log(f"$ {shlex.join(command)}")
        process = await asyncio.create_subprocess_exec(
            *command,
            cwd=self.repo,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.STDOUT,
        )
        assert process.stdout is not None
        while line := await process.stdout.readline():
            self.write_log(line.decode(errors="replace").rstrip())
        return await process.wait()

    async def lock_is_dirty(self) -> bool:
        process = await asyncio.create_subprocess_exec(
            "git",
            "status",
            "--porcelain",
            "--",
            "flake.lock",
            cwd=self.repo,
            stdout=asyncio.subprocess.PIPE,
        )
        stdout, _ = await process.communicate()
        return bool(stdout.strip())

    async def generate_candidate(self) -> None:
        selected = self.selected_inputs()
        if not selected:
            self.set_status("Select at least one input")
            return
        if await self.lock_is_dirty():
            self.set_status("Refusing: flake.lock already has uncommitted changes")
            self.write_log(
                "Commit or otherwise handle the existing flake.lock change first."
            )
            return

        self.set_busy(True)
        self.set_status("Generating candidate lock…")
        try:
            candidate_dir = Path(
                tempfile.mkdtemp(prefix="subvox-flake-update-")
            ).resolve()
            candidate = candidate_dir / "flake.lock"
            command = [
                "nix",
                "flake",
                "update",
                *selected,
                "--reference-lock-file",
                str(self.lock_file),
                "--output-lock-file",
                str(candidate),
            ]
            return_code = await self.run_command(command)
            if return_code != 0:
                self.set_status(f"Candidate generation failed ({return_code})")
                return

            self.candidate = candidate
            self.source_digest = lock_digest(self.lock_file)
            self.candidate_inputs = selected
            self.validated = False
            self.applied = False
            self.write_log("")
            for line in describe_lock_changes(self.lock_file, candidate):
                self.write_log(line)
            self.write_log(f"Candidate: {candidate}")
            self.set_status("Candidate ready; validate before applying")
        except (OSError, KeyError, ValueError, json.JSONDecodeError) as error:
            self.set_status("Candidate generation failed")
            self.write_log(f"Error: {error}")
        finally:
            self.set_busy(False)

    async def validate_candidate(self) -> None:
        if self.candidate is None:
            return
        if self.source_digest != lock_digest(self.lock_file):
            self.invalidate_candidate()
            self.write_log("flake.lock changed after candidate generation.")
            return

        self.set_busy(True)
        self.set_status("Evaluating candidate…")
        try:
            check_command = [
                "nix",
                "flake",
                "check",
                "--no-build",
                "--reference-lock-file",
                str(self.candidate),
            ]
            return_code = await self.run_command(check_command)
            if return_code != 0:
                self.set_status(f"Evaluation failed ({return_code})")
                return

            self.set_status("Building macOS system against candidate…")
            build_command = [
                "nix",
                "build",
                ".#darwinConfigurations.macos.config.system.build.toplevel",
                "--no-link",
                "--reference-lock-file",
                str(self.candidate),
                "--print-build-logs",
            ]
            return_code = await self.run_command(build_command)
            if return_code != 0:
                self.set_status(f"Candidate build failed ({return_code})")
                return

            self.validated = True
            self.set_status("Validated; candidate may be applied")
        except OSError as error:
            self.set_status("Validation failed")
            self.write_log(f"Error: {error}")
        finally:
            self.set_busy(False)

    async def apply_candidate(self) -> None:
        if self.candidate is None or not self.validated:
            return
        if self.source_digest != lock_digest(self.lock_file):
            self.invalidate_candidate()
            self.write_log("flake.lock changed after validation; candidate discarded.")
            return

        self.set_busy(True)
        try:
            temporary = self.lock_file.with_name(
                f".{self.lock_file.name}.{os.getpid()}.tmp"
            )
            shutil.copyfile(self.candidate, temporary)
            os.replace(temporary, self.lock_file)
            self.validated = False
            self.applied = True
            self.set_status("Candidate applied; review or commit flake.lock")
            self.write_log("Applied validated candidate to flake.lock.")
            await self.run_command(["git", "diff", "--stat", "--", "flake.lock"])
        except OSError as error:
            self.set_status("Apply failed")
            self.write_log(f"Error: {error}")
        finally:
            self.set_busy(False)

    async def commit_lock(self) -> None:
        if not self.applied:
            return
        self.set_busy(True)
        try:
            selected = ", ".join(self.candidate_inputs)
            message = f"chore: update {selected} inputs"
            return_code = await self.run_command(
                ["git", "commit", "-m", message, "--", "flake.lock"]
            )
            if return_code == 0:
                self.applied = False
                self.set_status("Committed flake.lock; nothing was pushed")
            else:
                self.set_status(f"Commit failed ({return_code})")
        finally:
            self.set_busy(False)

    def on_checkbox_changed(self, _event: Checkbox.Changed) -> None:
        if self.candidate is not None and not self.busy:
            self.invalidate_candidate()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        actions = {
            "generate": self.generate_candidate,
            "validate": self.validate_candidate,
            "apply": self.apply_candidate,
            "commit": self.commit_lock,
        }
        action = actions.get(event.button.id or "")
        if action is not None:
            self.run_worker(action(), exclusive=True, group="update")

    def action_generate(self) -> None:
        if not self.busy:
            self.run_worker(self.generate_candidate(), exclusive=True, group="update")

    def action_validate(self) -> None:
        if not self.busy and self.candidate is not None:
            self.run_worker(self.validate_candidate(), exclusive=True, group="update")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Open the guarded Textual flake input updater.",
        epilog="Selections: high, core, all, or individual root input names.",
    )
    parser.add_argument(
        "selection",
        nargs="*",
        help="initial groups or inputs; defaults to the high-frequency group",
    )
    arguments = parser.parse_args()
    try:
        selected = parse_initial_selection(arguments.selection)
    except ValueError as error:
        parser.error(str(error))
    UpdateInputsApp(selected).run()


if __name__ == "__main__":
    main()
