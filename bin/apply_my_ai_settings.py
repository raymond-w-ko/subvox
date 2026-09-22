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

Gateway setup: put base_url and api_key in ~/.config/ai/proxy.json.
See docs/ai-settings.md for details.
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
from urllib.parse import urlsplit

import tomlkit

HOME = Path.home()
# this script lives in subvox/bin, so the repo root is one level up
SUBVOX_ROOT = Path(__file__).resolve().parent.parent
SKILLS_DIR = SUBVOX_ROOT / "ai" / "skills"
CODEX_CONFIG = HOME / ".codex" / "config.toml"
CLAUDE_CONFIG = HOME / ".claude.json"
CLAUDE_SETTINGS = HOME / ".claude" / "settings.json"
CLAUDE_INSTALLED_PLUGINS = HOME / ".claude" / "plugins" / "installed_plugins.json"
GROK_CONFIG = Path(os.environ.get("GROK_HOME") or HOME / ".grok").expanduser() / "config.toml"
PI_MODELS = HOME / ".pi" / "agent" / "models.json"
PI_AUTH = HOME / ".pi" / "agent" / "auth.json"
AI_PROXY_CONFIG = HOME / ".config" / "ai" / "proxy.json"
# (plugin id, marketplace name, github repo), managed through `claude plugin`
CLAUDE_PLUGINS = [
    ("codex@openai-codex", "openai-codex", "openai/codex-plugin-cc"),
    ("fable-advisor@fable-advisor", "fable-advisor", "raymond-w-ko/fable-advisor"),
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
    *,
    sensitive: bool = False,
    create: bool = False,
) -> bool:
    """Make sure `keys` in the TOML or JSON file at `path` equals `desired`.

    `desired` may be a scalar or a dict. A dict entry is replaced as a whole
    so stale keys go away; the rest of the file is left untouched.
    """
    dotted = ".".join(keys)
    # Even unrelated edits can include credentials in unified diff context.
    sensitive = sensitive or path in (CODEX_CONFIG, CLAUDE_SETTINGS, PI_MODELS, GROK_CONFIG)
    exists = path.is_file()
    if not exists and not create:
        state.fail(f"{label}: {path} does not exist")
        return False

    is_toml = path.suffix == ".toml"
    try:
        text = path.read_text() if exists else ("" if is_toml else "{}\n")
        doc = tomlkit.parse(text) if is_toml else json.loads(text)
    except (OSError, ValueError, tomlkit.exceptions.ParseError):
        state.fail(f"{label}: cannot read or parse {path}")
        return False
    if not isinstance(doc, dict):
        state.fail(f"{label}: expected an object in {path}")
        return False

    current = unwrap(get_path(doc, keys))
    if current == desired:
        ok(f"{label}: {dotted} already correct in {path}")
        return True

    if is_toml:
        set_path(doc, keys, to_toml_value(desired), tomlkit.table)
        new_text = tomlkit.dumps(doc)
    else:
        set_path(doc, keys, desired, dict)
        new_text = json.dumps(doc, indent=2) + "\n"

    if state.dry_run:
        would(f"{label}: set {dotted} in {path}")
    else:
        try:
            if not exists:
                path.parent.mkdir(parents=True, exist_ok=True)
                with path.open("x", encoding="utf-8") as stream:
                    if sensitive and not WINDOWS:
                        os.chmod(path, 0o600)
                    stream.write(new_text)
            else:
                if sensitive and not WINDOWS:
                    path.chmod(0o600)
                path.write_text(new_text)
        except OSError:
            state.fail(f"{label}: cannot write {path}")
            return False
        fixed(f"{label}: set {dotted} in {path}")
    if sensitive:
        info(f"{label}: values and diff hidden (contains credentials)")
    else:
        info(f"{label}: {dotted} was {current!r}")
        show_diff(path, text, new_text)
    return True


# --- settings ---------------------------------------------------------------


