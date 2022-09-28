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

Build image: (Add the following flag for Apple M1: `--platform linux/x86_64`)
```shell
docker build -t mrb3-core-plugin .
```
Run container: (Add the following flag for Apple M1: `--platform linux/x86_64`)
```shell
docker run --name mrb3-core-plugin -d -p5003:5000 mrb3-core-plugin
```
Access from the browser:

    http://localhost:5002

## SCSS
compile the css for the login UI

```shell
sass ./scss/loginui.scss octoprint_mrbeam/static/css/loginui.css
```

## Set up local dev environment
Just run the `dev-setup.sh` script, that will:
- Create a virtual environment with all the requirements to run tests
- Install the pre-commit configuration for the auto formatting
