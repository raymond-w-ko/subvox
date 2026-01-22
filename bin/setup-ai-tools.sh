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
  git -C "$src_dir" pull
  cd $src_dir && cargo build --release
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
  cd $src_dir && cargo build --release
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
  git -C "$src_dir" pull
  git -C "$src_dir" fetch upstream
  git -C "$src_dir" merge upstream/main
  git -C "$src_dir" push
  make -C "$src_dir" build
  cp "$src_dir/$binary" "$HOME/bin/$binary"
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

build_am() {
  local src_dir="$HOME/src/mcp_agent_mail"
  local binary="am"
  local repo_url="https://github.com/Dicklesworthstone/mcp_agent_mail.git"

  section "Building $binary"
  uv python install 3.14
  ensure_repo "$src_dir" "$repo_url"
  pushd "$src_dir"
  git stash
  git pull
  git stash pop
  [[ -d .venv ]] || uv venv -p 3.14
  source .venv/bin/activate
  uv sync
  popd
}

build_prompt() {
  :
}

main() {
  check_dependencies
  build_dcg
  build_bd
  build_br
  build_bv
  build_gt
  build_am # must be last due to git stash pop merge conflicts
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    -s|--skip-existing) SKIP_EXISTING=true; shift ;;
    build-prompt) build_prompt; exit 0 ;;
    *) break ;;
  esac
done

main
