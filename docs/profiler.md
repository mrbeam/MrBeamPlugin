# Profiler

To use the profiler for running OctoPrint:

```sh
# Stop the octoprint service if it is running
sudo systemctl stop octoprint
# Activate the venv in which octoprint is installed (here it is `~/oprint`)
. ~/oprint/bin/activate
# Start the profiler
./profile.py -o my_octoprint.pstats

# OctoPrint is now running and being profiled. Do what you want to do, then exit it.
# [...]
```

This snippet creates a file `my_octoprint.profile` (By default it ouptuts `octoprint.profile`)

## Profile analysis

### kcachegrind

kcachegrind is a very well rounded profile analysis tool for other languages. However [pyprof2calltree] makes the pstats output digestible to it.

```sh
python2 -m pyprof2calltree -k -i octoprint.pstats
```

Warning: The python3 version of [pyprof2calltree] cannot read .pstats files written in our Python2 environment

```sh
python2 -m pip install pyprof2calltree
```

### RunSnakeRun

You can then use [RunSnakeRun] to analyse the outputted profile.

It can be slightly difficult to install, and it is more basic than [pyprof2calltree].

```sh
runsnake my_octoprint.pstats
```

If working on a remote device, you might want to consider sync that profile file to your desktop.

[runsnakerun]: http://www.vrplumber.com/programming/runsnakerun/
[pyprof2calltree]: https://pypi.org/project/pyprof2calltree/
