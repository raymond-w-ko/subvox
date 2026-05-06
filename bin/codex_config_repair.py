"""Repair helpers for Codex TOML config."""

from collections import Counter, OrderedDict
import re


TABLE_RE = re.compile(r"^\s*\[([^\[\]\n]+)\]\s*(?:#.*)?$")
KEY_VALUE_RE = re.compile(r"^\s*([^=\s][^=]*?)\s*=")


def _table_name(line: str) -> str | None:
    match = TABLE_RE.match(line)
    if not match:
        return None
    return match.group(1).strip()


def _is_http_headers_table(name: str | None) -> bool:
    return bool(name and name.endswith(".http_headers"))


def _split_sections(content: str) -> list[dict]:
    sections = []
    current = {"name": None, "header": None, "body": []}

    for line in content.splitlines():
        name = _table_name(line)
        if name is not None:
            sections.append(current)
            current = {"name": name, "header": line.strip(), "body": []}
        else:
            current["body"].append(line)

    sections.append(current)
    return sections


def collapse_duplicate_http_headers(content: str) -> str:
    """Collapse duplicate *.http_headers TOML tables, keeping the last key value."""
    sections = _split_sections(content)
    counts = Counter(
        section["name"]
        for section in sections
        if _is_http_headers_table(section["name"])
    )
    duplicate_names = {name for name, count in counts.items() if count > 1}
    if not duplicate_names:
        return content

    merged = {name: OrderedDict() for name in duplicate_names}
    for section in sections:
        name = section["name"]
        if name not in duplicate_names:
            continue

        for line in section["body"]:
            stripped = line.strip()
            if not stripped or stripped.startswith("#"):
                continue

            match = KEY_VALUE_RE.match(line)
            if not match:
                continue

            key = match.group(1).strip()
            merged[name][key] = stripped

    emitted = set()
    output = []
    for section in sections:
        name = section["name"]
        if name is None:
            output.extend(section["body"])
            continue

        if name in duplicate_names:
            if name in emitted:
                continue
            emitted.add(name)
            output.append(f"[{name}]")
            output.extend(merged[name].values())
            continue

        output.append(section["header"])
        output.extend(section["body"])

    trailing_newline = "\n" if content.endswith("\n") else ""
    return "\n".join(output).rstrip("\n") + trailing_newline
