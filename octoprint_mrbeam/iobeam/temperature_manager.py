import threading
import time
from octoprint.events import Events as OctoPrintEvents

from octoprint_mrbeam.util.uptime import get_uptime
from octoprint_mrbeam.mrbeam_events import MrBeamEvents
from octoprint_mrbeam.iobeam.iobeam_handler import IoBeamEvents, IoBeamValueEvents
from octoprint_mrbeam.mrb_logger import mrb_logger

# singleton
_instance = None


def temperatureManager(plugin):
    global _instance
    if _instance is None:
        _instance = TemperatureManager(plugin)
    return _instance


# This guy manages the temperature of the laser head
class TemperatureManager(object):
    TEMP_TIMER_INTERVAL = 3
    TEMP_MAX_AGE = 10  # seconds

    COOLING_THRESHOLD_CHECK_INTERVAL = 20  # seconds, only check every x seconds if the expected threshold for cooling is reached
    HYTERESIS_TEMPERATURE = (
        8  # degrees, if the temperature is below this value we can continue the job
    )

    # The laser should cool FIRST_COOLING_THRESHOLD_TEMPERATURE in under FIRST_COOLING_THRESHOLD_TIME seconds
    FIRST_COOLING_THRESHOLD_TEMPERATURE = 4  # degrees
    FIRST_COOLING_THRESHOLD_TIME = 40  # seconds

    # The laser should cool SECOND_COOLING_THRESHOLD_TEMPERATURE in under SECOND_COOLING_THRESHOLD_TIME seconds
    SECOND_COOLING_THRESHOLD_TEMPERATURE = 6  # degrees
    SECOND_COOLING_THRESHOLD_TIME = 60  # seconds

    # The laser should cool THIRD_COOLING_THRESHOLD_TEMPERATURE in under THIRD_COOLING_THRESHOLD_TIME seconds
    THIRD_COOLING_THRESHOLD_TEMPERATURE = 6  # degrees
    THIRD_COOLING_THRESHOLD_TIME = 140  # seconds

    def __init__(self, plugin):
        self._logger = mrb_logger("octoprint.plugins.mrbeam.iobeam.temperaturemanager")
        self._plugin = plugin
        self._event_bus = plugin._event_bus
        self.temperature = None
        self.temperature_ts = 0
        self.temperature_max = (
            plugin.laserhead_handler.current_laserhead_max_temperature
        )
        self._high_tmp_warn_offset = (
            self._plugin.laserhead_handler.current_laserhead_high_temperature_warn_offset
        )
        self.cooling_duration = (
            plugin.laserCutterProfileManager.get_current_or_default()["laser"][
                "cooling_duration"
            ]
        )
        self.temp_timer = None
        self.cooling_tigger_time = None
        self.cooling_tigger_temperature = None
        self._msg_is_temperature_recent = None
        self._id_is_temperature_recent = None
        self._shutting_down = False
        self._iobeam = None
        self._analytics_handler = None
        self._one_button_handler = None
        self._last_cooling_threshold_check_time = 0

        self.dev_mode = plugin._settings.get_boolean(["dev", "iobeam_disable_warnings"])

        msg = "TemperatureManager: initialized. temperature_max: {max}, high_tmp_warn_threshold: {high_tmp_warn_threshold}, {key}: {value}".format(
            max=self.temperature_max,
            high_tmp_warn_threshold=self.high_tmp_warn_threshold,
            key="cooling_duration",
            value=self.cooling_duration,
        )
        self._logger.info(msg)

        self._event_bus.subscribe(
            MrBeamEvents.MRB_PLUGIN_INITIALIZED, self._on_mrbeam_plugin_initialized
        )
        self._event_bus.subscribe(
            MrBeamEvents.LASER_JOB_ABORTED,
            self._on_event_laser_job_aborted,
        )

    def _on_mrbeam_plugin_initialized(self, event, payload):
        self._iobeam = self._plugin.iobeam
        self._analytics_handler = self._plugin.analytics_handler
        self._one_button_handler = self._plugin.onebutton_handler
        self._subscribe()
        self._start_temp_timer()

    def _on_event_laser_job_aborted(self, event, payload):
        """
        Called when a laser job is aborted. Will reset the temperature manager.
        Args:
            event: event name
            payload: payload of the event

        Returns:
            None
        """
        self.reset({"event": event})

    def _subscribe(self):
        self._iobeam.subscribe(IoBeamValueEvents.LASER_TEMP, self.handle_temp)

        self._iobeam.subscribe(IoBeamValueEvents.LASERHEAD_CHANGED, self.reset)

        self._event_bus.subscribe(OctoPrintEvents.PRINT_DONE, self.onEvent)
        self._event_bus.subscribe(OctoPrintEvents.PRINT_FAILED, self.onEvent)
        self._event_bus.subscribe(OctoPrintEvents.PRINT_CANCELLED, self.onEvent)
        self._event_bus.subscribe(OctoPrintEvents.SHUTDOWN, self.onEvent)

    def shutdown(self):
        self._shutting_down = True

    def reset(self, kwargs):
        """Resets the temperature manager to its initial state.

        Args:
            kwargs:

        Returns:
            None
        """
        self._logger.info(
            "TemperatureManager: Reset trigger Received : {}".format(
                kwargs.get("event", None)
            )
        )
        self.temperature_max = (
            self._plugin.laserhead_handler.current_laserhead_max_temperature
        )
        self._high_tmp_warn_offset = (
            self._plugin.laserhead_handler.current_laserhead_high_temperature_warn_offset
        )
        self.cooling_duration = (
            self._plugin.laserCutterProfileManager.get_current_or_default()["laser"][
                "cooling_duration"
            ]
        )
        self.cooling_tigger_time = None
        self.cooling_tigger_temperature = None
        self._last_cooling_threshold_check_time = 0

        msg = "TemperatureManager: Reset Done. temperature_max: {max}, high_tmp_warn_threshold: {high_tmp_warn_threshold}, {key}: {value}".format(
            max=self.temperature_max,
            high_tmp_warn_threshold=self.high_tmp_warn_threshold,
            key="cooling_duration",
            value=self.cooling_duration,
        )
        self._logger.info(msg)

    @property
    def high_tmp_warn_threshold(self):
        """Returns the temperature at which the user should be warned that the laserhead is too hot."""
        return self.temperature_max + self._high_tmp_warn_offset

    def onEvent(self, event, payload):
        self._logger.debug("TemperatureManager: Event received: {}".format(event))
        if event == IoBeamValueEvents.LASER_TEMP:
            self.handle_temp(payload)
        elif event in (
            OctoPrintEvents.PRINT_DONE,
            OctoPrintEvents.PRINT_FAILED,
            OctoPrintEvents.PRINT_CANCELLED,
        ):

            self.reset({"event": event})
        elif event == OctoPrintEvents.SHUTDOWN:
            self.shutdown()

    def handle_temp(self, kwargs):
        self.temperature = kwargs["temp"]
        if self.temperature_ts <= 0:
            self._logger.info(
                "laser_temp - first temperature from laserhead: %s", self.temperature
            )
        self.temperature_ts = time.time()
        self._check_temp_val()
        self._analytics_handler.collect_laser_temp_value(self.temperature)

    def cooling_stop(self, err_msg=None):
        """Stop the laser for cooling purpose."""
        if self._one_button_handler and self._one_button_handler.is_printing():
            self._logger.info(
                "cooling_stop() %s - _msg_is_temperature_recent: %s",
                err_msg,
                self._msg_is_temperature_recent,
                analytics=self._id_is_temperature_recent,
            )
            self.cooling_tigger_temperature = self.temperature
            self.cooling_tigger_time = get_uptime()

            self._one_button_handler.cooling_down_pause()
            self._event_bus.fire(
                MrBeamEvents.LASER_COOLING_PAUSE, dict(temp=self.temperature)
            )

    def cooling_resume(self):
        """
        Resume laser once the laser has cooled down enough.

        Returns:
            None
        """
        self._logger.debug("cooling_resume()")
        self._event_bus.fire(
            MrBeamEvents.LASER_COOLING_RESUME, dict(temp=self.temperature)
        )
        self._one_button_handler.cooling_down_end(only_if_behavior_is_cooling=True)
        self.cooling_tigger_time = None
        self.cooling_tigger_temperature = None

    def get_temperature(self):
        return self.temperature

    def is_cooling(self):
        return self.cooling_tigger_time is not None

    @property
    def cooling_since(self):
        """
        Returns the duration of the cooling process in seconds.
        Is 0 if cooling is currently not active.

        Returns:
            int: duration of cooling process in seconds

        """
        return get_uptime() - self.cooling_tigger_time if self.is_cooling() else 0

    def is_temperature_recent(self):
        if self.temperature is None:
            self._msg_is_temperature_recent = "is_temperature_recent(): Laser temperature is None. never received a temperature value."
            self._id_is_temperature_recent = "laser-temperature-none"
            return False
        age = time.time() - self.temperature_ts
        if age > self.TEMP_MAX_AGE:
            self._msg_is_temperature_recent = (
                "is_temperature_recent(): Laser temperature too old: must be more recent than %s s but actual age is %s s"
                % (self.TEMP_MAX_AGE, age)
            )
            self._id_is_temperature_recent = "laser-temperature-old"
            return False
        self._msg_is_temperature_recent = None
        self._id_is_temperature_recent = None
        return True

    def _temp_timer_callback(self):
        try:
            if not self._shutting_down:
                # self.request_temp()
                self._stop_if_temp_is_not_current()
                self._start_temp_timer()
        except:
            self._logger.exception("Exception in _temp_timer_callback(): ")
            # this might have been the reason for the exception. Let's try to stay alive anyway...
            self._start_temp_timer()

    def _start_temp_timer(self):
        if not self._shutting_down:
            self.temp_timer = threading.Timer(
                self.TEMP_TIMER_INTERVAL, self._temp_timer_callback
            )
            self.temp_timer.daemon = True
            self.temp_timer.name = "TemperatureTimer"
            self.temp_timer.start()
        else:
            self._logger.debug("Shutting down.")

    def _stop_if_temp_is_not_current(self):
        if not self.is_temperature_recent():
            self.cooling_stop(err_msg="Laser temperature is not recent. Stopping laser")

    def dismiss_high_temperature_warning(self):
        """Dismisses the high temperature warning.

        Returns:
            None
        """
        self._event_bus.fire(MrBeamEvents.HIGH_TEMPERATURE_WARNING_DISMISSED)

    @property
    def cooling_difference(self):
        """
        Returns the difference between the current temperature and the temperature when the cooling process was started.

        Returns:
            int: difference in degrees Celsius
        """
        return (
            self.cooling_tigger_temperature - self.temperature
            if self.is_cooling()
            else 0
        )

    def _fire_cooling_to_slow_event(self):
        """
        Fires the event that the cooling process is slowing down.

        Returns:
            None
        """
        self._event_bus.fire(
            MrBeamEvents.LASER_COOLING_TO_SLOW,
            dict(
                temp=self.temperature,
                cooling_differnece=self.cooling_difference,
                cooling_time=self.cooling_since,
            ),
        )

    def _check_temp_val(self):
        """
        Checks the current temperature value and fires events if necessary.

        Returns:
            None
        """
        if self.temperature is None:
            self._logger.error("Laser temperature is None.")
            msg = "Laser temperature not available, assuming high temperature and stop for cooling."
            self.cooling_stop(err_msg=msg)
            return
        # critical high temperature
        if self.temperature > self.high_tmp_warn_threshold:
            self._logger.warn(
                "High temperature warning triggered: tmp:%s threshold: %s",
                self.temperature,
                self.high_tmp_warn_threshold,
            )
            self._event_bus.fire(
                MrBeamEvents.LASER_HIGH_TEMPERATURE,
                dict(
                    tmp=self.temperature,
                    threshold=self.high_tmp_warn_threshold,
                ),
            )

        # cooling break
        if not self.is_cooling() and self.temperature > self.temperature_max:
            msg = "Laser temperature exceeded limit. Current temp: %s, max: %s" % (
                self.temperature,
                self.temperature_max,
            )
            self.cooling_stop(err_msg=msg)  # trigger a cooling stop

        elif self.is_cooling():
            self._check_cooling_threshold()

            # resume job if temperature is low enough after 25 seconds
            if (
                self.cooling_since > self.cooling_duration
                and self.cooling_difference >= self.HYTERESIS_TEMPERATURE
            ):
                self._logger.warn(
                    "Cooling break duration passed: %ss - Current temp: %s",
                    self.cooling_duration,
                    self.temperature,
                )
                self.cooling_resume()
            else:
                # self._logger.debug("Laser temperature nothing. Current temp: %s, self.is_cooling(): %s", self.temperatur, self.is_cooling())
                pass

    def _check_cooling_threshold(self):
        """
        Checks if the cooling thresholds are met and fires the corresponding events.

        Returns:
            None
        """
        # only check every COOLING_THRESHOLD_CHECK_INTERVAL seconds for the cooling thresholds
        if (
            get_uptime() - self._last_cooling_threshold_check_time
            > self.COOLING_THRESHOLD_CHECK_INTERVAL
        ):
            self._last_cooling_threshold_check_time = get_uptime()
            if (
                self.cooling_difference >= self.FIRST_COOLING_THRESHOLD_TEMPERATURE
                and self.cooling_since > self.FIRST_COOLING_THRESHOLD_TIME
            ) or (
                self.cooling_difference >= self.SECOND_COOLING_THRESHOLD_TEMPERATURE
                and self.cooling_since > self.SECOND_COOLING_THRESHOLD_TIME
            ):
                # expected cooling effect is met but hysteresis is not reached, re trigger cooling fan to speed up
                self._event_bus.fire(MrBeamEvents.LASER_COOLING_RE_TRIGGER_FAN)
            elif (
                self.cooling_difference < self.SECOND_COOLING_THRESHOLD_TEMPERATURE
                and self.cooling_since > self.SECOND_COOLING_THRESHOLD_TIME
            ) or self.cooling_since > self.THIRD_COOLING_THRESHOLD_TIME:
                # expected cooling effect is not met something is wrong
                self._fire_cooling_to_slow_event()
