#!/usr/bin/env python3
"""Setup global Claude settings by merging into existing ~/.claude/settings.json."""

import json
from pathlib import Path

# Hook entries to append (not replace)
PRE_COMPACT_HOOKS = [
    {"hooks": [{"command": "bd prime", "type": "command"}], "matcher": ""},
]

SESSION_START_HOOKS = [
    {"hooks": [{"command": "bd prime", "type": "command"}], "matcher": ""},
]


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


def get_desired_settings() -> dict:
    """Return the desired Claude settings (excluding hooks)."""
    return {
        "env": {
            "ENABLE_TOOL_SEARCH": "true",
        },
        "enabledPlugins": {},
        "statusLine": {
            "type": "command",
            "command": "~/subvox/bin/claude-statusline.sh",
            "padding": 0,
        },
    }


def main():
    settings_path = Path.home() / ".claude" / "settings.json"

    # Ensure .claude directory exists
    settings_path.parent.mkdir(parents=True, exist_ok=True)

    # Load existing settings if present
    existing = {}
    if settings_path.exists():
        try:
            existing = json.loads(settings_path.read_text())
            print(f"Loaded existing settings from {settings_path}")
        except json.JSONDecodeError as e:
            print(f"Warning: Could not parse existing settings: {e}")
            print("Starting with empty settings")

    # Merge desired settings into existing
    desired = get_desired_settings()
    merged = deep_merge(existing, desired)

    # Handle hooks separately - append to existing arrays
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

    # Write merged settings
    settings_path.write_text(json.dumps(merged, indent=2) + "\n")
    print(f"Wrote merged settings to {settings_path}")


if __name__ == "__main__":
    main()
