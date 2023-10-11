#!/bin/bash

# Create virtual environment and install requirements for python unit tests
virtualenv -p python2.7 venv2  # For this to work: pip install virtualenv==20.21.1
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
