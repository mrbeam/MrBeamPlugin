# pytest config file
import os

import octoprint
import pytest
from mock.mock import MagicMock
from octoprint.events import EventManager, Events
from octoprint.plugin import PluginManager

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


def settings_get_mock(*args, **kwargs):
    print("settings_get_mock: {}".format(args))
    if args == (["serial", "timeout"],) or args == (
        ["serial", "maxCommunicationTimeouts"],
    ):
        return {}
    elif (
        args == (["serial", "terminalLogSize"],)
        or args == (["serial", "resendRatioStart"],)
        or args == (["serial", "resendRatioThreshold"],)
    ):
        return 100
    return ""


@pytest.fixture
def mrbeam_plugin():
    plugin_manager_mock = MagicMock()

    # replace the actual plugin manager with the mock object
    octoprint.plugin.plugin_manager = plugin_manager_mock
    event_manager = EventManager()

    mrbeam_plugin = MrBeamPlugin()
    mrbeam_plugin._settings = sett
    mrbeam_plugin._settings.get = MagicMock(
        getBaseFolder=MagicMock(return_value=""), side_effect=settings_get_mock
    )
    mrbeam_plugin._settings.global_set = MagicMock()
    mrbeam_plugin._settings.get_boolean = MagicMock()
    mrbeam_plugin._event_bus = event_manager
    mrbeam_plugin.dust_manager = MagicMock()
    mrbeam_plugin.temperature_manager = MagicMock()
    mrbeam_plugin.compressor_handler = MagicMock()
    mrbeam_plugin.get_plugin_version = MagicMock()
    mrbeam_plugin.analytics_handler = MagicMock()
    mrbeam_plugin.iobeam = MagicMock()
    mrbeam_plugin.onebutton_handler = MagicMock()
    mrbeam_plugin._file_manager = MagicMock()
    mrbeam_plugin._basefolder = os.path.join(
        os.path.dirname(__package_path__), "octoprint_mrbeam"
    )
    mrbeam_plugin.laserhead_handler = MagicMock()
    mrbeam_plugin._event_bus.fire(Events.STARTUP)
    mrbeam_plugin.user_notification_system = MagicMock()
    mrbeam_plugin._printer = MagicMock()
    mrbeam_plugin._user_manager = MagicMock()
    mrbeam_plugin._plugin_version = "2.0.0dev0"

    yield mrbeam_plugin
