#!/usr/bin/env python3
"""Setup Claude and Codex agent settings."""

import json
import re
import sys
from pathlib import Path

# =============================================================================
# User Home Settings (~/.claude/settings.json)
# =============================================================================
HOME_SETTINGS = {
    "env": {
        "ANTHROPIC_DEFAULT_HAIKU_MODEL": "claude-sonnet-4-6[1m]",
        "ANTHROPIC_DEFAULT_SONNET_MODEL": "claude-sonnet-4-6[1m]",
    },
    "statusLine": {
        "type": "command",
        "command": "~/subvox/bin/claude-statusline.sh",
        "padding": 0,
    },
}

# =============================================================================
# Shared MCP config
# =============================================================================
MCP_AGENT_MAIL_URL = "http://127.0.0.1:8765/mcp/"
HTTP_BEARER_TOKEN_ENV_KEY = "HTTP_BEARER_TOKEN"
CLAUDE_MCP_AGENT_MAIL_NAME = "mcp_agent_mail"
CLAUDE_STALE_MCP_AGENT_MAIL_NAMES = ("agent-mail", "mcp-agent-mail")

# =============================================================================
# Project Directory Settings (<project>/.claude/settings.json)
# =============================================================================
PROJECT_SETTINGS = {}

# Hook entries for project directories (not user home)
PRE_COMPACT_HOOKS = []

SESSION_START_HOOKS = []

PRE_TOOL_USE_HOOKS = [
    {"hooks": [{"command": "dcg", "type": "command"}], "matcher": "Bash"},
]


def fff_mcp_path() -> str:
    """Return the absolute path to the local fff-mcp binary."""
    return str(Path.home() / "bin" / "fff-mcp")


def load_http_bearer_token() -> str:
    """Load the MCP Agent Mail bearer token from ~/.config/mcp-agent-mail/config.env."""
    env_path = Path.home() / ".config" / "mcp-agent-mail" / "config.env"
    if not env_path.exists():
        raise RuntimeError(
            f"Missing {env_path} with HTTP_BEARER_TOKEN. "
            "Make sure `am` has been run at least once."
        )

    for raw_line in env_path.read_text().splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("export "):
            line = line[len("export ") :].strip()
        if not line.startswith(f"{HTTP_BEARER_TOKEN_ENV_KEY}="):
            continue

        _, value = line.split("=", 1)
        value = value.strip().strip('"').strip("'")
        if value:
            return value
        break

    raise RuntimeError(
        f"Missing HTTP_BEARER_TOKEN in {env_path}. "
        "Make sure `am` has been run at least once."
    )


def dcg_exists() -> bool:
    """Check if dcg command exists in PATH or at ~/bin/dcg."""
    import shutil
    if shutil.which("dcg"):
        return True
    return (Path.home() / "bin" / "dcg").exists()


def deep_merge(base: dict, override: dict) -> dict:
    """Deep merge override into base, returning a new dict."""
    result = base.copy()
    for key, value in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = deep_merge(result[key], value)
        else:
            result[key] = value
    return result


def get_hook_commands(hook_entry: dict) -> set:
    """Extract command strings from a hook entry."""
    return {h.get("command") for h in hook_entry.get("hooks", [])}


def append_hooks(existing: list, desired: list) -> list:
    """Append desired hooks to existing, avoiding duplicates by command."""
    result = list(existing)
    existing_commands = set()
    for entry in existing:
        existing_commands.update(get_hook_commands(entry))

    for hook in desired:
        hook_commands = get_hook_commands(hook)
        if not hook_commands & existing_commands:
            result.append(hook)
    return result


def build_claude_json_settings(http_bearer_token: str) -> dict:
    """Build ~/.claude.json MCP server entries."""
    return {
        "mcpServers": {
            CLAUDE_MCP_AGENT_MAIL_NAME: {
                "type": "http",
                "url": MCP_AGENT_MAIL_URL,
                "headers": {
                    "Authorization": f"Bearer {http_bearer_token}",
                },
            },
            "fff": {
                "type": "stdio",
                "command": fff_mcp_path(),
                "args": [],
                "env": {},
            },
        },
    }


