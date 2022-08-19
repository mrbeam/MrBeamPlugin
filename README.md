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

## Set up local dev environment
Just run the `dev-setup.sh` script, that will:
- Create a virtual environment with all the requirements to run tests
- Install the pre-commit configuration for the auto formatting
