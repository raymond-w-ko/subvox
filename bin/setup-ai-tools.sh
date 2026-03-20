#!/usr/bin/env -S bash -eu

SKIP_EXISTING=false

section() {
  echo -e "\033[1;36m>>> $1 <<<\033[0m"
}

skip_if_exists() {
  local binary="$1"
  if [[ "$SKIP_EXISTING" == true ]] && [[ -f "$HOME/bin/$binary" ]]; then
    section "$binary: skipping (already exists)"
    return 0
  fi
  return 1
}

check_dependencies() {
  local missing=()

  command -v go &>/dev/null || missing+=("go")
  command -v cargo &>/dev/null || missing+=("cargo")
  command -v make &>/dev/null || missing+=("make")
  command -v uv &>/dev/null || missing+=("uv")

  if [[ ${#missing[@]} -gt 0 ]]; then
    echo "Error: missing required commands: ${missing[*]}" >&2
    exit 1
  fi
}

ensure_repo() {
  local src_dir="$1"
  local repo_url="$2"

  if [[ ! -d "$src_dir" ]]; then
    git clone "$repo_url" "$src_dir"
  else
    local current_url
    current_url=$(git -C "$src_dir" remote get-url origin 2>/dev/null || true)
    if [[ "$current_url" != "$repo_url" ]]; then
      git -C "$src_dir" remote set-url origin "$repo_url"
    fi
  fi
}

ensure_upstream() {
  local src_dir="$1"
  local upstream_url="$2"

  if git -C "$src_dir" remote get-url upstream &>/dev/null; then
    git -C "$src_dir" remote set-url upstream "$upstream_url"
  else
    git -C "$src_dir" remote add upstream "$upstream_url"
  fi
}

###############################################################################
# libraries only, no real executables
###############################################################################

build_asupersync() {
  local src_dir="$HOME/src/asupersync"
  local repo_url="https://github.com/Dicklesworthstone/asupersync.git"

  section "Updating $src_dir"
  ensure_repo "$src_dir" "$repo_url"
  git -C "$src_dir" pull
  git -C "$src_dir" restore Cargo.toml
  git -C "$src_dir" clean -fxd
}

build_frankensqlite() {
  local src_dir="$HOME/src/frankensqlite"
  local repo_url="https://github.com/Dicklesworthstone/frankensqlite.git"

  section "Updating $src_dir"
  ensure_repo "$src_dir" "$repo_url"
  git -C "$src_dir" pull
  git -C "$src_dir" restore Cargo.toml
  git -C "$src_dir" clean -fxd
}

build_frankensearch() {
  local src_dir="$HOME/src/frankensearch"
  local repo_url="https://github.com/Dicklesworthstone/frankensearch.git"

  section "Updating $src_dir"
  ensure_repo "$src_dir" "$repo_url"
  git -C "$src_dir" pull
  git -C "$src_dir" restore Cargo.toml
  git -C "$src_dir" clean -fxd
}

build_frankentui() {
  local src_dir="$HOME/src/frankentui"
  local repo_url="https://github.com/Dicklesworthstone/frankentui.git"

  section "Updating $src_dir"
  ensure_repo "$src_dir" "$repo_url"
  git -C "$src_dir" pull
  git -C "$src_dir" restore Cargo.toml
  git -C "$src_dir" clean -fxd
}

build_sqlmodel_rust() {
  local src_dir="$HOME/src/sqlmodel_rust"
  local repo_url="https://github.com/Dicklesworthstone/sqlmodel_rust.git"

  section "Updating $src_dir"
  ensure_repo "$src_dir" "$repo_url"
  git -C "$src_dir" pull
  git -C "$src_dir" restore Cargo.toml
  git -C "$src_dir" clean -fxd
}

build_tru() {
  local src_dir="$HOME/src/toon_rust"
  local binary="tru"
  local repo_url="https://github.com/Dicklesworthstone/toon_rust.git"

  skip_if_exists "$binary" && return
  section "Building $binary"
  ensure_repo "$src_dir" "$repo_url"
  pkill -x "$binary" || true
  git -C "$src_dir" fetch --all
  git -C "$src_dir" checkout main
  git -C "$src_dir" pull
  (cd "$src_dir" && cargo build --release)
  cp "$src_dir/target/release/$binary" "$HOME/bin/$binary"
}

build_dcg() {
  local src_dir="$HOME/src/destructive_command_guard"
  local binary="dcg"
  local repo_url="https://github.com/Dicklesworthstone/destructive_command_guard.git"

  skip_if_exists "$binary" && return
  section "Building $binary"
  ensure_repo "$src_dir" "$repo_url"
  pkill -x "$binary" || true
  git -C "$src_dir" pull
  (cd "$src_dir" && cargo build --release)
  cp "$src_dir/target/release/$binary" "$HOME/bin/$binary"
}

build_bd() {
  local src_dir="$HOME/src/beads"
  local binary="bd"
  local repo_url="https://github.com/steveyegge/beads.git"

  skip_if_exists "$binary" && return
  section "Building $binary"
  ensure_repo "$src_dir" "$repo_url"
  pkill -x "$binary" || true
  git -C "$src_dir" pull
  make -C "$src_dir" build
  cp "$src_dir/$binary" "$HOME/bin/$binary"
}

build_br() {
  local src_dir="$HOME/src/beads_rust"
  local binary="br"
  local repo_url="https://github.com/Dicklesworthstone/beads_rust.git"

  skip_if_exists "$binary" && return
  section "Building $binary"
  ensure_repo "$src_dir" "$repo_url"
  pkill -x "$binary" || true
  git -C "$src_dir" restore Cargo.lock
  git -C "$src_dir" switch main
  git -C "$src_dir" pull
  (cd "$src_dir" && cargo build --release)
  cp "$src_dir/target/release/$binary" "$HOME/bin/$binary"
}

build_bv() {
  local src_dir="$HOME/src/beads_viewer"
  local binary="bv"
  local repo_url="git@github.com:raymond-w-ko/beads_viewer.git"
  local upstream_url="https://github.com/Dicklesworthstone/beads_viewer.git"

  skip_if_exists "$binary" && return
  section "Building $binary"
  ensure_repo "$src_dir" "$repo_url"
  ensure_upstream "$src_dir" "$upstream_url"
  git -C "$src_dir" fetch upstream
  git -C "$src_dir" switch main
  git -C "$src_dir" merge upstream/main
  # git -C "$src_dir" push
  make -C "$src_dir" build
  cp "$src_dir/$binary" "$HOME/bin/$binary"
}

build_mcp_agent_mail_rust() {
  local src_dir="$HOME/src/mcp_agent_mail_rust"
  local binary1="am"
  local binary2="mcp-agent-mail"
  local repo_url="https://github.com/Dicklesworthstone/mcp_agent_mail_rust.git"

  skip_if_exists "$binary2" && return
  section "Building $binary1 + $binary2"
  ensure_repo "$src_dir" "$repo_url"
  git -C "$src_dir" restore Cargo.lock
  git -C "$src_dir" switch main
  git -C "$src_dir" pull
  (cd "$src_dir" && cargo build --release)
  cp "$src_dir/target/release/$binary1" "$HOME/bin/$binary1"
  cp "$src_dir/target/release/$binary2" "$HOME/bin/$binary2"
}


build_gt() {
  local src_dir="$HOME/src/gastown"
  local binary="gt"
  local repo_url="git@github.com:steveyegge/gastown.git"

  skip_if_exists "$binary" && return
  section "Building $binary"
  ensure_repo "$src_dir" "$repo_url"
  pkill -x "$binary" || true
  git -C "$src_dir" reset --hard
  git -C "$src_dir" clean -fxd
  git -C "$src_dir" pull
  make -C "$src_dir" build
  cp "$src_dir/$binary" "$HOME/bin/$binary"
}

################################################################################
################################################################################
################################################################################

create_template() {
  claude \
    --print \
    --dangerously-skip-permissions \
    "$(cat <<'EOF'
# Instructions

- read ~/src/beads_rust/AGENTS.md
- extract the following major sections (a major section is usually denoted by --- and then ##):
  - RULE 0
  - RULE NUMBER 1
  - Irreversible Git & Filesystem Actions — DO NOT EVER BREAK GLASS
  - ## (Your Project Info Here)
  - Beads (br) — Dependency-Aware Issue Tracking
  - bv — Graph-Aware Triage Engine
  - Beads Workflow Integration
  - Landing the Plane (Session Completion)
  - Note for Codex/GPT-5.2
  - Note on Built-in TODO Functionality
- write to ~/subvox/ai/agents-template.md in the above order **VERBATIM** except for the "Your Project Info Here", which is a placeholder.
EOF
)"
}

################################################################################
################################################################################
################################################################################

build_deps() {
  build_asupersync
  build_frankensqlite
  build_frankensearch
  build_frankentui
  build_sqlmodel_rust
}

main() {
  check_dependencies

  build_deps

  build_tru
  build_dcg

  build_br
  build_bv
  build_mcp_agent_mail_rust

  # we are using br for now instead of bd until gastown is stable
  [[ -f ~/bin/bd ]] && rm ~/bin/bd
  # build_bd
  # build_gt  # i don't use this enough to build and setup
}

################################################################################
################################################################################
while [[ $# -gt 0 ]]; do
  case "$1" in
    -s|--skip-existing) SKIP_EXISTING=true; shift ;;
    create-template) create_template; exit 0 ;;
    *) break ;;
  esac
done

main
