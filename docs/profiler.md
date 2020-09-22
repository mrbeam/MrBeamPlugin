# Profiler

To use the profiler for running OctoPrint:

```sh
# Stop the octoprint service if it is running
sudo systemctl stop octoprint
# Activate the venv in which octoprint is installed (here it is `~/oprint`)
. ~/oprint/bin/activate
# Start the profiler
./profile.py -o my_octoprint.profile

# OctoPrint is now running and being profiled. Do what you want to do, then exit it.
# [...]
```

This snippet creates a file `my_octoprint.profile` (By default it ouptuts `octoprint.profile`)

## Profile analysis

You can then use [RunSnakeRun] to analyse the outputted profile.

```sh
runsnake my_octoprint.profile
```

If working on a remote device, you might want to consider sync that profile file to your desktop.

[RunSnakeRun]: http://www.vrplumber.com/programming/runsnakerun/
