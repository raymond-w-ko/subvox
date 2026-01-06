#!/usr/bin/env -S bash -exu
# Requires: gh (GitHub CLI, must be logged in), jq

REPO_NAME="gt"
REPO_DIR=~/"$REPO_NAME"
GH_USER="${1:-$(gh api user --jq .login)}"

cd ~
if [[ -d "$REPO_NAME" ]]; then
  echo "========================================"
  echo "WARNING: This will DELETE $REPO_DIR"
  echo "========================================"
  read -p "Are you sure? (y/N) " -n 1 -r
  echo
  if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Aborted."
    exit 1
  fi
  rm -rf "$REPO_NAME"
fi
gt install "$REPO_DIR" --git
cd "$REPO_DIR"
git add .
git commit -m "Initial Gas Town HQ"
gh repo view "$GH_USER/$REPO_NAME" &>/dev/null && gh repo delete "$GH_USER/$REPO_NAME"
gt git-init --github "$GH_USER/$REPO_NAME"
