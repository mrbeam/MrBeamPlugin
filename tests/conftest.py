# pytest config file

import pytest
from flask_login import LoginManager

from octoprint.settings import settings
from octoprint_mrbeam import MrBeamPlugin

sett = settings(init=True)  # Initialize octoprint settings, necessary for MrBeamPlugin


# adds commandline option --baseurl
def pytest_addoption(parser):
    parser.addoption("--baseurl", action="store", default="http://localhost:5000")
    parser.addoption(
        "--rsc_folder", action="store", default="/home/teja/workspace/test_rsc"
    )


# injects params baseurl, rsc_folder in every test function
def pytest_generate_tests(metafunc):
    # This is called for every test. Only get/set command line arguments
    # if the argument is specified in the list of test "fixturenames".
    baseurl = metafunc.config.option.baseurl
    if "baseurl" in metafunc.fixturenames and baseurl is not None:
        metafunc.parametrize("baseurl", [baseurl])
    rsc_folder = metafunc.config.option.rsc_folder
    if "rsc_folder" in metafunc.fixturenames and rsc_folder is not None:
        metafunc.parametrize("rsc_folder", [rsc_folder])


@pytest.fixture
def mrbeam_plugin():
    mrbeam_plugin = MrBeamPlugin()
    mrbeam_plugin._settings = sett
    yield mrbeam_plugin


@pytest.fixture()
def app():
    from octoprint.server import app
    login_manager = LoginManager()
    login_manager.init_app(app)

    app.config.update({
        "TESTING": True,
    })

    yield app


@pytest.fixture()
def request_context(app):
    """Create the app and return the request context as a fixture"""
    return app.test_request_context
