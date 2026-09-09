#!/usr/bin/env -S uv run --script
#
# /// script
# requires-python = ">=3.14"
# dependencies = ["tomlkit"]
# ///
"""
apply my AI agent settings to the local machine.

Each "setting" is a small check-and-fix step. It prints one colored status
line so it is obvious what was already fine, what was changed, and what
could not be fixed. TOML and JSON config files are merged in place: only
the keys a setting owns are touched, everything else in the file is kept
(tomlkit preserves comments and formatting).

usage:
    apply_my_ai_settings.py            # check and fix
    apply_my_ai_settings.py --dry-run  # check only, never write
"""

from __future__ import annotations

import argparse
import difflib
import json
import os
import shutil
import subprocess
import sys
from collections.abc import Callable
from pathlib import Path
from typing import Any

import tomlkit

HOME = Path.home()
CODEX_CONFIG = HOME / ".codex" / "config.toml"
CLAUDE_CONFIG = HOME / ".claude.json"
# (plugin id, marketplace name, github repo), managed through `claude plugin`
CLAUDE_PLUGINS = [
    ("codex@openai-codex", "openai-codex", "openai/codex-plugin-cc"),
    ("fable-advisor@fable-advisor", "fable-advisor", "DannyMac180/fable-advisor"),
]
WINDOWS = os.name == "nt"
FFF_MCP_NAME = "fff-mcp.exe" if WINDOWS else "fff-mcp"
FFF_MCP_CANDIDATES = [HOME / "bin" / FFF_MCP_NAME, HOME / ".local" / "bin" / FFF_MCP_NAME]
FFF_MCP_ENV = {"FFF_MCP_IDLE_TIMEOUT_SECS": "0"}

# --- colors -----------------------------------------------------------------

# assume a modern terminal that understands ANSI colors, even on Windows
USE_COLOR = os.environ.get("NO_COLOR") is None


def paint(code: str, text: str) -> str:
    return f"\033[{code}m{text}\033[0m" if USE_COLOR else text


def ok(msg: str) -> None:
    print(f"  {paint('32', 'OK   ')} {msg}")


def fixed(msg: str) -> None:
    print(f"  {paint('33', 'FIXED')} {msg}")


def would(msg: str) -> None:
    print(f"  {paint('35', 'WOULD')} {msg}")


def warn(msg: str) -> None:
    print(f"  {paint('1;33', 'WARN ')} {msg}")


def fail(msg: str) -> None:
    print(f"  {paint('31', 'FAIL ')} {msg}")


def info(msg: str) -> None:
    print(f"  {paint('36', 'INFO ')} {msg}")


def header(msg: str) -> None:
    print(paint("1;36", f"== {msg}"))


def show_diff(path: Path, old: str, new: str) -> None:
    """Print a unified diff of a file rewrite, colored like git diff."""
    lines = difflib.unified_diff(
        old.splitlines(keepends=True),
        new.splitlines(keepends=True),
        fromfile=f"{path} (before)",
        tofile=f"{path} (after)",
    )
    for line in lines:
        line = line.rstrip("\n")
        if line.startswith(("+++", "---")):
            print(paint("1", f"        {line}"))
        elif line.startswith("@@"):
            print(paint("36", f"        {line}"))
        elif line.startswith("+"):
            print(paint("32", f"        {line}"))
        elif line.startswith("-"):
            print(paint("31", f"        {line}"))
        else:
            print(f"        {line}")


# --- state ------------------------------------------------------------------


class State:
    def __init__(self, dry_run: bool) -> None:
        self.dry_run = dry_run
        self.failures = 0
        self.warnings = 0
        # set by setting_fff_mcp_binary, consumed by the MCP config settings
        self.fff_mcp_bin: Path | None = None

    def warn(self, msg: str) -> None:
        self.warnings += 1
        warn(msg)

    def fail(self, msg: str) -> None:
        self.failures += 1
        fail(msg)


# --- file merge helpers -----------------------------------------------------


def to_toml_value(value: Any, top: bool = True) -> Any:
    """Convert plain Python data into tomlkit items.

    The top-level dict becomes a real table (`[mcp_servers.fff]`) and nested
    dicts become inline tables (`env = { ... }`), matching what codex writes.
    """
    if isinstance(value, dict):
        table = tomlkit.table() if top else tomlkit.inline_table()
        for key, item in value.items():
            table[key] = to_toml_value(item, top=False)
        return table
    if isinstance(value, list):
        array = tomlkit.array()
        for item in value:
            array.append(to_toml_value(item, top=False))
        return array
    return value


def get_path(doc: Any, keys: list[str]) -> Any:
    node = doc
    for key in keys:
        if not isinstance(node, dict) or key not in node:
            return None
        node = node[key]
    return node


def set_path(doc: Any, keys: list[str], value: Any, make_table: Callable[[], Any]) -> None:
    node = doc
    for key in keys[:-1]:
        if key not in node or not isinstance(node[key], dict):
            node[key] = make_table()
        node = node[key]
    node[keys[-1]] = value


