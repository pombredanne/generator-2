#!/bin/bash

# On push event - Trigger the build process

set -e;

GIT="/usr/bin/git";
PIP="venv/bin/pip3";
TREE="TREE"
PYTHON="venv/bin/python3";
GENERATOR="generator.py";
BUILD_SCRIPT="./build.sh";

REPO="repo";

if [[ ! -f "${GIT}" && ! -f "${PIP}" && ! -f "${PYTHON}" && ! -f "${GENERATOR}" ]]; then
	echo ">>> Required file/program not found, quitting...";
fi

# Pull the latest source
echo ">>> Fetching latest generator...";
"${GIT}" pull;

# Update the source definitions
echo ">>> Updating source files...";
pushd "${REPO}";
	"${GIT}" pull;
popd;

# Update python dependencies
echo ">>> Updating Python dependencies...";
"${PIP}" install --upgrade -r requirements.txt;
echo ">>> Dependencies updated"

# Building!
echo ">>> Starting build process...";
sudo rm -Rf "${TREE}"; # Since packages are built with root account
"${PYTHON}" "${GENERATOR}"; # Generate autobuild files
bash -c "${BUILD_SCRIPT}"; # Build packages from autobuild definitions
echo ">>> Done!"
