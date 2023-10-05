import time

from mock.mock import patch, MagicMock, call

import pytest
from octoprint_mrbeam.mrbeam_events import MrBeamEvents

from octoprint_mrbeam.iobeam.dust_manager import DustManager
from octoprint.events import Events as OctoPrintEvents

from tests.conftest import wait_till_event_received


class DustManagerMock(DustManager):
    FAN_TEST_DURATION = 0.1


@pytest.fixture
def dust_manager(mrbeam_plugin, monkeypatch):
    monkeypatch.setattr(DustManager, "FAN_TEST_DURATION", 0.01)
    dust_manager = DustManager(mrbeam_plugin)
    dust_manager._one_button_handler = MagicMock()
    dust_manager._analytics_handler = MagicMock()
    dust_manager._event_bus.fire(MrBeamEvents.MRB_PLUGIN_INITIALIZED)
    wait_till_event_received(
        dust_manager._event_bus, MrBeamEvents.MRB_PLUGIN_INITIALIZED
    )
    dust_manager._iobeam.send_fan_command = MagicMock(return_value=(True, None))
    return dust_manager


@pytest.mark.parametrize(
    "data",
    [
        {"rpm": None, "dust": None, "state": None, "connected": True},
        {"rpm": 1, "dust": 2, "state": None, "connected": True},
        {"rpm": None, "dust": 1, "state": 2, "connected": True},
        {"rpm": 2, "dust": None, "state": 1, "connected": True},
    ],
)
@patch("octoprint_mrbeam.iobeam.dust_manager.monotonic_time")
def test_handle_fan_data_when_data_is_missing_then_malfunction(
    mock_monotonic_time, data, dust_manager
):
    # Arrange
    mock_monotonic_time.return_value = 0
    dust_manager._handle_fan_data({"rpm": 0, "dust": 1, "state": 1, "connected": True})

    # Act
    with patch.object(
        dust_manager._plugin.hw_malfunction_handler, "report_hw_malfunction"
    ) as mock_report_hw_malfunction:
        dust_manager._handle_fan_data(data)
        mock_monotonic_time.return_value = 12
        dust_manager._handle_fan_data(data)

        # Assert
        calls = [
            call(
                {
                    "i2c_bus_malfunction": {
                        "code": "E-00FF-1030",
                        "stop_laser": False,
                    }
                }
            ),
            call(
                {
                    "i2c_bus_malfunction": {
                        "code": "E-00FF-1014",
                        "stop_laser": False,
                    }
                }
            ),
        ]
        mock_report_hw_malfunction.assert_has_calls(calls)


@patch("octoprint_mrbeam.iobeam.dust_manager.monotonic_time")
def test_handle_fan_data_when_rpm_is_zero_and_job_ios_running_then_malfunction(
    mock_monotonic_time, dust_manager
):
    # Arrange
    data = {"rpm": 0, "dust": 1, "state": 1, "connected": True}
    mock_monotonic_time.return_value = 0
    dust_manager._handle_fan_data(data)
    # Act
    dust_manager._one_button_handler.is_printing = MagicMock(return_value=True)
    with patch.object(
        dust_manager._plugin.hw_malfunction_handler, "report_hw_malfunction"
    ) as mock_report_hw_malfunction:
        mock_monotonic_time.return_value = 10000
        dust_manager._handle_fan_data(data)

        # Assert
        mock_report_hw_malfunction.assert_called_with(
            {"err_fan_not_spinning": {"code": "E-00FF-1027", "stop_laser": False}}
        )


def test_if_test_fan_rpm_was_triggered_when_job_was_started(dust_manager):
    # Arrange
    dust_manager._handle_fan_data({"rpm": 20, "dust": 1, "state": 1, "connected": True})
    dust_manager._handle_fan_data({"rpm": 30, "dust": 1, "state": 1, "connected": True})
    dust_manager._handle_fan_data({"rpm": 40, "dust": 1, "state": 1, "connected": True})

    # Act
    dust_manager._event_bus.fire(OctoPrintEvents.PRINT_STARTED)
    wait_till_event_received(dust_manager._event_bus, OctoPrintEvents.PRINT_STARTED)
    time.sleep(0.1)  # wait till test fan rom finishes

    # Assert


def test_if_test_fan_rpm_was_extended_when_rpm_diff_is_to_high(dust_manager):
    # Arrange
    dust_manager._handle_fan_data(
        {"rpm": 500, "dust": 1, "state": 1, "connected": True}
    )
    dust_manager._handle_fan_data(
        {"rpm": 1500, "dust": 1, "state": 1, "connected": True}
    )
    dust_manager._handle_fan_data(
        {"rpm": 3000, "dust": 1, "state": 1, "connected": True}
    )

    # Act
    dust_manager._event_bus.fire(OctoPrintEvents.PRINT_STARTED)
    wait_till_event_received(dust_manager._event_bus, OctoPrintEvents.PRINT_STARTED)
    time.sleep(0.1)  # wait till test fan rom finishes

    # Assert


def test_if_test_fan_rpm_was_triggered_when_it_didnt_run_for_a_while(
    dust_manager, monkeypatch
):
    # Arrange
    monkeypatch.setattr(dust_manager, "REPEAT_TEST_FAN_RPM_INTERVAL", 0.1)
    dust_manager._handle_fan_data({"rpm": 20, "dust": 1, "state": 1, "connected": True})
    dust_manager._handle_fan_data({"rpm": 30, "dust": 1, "state": 1, "connected": True})
    dust_manager._handle_fan_data({"rpm": 40, "dust": 1, "state": 1, "connected": True})

    # Act
    dust_manager._event_bus.fire(OctoPrintEvents.PRINT_STARTED)
    wait_till_event_received(dust_manager._event_bus, OctoPrintEvents.PRINT_STARTED)
    time.sleep(0.1)  # wait till test fan rom finishes
    print("now")
    dust_manager._event_bus.fire(MrBeamEvents.PRINT_PROGRESS)
    wait_till_event_received(dust_manager._event_bus, MrBeamEvents.PRINT_PROGRESS)
    time.sleep(0.1)  # wait till test fan rom finishes

    # Assert
