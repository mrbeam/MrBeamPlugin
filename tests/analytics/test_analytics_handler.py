import time

import pytest
from mock.mock import MagicMock

from octoprint_mrbeam import MrBeamEvents
from octoprint_mrbeam.analytics.analytics_handler import AnalyticsHandler

from octoprint_mrbeam.analytics.analytics_keys import AnalyticsKeys


@pytest.fixture
def analytics_handler(monkeypatch, mrbeam_plugin):
    monkeypatch.setattr(
        "octoprint_mrbeam.analytics.uploader.AnalyticsFileUploader", MagicMock()
    )  # monkeypatch the uploader
    analytics_handler = AnalyticsHandler(mrbeam_plugin)
    analytics_handler._event_bus.fire(MrBeamEvents.MRB_PLUGIN_INITIALIZED)
    return analytics_handler


def test_add_high_temp_warning_state_transition(mrbeam_plugin):
    # Arrange
    analytics_handler = AnalyticsHandler(mrbeam_plugin)
    analytics_handler._add_device_event = MagicMock()
    event = "event"
    state_before = "state_before"
    state_after = "state_after"
    disabled = True
    # Act
    analytics_handler.add_high_temp_warning_state_transition(
        event, state_before, state_after, disabled
    )
    # Assert
    analytics_handler._add_device_event.assert_called_with(
        AnalyticsKeys.HighTemperatureWarning.Event.STATE_TRANSITION,
        payload={
            AnalyticsKeys.HighTemperatureWarning.State.STATE_BEFORE: state_before,
            AnalyticsKeys.HighTemperatureWarning.State.STATE_AFTER: state_after,
            AnalyticsKeys.HighTemperatureWarning.State.EVENT: event,
            AnalyticsKeys.HighTemperatureWarning.State.FEATURE_DISABLED: disabled,
        },
        header_extension={AnalyticsKeys.Header.FEATURE_ID: "SW-991"},
    )


def test_on_event_high_temperature_dismissed(analytics_handler):
    # Arrange
    analytics_handler._add_device_event = MagicMock()

    # Act
    analytics_handler._event_bus.fire(MrBeamEvents.HIGH_TEMPERATURE_WARNING_DISMISSED)

    # Assert
    time.sleep(0.1)
    analytics_handler._add_device_event.assert_called_with(
        AnalyticsKeys.Device.HighTemp.WARNING_DISMISSED,
        header_extension={AnalyticsKeys.Header.FEATURE_ID: "SW-991"},
    )


def test_on_event_high_temperature_warning(analytics_handler):
    # Arrange
    analytics_handler._add_device_event = MagicMock()

    # Act
    analytics_handler._event_bus.fire(MrBeamEvents.HIGH_TEMPERATURE_CRITICAL_DISMISSED)

    # Assert that the mock method was called
    time.sleep(0.1)
    analytics_handler._add_device_event.assert_called_with(
        AnalyticsKeys.Device.HighTemp.CRITICAL_DISMISSED,
        header_extension={AnalyticsKeys.Header.FEATURE_ID: "SW-991"},
    )


def test_on_event_laser_cooling_to_slow(analytics_handler):
    # Arrange
    analytics_handler._add_device_event = MagicMock()

    # Act
    analytics_handler._event_bus.fire(MrBeamEvents.LASER_COOLING_RE_TRIGGER_FAN)

    # Assert that the mock method was called
    time.sleep(0.1)
    analytics_handler._add_device_event.assert_called_with(
        AnalyticsKeys.Job.Event.Cooling.COOLING_FAN_RETRIGGER,
        header_extension={AnalyticsKeys.Header.FEATURE_ID: "SW-991"},
    )


def test_on_event_laser_cooling_re_trigger_fan(analytics_handler):
    # Arrange
    analytics_handler._add_device_event = MagicMock()

    # Act
    analytics_handler._event_bus.fire(MrBeamEvents.LASER_COOLING_RE_TRIGGER_FAN)

    # Assert that the mock method was called
    time.sleep(0.1)
    analytics_handler._add_device_event.assert_called_with(
        AnalyticsKeys.Job.Event.Cooling.COOLING_FAN_RETRIGGER,
        header_extension={AnalyticsKeys.Header.FEATURE_ID: "SW-991"},
    )


def test_on_event_laser_high_temperature(analytics_handler, mrbeam_plugin):
    # Arrange
    analytics_handler._add_device_event = MagicMock()
    mrbeam_plugin.temperature_manager.high_tmp_warn_threshold = 60

    # Act
    analytics_handler._event_bus.fire(MrBeamEvents.LASER_HIGH_TEMPERATURE, dict(tmp=1))

    # Assert that the mock method was called
    time.sleep(0.1)
    analytics_handler._add_device_event.assert_called_with(
        AnalyticsKeys.Device.Event.LASER_HIGH_TEMPERATURE,
        header_extension={AnalyticsKeys.Header.FEATURE_ID: "SW-991"},
        payload={"temperature": 1, "threshold": 60},
    )


def test_on_event_high_temperature_shown_critical(analytics_handler):
    # Arrange
    analytics_handler._add_device_event = MagicMock()

    # Act
    analytics_handler._event_bus.fire(MrBeamEvents.HIGH_TEMPERATURE_CRITICAL_SHOW)

    # Assert that the mock method was called
    time.sleep(0.1)
    analytics_handler._add_device_event.assert_called_with(
        AnalyticsKeys.Device.HighTemp.CRITICAL_SHOWN,
        header_extension={AnalyticsKeys.Header.FEATURE_ID: "SW-991"},
    )


def test_on_event_high_temperature_shown_warning(analytics_handler):
    # Arrange
    analytics_handler._add_device_event = MagicMock()

    # Act
    analytics_handler._event_bus.fire(MrBeamEvents.HIGH_TEMPERATURE_WARNING_SHOW)

    # Assert that the mock method was called
    time.sleep(0.1)
    analytics_handler._add_device_event.assert_called_with(
        AnalyticsKeys.Device.HighTemp.WARNING_SHOWN,
        header_extension={AnalyticsKeys.Header.FEATURE_ID: "SW-991"},
    )
