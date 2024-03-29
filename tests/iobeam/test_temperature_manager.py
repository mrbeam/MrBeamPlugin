import pytest
from mock.mock import MagicMock, patch
from octoprint_mrbeam.util.uptime import get_uptime
from pytest import approx

from octoprint_mrbeam.mrbeam_events import MrBeamEvents

from octoprint_mrbeam.iobeam.temperature_manager import TemperatureManager


@pytest.fixture()
def temperature_manager(mrbeam_plugin):
    laser = MagicMock()
    temperature_manager = TemperatureManager(mrbeam_plugin, laser)
    temperature_manager.temperature_max = 50.0
    temperature_manager._high_tmp_warn_offset = 5.0
    temperature_manager._event_bus.fire = MagicMock()
    temperature_manager._analytics_handler = MagicMock()
    temperature_manager._one_button_handler = MagicMock()
    temperature_manager._temp_timer_callback = MagicMock()
    temperature_manager._on_mrbeam_plugin_initialized(
        MrBeamEvents.MRB_PLUGIN_INITIALIZED, None
    )

    return temperature_manager


def test_cooling_difference_if_not_cooling(mrbeam_plugin):
    # Arrange
    temperature_manager = TemperatureManager(mrbeam_plugin, MagicMock())

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
    temperature_manager = TemperatureManager(mrbeam_plugin, MagicMock())
    temperature_manager.cooling_tigger_temperature = 50.0
    temperature_manager.temperature = temperature
    temperature_manager.is_cooling = MagicMock(return_value=True)

    # Act
    cooling_difference = temperature_manager.cooling_difference

    # Assert
    assert cooling_difference == expected_result


def test_dismiss_high_temperature_warning(mrbeam_plugin):
    # Arrange
    temperature_manager = TemperatureManager(mrbeam_plugin, MagicMock())
    temperature_manager._event_bus.fire = MagicMock()
    # Act
    temperature_manager.dismiss_high_temperature_warning()

    # Assert
    temperature_manager._event_bus.fire.assert_called_with(
        MrBeamEvents.HIGH_TEMPERATURE_WARNING_DISMISSED
    )


def test_dismiss_high_temperature_critical(mrbeam_plugin):
    # Arrange
    temperature_manager = TemperatureManager(mrbeam_plugin, MagicMock())
    temperature_manager._event_bus.fire = MagicMock()
    # Act
    temperature_manager.dismiss_high_temperature_critical()

    # Assert
    temperature_manager._event_bus.fire.assert_called_with(
        MrBeamEvents.HIGH_TEMPERATURE_CRITICAL_DISMISSED
    )


def test_cooling_since_if_not_cooling(mrbeam_plugin):
    # Arrange
    temperature_manager = TemperatureManager(mrbeam_plugin, MagicMock())

    # Act
    cooling_since = temperature_manager.cooling_since

    # Assert
    assert cooling_since == 0


def test_cooling_since_if_cooling(temperature_manager):
    # Arrange
    temperature_manager.cooling_tigger_time = get_uptime() - 1000

    # Act
    cooling_since = temperature_manager.cooling_since

    # Assert
    assert cooling_since == approx(1000, rel=1e-4)


def test_handle_temp_invalid(temperature_manager):
    # Arrange
    temperature_manager.cooling_stop = MagicMock()
    temperature_manager._analytics_handler = MagicMock()

    # Act
    temperature_manager.handle_temp(kwargs={"temp": None})

    # Assert
    temperature_manager.cooling_stop.assert_called_once()


def test_handle_temp_critical_high_temperature_while_printing(temperature_manager):
    # Arrange
    temperature_manager._one_button_handler.is_printing = MagicMock(return_value=True)
    temperature_manager._laser.is_busy = MagicMock(return_value=True)

    # Act
    with patch(
        "octoprint_mrbeam.iobeam.temperature_manager.get_uptime",
        return_value=get_uptime() - 3,
    ):  # simulate a temperature received 3 seconds ago
        temperature_manager.handle_temp(kwargs={"temp": 55.1})

    # Assert
    temperature_manager._event_bus.fire.assert_called_with(
        MrBeamEvents.LASER_COOLING_TEMPERATURE_REACHED,
    )

    # Act
    temperature_manager.handle_temp(kwargs={"temp": 55.2})

    # Assert
    temperature_manager._event_bus.fire.assert_called_with(
        MrBeamEvents.LASER_HIGH_TEMPERATURE, {"threshold": 55.0, "tmp": 55.2}
    )


