"""Claude/Codex config helpers for setup-ai.py."""

from __future__ import annotations

import json
from pathlib import Path
import re
import shutil
import subprocess

from codex_config_repair import parse_with_repair


HOME = Path.home()
BIN = HOME / "bin"
AGENT_MAIL_CONFIG_ENV = HOME / ".config" / "mcp-agent-mail" / "config.env"
MCP_AGENT_MAIL_URL = "http://127.0.0.1:8765/mcp/"
HTTP_BEARER_TOKEN_ENV_KEY = "HTTP_BEARER_TOKEN"
CLAUDE_MCP_AGENT_MAIL_NAME = "mcp_agent_mail"
CLAUDE_STALE_MCP_AGENT_MAIL_NAMES = ("agent-mail", "mcp-agent-mail")

HOME_SETTINGS = {
    "effortLevel": "high",
    "env": {
        "ANTHROPIC_DEFAULT_HAIKU_MODEL": "claude-sonnet-4-6",
        "ANTHROPIC_DEFAULT_SONNET_MODEL": "claude-sonnet-4-6",
        "CLAUDE_CODE_DISABLE_1M_CONTEXT": "1",
        "CLAUDE_CODE_DISABLE_ADAPTIVE_THINKING": "1",
        "CLAUDE_CODE_DISABLE_AUTO_MEMORY": "1",
        "CLAUDE_CODE_SUBAGENT_MODEL": "sonnet",
    },
    "statusLine": {"type": "command", "command": "~/subvox/bin/claude-statusline.sh", "padding": 0},
}
CODEX_SETTINGS_BASE = {
    "model": "gpt-5.5",
    "model_reasoning_effort": "high",
    "plan_mode_reasoning_effort": "xhigh",
    "model_context_window": 272_000,
    "tool_output_token_limit": 25_000,
    "model_auto_compact_token_limit": 232_000,
    "suppress_unstable_features_warning": True,
    "personality": "pragmatic",
    "web_search": "live",
    "service_tier": "fast",
    "features": {"unified_exec": True, "shell_snapshot": True, "multi_agent": True, "remote_connections": True},
    "tui": {
        "status_line": [
            "model-with-reasoning",
            "project-name",
            "git-branch",
            "pull-request-number",
            "branch-changes",
            "permissions",
            "task-progress",
            "run-state",
        ],
        "theme": "base16",
        "status_line_use_colors": True,
        "model_availability_nux": {"gpt-5.5": 4},
    },
}
PROJECT_SETTINGS = {}
PRE_COMPACT_HOOKS: list[dict] = []
SESSION_START_HOOKS: list[dict] = []
PRE_TOOL_USE_HOOKS = [{"hooks": [{"command": "dcg", "type": "command"}], "matcher": "Bash"}]
STALE_MCP_FILES = [".mcp.json", "cline.mcp.json", "codex.mcp.json", "windsurf.mcp.json", "cursor.mcp.json"]


def run(cmd: tuple[str, ...]) -> str:
    proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, check=False)
    if proc.returncode:
        raise RuntimeError(f"{' '.join(cmd)} exited {proc.returncode}\n{proc.stdout[-8000:].rstrip()}")
    return proc.stdout.strip()


def require_commands(names: tuple[str, ...]) -> None:
    missing = sorted(name for name in set(names) if shutil.which(name) is None)
    if missing:
        raise RuntimeError(f"missing required commands: {', '.join(missing)}")


def load_json(path: Path) -> dict:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text())
    except json.JSONDecodeError as exc:
        print(f"Warning: Could not parse {path}: {exc}")
        return {}


def agent_mail_has_bearer_token() -> bool:
    try:
        load_http_bearer_token()
        return True
    except RuntimeError:
        return False


def load_http_bearer_token() -> str:
    if not AGENT_MAIL_CONFIG_ENV.exists():
        raise RuntimeError(f"missing {AGENT_MAIL_CONFIG_ENV} with HTTP_BEARER_TOKEN")
    for raw_line in AGENT_MAIL_CONFIG_ENV.read_text().splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("export "):
            line = line[len("export ") :].strip()
        if not line.startswith(f"{HTTP_BEARER_TOKEN_ENV_KEY}="):
            continue
        value = line.split("=", 1)[1].strip().strip('"').strip("'")
        if value:
            return value
    raise RuntimeError(f"missing HTTP_BEARER_TOKEN in {AGENT_MAIL_CONFIG_ENV}")


def deep_merge(base: dict, override: dict) -> dict:
    result = base.copy()
    for key, value in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = deep_merge(result[key], value)
        else:
            result[key] = value
    return result


def fff_mcp_path() -> str:
    return str(HOME / "bin" / "fff-mcp")


