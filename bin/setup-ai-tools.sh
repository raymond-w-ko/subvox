#!/usr/bin/env -S bash -exu

section() {
  echo -e "\033[1;36m>>> Building $1 <<<\033[0m"
}

show_incoming() {
  git fetch
  echo "=== Incoming commits ==="
  git log HEAD..@{u} --oneline || true
  echo "========================"
}

section "bd"
pushd ~/src/beads
pkill -x bd || true
show_incoming
git pull
make build
cp ./bd ~/bin/bd
popd

section "bv"
pushd ~/src/beads_viewer
show_incoming
git pull
git fetch up
git merge up/main
git push
make build
cp ./bv ~/bin/bv
popd

section "gt"
pushd ~/src/gastown
pkill -x gt || true
git reset --hard
git clean -fxd
show_incoming
git pull
make build
cp ./gt ~/bin/gt
popd

# i am no longer using the below, so exit here
exit 0

pushd ~/src/pi-mono
git pull
git fetch up
git merge up/main
git push
./make.sh
popd
