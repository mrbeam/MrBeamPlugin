import time

import octoprint
import pytest
from mock.mock import MagicMock, call
from octoprint.events import EventManager, Events

from octoprint_mrbeam.mrbeam_events import MrBeamEvents

from octoprint_mrbeam.fsm.high_temperature_fsm import HighTemperatureFSM


@pytest.fixture
def high_temp_fsm():
    plugin_manager_mock = MagicMock(spec=octoprint.plugin.plugin_manager)

    # replace the actual plugin manager with the mock object
    octoprint.plugin.plugin_manager = plugin_manager_mock
    event_manager = EventManager()
    event_manager.fire(Events.STARTUP)

    fsm = HighTemperatureFSM(event_manager, False, MagicMock())

    return fsm


def test_transistion_from_deactivated_to_monitoring():
    # Arrange
    fsm = HighTemperatureFSM(MagicMock(), False, MagicMock())
    assert fsm.deactivated.is_active
    fsm._analytics_handler.add_high_temp_warning_state_transition = MagicMock()
    # Act
    fsm.start_monitoring()

    # Assert
    assert fsm.monitoring.is_active
    fsm._analytics_handler.add_high_temp_warning_state_transition.assert_called_with(
        "start_monitoring", "deactivated", "monitoring", False
    )


def test_transistion_from_monitoring_to_warning():
    # Arrange
    fsm = HighTemperatureFSM(MagicMock(), False, MagicMock())
    fsm.start_monitoring()
    fsm._event_bus.fire = MagicMock()
    assert fsm.monitoring.is_active
    fsm._analytics_handler.add_high_temp_warning_state_transition = MagicMock()
    # Act
    fsm.warn()

    # Assert
    assert fsm.warning.is_active
    fsm._event_bus.fire.assert_called_with(
        MrBeamEvents.HIGH_TEMPERATURE_WARNING_SHOW,
        {"trigger": "high_temperature_warning"},
    )
    fsm._analytics_handler.add_high_temp_warning_state_transition.assert_called_with(
        "warn", "monitoring", "warning", False
    )


def test_transistion_from_warning_to_critical():
    # Arrange
    fsm = HighTemperatureFSM(MagicMock(), False, MagicMock())
    fsm.start_monitoring()
    fsm.warn()
    assert fsm.warning.is_active
    fsm._event_bus.fire = MagicMock()
    fsm._analytics_handler.add_high_temp_warning_state_transition = MagicMock()
    # Act
    fsm.critical()

    # Assert
    assert fsm.critically.is_active
    calls = [
        call(
            MrBeamEvents.HIGH_TEMPERATURE_CRITICAL_SHOW,
            {"trigger": "high_temperature_critically"},
        ),
        call(MrBeamEvents.LASER_JOB_ABORT, {"trigger": "high_temperature_critically"}),
        call(MrBeamEvents.LASER_HOME, {"trigger": "high_temperature_critically"}),
        call(
            MrBeamEvents.COMPRESSOR_DEACTIVATE,
            {"trigger": "high_temperature_critically"},
        ),
        call(
            MrBeamEvents.EXHAUST_DEACTIVATE, {"trigger": "high_temperature_critically"}
        ),
        call(MrBeamEvents.LED_ERROR_ENTER, {"trigger": "high_temperature_critically"}),
        call(MrBeamEvents.LASER_DEACTIVATE, {"trigger": "high_temperature_critically"}),
        call(MrBeamEvents.ALARM_ENTER, {"trigger": "high_temperature_critically"}),
    ]
    fsm._event_bus.fire.assert_has_calls(calls, any_order=False)
    fsm._analytics_handler.add_high_temp_warning_state_transition.assert_called_with(
        "critical", "warning", "critically", False
    )


