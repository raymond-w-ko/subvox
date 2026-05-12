#!/usr/bin/env bash
set -euo pipefail

script_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
skills_dir="${CODEX_HOME:-$HOME/.codex}/skills"

mkdir -p "$skills_dir"

for skill_path in "$script_dir"/*/; do
  [[ -d "$skill_path" ]] || continue

  skill_name="$(basename -- "$skill_path")"
  dest="$skills_dir/$skill_name"

  if [[ -e "$dest" || -L "$dest" ]]; then
    printf 'exists: %s\n' "$dest"
    continue
  fi

  ln -s "$skill_path" "$dest"
  printf 'linked: %s -> %s\n' "$dest" "$skill_path"
done
