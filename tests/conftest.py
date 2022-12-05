# pytest config file
from functools import wraps
from mock import patch

import pytest
from octoprint.events import EventManager
from octoprint.settings import settings
from octoprint.users import UserManager

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
def mrbeam_plugin(mocker, dummy_slicing_manager, dummy_file_manager, dummy_printer):
    mocker.patch("octoprint_mrbeam.MrBeamPlugin.set_serial_setting")
    mocker.patch("octoprint_mrbeam.analytics.analytics_handler.AnalyticsHandler")
    mocker.patch("octoprint_mrbeam.iobeam.onebutton_handler.OneButtonHandler")
    mocker.patch("octoprint_mrbeam.iobeam.lid_handler.LidHandler")
    mocker.patch("octoprint_mrbeam.analytics.usage_handler.UsageHandler")
    mocker.patch("octoprint_mrbeam.analytics.review_handler.ReviewHandler")
    mocker.patch("octoprint_mrbeam.iobeam.dust_manager.DustManager")
    mocker.patch("octoprint_mrbeam.iobeam.laserhead_handler.LaserheadHandler")
    mocker.patch("octoprint_mrbeam.iobeam.temperature_manager.TemperatureManager")
    mocker.patch("octoprint_mrbeam.filemanager.MrbFileManager")
    mocker.patch("octoprint_mrbeam.wizard_config.WizardConfig")
    mocker.patch("octoprint.users.UserManager")
    mocker.patch("octoprint_mrbeam.url_for", return_value="")
    # mocker.patch("octoprint_mrbeam.restricted_access", side=dummy_decorator)
    mocker.patch("octoprint_mrbeam.user_notification_system")
    mocker.patch("octoprint_mrbeam.MrBeamPlugin.isFirstRun", return_value=False)
    mocker.patch("octoprint_mrbeam.MrBeamPlugin._fixEmptyUserManager")
    mocker.patch("octoprint_mrbeam.MrBeamPlugin._getCurrentFile", return_value=(None, None))

    mrbeam_plugin = MrBeamPlugin()

    mrbeam_plugin._settings = sett
    mrbeam_plugin._printer = dummy_printer
    mrbeam_plugin._event_bus = EventManager()
    mrbeam_plugin._plugin_manager = None
    mrbeam_plugin._file_manager = None
    mrbeam_plugin._user_manager = UserManager()
    mrbeam_plugin._user_manager._users = []
    mrbeam_plugin._user_manager._customized = None
    mrbeam_plugin._analysis_queue = None
    mrbeam_plugin._connectivity_checker = None
    mrbeam_plugin._slicing_manager = dummy_slicing_manager

    mrbeam_plugin.initialize()
    mrbeam_plugin.mrb_file_manager = dummy_file_manager
    yield mrbeam_plugin


@pytest.fixture()
def app():
    from octoprint.server import app
    from flask_login import LoginManager

    login_manager = LoginManager()
    app.secret_key = 'dummy key'
    app.config['LOGIN_DISABLED'] = True  # To avoid 401 from @restricted_access
    login_manager.init_app(app)

    app.config.update({
        "TESTING": True,
    })

    yield app


@pytest.fixture()
def request_context(app):
    """Create the app and return the request context as a fixture"""
    return app.test_request_context


@pytest.fixture()
def dummy_slicing_manager():
    class DummySlicingManager:
        def get_slicer(self, _):
            return self

        def get_slicer_properties(self):
            return {"same_device": False}

    yield DummySlicingManager()


@pytest.fixture()
def dummy_file_manager():
    class DummyFileManager:
        def file_exists(self, a, b):
            return False

        def add_file_to_design_library(self, file_name, content):
            return

        def slice(self, *args, **kwargs):
            pass

    yield DummyFileManager()


@pytest.fixture()
def dummy_printer():
    class DummyPrinter:
        def set_colors(self, a, b):
            pass

        def on_comm_log(self, _):
            return

        def is_paused(self):
            return False

        def is_homed(self):
            return True

        def get_state_string(self):
            return ""

    yield DummyPrinter()


def dummy_decorator():
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            return f(*args, **kwargs)
        return decorated_function
    return decorator