def setup_claude_json(http_bearer_token: str) -> None:
    """Merge Claude MCP settings into ~/.claude.json."""
    claude_json_path = Path.home() / ".claude.json"

    existing = {}
    if claude_json_path.exists():
        try:
            existing = json.loads(claude_json_path.read_text())
            print(f"Loaded existing config from {claude_json_path}")
        except json.JSONDecodeError as e:
            print(f"Warning: Could not parse existing config: {e}")
            print("Starting with empty config")

    desired_settings = build_claude_json_settings(http_bearer_token)
    merged = deep_merge(existing, desired_settings)

    mcp = merged.get("mcpServers", {})
    desired_mcp = desired_settings["mcpServers"]
    mcp[CLAUDE_MCP_AGENT_MAIL_NAME] = desired_mcp[CLAUDE_MCP_AGENT_MAIL_NAME]
    mcp["fff"] = desired_mcp["fff"]
    for stale_name in CLAUDE_STALE_MCP_AGENT_MAIL_NAMES:
        if stale_name in mcp:
            del mcp[stale_name]
            print(f"Removed stale '{stale_name}' from mcpServers")

    claude_json_path.write_text(json.dumps(merged, indent=2) + "\n")
    print(f"Wrote config to {claude_json_path}")


def setup_home_settings(settings_path: Path) -> None:
    """Setup ~/.claude/settings.json + ~/.claude.json + ~/.codex/config.toml."""
    http_bearer_token = load_http_bearer_token()
    settings_path.parent.mkdir(parents=True, exist_ok=True)

    existing = {}
    if settings_path.exists():
        try:
            existing = json.loads(settings_path.read_text())
            print(f"Loaded existing settings from {settings_path}")
        except json.JSONDecodeError as e:
            print(f"Warning: Could not parse existing settings: {e}")
            print("Starting with empty settings")

    if has_bd_prime(existing):
        print("\033[1;31mWARNING: Found 'bd prime' in existing hooks.\033[0m")
        print("\033[1;31m'bd' (beads) is deprecated. Please migrate to beads_rust (br).\033[0m")
        print("\033[1;31mSee: https://github.com/Dicklesworthstone/beads_rust\033[0m")

    merged = deep_merge(existing, HOME_SETTINGS)

    settings_path.write_text(json.dumps(merged, indent=2) + "\n")
    print(f"Wrote home settings to {settings_path}")

    setup_claude_json(http_bearer_token)
    setup_codex_config(http_bearer_token)


# =============================================================================
# Codex CLI Settings (~/.codex/config.toml)
# =============================================================================
# 5.4 supports 1M but starts to get bad around 272k tokens, which is the same for 5.3 codex
CODEX_SETTINGS_BASE = {
    "model": "gpt-5.4",
    "model_reasoning_effort": "xhigh",
    "plan_mode_reasoning_effort": "xhigh",
    "model_context_window": 272_000,
    "tool_output_token_limit": 25_000,
    # Formula: 272000 - (tool_output_token_limit + 15000)
    # With tool_output_token_limit=25000 ⇒ 272000 - (25000 + 15000) = 232000
    "model_auto_compact_token_limit": 232_000,
    "suppress_unstable_features_warning": True,
    "personality": "pragmatic",
    "web_search": "live",
    "features": {
        "unified_exec": True,
        "shell_snapshot": True,
        "multi_agent": True,
    },
    "tui": {
        "status_line": [
            "model-with-reasoning",
            "current-dir",
            "project-root",
            "git-branch",
            "context-remaining",
            "context-window-size",
        ],
        "theme": "base16",
    },
}


