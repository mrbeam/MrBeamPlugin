# pytest config file
import os
import threading
import time

import octoprint
import pytest
from mock.mock import MagicMock
from octoprint.events import EventManager, Events
from octoprint.plugin import PluginManager

from octoprint.settings import settings
from octoprint.util import monotonic_time
from octoprint_mrbeam.mrbeam_events import MrBeamEvents

from octoprint_mrbeam import MrBeamPlugin, AirFilter

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
    plugin_manager_mock = MagicMock(spec=octoprint.plugin.plugin_manager)

    # replace the actual plugin manager with the mock object
    octoprint.plugin.plugin_manager = plugin_manager_mock
    event_manager = EventManager()

    mrbeam_plugin = MrBeamPlugin()
    mrbeam_plugin._settings = sett
    mrbeam_plugin._settings.get = MagicMock(
        return_value="", getBaseFolder=MagicMock(return_value="")
    )
    mrbeam_plugin._settings.get_boolean = MagicMock()
    mrbeam_plugin._settings.global_get = MagicMock()
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
    mrbeam_plugin._plugin_manager = MagicMock()
    mrbeam_plugin.laserhead_handler = MagicMock()
    mrbeam_plugin._event_bus.fire(Events.STARTUP)
    mrbeam_plugin.user_notification_system = MagicMock()
    mrbeam_plugin._printer = MagicMock()
    mrbeam_plugin.hw_malfunction_handler = MagicMock()
    mrbeam_plugin.is_boot_grace_period = MagicMock(return_value=False)
    mrbeam_plugin.airfilter = MagicMock()
    mrbeam_plugin.usage_handler = MagicMock()

    yield mrbeam_plugin


def wait_till_event_received(event_bus, event, timeout=5):
    event_done = threading.Event()

    def event_callback(event, payload):
        event_done.set()

    event_bus.subscribe(event, event_callback)
    starttime = monotonic_time()

    while not event_done.is_set():
        time.sleep(0.1)
        assert round(monotonic_time() - starttime, 2) <= timeout


@pytest.fixture
def air_filter(mrbeam_plugin):
    air_filter = AirFilter(mrbeam_plugin)
    air_filter._plugin.send_mrb_state = MagicMock()

    air_filter._event_bus.fire(MrBeamEvents.MRB_PLUGIN_INITIALIZED)
    wait_till_event_received(air_filter._event_bus, MrBeamEvents.MRB_PLUGIN_INITIALIZED)
    return air_filter