def setting_gateway(state: State) -> None:
    header("CLIProxyAPI: codex, claude, pi, and grok")
    try:
        proxy = json.loads(AI_PROXY_CONFIG.read_text())
    except (OSError, ValueError):
        state.fail(f"gateway: cannot read or parse {AI_PROXY_CONFIG}")
        return
    key = proxy.get("api_key") if isinstance(proxy, dict) else None
    if (
        not isinstance(key, str)
        or not key
        or any(c.isspace() for c in key)
        or key == "YOUR_GATEWAY_KEY"
    ):
        state.fail(f"gateway: set a non-empty api_key string in {AI_PROXY_CONFIG}")
        return
    base_url = proxy.get("base_url")
    try:
        if (
            not isinstance(base_url, str)
            or not base_url
            or any(c.isspace() for c in base_url)
        ):
            raise ValueError
        url = urlsplit(base_url)
        if (
            url.scheme not in ("http", "https")
            or not url.hostname
            or url.username is not None
            or url.password is not None
            or url.query
            or url.fragment
        ):
            raise ValueError
        url.port  # Validate an explicit port before changing either client.
    except ValueError:
        state.fail(f"gateway: set base_url to an HTTP(S) root URL in {AI_PROXY_CONFIG}")
        return
    base_url = base_url.rstrip("/")
    if base_url.endswith("/v1"):
        base_url = base_url[:-3]

    grok_model = proxy.get("grok_model", "grok-4.6")
    if (
        not isinstance(grok_model, str)
        or not grok_model
        or any(c.isspace() for c in grok_model)
    ):
        state.fail(f"gateway: set grok_model to a model ID in {AI_PROXY_CONFIG}")
        return

    if ensure_entry(
        state,
        CODEX_CONFIG,
        ["model_providers", "cliproxyapi"],
        {
            "name": "CLIProxyAPI",
            "base_url": base_url + "/v1",
            "wire_api": "responses",
            "experimental_bearer_token": key,
            "requires_openai_auth": False,
            "supports_websockets": True,
        },
        "codex",
        sensitive=True,
    ):
        ensure_entry(
            state,
            CODEX_CONFIG,
            ["model_provider"],
            "cliproxyapi",
            "codex",
            sensitive=True,
        )

    for name, value in {
        "ANTHROPIC_BASE_URL": base_url,
        "ANTHROPIC_AUTH_TOKEN": key,
        "ANTHROPIC_API_KEY": "",
    }.items():
        if not ensure_entry(
            state,
            CLAUDE_SETTINGS,
            ["env", name],
            value,
            "claude",
            sensitive=True,
            create=True,
        ):
            break

    setting_pi_gateway(state, base_url, key)
    setting_grok_gateway(state, base_url, key, grok_model)


def setting_grok_gateway(state: State, base_url: str, key: str, model: str) -> None:
    if not ensure_entry(
        state,
        GROK_CONFIG,
        ["model", "proxy"],
        {
            "name": "CLIProxyAPI",
            "model": model,
            "base_url": base_url + "/v1",
            "api_key": key,
            "api_backend": "responses",
            "supports_backend_search": True,
        },
        "grok",
        create=True,
    ):
        return

    for purpose in ("default", "web_search", "session_summary", "image_description"):
        if not ensure_entry(
            state, GROK_CONFIG, ["models", purpose], "proxy", "grok", create=True
        ):
            return


def setting_pi_gateway(state: State, base_url: str, key: str) -> None:
    # Pi interprets $ references and leading ! commands in apiKey strings.
    pi_key = key.replace("$", "$$")
    if pi_key.startswith("!"):
        pi_key = "$" + pi_key
    for provider, desired in {
        "openai": {"baseUrl": base_url + "/v1", "apiKey": pi_key},
        "xai": {"baseUrl": base_url + "/v1", "apiKey": pi_key},
        "anthropic": {
            "baseUrl": base_url,
            "apiKey": pi_key,
            "authHeader": True,
            "headers": {"x-api-key": ""},
        },
    }.items():
        if not ensure_entry(
            state,
            PI_MODELS,
            ["providers", provider],
            desired,
            "pi",
            create=True,
        ):
            return

    if not ensure_pi_anthropic_plugin_absent(state):
        return

    # Stored credentials take precedence over the gateway keys in models.json.
    auth_exists = PI_AUTH.exists() or PI_AUTH.is_symlink()
    auth_is_empty = False
    if PI_AUTH.is_file():
        try:
            auth_is_empty = json.loads(PI_AUTH.read_text()) == {}
        except (OSError, ValueError):
            pass
    try:
        if auth_is_empty:
            ok(f"pi: {PI_AUTH} already contains an empty object")
        elif state.dry_run:
            action = "replace" if auth_exists else "create"
            would(f"pi: {action} {PI_AUTH} with an empty object (all saved provider credentials)")
        else:
            PI_AUTH.write_text("{}\n")
            if not WINDOWS:
                PI_AUTH.chmod(0o600)
            action = "cleared" if auth_exists else "created"
            fixed(f"pi: {action} {PI_AUTH} (all saved provider credentials)")
    except OSError:
        state.fail(f"pi: cannot clear {PI_AUTH}")