def build_codex_settings(http_bearer_token: str) -> dict:
    """Build ~/.codex/config.toml settings."""
    return deep_merge(
        CODEX_SETTINGS_BASE,
        {
            "mcp_servers": {
                "mcp_agent_mail": {
                    "url": MCP_AGENT_MAIL_URL,
                    "startup_timeout_sec": 30.0,
                    "http_headers": {
                        "Authorization": f"Bearer {http_bearer_token}",
                    },
                },
                "fff": {
                    "command": fff_mcp_path(),
                },
            },
        },
    )


def _toml_key(key: str) -> str:
    """Quote a TOML key if it contains non-bare characters."""
    if re.match(r"^[A-Za-z0-9_-]+$", key):
        return key
    return f'"{key}"'


def _toml_value(value) -> str:
    """Serialize a Python value to a TOML value string."""
    if isinstance(value, bool):
        return str(value).lower()
    if isinstance(value, float):
        # Use repr to avoid trailing zeros; TOML requires decimal point
        s = repr(value)
        return s if "." in s else s + ".0"
    if isinstance(value, int):
        return str(value)
    if isinstance(value, str):
        return f'"{value}"'
    if isinstance(value, list):
        items = ", ".join(_toml_value(v) for v in value)
        return f"[{items}]"
    raise ValueError(f"Unsupported TOML value type: {type(value)}")


def _dict_to_toml_lines(data: dict, path: list) -> list:
    """Recursively convert a dict to TOML lines."""
    lines = []
    scalars = [(k, v) for k, v in data.items() if not isinstance(v, dict)]
    tables = [(k, v) for k, v in data.items() if isinstance(v, dict)]

    if path and scalars:
        section = ".".join(_toml_key(p) for p in path)
        lines.append(f"\n[{section}]")

    for k, v in scalars:
        lines.append(f"{_toml_key(k)} = {_toml_value(v)}")

    for k, v in tables:
        lines.extend(_dict_to_toml_lines(v, path + [k]))

    return lines


def dict_to_toml(data: dict) -> str:
    """Convert a dict to a TOML string."""
    lines = _dict_to_toml_lines(data, [])
    return "\n".join(lines) + "\n"


def _extract_project_sections(content: str) -> str:
    """Extract [projects.*] sections from existing TOML content."""
    lines = content.splitlines(keepends=True)
    project_lines = []
    in_project = False
    for line in lines:
        stripped = line.strip()
        if stripped.startswith("[projects."):
            in_project = True
            project_lines.append(line)
        elif stripped.startswith("[") and not stripped.startswith("[projects."):
            in_project = False
        elif in_project:
            project_lines.append(line)
    return "".join(project_lines)


def setup_codex_config(http_bearer_token: str) -> None:
    """Deep-merge Codex settings into ~/.codex/config.toml, preserving existing keys."""
    import tomllib

    config_path = Path.home() / ".codex" / "config.toml"
    config_path.parent.mkdir(parents=True, exist_ok=True)

    existing = {}
    if config_path.exists():
        try:
            existing = tomllib.loads(config_path.read_text())
            print(f"Loaded existing codex config from {config_path}")
        except Exception as e:
            print(f"Warning: Could not parse existing codex config: {e}")

    desired_settings = build_codex_settings(http_bearer_token)
    merged = deep_merge(existing, desired_settings)
    desired_mcp = desired_settings["mcp_servers"]
    merged.setdefault("mcp_servers", {})
    merged["mcp_servers"]["mcp_agent_mail"] = desired_mcp["mcp_agent_mail"]
    merged["mcp_servers"]["fff"] = desired_mcp["fff"]

    # Serialize: projects go last for readability
    projects = merged.pop("projects", {})
    content = dict_to_toml(merged)
    if projects:
        content += "\n" + dict_to_toml({"projects": projects})

    config_path.write_text(content)
    print(f"Wrote codex settings to {config_path}")


