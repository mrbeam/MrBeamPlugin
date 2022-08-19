#!/bin/bash

# Create virtual environment and install requirements for python unit tests
virtualenv -p /usr/bin/python2.7 venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements-dev.txt

# for cypress tests
nvm install 18.7.0
npm install

# for JS unit tests
cd tests/javascript/
npm install

# Install pre-commit config
pre-commit install
