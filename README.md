Spiral controller
=================

This is the automated controller of the spiral repository.

It generates autobuild files from the [repo](https://github.com/spiral-repo/repo), and uses [ciel](https://github.com/AOSC-Dev/ciel) to build them.

It also updates itself as well.

Deployment
----------

1. Download the controller and clone the [repo](https://github.com/spiral-repo/repo).
2. Install the requirements listed in [requirements.txt](requirements.txt).
3. Create a symlink inside the controller directory to the [repo](https://github.com/spiral-repo/repo) and name it as `repo`. OR change the path [here](https://github.com/spiral-repo/generator/blob/master/generate.py#L108).
4. Initialize a ciel directory here.
5. Setup GitHub webhook listener, execute [on_push.sh](on_push.sh) when event `push` happens.
6. Setup [p-vector](https://github.com/AOSC-Dev/p-vector) for `dists` files generation.
7. Setup crontab/systemd-timer to execute [on_push.sh](on_push.sh) automatically to make sure all packages are up to date.