#!/bin/bash

set -e;

pushd repo
git pull
popd

sudo rm -Rf TREE OUTPUT
venv/bin/python3 generate.py
bash -c ./build.sh