def ensure_pi_anthropic_plugin_absent(state: State) -> bool:
    if WINDOWS:
        info("pi: skipping pi.sh plugin check on Windows")
        return True

    plugin = "npm:pi-anthropic-oauth"
    binary = shutil.which("pi.sh")
    if binary is None:
        state.fail("pi: pi.sh is not on PATH; cannot check conflicting plugin")
        return False

    def run(*args: str) -> str:
        proc = subprocess.run(
            [binary, *args], capture_output=True, text=True, timeout=180
        )
        if proc.returncode != 0:
            raise RuntimeError(f"pi.sh {' '.join(args)} failed (exit {proc.returncode})")
        return proc.stdout

    def installed() -> bool:
        return plugin in {line.strip() for line in run("list").splitlines()}

    try:
        if not installed():
            ok(f"pi: {plugin} already absent")
            return True
        if state.dry_run:
            would(f"pi.sh uninstall {plugin}")
            return True
        run("uninstall", plugin)
        if installed():
            state.fail(f"pi: {plugin} still installed after uninstall")
            return False
    except RuntimeError as error:
        state.fail(str(error))
        return False
    except (OSError, subprocess.TimeoutExpired):
        state.fail("pi: package command could not complete")
        return False
    fixed(f"pi: uninstalled {plugin} (restart pi to unload)")
    return True


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
            # fff-mcp refuses to start in $HOME to avoid over-indexing, so run
            # the smoke test from the subvox checkout instead
            cwd=SUBVOX_ROOT,
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

    A marketplace name comes from its marketplace.json, so a fork keeps the
    upstream name. When the known marketplace points at a different repo (e.g.
    upstream instead of the fork), the plugin is uninstalled and the marketplace
    removed and re-added from `repo` before installing.
    """
    header(f"claude: plugin {plugin_id}")

    def known_marketplaces() -> dict[str, dict[str, Any]]:
        return {m["name"]: m for m in claude_json("plugin", "marketplace", "list")}

    def known_repos() -> dict[str, str]:
        return {name: m.get("repo", "") for name, m in known_marketplaces().items()}

    def marketplace_sha() -> str | None:
        """HEAD of the marketplace checkout, i.e. the commit an install would fetch."""
        location = known_marketplaces().get(marketplace, {}).get("installLocation")
        if not location:
            return None
        proc = subprocess.run(
            ["git", "-C", location, "rev-parse", "HEAD"], capture_output=True, text=True
        )
        return proc.stdout.strip() or None

    try:
        repos = known_repos()
    except (OSError, RuntimeError, json.JSONDecodeError, KeyError) as error:
        state.fail(f"cannot query claude marketplaces: {error}")
        return

    if marketplace in repos and repos[marketplace] != repo:
        stale = repos[marketplace]
        if state.dry_run:
            would(f"claude plugin uninstall {plugin_id} --scope user")
            would(f"claude plugin marketplace remove {marketplace}  # was {stale}")
            would(f"claude plugin marketplace add {repo}")
            would(f"claude plugin install {plugin_id} --scope user -y")
            return
        claude_run("plugin", "uninstall", plugin_id, "--scope", "user")
        claude_run("plugin", "marketplace", "remove", marketplace)
        repos = known_repos()
        if marketplace in repos:
            state.fail(f"marketplace {marketplace} ({stale}) still present after remove")
            return
        fixed(f"removed marketplace {marketplace} ({stale}) and its plugin")
    marketplaces = set(repos)

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

    def installed_sha() -> str | None:
        """`claude plugin list --json` omits the commit, so read the registry file."""
        try:
            entries = json.loads(CLAUDE_INSTALLED_PLUGINS.read_text())["plugins"][plugin_id]
        except (OSError, ValueError, KeyError):
            return None
        for entry in entries:
            if entry.get("scope") == "user":
                return entry.get("gitCommitSha")
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
        head, current = marketplace_sha(), installed_sha()
        if head and current and head != current:
            would(f"reinstall {plugin_id} (marketplace cache at {head[:12]}, installed {current[:12]})")
    else:
        before = plugin.get("version")
        claude_run("plugin", "update", plugin_id, "--scope", "user", "-y")
        plugin = installed() or plugin
        after = plugin.get("version")
        # `claude plugin update` only compares version strings, so a fork that
        # changes code without bumping plugin.json looks up to date. Compare the
        # installed commit against the refreshed marketplace checkout instead.
        head, current = marketplace_sha(), installed_sha()
        if after != before:
            fixed(f"updated {plugin_id} {before} -> {after} (restart claude to apply)")
        elif head and current and head != current:
            claude_run("plugin", "uninstall", plugin_id, "--scope", "user")
            claude_run("plugin", "install", plugin_id, "--scope", "user", "-y")
            plugin = installed()
            if plugin is None:
                state.fail(f"{plugin_id} missing after reinstall")
                return
            current = installed_sha()
            if current != head:
                state.fail(f"{plugin_id} still at {current} after reinstall, expected {head}")
                return
            fixed(f"reinstalled {plugin_id} at {head[:12]} (restart claude to apply)")
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


def setting_claude_agents_md(state: State) -> None:
    """Enable agents-md@builtin, a mod that ships inside Claude Code.
    Its option is read only from user, --settings, or managed settings, never a project's .claude/settings.json.
    claude-md-and-agents-md loads AGENTS.md beside CLAUDE.md and deduplicates @-imported files.
    The change applies at the next context build: new conversation, /clear, or compaction.
    The mod is behind the GrowthBook flag tengu_agents_md_mod (default off); GrowthBook is not fetched for gateway users, so the script seeds the flag in the disk cache ~/.claude.json.
    A future Claude Code release may drop the gate, at which point the seed is harmless.
    """
    header("claude: built-in agents-md mod")
    # built-in mods are gated on a GrowthBook flag; gateway users never fetch it, so seed the disk cache
    if not ensure_entry(
        state,
        CLAUDE_CONFIG,
        ["cachedGrowthBookFeatures", "tengu_agents_md_mod"],
        True,
        "claude",
        sensitive=True,
    ):
        return
    if not ensure_entry(
        state,
        CLAUDE_SETTINGS,
        ["enabledPlugins", "agents-md@builtin"],
        True,
        "claude",
        create=True,
    ):
        return
    ensure_entry(
        state,
        CLAUDE_SETTINGS,
        ["pluginConfigs", "agents-md@builtin", "options", "instructionFiles"],
        "claude-md-and-agents-md",
        "claude",
        create=True,
    )


def setting_skill_symlinks(state: State) -> None:
    """Link shared skills into Codex, Agents, and Claude skill directories.
    The helper links directories under ai/skills into each harness skill directory.
    The shell/PowerShell helper stays the single source of truth for the target list and skip rules.
    Dry-run mode passes through to the helper without creating directories or links.
    """
    header("skills: symlink shared skills into codex, agents, and claude")
    script = SKILLS_DIR / ("symlink-skills.ps1" if WINDOWS else "symlink-skills.sh")
    if not script.is_file():
        state.fail(f"skills: {script} is missing")
        return

    if WINDOWS:
        executable = shutil.which("pwsh") or shutil.which("powershell")
        if executable is None:
            state.fail("skills: pwsh or powershell not on PATH")
            return
        cmd = [executable, "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", str(script)]
        if state.dry_run:
            cmd.append("-DryRun")
    else:
        cmd = ["bash", str(script)]
        if state.dry_run:
            cmd.append("--dry-run")

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
    except (OSError, subprocess.TimeoutExpired) as error:
        state.fail(f"skills: cannot run {script.name}: {error}")
        return
    if result.returncode != 0:
        stderr = next((line.strip() for line in reversed(result.stderr.splitlines()) if line.strip()), "(no stderr)")
        state.fail(f"skills: {script.name} exited {result.returncode}: {stderr}")
        return

    target: str | None = None
    existing = 0
    missing_manifest: set[str] = set()
    for raw_line in result.stdout.splitlines():
        line = raw_line.rstrip()
        if not line:
            continue
        if line.startswith("== ") and line.endswith(" =="):
            if target is not None:
                ok(f"skills: {target}: {existing} already linked")
            target = line[3:-3]
            existing = 0
        elif line.startswith("linked: "):
            dest = line[len("linked: ") :].split(" -> ", 1)[0]
            fixed(f"skills: linked {dest}")
        elif line.startswith("would link: "):
            dest = line[len("would link: ") :].split(" -> ", 1)[0]
            would(f"skills: link {dest}")
        elif line.startswith("exists: "):
            dest = line[len("exists: ") :]
            existing += 1
            dest_path = Path(dest)
            expected = SKILLS_DIR / dest_path.name
            if not dest_path.exists():
                state.warn(f"skills: {dest} is a broken link")
            elif dest_path.resolve() != expected.resolve():
                state.warn(f"skills: {dest} points at {dest_path.resolve()}, not {expected}")
        elif line.startswith("skip (Claude subagent skill): "):
            path = line[len("skip (Claude subagent skill): ") :]
            skill_name = Path(path.rstrip("/\\")).name
            info(f"skills: skipped Claude subagent skill {skill_name} for {target}")
        elif line.startswith("skip (no SKILL.md): "):
            path = line[len("skip (no SKILL.md): ") :]
            # the helper reports this once per target; warn once per directory
            if path not in missing_manifest:
                missing_manifest.add(path)
                state.warn(f"skills: {path} has no SKILL.md")
        else:
            state.warn(f"skills: unexpected line from {script.name}: {line}")
    if target is not None:
        ok(f"skills: {target}: {existing} already linked")


SETTINGS: list[Callable[[State], None]] = [
    setting_fff_mcp_binary,
    setting_codex_model,
    setting_codex_fff_mcp,
    setting_claude_fff_mcp,
    setting_gateway,
    setting_claude_plugins,
    setting_claude_agents_md,
    setting_skill_symlinks,
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
