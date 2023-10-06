from mock.mock import patch, MagicMock, call

import pytest

from octoprint_mrbeam.iobeam.dust_manager import DustManager


@pytest.fixture
def dust_manager(mrbeam_plugin):
    dust_manager = DustManager(mrbeam_plugin)
    dust_manager._one_button_handler = MagicMock()
    dust_manager._analytics_handler = MagicMock()
    return dust_manager


@pytest.mark.parametrize(
    "data",
    [
        {"rpm": None, "dust": None, "state": None},
        {"rpm": 1, "dust": 2, "state": None},
        {"rpm": None, "dust": 1, "state": 2},
        {"rpm": 2, "dust": None, "state": 1},
    ],
)
@patch("octoprint_mrbeam.iobeam.dust_manager.monotonic_time")
def test_handle_fan_data_when_data_is_missing_then_malfunction(
    mock_monotonic_time, data, dust_manager
):
    # Arrange
    mock_monotonic_time.return_value = 0
    dust_manager._handle_fan_data({"rpm": 0, "dust": 1, "state": 1})

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
    data = {"rpm": 0, "dust": 1, "state": 1}
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
