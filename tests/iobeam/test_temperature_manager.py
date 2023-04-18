import pytest
from mock.mock import MagicMock
from octoprint_mrbeam.util.uptime import get_uptime

from octoprint_mrbeam.mrbeam_events import MrBeamEvents

from octoprint_mrbeam.iobeam.temperature_manager import TemperatureManager


def test_cooling_difference_if_not_cooling(mrbeam_plugin):
    # Arrange
    temperature_manager = TemperatureManager(mrbeam_plugin)

    # Act
    cooling_difference = temperature_manager.cooling_difference

    # Assert
    assert cooling_difference == 0


@pytest.mark.parametrize(
    "temperature,expected_result",
    [
        (20.0, 30.0),
        (60.0, -10.0),
    ],
)
def test_cooling_difference_if_cooling(temperature, expected_result, mrbeam_plugin):
    # Arrange
    temperature_manager = TemperatureManager(mrbeam_plugin)
    temperature_manager.cooling_tigger_temperature = 50.0
    temperature_manager.temperature = temperature
    temperature_manager.is_cooling = MagicMock(return_value=True)

    # Act
    cooling_difference = temperature_manager.cooling_difference

    # Assert
    assert cooling_difference == expected_result


def test_dismiss_high_temperature_warning(mrbeam_plugin):
    # Arrange
    temperature_manager = TemperatureManager(mrbeam_plugin)
    temperature_manager._event_bus.fire = MagicMock()
    # Act
    temperature_manager.dismiss_high_temperature_warning()

    # Assert
    temperature_manager._event_bus.fire.assert_called_with(
        MrBeamEvents.HIGH_TEMPERATURE_WARNING_DISMISSED
    )


def test_cooling_since_if_not_cooling(mrbeam_plugin):
    # Arrange
    temperature_manager = TemperatureManager(mrbeam_plugin)

    # Act
    cooling_since = temperature_manager.cooling_since

    # Assert
    assert cooling_since == 0


def test_cooling_since_if_cooling(mrbeam_plugin):
    # Arrange
    temperature_manager = TemperatureManager(mrbeam_plugin)
    temperature_manager.cooling_tigger_time = get_uptime() - 1000

    # Act
    cooling_since = temperature_manager.cooling_since

    # Assert
    assert cooling_since == 1000


def test_handle_temp_invalid(mrbeam_plugin):
    # Arrange
    temperature_manager = TemperatureManager(mrbeam_plugin)
    temperature_manager.cooling_stop = MagicMock()
    temperature_manager._analytics_handler = MagicMock()

    # Act
    temperature_manager.handle_temp(kwargs={"temp": None})

    # Assert
    temperature_manager.cooling_stop.assert_called_once()


def test_handle_temp_critical_high_temperature(mrbeam_plugin):
    # Arrange
    temperature_manager = TemperatureManager(mrbeam_plugin)
    temperature_manager.cooling_stop = MagicMock()
    temperature_manager._analytics_handler = MagicMock()
    temperature_manager.temperature_max = 50.0
    temperature_manager._high_tmp_warn_offset = 5.0
    temperature_manager._event_bus.fire = MagicMock()

    # Act
    temperature_manager.handle_temp(kwargs={"temp": 55.1})

    # Assert
    temperature_manager._event_bus.fire.assert_called_with(
        MrBeamEvents.LASER_HIGH_TEMPERATURE, {"threshold": 55.0, "tmp": 55.1}
    )


def test_handle_temp_trigger_cooling(mrbeam_plugin):
    # Arrange
    temperature_manager = TemperatureManager(mrbeam_plugin)
    temperature_manager.cooling_stop = MagicMock()
    temperature_manager._analytics_handler = MagicMock()
    temperature_manager.temperature_max = 50.0
    temperature_manager._high_tmp_warn_offset = 5.0
    temperature_manager._event_bus.fire = MagicMock()
    temperature_manager.cooling_stop = MagicMock()

    # Act
    temperature_manager.handle_temp(kwargs={"temp": 50.1})

    # Assert
    temperature_manager.cooling_stop.assert_called_once()


