from octoprint_mrbeam.mrb_logger import mrb_logger
from statemachine import State
from statemachine import StateMachine

from octoprint_mrbeam.mrbeam_events import MrBeamEvents


class HighTemperatureFSM(StateMachine):
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
        super(HighTemperatureFSM, self).__init__()
        self._event_bus = event_bus
        self._subscribe_to_events()
        self._disabled = disabled
        self._analytics_handler = analytics_handler
        self._logger = mrb_logger("octoprint.plugins.mrbeam.fsm.high_temperature_fsm")

    # def on_enter_<state>.... for handling state enter
    # def on_exit_<state>.... for handling state exit
    def on_enter_warning(self):
        self._logger.info("on_enter_warning")
        payload = {"trigger": "high_temperature_warning"}
        if self._disabled:
            self._logger.info(
                "Warning state entered but feature is disabled. Will silent dismiss."
            )
            self.silent_dismiss()
        else:
            self._event_bus.fire(MrBeamEvents.HIGH_TEMPERATURE_WARNING_SHOW, payload)

    def on_enter_critically(self):
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
            self._event_bus.fire(MrBeamEvents.LASER_DEACTIVATE, payload)
            self._event_bus.fire(MrBeamEvents.ALARM_ENTER, payload)

    def on_enter_dismissed(self):
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

    def _subscribe_to_events(self):
        self._event_bus.subscribe(
            MrBeamEvents.HIGH_TEMPERATURE_WARNING_DISMISSED,
            self.dismiss,
        )
        self._event_bus.subscribe(
            MrBeamEvents.HIGH_TEMPERATURE_CRITICAL_DISMISSED,
            self.dismiss,
        )
        self._event_bus.subscribe(MrBeamEvents.LASER_COOLING_TO_SLOW, self.warn)
        self._event_bus.subscribe(MrBeamEvents.LASER_HIGH_TEMPERATURE, self.critical)
        self._event_bus.subscribe(MrBeamEvents.LASER_COOLING_RESUME, self.deactivate)

    def before_start_monitoring(self, event_data=None):
        self._add_transistion_analytics_entry(event_data)

    def before_warn(self, event_data=None):
        self._add_transistion_analytics_entry(event_data)

    def before_critical(self, event_data=None):
        self._add_transistion_analytics_entry(event_data)

    def before_dismiss(self, event_data=None):
        self._add_transistion_analytics_entry(event_data)

    def before_deactivate(self, event_data=None):
        self._add_transistion_analytics_entry(event_data)

    def before_silent_dismiss(self, event_data=None):
        self._add_transistion_analytics_entry(event_data)

    def _add_transistion_analytics_entry(self, event_data):
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
