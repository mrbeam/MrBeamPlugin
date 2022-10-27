#!/bin/bash

# Create virtual environment and install requirements for python unit tests
virtualenv -p python3.10.6 venv3-dev
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements-dev.txt

# for cypress tests
nvm install 18.7.0
npm install

#for sass
npm install -g sass

# for JS unit tests
cd tests/javascript/
npm install

# Install pre-commit config
pre-commit install
