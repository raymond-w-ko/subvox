#!/usr/bin/env -S bash -exu
pushd ~/src/beads
git pull
go build ./cmd/bd
cp ./bd ~/bin/bd
popd

pushd ~/src/beads_viewer
git fetch up
git merge up/main
go build ./cmd/bv
cp ./bv ~/bin/bv
popd
