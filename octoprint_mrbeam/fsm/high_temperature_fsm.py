"""FSM of the high temperature warning feature.

See SW-1158 and the epic SW-991
"""
from octoprint_mrbeam.mrb_logger import mrb_logger
from statemachine import State
from statemachine import StateMachine

from octoprint_mrbeam.mrbeam_events import MrBeamEvents


class HighTemperatureFSM(StateMachine):
    """FSM of the high temperature warning feature."""

    deactivated = State("Deactivated", initial=True)
    monitoring = State("Monitoring")
    warning = State("Warning")
    critically = State("Critically")
    dismissed = State("Dismissed")

    start_monitoring = deactivated.to(monitoring)
    warn = monitoring.to(warning) | warning.to(critically)
    critical = warning.to(critically) | monitoring.to(critically)
    dismiss = warning.to(dismissed) | critically.to(dismissed)
    deactivate = dismissed.to(deactivated) | monitoring.to(deactivated)
    silent_dismiss = warning.to(monitoring) | critically.to(dismissed)

    def __init__(self, event_bus=None, disabled=False, analytics_handler=None):
        """Initialize the FSM.

        Args:
            event_bus: event bus of octoprint
            disabled: if the warnings should be disabled
            analytics_handler: analytics handler of the MrBeamPlugin
        """
        super(HighTemperatureFSM, self).__init__()
        self._logger = mrb_logger("octoprint.plugins.mrbeam.fsm.high_temperature_fsm")
        self._event_bus = event_bus
        self._subscribe_to_events()
        self._disabled = disabled
        self._analytics_handler = analytics_handler

    # def on_enter_<state>.... for handling state enter
    # def on_exit_<state>.... for handling state exit
    def on_enter_warning(self):
        """Handle the state enter of the warning state.

        Returns:
            None
        """
        self._logger.info("on_enter_warning")
        payload = {"trigger": "high_temperature_warning"}
        if self._disabled:
            self._logger.info(
                "Warning state entered but feature is disabled. Will silent dismiss."
            )
            self.silent_dismiss()
        else:
            self._event_bus.fire(MrBeamEvents.HIGH_TEMPERATURE_WARNING_SHOW, payload)
            self._event_bus.fire(MrBeamEvents.LED_ERROR_ENTER, payload)

    def on_enter_critically(self):
        """Handle the state enter of the critically state.

        Returns:
            None
        """
        self._logger.info("on_enter_critically")
        payload = {"trigger": "high_temperature_critically"}
        if self._disabled:
            self._logger.info(
                "Critical state entered but feature is disabled. Will silent dismiss."
            )
            self.silent_dismiss()
        else:
            self._event_bus.fire(
                MrBeamEvents.HIGH_TEMPERATURE_CRITICAL_SHOW, payload
            )  # or SHOW_HIGH_TEMPERATURE_WARNING
            self._event_bus.fire(MrBeamEvents.LASER_JOB_ABORT, payload)
            self._event_bus.fire(MrBeamEvents.LASER_HOME, payload)
            self._event_bus.fire(MrBeamEvents.COMPRESSOR_DEACTIVATE, payload)
            self._event_bus.fire(MrBeamEvents.EXHAUST_DEACTIVATE, payload)
            self._event_bus.fire(MrBeamEvents.LED_ERROR_ENTER, payload)
            self._event_bus.fire(MrBeamEvents.ALARM_ENTER, payload)

    def on_enter_dismissed(self):
        """Handle the state enter of the dismissed state.

        Returns:
            None
        """
        self._logger.info("on_enter_dismissed")
        payload = {"trigger": "high_temperature_dismissed"}
        if self._disabled:
            self._logger.info(
                "Dismissed state entered but feature is disabled. Will do nothing."
            )
        else:
            self._event_bus.fire(MrBeamEvents.HIGH_TEMPERATURE_CRITICAL_HIDE, payload)
            self._event_bus.fire(MrBeamEvents.HIGH_TEMPERATURE_WARNING_HIDE, payload)
            self._event_bus.fire(MrBeamEvents.LED_ERROR_EXIT, payload)
            self._event_bus.fire(MrBeamEvents.ALARM_EXIT, payload)

    def before_start_monitoring(self, event_data=None):
        """Handle the before state enter of the monitoring state.

        Args:
            event_data: event data of the event that triggered the transition

        Returns:
            None
        """
        self._add_transistion_analytics_entry(event_data)

    def before_warn(self, event_data=None):
        """Handle the before state enter of the warning state.

        Args:
            event_data: event data of the event that triggered the transition

        Returns:
            None
        """
        self._add_transistion_analytics_entry(event_data)

    def before_critical(self, event_data=None):
        """Handle the before state enter of the critical state.

        Args:
            event_data: event data of the event that triggered the transition

        Returns:
            None
        """
        self._add_transistion_analytics_entry(event_data)

    def before_dismiss(self, event_data=None):
        """Handle the before state enter of the dismissed state.

        Args:
            event_data: event data of the event that triggered the transition

        Returns:
            None
        """
        self._add_transistion_analytics_entry(event_data)

    def before_deactivate(self, event_data=None):
        """Handle the before state enter of the deactivated state.

        Args:
            event_data: event data of the event that triggered the transition

        Returns:
            None
        """
        self._add_transistion_analytics_entry(event_data)

    def before_silent_dismiss(self, event_data=None):
        """Handle the before state enter of the silent dismissed state.

        Args:
            event_data: event data of the event that triggered the transition

        Returns:
            None
        """
        self._add_transistion_analytics_entry(event_data)

    def _add_transistion_analytics_entry(self, event_data):
        """Add an analytics entry for the state transition.

        Args:
            event_data: event data of the event that triggered the transition

        Returns:
            None
        """
        self._logger.info(
            "Event %s - Transition from %s to %s",
            event_data.event,
            event_data.transition.source.id,
            event_data.transition.target.id,
        )
        self._analytics_handler.add_high_temp_warning_state_transition(
            event_data.event,
            event_data.transition.source.id,
            event_data.transition.target.id,
            self._disabled,
        )

    def _subscribe_to_events(self):
        """Subscribe to the events of the event bus.

        Returns:
            None
        """
        self._event_bus.subscribe(
            MrBeamEvents.HIGH_TEMPERATURE_WARNING_DISMISSED,
            self._on_event_dismissed,
        )
        self._event_bus.subscribe(
            MrBeamEvents.HIGH_TEMPERATURE_CRITICAL_DISMISSED,
            self._on_event_dismissed,
        )
        self._event_bus.subscribe(
            MrBeamEvents.LASER_COOLING_TO_SLOW, self._on_event_laser_cooling_to_slow
        )
        self._event_bus.subscribe(
            MrBeamEvents.LASER_HIGH_TEMPERATURE, self._on_event_laser_high_temperature
        )
        self._event_bus.subscribe(
            MrBeamEvents.LASER_COOLING_RESUME, self._on_event_laser_cooling_resume
        )
        self._event_bus.subscribe(
            MrBeamEvents.LASER_COOLING_TEMPERATURE_REACHED,
            self._on_event_laser_cooling_temperature_reached,
        )

    def _on_event_laser_cooling_temperature_reached(self, event, payload):
        """Handle the event laser cooling temperature reached.

        Args:
            event: event that triggered the handler
            payload: payload of the event

        Returns:
            None
        """
        self._logger.info("on_event_laser_cooling_temperature_reached")
        if self.deactivated.is_active:
            self.start_monitoring()

    def _on_event_laser_cooling_to_slow(self, event, payload):
        """Handle the event laser cooling to slow.

        Args:
            event: event that triggered the handler
            payload: payload of the event

        Returns:
            None
        """
        self._logger.info("on_event_laser_cooling_to_slow")
        if self.monitoring.is_active or self.warning.is_active:
            self.warn()

    def _on_event_laser_high_temperature(self, event, payload):
        """Handle the event laser high temperature.

        Args:
            event: event that triggered the handler
            payload: payload of the event

        Returns:
            None
        """
        self._logger.info("on_event_Laser_High_Temperature")
        if self.monitoring.is_active or self.warning.is_active:
            self.critical()

    def _on_event_laser_cooling_resume(self, event, payload):
        """Handle the event laser cooling resume.

        Args:
            event: event that triggered the handler
            payload: payload of the event

        Returns:
            None
        """
        self._logger.info("on_event_laser_cooling_resume")
        if self.monitoring.is_active or self.dismissed.is_active:
            self.deactivate()

    def _on_event_dismissed(self, event, payload):
        """Handle the event dismissed.

        Args:
            event: event that triggered the handler
            payload: payload of the event

        Returns:
            None
        """
        self._logger.info("on_event_dismissed")
        if not self.dismissed.is_active:
            self.dismiss()