def has_bd_prime(settings: dict) -> bool:
    """Check if settings contain 'bd prime' in any hooks."""
    hooks = settings.get("hooks", {})
    for hook_list in hooks.values():
        for entry in hook_list:
            for hook in entry.get("hooks", []):
                if hook.get("command") == "bd prime":
                    return True
    return False


STALE_MCP_FILES = [
    ".mcp.json",
    "cline.mcp.json",
    "codex.mcp.json",
    "windsurf.mcp.json",
    "cursor.mcp.json",
]


def cleanup_stale_mcp_files(target_dir: Path) -> None:
    """Interactively delete stale MCP config files from the project directory."""
    for name in STALE_MCP_FILES:
        path = target_dir / name
        if not path.exists():
            continue
        answer = input(f"Delete stale MCP config {path}? [y/N] ").strip().lower()
        if answer == "y":
            path.unlink()
            print(f"  Deleted {path}")
        else:
            print(f"  Skipped {path}")


def setup_project_settings(settings_path: Path, target_dir: Path) -> None:
    """Setup full settings for project directory including hooks."""
    cleanup_stale_mcp_files(target_dir)

    # MCP Agent Mail integration disabled for now
    # integrate_script = Path.home() / "src" / "mcp_agent_mail" / "scripts" / "automatically_detect_all_installed_coding_agents_and_install_mcp_agent_mail_in_all.sh"
    # if integrate_script.exists():
    #     print("Running MCP Agent Mail integration script...")
    #     subprocess.run(["bash", str(integrate_script), "--project-dir", str(target_dir)], check=False)
    # else:
    #     print(f"Note: MCP Agent Mail integration script not found at {integrate_script}")

    settings_path.parent.mkdir(parents=True, exist_ok=True)

    existing = {}
    if settings_path.exists():
        try:
            existing = json.loads(settings_path.read_text())
            print(f"Loaded existing settings from {settings_path}")
        except json.JSONDecodeError as e:
            print(f"Warning: Could not parse existing settings: {e}")
            print("Starting with empty settings")

    # Warn about deprecated bd prime usage
    if has_bd_prime(existing):
        print("\033[1;31mWARNING: Found 'bd prime' in existing hooks.\033[0m")
        print("\033[1;31m'bd' (beads) is deprecated. Please migrate to beads_rust (br).\033[0m")
        print("\033[1;31mSee: https://github.com/Dicklesworthstone/beads_rust\033[0m")

    merged = deep_merge(existing, PROJECT_SETTINGS)

    # Handle hooks - append to existing arrays
    existing_hooks = existing.get("hooks", {})
    merged["hooks"] = {
        **existing_hooks,
        "PreCompact": append_hooks(
            existing_hooks.get("PreCompact", []), PRE_COMPACT_HOOKS
        ),
        "SessionStart": append_hooks(
            existing_hooks.get("SessionStart", []), SESSION_START_HOOKS
        ),
    }

    # Conditionally add PreToolUse hooks if dcg exists
    if dcg_exists():
        merged["hooks"]["PreToolUse"] = append_hooks(
            existing_hooks.get("PreToolUse", []), PRE_TOOL_USE_HOOKS
        )

    settings_path.write_text(json.dumps(merged, indent=2) + "\n")
    print(f"Wrote project settings to {settings_path}")


def main():
    # Parse optional directory argument
    if len(sys.argv) > 1:
        target_dir = Path(sys.argv[1]).resolve()
    else:
        target_dir = Path.home()

    settings_path = target_dir / ".claude" / "settings.json"
    is_home = target_dir == Path.home()

    if is_home:
        print(f"Setting up home directory settings ({settings_path})")
        setup_home_settings(settings_path)
    else:
        settings_path = target_dir / ".claude" / "settings.json"
        print(f"Setting up project directory settings ({settings_path})")
        setup_project_settings(settings_path, target_dir)


if __name__ == "__main__":
    try:
        main()
    except RuntimeError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
