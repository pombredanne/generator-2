#!/bin/bash

set -e;

REPO="TREE"; # Path to generated autobuild definitions
CATEGORY="extra-spiral"; # The category of packages that will be built
CIEL="/usr/local/bin/ciel"; # Path to ciel binary

if [ ! -f "${CIEL}" ]; then
	echo ">>> Ciel not found, quitting...";
	exit 127;
fi

if [ ! -d "${REPO}/${CATEGORY}" ]; then
	echo ">>> Autobuild files not found, quitting...";
	exit 1
fi

# Upgrade container manually, since ciel update-os is broken right now
echo ">>> Updating container";
sudo ${CIEL} add update;
sudo ${CIEL} shell -i update "apt update && apt dist-upgrade -y";
sudo ${CIEL} commit -i update;
sudo ${CIEL} del update;
echo ">>> Container updated";

# Build packages
set +e; # Since it may fail...

echo ">>> Start building packages..."
for package in $(ls "${REPO}/${CATEGORY}"); do
    echo ">>> Building ${package}";
    sudo ${CIEL} add ${package};
    sudo ${CIEL} build -i ${package} ${package};
    sudo ${CIEL} del ${package};
    echo ">>> Finished building ${package}";
done
echo ">>> Finished building packages"