def test_transistion_from_monitoring_to_critical():
    # Arrange
    fsm = HighTemperatureFSM(MagicMock(), False, MagicMock())
    fsm.start_monitoring()
    assert fsm.monitoring.is_active
    fsm._event_bus.fire = MagicMock()
    fsm._analytics_handler.add_high_temp_warning_state_transition = MagicMock()
    # Act
    fsm.critical()

    # Assert
    assert fsm.critically.is_active
    calls = [
        call(
            MrBeamEvents.HIGH_TEMPERATURE_CRITICAL_SHOW,
            {"trigger": "high_temperature_critically"},
        ),
        call(MrBeamEvents.LASER_JOB_ABORT, {"trigger": "high_temperature_critically"}),
        call(MrBeamEvents.LASER_HOME, {"trigger": "high_temperature_critically"}),
        call(
            MrBeamEvents.COMPRESSOR_DEACTIVATE,
            {"trigger": "high_temperature_critically"},
        ),
        call(
            MrBeamEvents.EXHAUST_DEACTIVATE, {"trigger": "high_temperature_critically"}
        ),
        call(MrBeamEvents.LED_ERROR_ENTER, {"trigger": "high_temperature_critically"}),
        call(MrBeamEvents.LASER_DEACTIVATE, {"trigger": "high_temperature_critically"}),
        call(MrBeamEvents.ALARM_ENTER, {"trigger": "high_temperature_critically"}),
    ]
    fsm._event_bus.fire.assert_has_calls(calls, any_order=False)
    fsm._analytics_handler.add_high_temp_warning_state_transition.assert_called_with(
        "critical", "monitoring", "critically", False
    )


def test_transistion_from_warning_to_dismissed():
    # Arrange
    fsm = HighTemperatureFSM(MagicMock(), False, MagicMock())
    fsm.start_monitoring()
    fsm.warn()
    assert fsm.warning.is_active
    fsm._event_bus.fire = MagicMock()
    fsm._analytics_handler.add_high_temp_warning_state_transition = MagicMock()
    # Act
    fsm.dismiss()

    # Assert
    assert fsm.dismissed.is_active
    calls = [
        call(
            MrBeamEvents.HIGH_TEMPERATURE_CRITICAL_HIDE,
            {"trigger": "high_temperature_dismissed"},
        ),
        call(
            MrBeamEvents.HIGH_TEMPERATURE_WARNING_HIDE,
            {"trigger": "high_temperature_dismissed"},
        ),
        call(MrBeamEvents.LED_ERROR_EXIT, {"trigger": "high_temperature_dismissed"}),
        call(
            MrBeamEvents.ALARM_EXIT,
            {"trigger": "high_temperature_dismissed"},
        ),
    ]
    fsm._event_bus.fire.assert_has_calls(calls, any_order=False)
    fsm._analytics_handler.add_high_temp_warning_state_transition.assert_called_with(
        "dismiss", "warning", "dismissed", False
    )


def test_transistion_from_critical_to_dismissed():
    # Arrange
    fsm = HighTemperatureFSM(MagicMock(), False, MagicMock())
    fsm.start_monitoring()
    fsm.warn()
    fsm.critical()
    assert fsm.critically.is_active
    fsm._event_bus.fire = MagicMock()
    fsm._analytics_handler.add_high_temp_warning_state_transition = MagicMock()
    # Act
    fsm.dismiss()

    # Assert
    assert fsm.dismissed.is_active
    calls = [
        call(
            MrBeamEvents.HIGH_TEMPERATURE_CRITICAL_HIDE,
            {"trigger": "high_temperature_dismissed"},
        ),
        call(
            MrBeamEvents.HIGH_TEMPERATURE_WARNING_HIDE,
            {"trigger": "high_temperature_dismissed"},
        ),
        call(MrBeamEvents.LED_ERROR_EXIT, {"trigger": "high_temperature_dismissed"}),
        call(
            MrBeamEvents.ALARM_EXIT,
            {"trigger": "high_temperature_dismissed"},
        ),
    ]
    fsm._event_bus.fire.assert_has_calls(calls, any_order=False)
    fsm._analytics_handler.add_high_temp_warning_state_transition.assert_called_with(
        "dismiss", "critically", "dismissed", False
    )


def test_transistion_from_dismissed_to_deactivated():
    # Arrange
    fsm = HighTemperatureFSM(MagicMock(), False, MagicMock())
    fsm.start_monitoring()
    fsm.warn()
    fsm.critical()
    fsm.dismiss()
    assert fsm.dismissed.is_active
    fsm._analytics_handler.add_high_temp_warning_state_transition = MagicMock()
    # Act
    fsm.deactivate()

    # Assert
    assert fsm.deactivated.is_active
    fsm._analytics_handler.add_high_temp_warning_state_transition.assert_called_with(
        "deactivate", "dismissed", "deactivated", False
    )


def test_transistion_from_warning_to_monitoring():
    # Arrange
    fsm = HighTemperatureFSM(MagicMock(), False, MagicMock())
    fsm.start_monitoring()
    fsm.warn()
    assert fsm.warning.is_active
    fsm._analytics_handler.add_high_temp_warning_state_transition = MagicMock()
    # Act
    fsm.dismiss()

    # Assert
    assert fsm.dismissed.is_active
    fsm._analytics_handler.add_high_temp_warning_state_transition.assert_called_with(
        "dismiss", "warning", "dismissed", False
    )


