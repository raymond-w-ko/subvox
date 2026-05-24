"""Surgical repair helpers for Codex TOML config."""

from __future__ import annotations

import re
import tomllib


TABLE_RE = re.compile(r"^\s*\[([^\[\]\n]+)\]\s*(?:#.*)?$")
KEY_VALUE_RE = re.compile(r"^\s*([^=\s][^=]*?)\s*=")
DUPLICATE_DECL_RE = re.compile(r"Cannot declare \(([^)]+)\) twice")
MAX_REPAIR_ITERATIONS = 16


def _dotted_path(path_repr: str) -> list[str]:
    return [part.strip().strip("'\"") for part in path_repr.split(",") if part.strip()]


def repair_duplicate_declaration(content: str, error_message: str) -> str | None:
    """Detect a ``Cannot declare (...) twice`` TOML error and drop the inline duplicate.

    Triggered by configs such as::

        [mcp_servers.mcp_agent_mail]
        http_headers = { Authorization = "Bearer …" }
        [mcp_servers.mcp_agent_mail.http_headers]
        Authorization = "Bearer …"

    The inline assignment is removed; the dedicated table is preserved.
    Returns ``None`` if the error does not match this pattern or both
    declarations cannot be located.
    """
    match = DUPLICATE_DECL_RE.search(error_message)
    if not match:
        return None

    parts = _dotted_path(match.group(1))
    if len(parts) < 2:
        return None

    full_table = ".".join(parts)
    parent_table = ".".join(parts[:-1])
    key = parts[-1]

    lines = content.splitlines()
    inline_idx: int | None = None
    table_idx: int | None = None
    current_table = ""

    for i, line in enumerate(lines):
        table_match = TABLE_RE.match(line)
        if table_match:
            current_table = table_match.group(1).strip()
            if current_table == full_table and table_idx is None:
                table_idx = i
            continue
        if current_table == parent_table and inline_idx is None:
            kv_match = KEY_VALUE_RE.match(line)
            if kv_match and kv_match.group(1).strip() == key:
                inline_idx = i

    if inline_idx is None or table_idx is None:
        return None

    del lines[inline_idx]
    trailing = "\n" if content.endswith("\n") else ""
    return "\n".join(lines) + trailing


def parse_with_repair(content: str) -> tuple[dict, str]:
    """Parse Codex TOML, surgically removing inline/table duplicates as needed.

    Returns ``(data, repaired_content)``. Re-raises the original TOML error if
    the configuration cannot be repaired heuristically.
    """
    repaired = content
    for _ in range(MAX_REPAIR_ITERATIONS):
        try:
            return tomllib.loads(repaired), repaired
        except tomllib.TOMLDecodeError as exc:
            attempt = repair_duplicate_declaration(repaired, str(exc))
            if attempt is None or attempt == repaired:
                raise
            repaired = attempt
    raise RuntimeError("codex config repair exceeded iteration limit")