def build_claude_json_settings(token: str) -> dict:
    return {
        "mcpServers": {
            CLAUDE_MCP_AGENT_MAIL_NAME: {
                "type": "http",
                "url": MCP_AGENT_MAIL_URL,
                "headers": {"Authorization": f"Bearer {token}"},
            },
            "fff": {"type": "stdio", "command": fff_mcp_path(), "args": [], "env": {}},
        }
    }


def build_claude_json_settings_without_agent_mail() -> dict:
    return {"mcpServers": {"fff": {"type": "stdio", "command": fff_mcp_path(), "args": [], "env": {}}}}


def build_codex_settings(token: str) -> dict:
    return deep_merge(
        CODEX_SETTINGS_BASE,
        {
            "mcp_servers": {
                "mcp_agent_mail": {
                    "url": MCP_AGENT_MAIL_URL,
                    "startup_timeout_sec": 30.0,
                    "http_headers": {"Authorization": f"Bearer {token}"},
                },
                "fff": {"command": fff_mcp_path()},
            }
        },
    )


def merge_codex_settings(existing: dict, token: str | None, disable_agent_mail: bool = False) -> dict:
    desired = (
        build_codex_settings(token)
        if token
        else deep_merge(CODEX_SETTINGS_BASE, {"mcp_servers": {"fff": {"command": fff_mcp_path()}}})
    )
    merged = deep_merge(existing, desired)
    mcp_servers = merged.setdefault("mcp_servers", {})
    if disable_agent_mail:
        mcp_servers.pop("mcp_agent_mail", None)
    elif token:
        mcp_servers["mcp_agent_mail"] = desired["mcp_servers"]["mcp_agent_mail"]
    mcp_servers["fff"] = desired["mcp_servers"]["fff"]
    return merged


def merge_claude_json_settings(existing: dict, token: str | None, disable_agent_mail: bool = False) -> dict:
    desired = build_claude_json_settings(token) if token else build_claude_json_settings_without_agent_mail()
    merged = deep_merge(existing, desired)
    mcp_servers = merged.setdefault("mcpServers", {})
    if disable_agent_mail:
        mcp_servers.pop(CLAUDE_MCP_AGENT_MAIL_NAME, None)
    elif token:
        mcp_servers[CLAUDE_MCP_AGENT_MAIL_NAME] = desired["mcpServers"][CLAUDE_MCP_AGENT_MAIL_NAME]
    mcp_servers["fff"] = desired["mcpServers"]["fff"]
    for stale in CLAUDE_STALE_MCP_AGENT_MAIL_NAMES:
        mcp_servers.pop(stale, None)
    return merged


def merge_claude_home_settings(existing: dict, disable_agent_mail: bool = False) -> dict:
    merged = deep_merge(existing, HOME_SETTINGS)
    if disable_agent_mail:
        merged.setdefault("mcpServers", {}).pop("mcp-agent-mail", None)
    return merged


def _toml_key(key: str) -> str:
    return key if re.match(r"^[A-Za-z0-9_-]+$", key) else json.dumps(key)


def _toml_value(value) -> str:
    if isinstance(value, bool):
        return str(value).lower()
    if isinstance(value, (int, float)):
        return repr(value)
    if isinstance(value, str):
        return json.dumps(value)
    if isinstance(value, list):
        return "[" + ", ".join(_toml_value(item) for item in value) + "]"
    raise ValueError(f"unsupported TOML value type: {type(value)}")


def _dict_to_toml_lines(data: dict, path: list[str]) -> list[str]:
    lines: list[str] = []
    scalars = [(k, v) for k, v in data.items() if not isinstance(v, dict)]
    tables = [(k, v) for k, v in data.items() if isinstance(v, dict)]
    if path and scalars:
        lines.append(f"\n[{'.'.join(_toml_key(part) for part in path)}]")
    lines.extend(f"{_toml_key(k)} = {_toml_value(v)}" for k, v in scalars)
    for key, value in tables:
        lines.extend(_dict_to_toml_lines(value, path + [key]))
    return lines


def dict_to_toml(data: dict) -> str:
    return "\n".join(_dict_to_toml_lines(data, [])) + "\n"


def codex_dict_to_toml(data: dict) -> str:
    data = dict(data)
    projects = data.pop("projects", {})
    content = dict_to_toml(data)
    return content + ("\n" + dict_to_toml({"projects": projects}) if projects else "")


def load_codex_config(config_path: Path) -> dict:
    content = config_path.read_text()
    data, repaired = parse_with_repair(content)
    if repaired != content:
        config_path.write_text(repaired)
        print(f"Repaired duplicate Codex declaration in {config_path}")
    return data


def repair_codex_config() -> None:
    config_path = HOME / ".codex" / "config.toml"
    if not config_path.exists():
        print(f"No Codex config found at {config_path}")
        return
    data, _ = parse_with_repair(config_path.read_text())
    config_path.write_text(codex_dict_to_toml(data))
    print(f"Parsed and rewrote Codex config at {config_path}")


