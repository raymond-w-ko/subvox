#!/usr/bin/env python3
"""Setup Claude settings by merging into existing settings.json."""

import json
import subprocess
import sys
from pathlib import Path

# =============================================================================
# User Home Settings (~/.claude/settings.json)
# =============================================================================
HOME_SETTINGS = {
    "env": {
        "ENABLE_TOOL_SEARCH": "true",
        "ANTHROPIC_DEFAULT_HAIKU_MODEL": "claude-sonnet-4-5-20250929",
    },
    "statusLine": {
        "type": "command",
        "command": "~/subvox/bin/claude-statusline.sh",
        "padding": 0,
    },
}

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


def setup_home_settings(settings_path: Path) -> None:
    """Setup minimal settings for user home directory."""
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

    merged = deep_merge(existing, HOME_SETTINGS)
    settings_path.write_text(json.dumps(merged, indent=2) + "\n")
    print(f"Wrote home settings to {settings_path}")


def has_bd_prime(settings: dict) -> bool:
    """Check if settings contain 'bd prime' in any hooks."""
    hooks = settings.get("hooks", {})
    for hook_list in hooks.values():
        for entry in hook_list:
            for hook in entry.get("hooks", []):
                if hook.get("command") == "bd prime":
                    return True
    return False


def setup_project_settings(settings_path: Path, target_dir: Path) -> None:
    """Setup full settings for project directory including hooks."""
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
        print(f"Setting up project directory settings ({settings_path})")
        setup_project_settings(settings_path, target_dir)


if __name__ == "__main__":
    main()
