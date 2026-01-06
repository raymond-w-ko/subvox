#!/usr/bin/env -S bash -exu
pushd ~/src/beads
git pull
make build
cp ./bd ~/bin/bd
popd

pushd ~/src/gastown
git pull
make build
cp ./gt ~/bin/gt
popd

pushd ~/src/beads_viewer
git pull
git fetch up
git merge up/main
git push
make build
cp ./bv ~/bin/bv
popd

exit 0

pushd ~/src/pi-mono
git pull
git fetch up
git merge up/main
git push
./make.sh
popd