def has_bd_prime(settings: dict) -> bool:
    for hook_list in settings.get("hooks", {}).values():
        for entry in hook_list:
            for hook in entry.get("hooks", []):
                if hook.get("command") == "bd prime":
                    return True
    return False


def append_hooks(existing: list, desired: list) -> list:
    result = list(existing)
    commands = {hook.get("command") for entry in existing for hook in entry.get("hooks", [])}
    for hook in desired:
        desired_commands = {item.get("command") for item in hook.get("hooks", [])}
        if not desired_commands & commands:
            result.append(hook)
    return result


def warn_bd_prime(settings: dict) -> None:
    if has_bd_prime(settings):
        print("\033[1;31mWARNING: Found 'bd prime'; migrate to beads_rust (br).\033[0m")


def setup_claude_json(token: str | None, disable_agent_mail: bool = False) -> None:
    path = HOME / ".claude.json"
    merged = merge_claude_json_settings(load_json(path), token, disable_agent_mail=disable_agent_mail)
    path.write_text(json.dumps(merged, indent=2) + "\n")
    print(f"Wrote config to {path}")


def setup_codex_config(token: str | None, disable_agent_mail: bool = False) -> None:
    path = HOME / ".codex" / "config.toml"
    path.parent.mkdir(parents=True, exist_ok=True)
    existing = load_codex_config(path) if path.exists() else {}
    merged = merge_codex_settings(existing, token, disable_agent_mail=disable_agent_mail)
    path.write_text(codex_dict_to_toml(merged))
    print(f"Wrote codex settings to {path}")


def setup_home_settings(disable_agent_mail: bool = False) -> None:
    token = None if disable_agent_mail else load_http_bearer_token()
    path = HOME / ".claude" / "settings.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    existing = load_json(path)
    warn_bd_prime(existing)
    merged = merge_claude_home_settings(existing, disable_agent_mail=disable_agent_mail)
    path.write_text(json.dumps(merged, indent=2) + "\n")
    print(f"Wrote home settings to {path}")
    setup_claude_json(token, disable_agent_mail=disable_agent_mail)
    setup_codex_config(token, disable_agent_mail=disable_agent_mail)


def setup_project_settings(target_dir: Path) -> None:
    for name in STALE_MCP_FILES:
        path = target_dir / name
        if path.exists():
            print(f"Stale MCP config present, left untouched: {path}")
    settings_path = target_dir / ".claude" / "settings.json"
    settings_path.parent.mkdir(parents=True, exist_ok=True)
    existing = load_json(settings_path)
    warn_bd_prime(existing)
    merged = deep_merge(existing, PROJECT_SETTINGS)
    existing_hooks = existing.get("hooks", {})
    merged["hooks"] = {
        **existing_hooks,
        "PreCompact": append_hooks(existing_hooks.get("PreCompact", []), PRE_COMPACT_HOOKS),
        "SessionStart": append_hooks(existing_hooks.get("SessionStart", []), SESSION_START_HOOKS),
    }
    if shutil.which("dcg") or (BIN / "dcg").exists():
        merged["hooks"]["PreToolUse"] = append_hooks(existing_hooks.get("PreToolUse", []), PRE_TOOL_USE_HOOKS)
    settings_path.write_text(json.dumps(merged, indent=2) + "\n")
    print(f"Wrote project settings to {settings_path}")


def setup_global_agent_configs(disable_agent_mail: bool = False) -> None:
    print("\033[1;36m>>> Writing Claude + Codex MCP config <<<\033[0m")
    repair_codex_config()
    if disable_agent_mail:
        print("MCP Agent Mail setup: disabled")
    elif agent_mail_has_bearer_token():
        print("MCP Agent Mail setup: skipping; bearer token exists")
    else:
        am = BIN / "am"
        am_cmd = str(am) if am.exists() else shutil.which("am")
        if not am_cmd:
            raise RuntimeError("missing am; cannot create MCP Agent Mail bearer token")
        run((am_cmd, "setup", "run", "--agent", "codex", "--project-dir", str(HOME), "--no-hooks", "-y"))
    setup_home_settings(disable_agent_mail=disable_agent_mail)


def create_template() -> None:
    require_commands(("claude",))
    prompt = """# Instructions

- read ~/src/mcp_agent_mail_rust/AGENTS.md
- extract the following major sections (a major section is usually denoted by --- and then ##):
  - the very first line: `# AGENTS.md — __PROJECT_NAME__`
  - RULE 0
  - RULE NUMBER 1
  - Irreversible Git & Filesystem Actions — DO NOT EVER BREAK GLASS
  - Third-Party Library Usage
- write to ~/subvox/ai/AGENTS.template.md in the above order. 
"""
    run(("claude", "--print", "--dangerously-skip-permissions", prompt))
