import time
import threading
from octoprint.events import Events as OctoPrintEvents
from octoprint_mrbeam.mrbeam_events import MrBeamEvents
from octoprint_mrbeam.iobeam.iobeam_handler import IoBeamValueEvents, IoBeamEvents
from octoprint_mrbeam.mrb_logger import mrb_logger
from collections import deque

# singleton
_instance = None


def dustManager(plugin):
    global _instance
    if _instance is None:
        _instance = DustManager(plugin)
    return _instance


class DustManager(object):

    DEFAULT_VALIDATION_TIMER_INTERVAL = 3.0
    BOOST_TIMER_INTERVAL = 0.2
    MAX_TIMER_BOOST_DURATION = 3.0

    DEFAUL_DUST_MAX_AGE = 10  # seconds
    FAN_MAX_INTENSITY = 100

    FINAL_DUSTING_PHASE1_DURATION = 30
    FINAL_DUSTING_PHASE2_DURATION = 120
    FINAL_DUSTING_PHASE2_INTENSITY = 15

    FAN_COMMAND_RETRIES = 2
    FAN_COMMAND_WAITTIME = 1.0

    FAN_COMMAND_ON = "on"
    FAN_COMMAND_OFF = "off"
    FAN_COMMAND_AUTO = "auto"

    DATA_TYPE_DYNAMIC = "dynamic"
    DATA_TYPE_CONENCTED = "connected"

    FAN_TEST_RPM_PERCENTAGE = 50
    FAN_TEST_DURATION = 35  # seconds

    def __init__(self, plugin):
        self._plugin = plugin
        self._logger = mrb_logger("octoprint.plugins.mrbeam.iobeam.dustmanager")
        self.dev_mode = plugin._settings.get_boolean(["dev", "iobeam_disable_warnings"])
        self._event_bus = plugin._event_bus
        self._printer = plugin._printer

        self.is_final_extraction_mode = False

        self._state = None
        self._dust = None
        self._rpm = None
        self._connected = None
        self._data_ts = 0

        self._init_ts = time.time()
        self._last_event = None
        self._shutting_down = False
        self._final_extraction_thread = None
        self._continue_final_extraction = False
        self._user_abort_final_extraction = False
        self._validation_timer = None
        self._validation_timer_interval = self.DEFAULT_VALIDATION_TIMER_INTERVAL
        self._timer_boost_ts = 0
        self._fan_timers = []
        self._last_command = dict(action=None, value=None)
        self._just_initialized = False

        self._last_rpm_values = deque(maxlen=5)
        self._last_pressure_values = deque(maxlen=5)
        self._job_dust_values = []

        self.extraction_limit = 0.3
        self.extraction_limit = 0.01

        self._event_bus.subscribe(
            MrBeamEvents.MRB_PLUGIN_INITIALIZED, self._on_mrbeam_plugin_initialized
        )

    def _on_mrbeam_plugin_initialized(self, event, payload):
        self._usage_handler = self._plugin.usage_handler
        self._iobeam = self._plugin.iobeam
        self._analytics_handler = self._plugin.analytics_handler
        self._one_button_handler = self._plugin.onebutton_handler

        self._start_validation_timer()
        self._just_initialized = True
        self._logger.debug("initialized!")

        self._subscribe()

    def get_fan_state(self):
        return self._state

    def get_fan_rpm(self):
        return self._rpm

    def get_dust(self):
        return self._dust

    def get_mean_job_dust(self):
        if self._job_dust_values:
            mean_job_dust = sum(self._job_dust_values) / len(self._job_dust_values)
        else:
            mean_job_dust = None
        return mean_job_dust

    def is_fan_connected(self):
        return self._connected

    def set_user_abort_final_extraction(self):
        self._user_abort_final_extraction = True

    def shutdown(self):
        self._shutting_down = True

    def _subscribe(self):
        self._iobeam.subscribe(IoBeamValueEvents.DYNAMIC_VALUE, self._handle_fan_data)
        self._iobeam.subscribe(
            IoBeamValueEvents.EXHAUST_DYNAMIC_VALUE, self._handle_exhaust_data
        )
        self._iobeam.subscribe(
            IoBeamValueEvents.FAN_ON_RESPONSE, self._on_command_response
        )
        self._iobeam.subscribe(
            IoBeamValueEvents.FAN_OFF_RESPONSE, self._on_command_response
        )
        self._iobeam.subscribe(
            IoBeamValueEvents.FAN_AUTO_RESPONSE, self._on_command_response
        )
        self._event_bus.subscribe(IoBeamEvents.LID_OPENED, self._onEvent)
        self._event_bus.subscribe(MrBeamEvents.READY_TO_LASER_START, self._onEvent)
        self._event_bus.subscribe(IoBeamEvents.CONNECT, self._onEvent)
        self._event_bus.subscribe(MrBeamEvents.READY_TO_LASER_CANCELED, self._onEvent)
        self._event_bus.subscribe(MrBeamEvents.BUTTON_PRESS_REJECT, self._onEvent)
        self._event_bus.subscribe(OctoPrintEvents.SLICING_DONE, self._onEvent)
        self._event_bus.subscribe(OctoPrintEvents.PRINT_STARTED, self._onEvent)
        self._event_bus.subscribe(OctoPrintEvents.PRINT_DONE, self._onEvent)
        self._event_bus.subscribe(OctoPrintEvents.PRINT_FAILED, self._onEvent)
        self._event_bus.subscribe(OctoPrintEvents.PRINT_CANCELLED, self._onEvent)
        self._event_bus.subscribe(OctoPrintEvents.PRINT_RESUMED, self._onEvent)
        self._event_bus.subscribe(OctoPrintEvents.SHUTDOWN, self._onEvent)

    def _handle_exhaust_data(self, args):
        """
        hanldes exhaust data comming from iobeam EXHAUST_DYNAMIC_VALUE event

        Args:
            args: data from the iobeam event

        Returns:

        """
        pressure = args.get("pressure", None)
        if pressure is not None:
            self._logger.debug(
                "last pressure values append {} - {}".format(
                    pressure, self._last_pressure_values
                )
            )
            self._last_pressure_values.append(pressure)

    def _handle_fan_data(self, args):
        err = False
        if args["state"] is not None:
            self._state = args["state"]
        else:
            err = True
        if args["dust"] is not None:
            self._dust = args["dust"]

            if self._printer.is_printing():
                self._job_dust_values.append(self._dust)
        else:
            err = True
        if args["rpm"] is not None:
            self._rpm = args["rpm"]
        else:
            err = True

        self._connected = args["connected"]

        if self._connected is not None:
            self._unboost_timer_interval()

        if not err:
            self._data_ts = time.time()

        self._validate_values()
        self._send_dust_to_analytics(self._dust)

        self._last_rpm_values.append(self._rpm)

    def _on_command_response(self, args):
        self._logger.debug("Fan command response: %s", args)
        if args["success"]:
            if (
                "request_id" not in args["message"]
                or args["message"]["request_id"] != self._last_command
            ):
                # I'm not sure if we need to check or what to do if the command doesn't match.
                self._logger.warn(
                    "Fan command response doesn't match expected command: expected: {} received: {} args: {}".format(
                        self._last_command, args.get("response", None), args
                    )
                )
        else:
            # TODO ANDY stop laser
            self._logger.error(
                "Fan command responded error: received: fan:{} args: {}".format(
                    args["message"], args
                ),
                analytics="fan-command-error-response",
            )

    def _onEvent(self, event, payload):
        if event in (OctoPrintEvents.SLICING_DONE, MrBeamEvents.READY_TO_LASER_START):
            self._start_dust_extraction(cancel_all_timers=True)
            self._boost_timer_interval()
        elif event == OctoPrintEvents.PRINT_STARTED:
            # We start the test of the fan at 50%
            self._start_test_fan_rpm()
        elif event in (MrBeamEvents.BUTTON_PRESS_REJECT, OctoPrintEvents.PRINT_RESUMED):
            # just in case reset iobeam to start fan. In case fan got unplugged fanPCB might get restarted.
            self._start_dust_extraction(cancel_all_timers=False)
        elif event == MrBeamEvents.READY_TO_LASER_CANCELED:
            self._stop_dust_extraction()
            self._unboost_timer_interval()
        elif event in (
            OctoPrintEvents.PRINT_DONE,
            OctoPrintEvents.PRINT_FAILED,
            OctoPrintEvents.PRINT_CANCELLED,
        ):
            self._last_event = event
            self._do_final_extraction()
            self._job_dust_values = []
        elif event == OctoPrintEvents.SHUTDOWN:
            self.shutdown()
        elif event == IoBeamEvents.CONNECT:
            if self._just_initialized:
                self._stop_dust_extraction()
                self._just_initialized = False
        elif event == IoBeamEvents.LID_OPENED:
            if self.is_final_extraction_mode:
                self.set_user_abort_final_extraction()

    def _start_test_fan_rpm(self):
        self._logger.debug(
            "FAN_TEST_RPM: Start - setting fan to %s for %ssec",
            self.FAN_TEST_RPM_PERCENTAGE,
            self.FAN_TEST_DURATION,
        )
        self._start_dust_extraction(
            self.FAN_TEST_RPM_PERCENTAGE, cancel_all_timers=True
        )
        self._boost_timer_interval()

        t = threading.Timer(self.FAN_TEST_DURATION, self._finish_test_fan_rpm)
        t.setName("DustManager:_finish_test_fan_rpm")
        t.daemon = True
        t.start()
        self._fan_timers.append(t)

    def _finish_test_fan_rpm(self):
        try:
            # Write to analytics if the values are valid
            if self._validate_values():
                data = dict(
                    rpm_val=list(self._last_rpm_values),
                    fan_state=self._state,
                    usage_count=self._usage_handler.get_total_usage(),
                    prefilter_count=self._usage_handler.get_prefilter_usage(),
                    carbon_filter_count=self._usage_handler.get_carbon_filter_usage(),
                    pressure_val=list(self._last_pressure_values),
                )
                self._analytics_handler.add_fan_rpm_test(data)

            # Set fan to auto again
            self._logger.debug("FAN_TEST_RPM: End - setting fan to auto")
            self._start_dust_extraction(cancel_all_timers=False)
            self._boost_timer_interval()
        except:
            self._logger.exception("Exception in _finish_test_fan_rpm")

    def _pause_laser(self, trigger, analytics=None, log_message=None):
        """
        Stops laser and switches to paused mode.
        Should be called when air filters gets disconnected, dust value gets too high or when any error occurs...
        :param trigger: A string to identify the cause/trigger that initiated paused mode
        """
        if self._one_button_handler.is_printing():
            self._logger.error(log_message, analytics=analytics)
            self._logger.info("_pause_laser() trigger: %s", trigger)
            self._one_button_handler.pause_laser(need_to_release=False, trigger=trigger)

    def _start_dust_extraction(self, value=None, cancel_all_timers=True):
        """
        Turn on fan on auto mode or set to constant value.
        :param value: Default: auto. 0-100 if constant value required.
        :return:
        """
        if cancel_all_timers:
            self._cancel_all_fan_timers()
        if value is None or value == self.FAN_COMMAND_AUTO:
            self._send_fan_command(self.FAN_COMMAND_AUTO)
        else:
            if value > 100:
                value = 100
            elif value < 0:
                value = 0
            self._send_fan_command(self.FAN_COMMAND_ON, int(value))

    def _stop_dust_extraction(self):
        self._send_fan_command(self.FAN_COMMAND_OFF)

    def _cancel_all_fan_timers(self):
        try:
            c = []
            for t in self._fan_timers:
                if t is not None and t.is_alive():
                    c.append(t.getName())
                    t.cancel()
            self._continue_final_extraction = False
            self._user_abort_final_extraction = False
            self._fan_timers = []
            if c:
                self._logger.debug(
                    "_cancel_all_fan_timers: canceled %s timers: %s", len(c), c
                )
        except:
            self._logger.exception("Exception in _cancel_all_fan_timers:")

    def _do_final_extraction(self):
        if self._final_extraction_thread is None:
            self._final_extraction_thread = threading.Thread(
                target=self.__do_final_extraction_threaded
            )
            self._final_extraction_thread.daemon = True
            self._final_extraction_thread.start()

    def __do_final_extraction_threaded(self):
        try:
            self._cancel_all_fan_timers()
            if self._dust is not None:
                self._logger.debug(
                    "Final extraction: Starting trial extraction. current: {}, threshold: {}".format(
                        self._dust, self.extraction_limit
                    )
                )
                dust_start_ts = self._data_ts
                self._continue_final_extraction = True
                self._user_abort_final_extraction = False
                if self.__continue_dust_extraction(
                    self.extraction_limit, dust_start_ts
                ):
                    self._logger.debug("Final extraction: DUSTING_MODE_START")
                    self.is_final_extraction_mode = True
                    self._plugin.fire_event(MrBeamEvents.DUSTING_MODE_START)
                    self._start_dust_extraction(
                        self.FAN_MAX_INTENSITY, cancel_all_timers=False
                    )
                    while (
                        self._continue_final_extraction
                        and not self._user_abort_final_extraction
                        and self.__continue_dust_extraction(
                            self.extraction_limit, dust_start_ts
                        )
                    ):
                        time.sleep(1)
                    self.is_final_extraction_mode = False
                    self._logger.debug(
                        "Final extraction: DUSTING_MODE_START end. duration was: %s",
                        time.time() - dust_start_ts,
                    )
                if self._continue_final_extraction:
                    self._start_final_extraction_phase2(
                        self.FINAL_DUSTING_PHASE2_DURATION
                    )
                    self._continue_final_extraction = False
                    self.send_laser_job_event()

                self._final_extraction_thread = None
                self.is_final_extraction_mode = False
                self._user_abort_final_extraction = False
            else:
                self._logger.warning(
                    "No dust value received so far. Skipping trial dust extraction!"
                )
                self._stop_dust_extraction()
                self.is_final_extraction_mode = False
                self.send_laser_job_event()
        except:
            self._logger.exception("Exception in __do_final_extraction_threaded(): ")

    def send_laser_job_event(self):
        try:
            self._logger.debug("Last event: {}".format(self._last_event))
            my_event = None
            if self._last_event == OctoPrintEvents.PRINT_DONE:
                my_event = MrBeamEvents.LASER_JOB_DONE
            elif self._last_event == OctoPrintEvents.PRINT_CANCELLED:
                my_event = MrBeamEvents.LASER_JOB_CANCELLED
            elif self._last_event == OctoPrintEvents.PRINT_FAILED:
                my_event = MrBeamEvents.LASER_JOB_FAILED
            if my_event:
                # if this event comes to soon after the OP PrintDone, the actual order ca get mixed up.
                # Resend to make sure we end with a green state
                threading.Timer(
                    1.0, self._plugin.fire_event, [my_event, dict(resent=True)]
                ).start()
        except:
            self._logger.exception(
                "Exception send_laser_done_event send_laser_job_event(): "
            )

    def __continue_dust_extraction(self, value, started):
        if time.time() - started > self.FINAL_DUSTING_PHASE1_DURATION:
            return False
        if self._dust is not None and self._dust < value:
            return False
        return True

    def _start_final_extraction_phase2(self, value):
        self._logger.debug("Final extraction: Starting phase2 for %s secs", value)
        self._start_dust_extraction(
            value=self.FINAL_DUSTING_PHASE2_INTENSITY, cancel_all_timers=False
        )
        my_timer = threading.Timer(value, self._final_extraction_phase2_timed)
        my_timer.setName("DustManager:final_extraction_phase2")
        my_timer.daemon = True
        my_timer.start()
        self._fan_timers.append(my_timer)

    def _final_extraction_phase2_timed(self):
        self._logger.debug("Final extraction: DONE. Stopping phase2")
        self._stop_dust_extraction()

    def _send_fan_command(self, action, value=None):
        self._logger.debug("Sending fan command: action: %s, value: %s", action, value)
        ok, self._last_command = self._iobeam.send_fan_command(action, value)
        if not ok:
            self._logger.error(
                "Failed to send fan command to iobeam: %s %s", action, value
            )
        return ok

    def _send_dust_to_analytics(self, val):
        """
        Sends dust value periodically to analytics_handler to get overall stats and dust profile.
        :param val: measured dust value
        :return:
        """
        self._analytics_handler.collect_dust_value(val)

    def _validate_values(self):
        result = True
        errs = []
        if time.time() - self._data_ts > self.DEFAUL_DUST_MAX_AGE:
            result = False
            errs.append("data too old. age:{:.2f}".format(time.time() - self._data_ts))

        if self._state is None:
            result = False
            errs.append("fan state:{}".format(self._state))
        if self._rpm is None or self._rpm <= 0:
            result = False
            errs.append("rpm:{}".format(self._rpm))
        if self._dust is None:
            result = False
            errs.append("dust:{}".format(self._dust))

        if self._one_button_handler.is_printing() and self._state == 0:
            self._logger.warn("Restarting fan since _state was 0 in printing state.")
            self._start_dust_extraction(cancel_all_timers=False)

        if not result and not self._plugin.is_boot_grace_period():
            msg = "Fan error: {errs}".format(errs=", ".join(errs))
            log_message = (
                msg
                + " - Data from iobeam: state:{state}, rpm:{rpm}, dust:{dust}, connected:{connected}, age:{age:.2f}s".format(
                    state=self._state,
                    rpm=self._rpm,
                    dust=self._dust,
                    connected=self._connected,
                    age=(time.time() - self._data_ts),
                )
            )
            self._pause_laser(
                trigger=msg, analytics="invalid-old-fan-data", log_message=msg
            )

        elif self._connected == False:
            result = False
            msg = "Air filter is not connected: state:{state}, rpm:{rpm}, dust:{dust}, connected:{connected}, age:{age:.2f}s".format(
                state=self._state,
                rpm=self._rpm,
                dust=self._dust,
                connected=self._connected,
                age=(time.time() - self._data_ts),
            )
            self._pause_laser(trigger="Air filter not connected.", log_message=msg)

        # TODO: check for error case in connected val (currently, connected == True/False/None)
        return result

    def _validation_timer_callback(self):
        try:
            # self._request_value(self.DATA_TYPE_DYNAMIC)
            self._validate_values()
            self._start_validation_timer(delay=self._validation_timer_interval)
        except:
            self._logger.exception("Exception in _validation_timer_callback(): ")
            self._start_validation_timer(delay=self._validation_timer_interval)

    def _start_validation_timer(self, delay=0):
        if self._validation_timer:
            self._validation_timer.cancel()
        if (
            self._timer_boost_ts > 0
            and time.time() - self._timer_boost_ts > self.MAX_TIMER_BOOST_DURATION
        ):
            self._unboost_timer_interval()
        if not self._shutting_down:
            if delay <= 0:
                self._validation_timer_callback()
            else:
                self._validation_timer = threading.Timer(
                    delay, self._validation_timer_callback
                )
                self._validation_timer.setName("DustManager:_validation_timer")
                self._validation_timer.daemon = True
                self._validation_timer.start()
        else:
            self._logger.debug("Shutting down.")

    def _boost_timer_interval(self):
        self._timer_boost_ts = time.time()
        self._validation_timer_interval = self.BOOST_TIMER_INTERVAL
        # want the boost immediately, se reset current timer
        self._start_validation_timer()

    def _unboost_timer_interval(self):
        self._timer_boost_ts = 0
        self._validation_timer_interval = self.DEFAULT_VALIDATION_TIMER_INTERVAL
        # must not call _start_validation_timer()!!
