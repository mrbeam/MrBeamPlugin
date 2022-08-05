# MrBeam

**TODO:** Describe what your plugin does.

## Setup

Install via the bundled [Plugin Manager](https://github.com/foosel/OctoPrint/wiki/Plugin:-Plugin-Manager)
or manually using this URL:

    https://github.com/hungerpirat/MrBeamPlugin/archive/master.zip

**TODO:** Describe how to install your plugin, if more needs to be done than just installing it via pip or through
the plugin manager.

## Configuration

**TODO:** Describe your plugin's configuration options (if any).

## Docker

Build image:

```shell
docker build -t mrbeam_plugin .
```

Run container:

```shell
docker run --name mrbeam-plugin -d -p5002:5000 mrbeam_plugin
```

Access from the browser:

    http://localhost:5002

## Running unit tests

Create a Python 2 virtual environment and activate it:

```shell
virtualenv -p /usr/bin/python2.7 tests_venv
source tests_venv/bin/activate
```

Install test requirements:

```shell
pip install -r test-requirements.txt
```

Run the unit tests directly from **Pycharm** or from the command line:

```shell
python -m pytest tests/
```
