#!/usr/bin/env bash
set -euo pipefail

script_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
claude_skills_dir="$HOME/.claude/skills"

# Target skill directories for each harness. ~/.agents/skills is the universal
# location (pi and other Agent Skills harnesses read it); ~/.codex/skills and
# ~/.claude/skills are harness-specific.
targets=(
  "${CODEX_HOME:-$HOME/.codex}/skills"
  "$HOME/.agents/skills"
  "$claude_skills_dir"
)

link_into() {
  local skills_dir="$1"
  mkdir -p "$skills_dir"

  for skill_path in "$script_dir"/*/; do
    [[ -d "$skill_path" ]] || continue
    [[ -f "${skill_path}SKILL.md" ]] || { printf 'skip (no SKILL.md): %s\n' "$skill_path"; continue; }

    skill_name="$(basename -- "$skill_path")"

    # Do not expose Claude-spawning subagent skills inside Claude itself.
    if [[ "$skills_dir" == "$claude_skills_dir" &&
      ( "$skill_name" == "claude-subagent" || "$skill_name" == "fable-subagent" ) ]]; then
      printf 'skip (Claude subagent skill): %s\n' "$skill_path"
      continue
    fi

    dest="$skills_dir/$skill_name"

    if [[ -e "$dest" || -L "$dest" ]]; then
      printf 'exists: %s\n' "$dest"
      continue
    fi

    ln -s "$skill_path" "$dest"
    printf 'linked: %s -> %s\n' "$dest" "$skill_path"
  done
}

for target in "${targets[@]}"; do
  printf '\n== %s ==\n' "$target"
  link_into "$target"
done