def unwrap(value: Any) -> Any:
    """Turn tomlkit containers into plain Python data for comparison."""
    return value.unwrap() if hasattr(value, "unwrap") else value


def ensure_entry(
    state: State,
    path: Path,
    keys: list[str],
    desired: Any,
    label: str,
) -> None:
    """Make sure `keys` in the TOML or JSON file at `path` equals `desired`.

    `desired` may be a scalar or a dict. A dict entry is replaced as a whole
    so stale keys go away; the rest of the file is left untouched.
    """
    dotted = ".".join(keys)
    if not path.is_file():
        state.fail(f"{label}: {path} does not exist")
        return

    is_toml = path.suffix == ".toml"
    text = path.read_text()
    doc = tomlkit.parse(text) if is_toml else json.loads(text)

    current = unwrap(get_path(doc, keys))
    if current == desired:
        ok(f"{label}: {dotted} already correct in {path}")
        return

    if is_toml:
        set_path(doc, keys, to_toml_value(desired), tomlkit.table)
        new_text = tomlkit.dumps(doc)
    else:
        set_path(doc, keys, desired, dict)
        new_text = json.dumps(doc, indent=2) + "\n"

    if state.dry_run:
        would(f"{label}: set {dotted} in {path}")
    else:
        path.write_text(new_text)
        fixed(f"{label}: set {dotted} in {path}")
    info(f"{label}: {dotted} was {current!r}")
    show_diff(path, text, new_text)


# --- settings ---------------------------------------------------------------


def setting_fff_mcp_binary(state: State) -> None:
    header("fff-mcp binary")
    found = [p for p in FFF_MCP_CANDIDATES if p.is_symlink() or p.exists()]
    if not found:
        state.fail("no fff-mcp found, looked in " + ", ".join(map(str, FFF_MCP_CANDIDATES)))
        return
    binary = found[0]
    if len(found) > 1:
        info("using " + str(binary) + ", ignoring " + ", ".join(map(str, found[1:])))
    if binary.is_symlink():
        target = binary.resolve()
        if not target.is_file():
            state.fail(f"{binary} is a symlink to {target}, which does not exist")
            return
        ok(f"{binary} -> {target}")
    elif binary.is_file():
        state.warn(f"{binary} is a regular file, expected a symlink to the real binary")
    else:
        state.fail(f"{binary} is not a file")
        return
    if not os.access(binary, os.X_OK):
        state.fail(f"{binary} is not executable")
        return
    ok(f"{binary} is an executable binary")
    state.fff_mcp_bin = binary

    # Speak enough MCP to make sure the binary actually starts and answers.
    request = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "initialize",
        "params": {
            "protocolVersion": "2024-11-05",
            "capabilities": {},
            "clientInfo": {"name": "apply_my_ai_settings", "version": "0"},
        },
    }
    try:
        proc = subprocess.run(
            [str(binary)],
            input=json.dumps(request) + "\n",
            capture_output=True,
            text=True,
            timeout=10,
            env={**os.environ, **FFF_MCP_ENV},
        )
        first_line = proc.stdout.splitlines()[0] if proc.stdout else ""
        response = json.loads(first_line) if first_line else {}
    except subprocess.TimeoutExpired:
        # a server that ignores stdin EOF and idles is still a working server
        response = None
    except (OSError, json.JSONDecodeError, IndexError) as error:
        state.fail(f"MCP initialize handshake failed: {error}")
        return

    if response is None:
        ok("MCP server started (handshake timed out waiting for exit, treated as alive)")
        return
    server = response.get("result", {}).get("serverInfo", {})
    if not server:
        state.fail(f"MCP initialize returned no serverInfo: {first_line[:200]}")
        return
    ok(f"MCP initialize handshake works ({server.get('name')} {server.get('version')})")


def setting_codex_fff_mcp(state: State) -> None:
    header("codex: fff MCP server")
    if state.fff_mcp_bin is None:
        state.fail("codex: skipped, no usable fff-mcp binary")
        return
    ensure_entry(
        state,
        CODEX_CONFIG,
        ["mcp_servers", "fff"],
        {"command": str(state.fff_mcp_bin), "env": FFF_MCP_ENV},
        "codex",
    )


def setting_claude_fff_mcp(state: State) -> None:
    header("claude: fff MCP server")
    if state.fff_mcp_bin is None:
        state.fail("claude: skipped, no usable fff-mcp binary")
        return
    ensure_entry(
        state,
        CLAUDE_CONFIG,
        ["mcpServers", "fff"],
        {
            "type": "stdio",
            "command": str(state.fff_mcp_bin),
            "args": [],
            "env": FFF_MCP_ENV,
        },
        "claude",
    )


def setting_codex_model(state: State) -> None:
    header("codex: model")
    for key, value in {
        "model": "gpt-6-astra",
        "model_reasoning_effort": "high",
    }.items():
        ensure_entry(state, CODEX_CONFIG, [key], value, "codex")