def test_handle_temp_critical_high_temperature_while_not_lasering(temperature_manager):
    # Arrange
    temperature_manager._one_button_handler.is_printing = MagicMock(return_value=False)
    temperature_manager._laser.is_busy = MagicMock(return_value=False)

    # Act
    with patch(
        "octoprint_mrbeam.iobeam.temperature_manager.get_uptime",
        return_value=get_uptime() - 3,
    ):  # simulate a temperature received 3 seconds ago
        temperature_manager.handle_temp(kwargs={"temp": 55.1})

    temperature_manager._event_bus.fire.assert_called_with(
        MrBeamEvents.LASER_COOLING_TEMPERATURE_REACHED,
    )
    temperature_manager.high_temp_fsm.start_monitoring()  # this would be triggered by the event

    # Act
    temperature_manager.handle_temp(kwargs={"temp": 55.2})

    # Assert
    temperature_manager._event_bus.fire.assert_called_with(
        MrBeamEvents.LASER_HIGH_TEMPERATURE, {"threshold": 55.0, "tmp": 55.2}
    )


def test_handle_temp_trigger_cooling(temperature_manager):
    # Arrange
    temperature_manager.cooling_stop = MagicMock()

    # Act
    temperature_manager.handle_temp(kwargs={"temp": 50.1})

    # Assert
    temperature_manager.cooling_stop.assert_called_once()


def test_handle_temp_stop_cooling_after_hysteresis(temperature_manager):
    # Arrange
    temperature_manager.cooling_stop = MagicMock()
    temperature_manager.hysteresis_temperature = 28
    temperature_manager.cooling_resume = MagicMock()
    temperature_manager.cooling_tigger_time = (
        get_uptime() - 26
    )  # when the cooling started
    temperature_manager.cooling_tigger_temperature = 50.0

    # Act
    temperature_manager.handle_temp(kwargs={"temp": 28})

    # Assert
    temperature_manager.cooling_resume.assert_called_once()


def test_handle_temp_fire_cooling_to_slow_event_second_threshold(temperature_manager):
    # Arrange
    temperature_manager.cooling_tigger_time = (
        get_uptime() - 61
    )  # when the cooling started this needs to longer as 25 seconds
    temperature_manager.cooling_tigger_temperature = 50.0

    # Act
    temperature_manager.handle_temp(kwargs={"temp": 49})
    temperature_manager._last_cooling_threshold_check_time = get_uptime() - 21
    temperature_manager.handle_temp(kwargs={"temp": 49})
    temperature_manager._last_cooling_threshold_check_time = get_uptime() - 21
    temperature_manager.handle_temp(kwargs={"temp": 49})

    # Assert
    temperature_manager._event_bus.fire.assert_called_with(
        MrBeamEvents.LASER_COOLING_TO_SLOW,
        dict(temp=49, cooling_difference=1.0, cooling_time=approx(61, rel=1)),
    )


def test_handle_temp_fire_cooling_to_slow_event_third_threshold(temperature_manager):
    # Arrange
    temperature_manager.cooling_tigger_time = (
        get_uptime() - 140
    )  # when the cooling started this needs to longer as 25 seconds
    temperature_manager.cooling_tigger_temperature = 50.0

    # Act
    temperature_manager.handle_temp(kwargs={"temp": 49})
    temperature_manager._last_cooling_threshold_check_time = get_uptime() - 21

    # Assert
    temperature_manager._event_bus.fire.assert_called_with(
        MrBeamEvents.LASER_COOLING_TO_SLOW,
        dict(
            temp=49,
            cooling_difference=1.0,
            cooling_time=approx(141, rel=0.01),
        ),
    )


@pytest.mark.parametrize(
    "temp, time",
    [
        (46, 41),
        (46, 50),
        (44, 61),
        (43, 70),
    ],
)
def test_handle_temp_fire_re_trigger_cooling_fan(temp, time, temperature_manager):
    # Arrange
    temperature_manager.cooling_tigger_time = (
        get_uptime() - time
    )  # when the cooling started this needs to longer as 25 seconds
    temperature_manager.cooling_tigger_temperature = 50.0
    temperature_manager.hysteresis_temperature = 28

    # Act
    temperature_manager.handle_temp(kwargs={"temp": temp})

    # Assert
    temperature_manager._event_bus.fire.assert_called_with(
        MrBeamEvents.LASER_COOLING_RE_TRIGGER_FAN,
    )


