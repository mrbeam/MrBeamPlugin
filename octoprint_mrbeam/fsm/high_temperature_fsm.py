from statemachine import State
from statemachine import StateMachine

from octoprint_mrbeam.mrbeam_events import MrBeamEvents


class HighTemperatureFSM(StateMachine):
    deactivated = State("Deactivated", initial=True)
    monitoring = State("Monitoring")
    warning = State("Warning")
    criticaly = State("Criticaly")
    dismissed = State("Dismissed")

    start_monitoring = deactivated.to(monitoring)
    warn = monitoring.to(warning) | warning.to(criticaly)
    critical = warning.to(criticaly) | monitoring.to(criticaly)
    dismiss = warning.to(dismissed) | criticaly.to(dismissed)
    deactivate = dismissed.to(deactivated) | monitoring.to(deactivated)

    def __int__(self, event_bus=None):
        self._event_bus = event_bus
        self._subscribe_to_events()

    # def on_enter_<state>.... for handling state enter
    # def on_exit_<state>.... for handling state exit
    def on_enter_warning(self):
        payload = {"trigger": "high_temperature_warning"}
        self._event_bus.fire(MrBeamEvents.HIGH_TEMPERATURE_WARNING_SHOW, payload)

    def on_enter_criticaly(self):
        payload = {"trigger": "high_temperature_criticaly"}
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
        payload = {"trigger": "high_temperature_dismissed"}
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
