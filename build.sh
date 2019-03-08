#!/bin/bash

set -e;

REPO="TREE";

# Upgrade container manually, since ciel update-os is broken right now
echo ">>> Updaing container"
sudo ciel add update;
sudo ciel shell -i update "apt update && apt dist-upgrade -y";
sudo ciel commit -i update;
sudo ciel del update;

set +e;

echo ">>> Start building..."
for package in $(ls "$REPO"/extra-spiral); do
    echo ">>> Building $package"
    sudo ciel add $package;
    sudo ciel build -i $package $package;
    sudo ciel del $package;
    echo ">>> Build finished"
done
echo ">>> All done."