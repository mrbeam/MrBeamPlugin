# pytest config file
import os

import pytest
from mock.mock import MagicMock

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
    mrbeam_plugin._settings.get = MagicMock(
        return_value="", getBaseFolder=MagicMock(return_value="")
    )
    mrbeam_plugin._settings.get_boolean = MagicMock()
    mrbeam_plugin._event_bus = MagicMock()
    mrbeam_plugin.get_plugin_version = MagicMock()
    mrbeam_plugin._basefolder = os.path.join(
        os.path.dirname(__package_path__), "octoprint_mrbeam"
    )
    mrbeam_plugin.laserhead_handler = MagicMock()

    yield mrbeam_plugin