def test_feature_is_disabled_transition_from_monitoring_to_warning():
    # Arrange
    fsm = HighTemperatureFSM(MagicMock(), True, MagicMock())
    fsm.start_monitoring()
    assert fsm.monitoring.is_active
    fsm._analytics_handler.add_high_temp_warning_state_transition = MagicMock()
    fsm._event_bus.fire = MagicMock()
    # Act
    fsm.warn()

    # Assert
    assert fsm.monitoring.is_active
    fsm._event_bus.fire.assert_not_called()
    calls = [
        call("warn", "monitoring", "warning", True),
        call("silent_dismiss", "warning", "monitoring", True),
    ]
    fsm._analytics_handler.add_high_temp_warning_state_transition.assert_has_calls(
        calls, any_order=False
    )


def test_feature_is_disabled_transition_from_monitoring_to_critical():
    # Arrange
    fsm = HighTemperatureFSM(MagicMock(), True, MagicMock())
    fsm.start_monitoring()
    assert fsm.monitoring.is_active
    fsm._analytics_handler.add_high_temp_warning_state_transition = MagicMock()
    fsm._event_bus.fire = MagicMock()
    # Act
    fsm.critical()

    # Assert
    assert fsm.dismissed.is_active
    fsm._event_bus.fire.assert_not_called()
    calls = [
        call("critical", "monitoring", "critically", True),
        call("silent_dismiss", "critically", "dismissed", True),
    ]
    fsm._analytics_handler.add_high_temp_warning_state_transition.assert_has_calls(
        calls, any_order=False
    )


def test_event_trigger_HIGH_TEMPERATURE_WARNING_DISMISSED(high_temp_fsm):
    # Arrange

    high_temp_fsm.start_monitoring()
    high_temp_fsm.warn()
    assert high_temp_fsm.warning.is_active

    # Act
    high_temp_fsm._event_bus.fire(MrBeamEvents.HIGH_TEMPERATURE_WARNING_DISMISSED)

    # Assert
    time.sleep(0.1)
    assert high_temp_fsm.dismissed.is_active


def test_event_trigger_HIGH_TEMPERATURE_CRITICAL_DISMISSED(high_temp_fsm):
    # Arrange

    high_temp_fsm.start_monitoring()
    high_temp_fsm.warn()
    high_temp_fsm.critical()
    assert high_temp_fsm.critically.is_active

    # Act
    high_temp_fsm._event_bus.fire(MrBeamEvents.HIGH_TEMPERATURE_CRITICAL_DISMISSED)

    # Assert
    time.sleep(0.1)
    assert high_temp_fsm.dismissed.is_active


def test_event_trigger_LASER_COOLING_TO_SLOW(high_temp_fsm):
    high_temp_fsm.start_monitoring()
    assert high_temp_fsm.monitoring.is_active

    # Act
    high_temp_fsm._event_bus.fire(MrBeamEvents.LASER_COOLING_TO_SLOW)

    # Assert
    time.sleep(0.1)
    assert high_temp_fsm.warning.is_active


def test_event_trigger_LASER_HIGH_TEMPERATURE(high_temp_fsm):
    high_temp_fsm.start_monitoring()
    assert high_temp_fsm.monitoring.is_active

    # Act
    high_temp_fsm._event_bus.fire(MrBeamEvents.LASER_HIGH_TEMPERATURE)

    # Assert
    time.sleep(0.1)
    assert high_temp_fsm.critically.is_active


def test_event_trigger_LASER_COOLING_RESUME(high_temp_fsm):
    high_temp_fsm.start_monitoring()
    assert high_temp_fsm.monitoring.is_active

    # Act
    high_temp_fsm._event_bus.fire(MrBeamEvents.LASER_COOLING_RESUME)

    # Assert
    time.sleep(0.1)
    assert high_temp_fsm.deactivated.is_active


def test_event_trigger_LASER_COOLING_TEMPERATURE_REACHED(high_temp_fsm):
    assert high_temp_fsm.deactivated.is_active

    # Act
    high_temp_fsm._event_bus.fire(MrBeamEvents.LASER_COOLING_TEMPERATURE_REACHED)

    # Assert
    time.sleep(0.1)
    assert high_temp_fsm.monitoring.is_active