@pytest.mark.parametrize(
    "temp, time",
    [
        (45, 10),
        (45, 20),
        (45, 30),
        (47, 41),
        (46, 80),
        (46, 90),
        (46, 100),
        (44, 110),
        (43, 120),
        (43, 130),
    ],
)
def test_handle_temp_fire_no_event(temp, time, temperature_manager):
    # Arrange
    temperature_manager.cooling_tigger_time = (
        get_uptime() - time
    )  # when the cooling started this needs to longer as 25 seconds
    temperature_manager.cooling_tigger_temperature = 50.0
    temperature_manager.hysteresis_temperature = 28

    # Act
    temperature_manager.handle_temp(kwargs={"temp": temp})

    # Assert
    temperature_manager._event_bus.fire.assert_not_called()


def test_cooling_resume(mrbeam_plugin):
    # Arrange
    temperature_manager = TemperatureManager(mrbeam_plugin, MagicMock())
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


def test_fire_of_LASER_COOLING_RESUME_after_cancel_or_abort(temperature_manager):
    # Arrange
    temperature_manager._one_button_handler = MagicMock(cooling_down_end=MagicMock())
    temperature_manager.high_temp_fsm.start_monitoring()
    temperature_manager.high_temp_fsm.warn()
    temperature_manager.high_temp_fsm.dismiss()
    temperature_manager.handle_temp(kwargs={"temp": 50})
    temperature_manager._plugin.laserhead_handler.current_laserhead_max_temperature = 50
    temperature_manager._plugin.laserhead_handler.current_laserhead_high_temperature_warn_offset = (
        5
    )
    temperature_manager.reset({"event": "mock_reset"})
    temperature_manager._event_bus.fire = MagicMock()

    # Act
    temperature_manager.handle_temp(kwargs={"temp": 30})

    # Assert
    temperature_manager._event_bus.fire.assert_called_with(
        MrBeamEvents.LASER_COOLING_RESUME, dict(temp=30)
    )
    assert temperature_manager.cooling_tigger_time == None
    assert temperature_manager.cooling_tigger_temperature == None
    temperature_manager._one_button_handler.cooling_down_end.assert_called_once()


def test_is_cooling_by_time(temperature_manager):
    # Arrange
    temperature_manager.cooling_tigger_time = get_uptime()
    temperature_manager._one_button_handler.is_paused = MagicMock(return_value=True)

    # Act
    result = temperature_manager.is_cooling()

    # Assert
    assert result is True


def test_is_cooling_by_one_button_hander_is_paused(temperature_manager):
    # Arrange
    temperature_manager.cooling_tigger_time = get_uptime()
    temperature_manager._one_button_handler.is_paused = MagicMock(return_value=False)

    # Act
    result = temperature_manager.is_cooling()

    # Assert
    assert result is False


def test_is_cooling_by_fsm_state(temperature_manager):
    # Arrange
    temperature_manager.high_temp_fsm.start_monitoring()
    temperature_manager.high_temp_fsm.warn()
    temperature_manager.high_temp_fsm.dismiss()
    temperature_manager.cooling_tigger_time = None

    # Act
    result = temperature_manager.is_cooling()

    # Assert
    assert result is True


def test_is_cooling_is_false_if_no_time_or_state(temperature_manager):
    # Arrange
    temperature_manager.high_temp_fsm.start_monitoring()
    temperature_manager.high_temp_fsm.warn()
    temperature_manager.cooling_tigger_time = None

    # Act
    result = temperature_manager.is_cooling()

    # Assert
    assert result is False


def test_job_pauses_when_temperature_was_not_recent(temperature_manager):
    # Arrange
    temperature_manager.cooling_stop = MagicMock()

    # Act
    temperature_manager.handle_temp(kwargs={"temp": None})

    # Assert
    temperature_manager.cooling_stop.assert_called_once_with(
        err_msg="Laser temperature not available, assuming high temperature and stop for cooling."
    )


def test_job_resumes_when_temp_was_not_recent(temperature_manager):
    # Arrange
    temperature_manager.cooling_tigger_temperature = 40
    temperature_manager.cooling_tigger_time = get_uptime() - 30
    temperature_manager._one_button_handler.is_paused = MagicMock(return_value=True)
    temperature_manager.cooling_resume = MagicMock()

    # Act
    temperature_manager.handle_temp(kwargs={"temp": 41})

    # Assert
    temperature_manager.cooling_resume.assert_called_once()
