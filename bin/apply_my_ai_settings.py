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
import json
import os
import subprocess
import sys
from collections.abc import Callable
from pathlib import Path
from typing import Any

import tomlkit

HOME = Path.home()
CODEX_CONFIG = HOME / ".codex" / "config.toml"
CLAUDE_CONFIG = HOME / ".claude.json"
# claude honors CLAUDE_CONFIG_DIR, so honor it too (handy for testing)
CLAUDE_DIR = Path(os.environ.get("CLAUDE_CONFIG_DIR", HOME / ".claude"))
CLAUDE_SETTINGS = CLAUDE_DIR / "settings.json"
CODEX_PLUGIN = "codex@openai-codex"
CODEX_MARKETPLACE = "openai-codex"
CODEX_MARKETPLACE_REPO = "openai/codex-plugin-cc"
FFF_MCP_BIN = HOME / "bin" / "fff-mcp"
FFF_MCP_ENV = {"FFF_MCP_IDLE_TIMEOUT_SECS": "0"}

# --- colors -----------------------------------------------------------------

USE_COLOR = sys.stdout.isatty() and os.environ.get("NO_COLOR") is None


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


# --- state ------------------------------------------------------------------


class State:
    def __init__(self, dry_run: bool) -> None:
        self.dry_run = dry_run
        self.failures = 0
        self.warnings = 0

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

    if unwrap(get_path(doc, keys)) == desired:
        ok(f"{label}: {dotted} already correct in {path}")
        return

    if state.dry_run:
        would(f"{label}: set {dotted} in {path}")
        return

    if is_toml:
        set_path(doc, keys, to_toml_value(desired), tomlkit.table)
        path.write_text(tomlkit.dumps(doc))
    else:
        set_path(doc, keys, desired, dict)
        path.write_text(json.dumps(doc, indent=2) + "\n")
    fixed(f"{label}: set {dotted} in {path}")


# --- settings ---------------------------------------------------------------


def setting_fff_mcp_binary(state: State) -> None:
    header("fff-mcp binary")
    if FFF_MCP_BIN.is_symlink():
        target = FFF_MCP_BIN.resolve()
        if not target.is_file():
            state.fail(f"{FFF_MCP_BIN} is a symlink to {target}, which does not exist")
            return
        ok(f"{FFF_MCP_BIN} -> {target}")
    elif FFF_MCP_BIN.is_file():
        state.warn(f"{FFF_MCP_BIN} is a regular file, expected a symlink to the real binary")
    else:
        state.fail(f"{FFF_MCP_BIN} does not exist")
        return
    if not os.access(FFF_MCP_BIN, os.X_OK):
        state.fail(f"{FFF_MCP_BIN} is not executable")
        return
    ok(f"{FFF_MCP_BIN} is an executable binary")

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
            [str(FFF_MCP_BIN)],
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
    ensure_entry(
        state,
        CODEX_CONFIG,
        ["mcp_servers", "fff"],
        {"command": str(FFF_MCP_BIN), "env": FFF_MCP_ENV},
        "codex",
    )


def setting_claude_fff_mcp(state: State) -> None:
    header("claude: fff MCP server")
    ensure_entry(
        state,
        CLAUDE_CONFIG,
        ["mcpServers", "fff"],
        {
            "type": "stdio",
            "command": str(FFF_MCP_BIN),
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


def setting_claude_codex_plugin(state: State) -> None:
    header("claude: codex plugin")
    ensure_entry(
        state,
        CLAUDE_SETTINGS,
        ["enabledPlugins", "codex@openai-codex"],
        True,
        "claude",
    )
    ensure_entry(
        state,
        CLAUDE_SETTINGS,
        ["extraKnownMarketplaces", "openai-codex"],
        {"source": {"source": "github", "repo": "openai/codex-plugin-cc"}},
        "claude",
    )


def claude_json(*args: str) -> Any:
    """Run `claude <args> --json` and return the parsed output."""
    proc = subprocess.run(
        ["claude", *args, "--json"], capture_output=True, text=True, timeout=60
    )
    if proc.returncode != 0:
        raise RuntimeError(f"claude {' '.join(args)} failed: {proc.stderr.strip()}")
    return json.loads(proc.stdout)


def claude_run(*args: str) -> bool:
    """Run a mutating `claude` command, echoing its last output line.

    `claude plugin` exits 0 even when it reports a failure, so callers must
    verify the result with `claude_json` instead of trusting the exit code.
    """
    proc = subprocess.run(["claude", *args], capture_output=True, text=True, timeout=180)
    output = (proc.stdout + proc.stderr).strip().splitlines()
    if output:
        info(output[-1])
    return proc.returncode == 0


def setting_claude_codex_plugin_installed(state: State) -> None:
    """Install the codex plugin the way `/plugin install codex@openai-codex`
    would inside claude code. The marketplace must be fetched first;
    the `extraKnownMarketplaces` settings entry alone is not enough."""
    header("claude: codex plugin installed")
    try:
        marketplaces = {m["name"] for m in claude_json("plugin", "marketplace", "list")}
    except (OSError, RuntimeError, json.JSONDecodeError, KeyError) as error:
        state.fail(f"cannot query claude marketplaces: {error}")
        return

    if CODEX_MARKETPLACE in marketplaces:
        ok(f"marketplace {CODEX_MARKETPLACE} is known to claude")
    elif state.dry_run:
        would(f"claude plugin marketplace add {CODEX_MARKETPLACE_REPO}")
    else:
        claude_run("plugin", "marketplace", "add", CODEX_MARKETPLACE_REPO)
        marketplaces = {m["name"] for m in claude_json("plugin", "marketplace", "list")}
        if CODEX_MARKETPLACE not in marketplaces:
            state.fail(f"marketplace {CODEX_MARKETPLACE} still missing after add")
            return
        fixed(f"added marketplace {CODEX_MARKETPLACE}")

    def installed() -> dict[str, Any] | None:
        for plugin in claude_json("plugin", "list"):
            if plugin.get("id") == CODEX_PLUGIN and plugin.get("scope") == "user":
                return plugin
        return None

    plugin = installed()
    if plugin:
        ok(f"{CODEX_PLUGIN} {plugin.get('version')} installed (user scope)")
    elif state.dry_run:
        would(f"claude plugin install {CODEX_PLUGIN} --scope user -y")
        return
    else:
        claude_run("plugin", "install", CODEX_PLUGIN, "--scope", "user", "-y")
        plugin = installed()
        if not plugin:
            state.fail(f"{CODEX_PLUGIN} still not installed after install")
            return
        fixed(f"installed {CODEX_PLUGIN} {plugin.get('version')} (user scope)")

    if plugin.get("enabled"):
        ok(f"{CODEX_PLUGIN} is enabled")
    else:
        state.fail(f"{CODEX_PLUGIN} is installed but disabled")


SETTINGS: list[Callable[[State], None]] = [
    setting_fff_mcp_binary,
    setting_codex_model,
    setting_codex_fff_mcp,
    setting_claude_fff_mcp,
    setting_claude_codex_plugin,
    setting_claude_codex_plugin_installed,
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