def claude_bin() -> str:
    # on Windows `claude` is a .cmd shim, which subprocess only finds via which()
    found = shutil.which("claude")
    if not found:
        raise RuntimeError("claude is not on PATH")
    return found


def claude_json(*args: str) -> Any:
    """Run `claude <args> --json` and return the parsed output."""
    proc = subprocess.run(
        [claude_bin(), *args, "--json"], capture_output=True, text=True, timeout=60
    )
    if proc.returncode != 0:
        raise RuntimeError(f"claude {' '.join(args)} failed: {proc.stderr.strip()}")
    return json.loads(proc.stdout)


def claude_run(*args: str) -> bool:
    """Run a mutating `claude` command, echoing its last output line.

    `claude plugin` exits 0 even when it reports a failure, so callers must
    verify the result with `claude_json` instead of trusting the exit code.
    """
    proc = subprocess.run([claude_bin(), *args], capture_output=True, text=True, timeout=180)
    output = (proc.stdout + proc.stderr).strip().splitlines()
    if output:
        info(output[-1])
    return proc.returncode == 0


def ensure_claude_plugin(state: State, plugin_id: str, marketplace: str, repo: str) -> None:
    """Install or update a plugin the way these would inside claude code:

        /plugin marketplace add <repo>
        /plugin install <plugin_id>

    `claude plugin marketplace add` and `claude plugin install` write the
    `extraKnownMarketplaces` and `enabledPlugins` entries to settings.json
    themselves, so nothing is edited by hand here. When the plugin is already
    installed, the marketplace and plugin are updated to the latest release.
    """
    header(f"claude: plugin {plugin_id}")
    try:
        marketplaces = {m["name"] for m in claude_json("plugin", "marketplace", "list")}
    except (OSError, RuntimeError, json.JSONDecodeError, KeyError) as error:
        state.fail(f"cannot query claude marketplaces: {error}")
        return

    if marketplace not in marketplaces:
        if state.dry_run:
            would(f"claude plugin marketplace add {repo}")
        else:
            claude_run("plugin", "marketplace", "add", repo)
            marketplaces = {m["name"] for m in claude_json("plugin", "marketplace", "list")}
            if marketplace not in marketplaces:
                state.fail(f"marketplace {marketplace} still missing after add")
                return
            fixed(f"added marketplace {marketplace}")
    elif state.dry_run:
        ok(f"marketplace {marketplace} is known to claude")
    else:
        claude_run("plugin", "marketplace", "update", marketplace)
        ok(f"marketplace {marketplace} refreshed")

    def installed() -> dict[str, Any] | None:
        for plugin in claude_json("plugin", "list"):
            if plugin.get("id") == plugin_id and plugin.get("scope") == "user":
                return plugin
        return None

    plugin = installed()
    if plugin is None:
        if state.dry_run:
            would(f"claude plugin install {plugin_id} --scope user -y")
            return
        claude_run("plugin", "install", plugin_id, "--scope", "user", "-y")
        plugin = installed()
        if plugin is None:
            state.fail(f"{plugin_id} still not installed after install")
            return
        fixed(f"installed {plugin_id} {plugin.get('version')} (user scope)")
    elif state.dry_run:
        ok(f"{plugin_id} {plugin.get('version')} installed (user scope)")
    else:
        before = plugin.get("version")
        claude_run("plugin", "update", plugin_id, "--scope", "user", "-y")
        plugin = installed() or plugin
        after = plugin.get("version")
        if after != before:
            fixed(f"updated {plugin_id} {before} -> {after} (restart claude to apply)")
        else:
            ok(f"{plugin_id} {after} is the latest version")

    if plugin.get("enabled"):
        ok(f"{plugin_id} is enabled")
    elif state.dry_run:
        would(f"claude plugin enable {plugin_id}")
    else:
        claude_run("plugin", "enable", plugin_id)
        plugin = installed() or plugin
        if plugin.get("enabled"):
            fixed(f"enabled {plugin_id}")
        else:
            state.fail(f"{plugin_id} still disabled after enable")


def setting_claude_plugins(state: State) -> None:
    for plugin_id, marketplace, repo in CLAUDE_PLUGINS:
        ensure_claude_plugin(state, plugin_id, marketplace, repo)


SETTINGS: list[Callable[[State], None]] = [
    setting_fff_mcp_binary,
    setting_codex_model,
    setting_codex_fff_mcp,
    setting_claude_fff_mcp,
    setting_claude_plugins,
]


# --- main -------------------------------------------------------------------


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.strip().splitlines()[0])
    parser.add_argument(
        "-n",
        "--dry-run",
        action="store_true",
        help="report what would change without writing any file",
    )
    args = parser.parse_args(argv)

    state = State(dry_run=args.dry_run)
    for setting in SETTINGS:
        setting(state)

    print()
    if state.failures:
        fail(f"{state.failures} setting(s) could not be applied")
        return 1
    done = "dry run complete" if state.dry_run else "all settings applied"
    if state.warnings:
        warn(f"{done} with {state.warnings} warning(s)")
    else:
        ok(done)
    return 0


if __name__ == "__main__":
    sys.exit(main())
