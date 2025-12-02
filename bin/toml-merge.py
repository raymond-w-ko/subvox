#!/usr/bin/env -S uv run --script
#
# /// script
# requires-python = ">=3.14"
# dependencies = ["tomlkit"]
# ///
#!/usr/bin/env python3
"""
merge two TOML files with template precedence.

usage:
    merge_toml.py base.toml template.toml [output.toml]

semantics:
    - parse base.toml and template.toml with tomlkit
    - perform a deep merge where:
        merged = deep_merge(base, template)
      so values from template override values from base
      at all levels for tables/maps.
    - for non-mapping values (scalars, arrays, etc.), the
      template value completely replaces the base value.
    - comments and formatting are preserved as far as tomlkit allows.
"""

import sys
from collections.abc import MutableMapping

try:
    from tomlkit import parse, dumps
except ImportError:
    sys.stderr.write("error: tomlkit is required. install with `pip install tomlkit`.\n")
    sys.exit(1)


def deep_merge(base, override):
    """
    recursively merge two mapping-like TOML structures.

    rules:
        - if both base[key] and override[key] are mappings, merge them recursively.
        - otherwise, override[key] replaces base[key].
        - keys only in override are added.
        - keys only in base are kept.
    """
    if not isinstance(base, MutableMapping) or not isinstance(override, MutableMapping):
        # if either side is not a mapping (table/document), override wins
        return override

    # mutate base in place to preserve tomlkit node types/metadata
    for key, override_val in override.items():
        if key in base:
            base_val = base[key]
            if isinstance(base_val, MutableMapping) and isinstance(override_val, MutableMapping):
                base[key] = deep_merge(base_val, override_val)
            else:
                base[key] = override_val
        else:
            base[key] = override_val
    return base


def main(argv=None):
    if argv is None:
        argv = sys.argv[1:]

    if not (2 <= len(argv) <= 3):
        sys.stderr.write(
            "usage: merge_toml.py base.toml template.toml [output.toml]\n"
            "note: template values take precedence over base values.\n"
        )
        return 1

    base_path = argv[0]
    template_path = argv[1]
    output_path = argv[2] if len(argv) == 3 else None

    try:
        with open(base_path, "r", encoding="utf-8") as f:
            base_doc = parse(f.read())
    except OSError as e:
        sys.stderr.write(f"error: cannot read base file '{base_path}': {e}\n")
        return 1

    try:
        with open(template_path, "r", encoding="utf-8") as f:
            template_doc = parse(f.read())
    except OSError as e:
        sys.stderr.write(f"error: cannot read template file '{template_path}': {e}\n")
        return 1

    merged = deep_merge(base_doc, template_doc)
    output_toml = dumps(merged)

    if output_path:
        try:
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(output_toml)
        except OSError as e:
            sys.stderr.write(f"error: cannot write output file '{output_path}': {e}\n")
            return 1
    else:
        sys.stdout.write(output_toml)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