def test_handle_temp_stop_cooling_after_hysteresis(mrbeam_plugin):
    # Arrange
    temperature_manager = TemperatureManager(mrbeam_plugin)
    temperature_manager.cooling_stop = MagicMock()
    temperature_manager._analytics_handler = MagicMock()
    temperature_manager.temperature_max = 50.0
    temperature_manager._high_tmp_warn_offset = 5.0
    temperature_manager.hysteresis_temperature = 28
    temperature_manager._event_bus.fire = MagicMock()
    temperature_manager.cooling_resume = MagicMock()
    temperature_manager.cooling_tigger_time = (
        get_uptime() - 26
    )  # when the cooling started
    temperature_manager.cooling_tigger_temperature = 50.0

    # Act
    temperature_manager.handle_temp(kwargs={"temp": 28})

    # Assert
    temperature_manager.cooling_resume.assert_called_once()


def test_handle_temp_fire_cooling_to_slow_event_second_threshold(mrbeam_plugin):
    # Arrange
    temperature_manager = TemperatureManager(mrbeam_plugin)
    temperature_manager._event_bus.fire = MagicMock()
    temperature_manager._analytics_handler = MagicMock()
    temperature_manager.cooling_tigger_time = (
        get_uptime() - 61
    )  # when the cooling started this needs to longer as 25 seconds
    temperature_manager.cooling_tigger_temperature = 50.0
    temperature_manager.temperature_max = 50.0

    # Act
    temperature_manager.handle_temp(kwargs={"temp": 49})

    # Assert
    temperature_manager._event_bus.fire.assert_called_with(
        MrBeamEvents.LASER_COOLING_TO_SLOW,
        dict(temp=49, cooling_differnece=1.0, cooling_time=61),
    )


def test_handle_temp_fire_cooling_to_slow_event_third_threshold(mrbeam_plugin):
    # Arrange
    temperature_manager = TemperatureManager(mrbeam_plugin)
    temperature_manager._event_bus.fire = MagicMock()
    temperature_manager._analytics_handler = MagicMock()
    temperature_manager.cooling_tigger_time = (
        get_uptime() - 141
    )  # when the cooling started this needs to longer as 25 seconds
    temperature_manager.cooling_tigger_temperature = 50.0
    temperature_manager.temperature_max = 50.0

    # Act
    temperature_manager.handle_temp(kwargs={"temp": 49})

    # Assert
    temperature_manager._event_bus.fire.assert_called_with(
        MrBeamEvents.LASER_COOLING_TO_SLOW,
        dict(temp=49, cooling_differnece=1.0, cooling_time=141),
    )


@pytest.mark.parametrize(
    "temp, time",
    [
        (46, 41),
        (46, 50),
        (46, 60),
        (46, 70),
        (44, 61),
        (43, 70),
        (43, 80),
        (43, 90),
    ],
)
def test_handle_temp_fire_cooling_to_slow_re_trigger_cooling_fan(
    temp, time, mrbeam_plugin
):
    # Arrange
    temperature_manager = TemperatureManager(mrbeam_plugin)
    temperature_manager._event_bus.fire = MagicMock()
    temperature_manager._analytics_handler = MagicMock()
    temperature_manager.cooling_tigger_time = (
        get_uptime() - time
    )  # when the cooling started this needs to longer as 25 seconds
    temperature_manager.cooling_tigger_temperature = 50.0
    temperature_manager.hysteresis_temperature = 28
    temperature_manager.temperature_max = 50.0
    temperature_manager._high_tmp_warn_offset = 5.0

    # Act
    temperature_manager.handle_temp(kwargs={"temp": temp})

    # Assert
    temperature_manager._event_bus.fire.assert_called_with(
        MrBeamEvents.LASER_COOLING_RE_TRIGGER_FAN,
    )


def test_cooling_resume(mrbeam_plugin):
    # Arrange
    temperature_manager = TemperatureManager(mrbeam_plugin)
    temperature_manager._event_bus.fire = MagicMock()
    temperature_manager._one_button_handler = MagicMock(cooling_down_end=MagicMock())

    # Act
    temperature_manager.cooling_resume()

    # Assert
    temperature_manager._event_bus.fire.assert_called_with(
        MrBeamEvents.LASER_COOLING_RESUME, dict(temp=None)
    )
    assert temperature_manager.cooling_tigger_time == None
    assert temperature_manager.cooling_tigger_temperature == None
    temperature_manager._one_button_handler.cooling_down_end.assert_called_once()
