import socket
import sys
import threading
import time
import datetime
import collections
import json
from distutils.version import LooseVersion

from octoprint_mrbeam import IS_X86

from octoprint.events import Events as OctoPrintEvents

from octoprint_mrbeam.mrb_logger import mrb_logger
from octoprint_mrbeam.lib.rwlock import RWLock
from flask.ext.babel import gettext
from octoprint_mrbeam.mrbeam_events import MrBeamEvents

# singleton
_instance = None


def ioBeamHandler(plugin):
    global _instance
    if _instance is None:
        _instance = IoBeamHandler(plugin)
    return _instance


class IoBeamEvents(object):
    """
    These events are meant to be handled by OctoPrints event system
    """

    CONNECT = "iobeam.connect"
    DISCONNECT = "iobeam.disconnect"
    ONEBUTTON_PRESSED = "iobeam.onebutton.pressed"
    ONEBUTTON_DOWN = "iobeam.onebutton.down"
    ONEBUTTON_RELEASED = "iobeam.onebutton.released"
    INTERLOCK_OPEN = "iobeam.interlock.open"
    INTERLOCK_CLOSED = "iobeam.interlock.closed"
    LID_OPENED = "iobeam.lid.opened"
    LID_CLOSED = "iobeam.lid.closed"


class IoBeamValueEvents(object):
    """
    These Values / events are not intended to be handled byt OctoPrints event system
    but by IoBeamHandler's own event system
    """

    LASER_TEMP = "iobeam.laser.temp"
    DUST_VALUE = "iobeam.dust.value"
    RPM_VALUE = "iobeam.rpm.value"
    RPM_VALUE = "iobeam.rpm.value"
    STATE_VALUE = "iobeam.state.value"
    DYNAMIC_VALUE = "iobeam.dynamic.value"
    EXHAUST_DYNAMIC_VALUE = "iobeam.exhaust.dynamic"
    CONNECTED_VALUE = "iobeam.connected.value"
    FAN_ON_RESPONSE = "iobeam.fan.on.response"
    FAN_OFF_RESPONSE = "iobeam.fan.off.response"
    FAN_AUTO_RESPONSE = "iobeam.fan.auto.response"
    FAN_FACTOR_RESPONSE = "iobeam.fan.factor.response"
    COMPRESSOR_STATIC = "iobeam.compressor.static"
    COMPRESSOR_DYNAMIC = "iobeam.compressor.dynamic"
    LASERHEAD_CHANGED = "iobeam.laserhead.changed"


class IoBeamHandler(object):

    # How to test and debug:
    # in config.yaml set
    #      [plugins mrbeam dev debug] to true (suppresses reconnect on socket timeout) and
    #      [plugins mrbeam dev sockets iobeam] to '/tmp/mrbeam_iobeam.sock' to open the socket without sudo pw
    # and then use  "/usr/bin/nc -U -l /tmp/mrbeam_iobeam.sock"
    #
    # How to get debug info:
    #       echo "info" |  nc -U -w1 /var/run/mrbeam_iobeam.sock

    SOCKET_FILE = "/var/run/mrbeam_iobeam.sock"
    MAX_ERRORS = 50

    IOBEAM_MIN_REQUIRED_VERSION = "0.7.4"

    CLIENT_NAME = "MrBeamPlugin"

    PROCESSING_TIMES_LOG_LENGTH = 100
    PROCESSING_TIME_WARNING_THRESHOLD = 0.7

    MESSAGE_LENGTH_MAX = 4096
    MESSAGE_NEWLINE = "\n"
    MESSAGE_SEPARATOR = ":"
    MESSAGE_OK = "ok"
    MESSAGE_ERROR = "error"
    MESSAGE_COMMAND = "command"
    MESSAGE_REQUEST = "request"

    MESSAGE_DEVICE_ONEBUTTON = "onebtn"
    MESSAGE_DEVICE_LID = "lid"
    MESSAGE_DEVICE_INTERLOCK = "intlk"
    MESSAGE_DEVICE_STEPRUN = "steprun"
    MESSAGE_DEVICE_FAN = "fan"
    MESSAGE_DEVICE_LASER = "laser"
    MESSAGE_DEVICE_UNUSED = "unused"
    MESSAGE_DEVICE_IOBEAM = "iobeam"
    MESSAGE_DEVICE_COMPRESSOR = "compressor"

    MESSAGE_ACTION_ONEBUTTON_PRESSED = "pr"
    MESSAGE_ACTION_ONEBUTTON_DOWN = "dn"
    MESSAGE_ACTION_ONEBUTTON_RELEASED = "rl"
    MESSAGE_ACTION_ONEBUTTON_UP = "up"

    MESSAGE_ACTION_INTERLOCK_OPEN = "op"
    MESSAGE_ACTION_INTERLOCK_CLOSED = "cl"

    MESSAGE_ACTION_LID_OPENED = "op"
    MESSAGE_ACTION_LID_CLOSED = "cl"

    MESSAGE_IOBEAM_VERSION_0_2_3 = "0.2.3"
    MESSAGE_IOBEAM_VERSION_0_2_4 = "0.2.4"

    MESSAGE_ACTION_LASER_TEMP = "temp"
    MESSAGE_ACTION_DUST_VALUE = "dust"
    MESSAGE_ACTION_FAN_ON = "on"
    MESSAGE_ACTION_FAN_OFF = "off"
    MESSAGE_ACTION_FAN_AUTO = "auto"
    MESSAGE_ACTION_FAN_FACTOR = "factor"
    MESSAGE_ACTION_FAN_VERSION = "version"
    MESSAGE_ACTION_FAN_RPM = "rpm"
    MESSAGE_ACTION_FAN_PWM_MIN = "pwm_min"
    MESSAGE_ACTION_FAN_TPR = "tpr"
    MESSAGE_ACTION_FAN_STATE = "state"
    MESSAGE_ACTION_FAN_DYNAMIC = "dynamic"
    MESSAGE_ACTION_FAN_CONNECTED = "connected"
    MESSAGE_ACTION_FAN_SERIAL = "serial"
    MESSAGE_ACTION_FAN_TYPE = "type"
    MESSAGE_ACTION_FAN_EXHAUST = "exhaust"
    MESSAGE_ACTION_FAN_LINK_QUALITY = "link_quality"
    MESSAGE_ACTION_COMPRESSOR_ON = "on"

    # Possible datasets
    DATASET_FAN_DYNAMIC = "fan_dynamic"
    DATASET_FAN_STATIC = "fan_static"
    DATASET_COMPRESSOR_DYNAMIC = "compressor_dynamic"
    DATASET_COMPRESSOR_STATIC = "compressor_static"
    DATASET_FAN_EXHAUST = "fan_exhaust"
    DATASET_FAN_LINK_QUALITY = "fan_link_quality"
    DATASET_PCF = "pcf"
    DATASET_LID = "lid"
    DATASET_INTERLOCK = "intlk"
    DATASET_STEPRUN = "steprun"
    DATASET_LASER = "laser"
    DATASET_LASERHEAD = "laserhead"
    DATASET_LASERHEAD_SHORT = "laserhead_short"
    DATASET_IOBEAM = "iobeam"
    DATASET_HW_MALFUNCTION = "hardware_malfunction"
    DATASET_I2C = "i2c"
    DATASET_I2C_MONITORING = "i2c_monitoring"
    DATASET_REED_SWITCH = "reed_switch"
    DATASET_ANALYTICS = "analytics"

    def __init__(self, plugin):
        self._plugin = plugin
        self._event_bus = plugin._event_bus
        self._socket_file = plugin._settings.get(["dev", "sockets", "iobeam"])
        self._logger = mrb_logger("octoprint.plugins.mrbeam.iobeam")

        self._shutdown_signaled = False
        self._isConnected = False
        self._my_socket = None
        self._errors = 0
        self._unknown_datasets = []
        self._callbacks = dict()
        self._callbacks_lock = RWLock()

        self._laserhead_handler = None

        self.iobeam_version = None

        self._connectionException = None
        self._interlocks = dict()

        self.processing_times_log = collections.deque(
            [], self.PROCESSING_TIMES_LOG_LENGTH
        )

        self.request_id = 1
        self._request_id_lock = threading.Lock()
        self._last_i2c_monitoring_dataset = None

        self._settings = plugin._settings

        self._event_bus.subscribe(
            MrBeamEvents.MRB_PLUGIN_INITIALIZED, self._on_mrbeam_plugin_initialized
        )

    def _on_mrbeam_plugin_initialized(self, event, payload):
        self._laserhead_handler = self._plugin.laserhead_handler
        self._hw_malfunction_handler = self._plugin.hw_malfunction_handler
        self._user_notification_system = self._plugin.user_notification_system

        self._subscribe()

        # We only start the iobeam listener now
        iobeam_worker = threading.Timer(1.0, self._initWorker, [self._socket_file])
        iobeam_worker.daemon = True
        iobeam_worker.start()

    def isRunning(self):
        return self._worker.is_alive()

    def isConnected(self):
        return self._isConnected

    def shutdown(self, *args):
        self._logger.debug("shutdown() args: %s", args)
        global _instance
        _instance = None
        self._shutdown_signaled = True

    def shutdown_fan(self):
        self.send_fan_command(self.MESSAGE_ACTION_FAN_OFF)

    def is_interlock_closed(self):
        return len(self._interlocks.keys()) == 0

    def open_interlocks(self):
        return self._interlocks.keys()

    def send_temperature_request(self):
        """
        Request a single temperature value from iobeam.
        :return: True if the command was sent sucessfully.
        """
        return self._send_command(
            self.get_request_msg([self.MESSAGE_DEVICE_LASER + "_temp"])
        )

    def send_fan_command(self, action, value=None):
        """
        Send the specified command as fan:<command>
        :param command: One of the three values (ON:<0-100>/OFF/AUTO)
        :return: True if the command was sent sucessfull (does not mean it was sucessfully executed)
        """
        command = self.get_command_msg(self.MESSAGE_DEVICE_FAN, action, value)
        return self._send_command(command), command["request_id"]

    def send_compressor_command(self, value=0):
        command = self.get_command_msg(
            self.MESSAGE_DEVICE_COMPRESSOR, self.MESSAGE_ACTION_COMPRESSOR_ON, value
        )
        succ = self._send_command(command)
        self._logger.info(
            "send_compressor_command(): succ: %s, command: %s", succ, command
        )
        return succ, command["request_id"]

    def send_analytics_request(self, *args, **kwargs):
        """
        Requests a analytics dataset from iobeam
        :return: True if the command was sent successful (does not mean it was successfully executed)
        """
        return self._send_command(self.get_request_msg([self.DATASET_ANALYTICS]))

    def _send_command(self, command):
        """
        Sends a command to iobeam
        :param command: Must not be None. May or may not end with a new line.
        :return: Boolean success
        """
        if command is None:
            raise ValueError("Command must not be None in send_command().")
        if self._shutdown_signaled:
            return False
        if not self._isConnected:
            self._logger.warn(
                "send_command() Can't send command since socket is not connected (yet?). Command: %s",
                command,
            )
            return False
        if self._my_socket is None:
            self._logger.error(
                "send_command() Can't send command while there's no connection on socket but _isConnected()=True!  Command: %s",
                command,
            )
            return False

        try:
            self._my_socket.sendall("{}\n".format(json.dumps(command)))
        except Exception as e:
            self._errors += 1
            if IS_X86:
                self._logger.debug(
                    "Exception while sending command '%s' to socket: %s", command, e
                )
            else:
                self._logger.error(
                    "Exception while sending command '%s' to socket: %s", command, e
                )
                return False
        return True

    def is_iobeam_version_ok(self):
        if self.iobeam_version is None:
            return False
        vers_obj = None
        try:
            vers_obj = LooseVersion(self.iobeam_version)
        except ValueError as e:
            self._logger.error(
                "iobeam version invalid: '{}'. ValueError from LooseVersion: {}".format(
                    self.iobeam_version, e
                )
            )
            return False
        if vers_obj < LooseVersion(self.IOBEAM_MIN_REQUIRED_VERSION):
            return False
        else:
            return True

    def notify_user_old_iobeam(self):
        self._logger.error(
            "Received iobeam version: %s - version OUTDATED. IOBEAM_MIN_REQUIRED_VERSION: %s",
            self.iobeam_version,
            self.IOBEAM_MIN_REQUIRED_VERSION,
        )
        self._user_notification_system.show_notifications(
            self._user_notification_system.get_legacy_notification(
                title="Software Update required",
                text="Module 'iobeam' is outdated. Please run software update from 'Settings' > 'Software Update' before you start a laser job.",
                is_err=True,
            )
        )

    def subscribe(self, event, callback):
        """
        Subscibe to an event
        :param event:
        :param callback:
        """
        try:
            self._callbacks_lock.writer_acquire()
            if event in self._callbacks:
                self._callbacks[event].append(callback)
            else:
                self._callbacks[event] = [callback]
        except:
            self._logger.exception(
                "Exception while subscribing to event '{}': ".format(event)
            )
        finally:
            self._callbacks_lock.writer_release()

    def _call_callback(self, _trigger_event, message, kwargs={}):
        try:
            self._callbacks_lock.reader_acquire()
            if _trigger_event in self._callbacks:
                _callback_array = self._callbacks[_trigger_event]
                kwargs["event"] = _trigger_event
                kwargs["message"] = message

                # If handling of these messages blockes iobeam_handling, we might need a threadpool or so.
                # One thread for handling this is almost the same bottleneck as current solution,
                # so I think we would need a thread pool here... But maybe this would be just over engineering.
                self.__execute_callback_called_by_new_thread(
                    _trigger_event, False, _callback_array, kwargs
                )

                # thread_params = dict(target = self.__execute_callback_called_by_new_thread,
                #                      name = "iobeamCB_{}".format(_trigger_event),
                #                      args = (_trigger_event, _callback_array),
                #                      kwargs = kwargs)
                # my_thread = threading.Thread(**thread_params)
                # my_thread.daemon = True
                # my_thread.start()
        except:
            self._logger.exception(
                "Exception in _call_callback() _trigger_event: %s, message: %s, kwargs: %s",
                _trigger_event,
                message,
                kwargs,
            )
        finally:
            self._callbacks_lock.reader_release()

    def __execute_callback_called_by_new_thread(
        self, _trigger_event, acquire_lock, _callback_array, kwargs
    ):
        try:
            if acquire_lock:
                # It's a terrible idea to acquire this lock two times in a row on the same thread.
                # It happened that there was a write request in between -> dead lock like in a text book ;-)
                self._callbacks_lock.reader_acquire()
            for my_cb in _callback_array:
                try:
                    my_cb(kwargs)
                except Exception as e:
                    self._logger.exception(
                        "Exception in a callback for event: %s : ", _trigger_event
                    )
        except:
            self._logger.exception(
                "Exception in __execute_callback_called_by_new_thread() for event: %s : ",
                _trigger_event,
            )
        finally:
            if acquire_lock:
                self._callbacks_lock.reader_release()

    def _subscribe(self):
        self._event_bus.subscribe(OctoPrintEvents.SHUTDOWN, self.shutdown)
        self._event_bus.subscribe(
            OctoPrintEvents.PRINT_DONE, self.send_analytics_request
        )
        self._event_bus.subscribe(
            OctoPrintEvents.PRINT_FAILED, self.send_analytics_request
        )
        self._event_bus.subscribe(
            OctoPrintEvents.PRINT_CANCELLED, self.send_analytics_request
        )
        self._event_bus.subscribe(OctoPrintEvents.ERROR, self.send_analytics_request)

    def _initWorker(self, socket_file=None):
        self._logger.debug("initializing worker thread")

        # this is needed for unit tests
        if socket_file is not None:
            self.SOCKET_FILE = socket_file

        # this si executed on a TimerThread. let's start a plain thread, just to have it "clean"
        self._worker = threading.Thread(target=self._work, name="iobeamHandler")
        self._worker.daemon = True
        self._worker.start()

    def _work(self):
        try:
            threading.current_thread().name = self.__class__.__name__
            self._logger.debug(
                "Worker thread starting, connecting to socket: %s", self.SOCKET_FILE
            )

            while not self._shutdown_signaled:
                self._my_socket = None
                self._isConnected = False
                try:
                    temp_socket = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
                    temp_socket.settimeout(10)
                    # self._logger.debug("Connecting to socket...")
                    temp_socket.connect(self.SOCKET_FILE)
                    self._my_socket = temp_socket
                except socket.error as e:
                    self._isConnected = False
                    if IS_X86:
                        if not self._connectionException == str(e):
                            self._logger.error(
                                "IoBeamHandler not able to connect to socket %s, reason: %s. I'll keept trying but I won't log further failures.",
                                self.SOCKET_FILE,
                                e,
                            )
                            self._connectionException = str(e)
                    else:
                        self._logger.error(
                            "IoBeamHandler not able to connect to socket %s, reason: %s. ",
                            self.SOCKET_FILE,
                            e,
                        )

                    time.sleep(1)
                    continue

                self._isConnected = True
                self._errors = 0
                self._connectionException = None

                client_msg = self._send_identification()
                self._logger.info(
                    "iobeam connection established. Identified ourselves as '%s'",
                    client_msg["client"],
                )
                self._fireEvent(IoBeamEvents.CONNECT)

                temp_buffer = b""
                while not self._shutdown_signaled:
                    try:

                        # Read MESSAGE_LENGTH_MAX bytes of data
                        data = None
                        try:
                            sock_data = self._my_socket.recv(self.MESSAGE_LENGTH_MAX)
                            if (
                                len(temp_buffer) >= self.MESSAGE_LENGTH_MAX
                                or len(sock_data) >= self.MESSAGE_LENGTH_MAX - 5
                            ):
                                self._logger.info(
                                    "Receiving long message - buffer size: %s, receiving size : %s",
                                    len(temp_buffer),
                                    len(sock_data),
                                )
                            data = temp_buffer + sock_data
                        except Exception as e:
                            # if self.dev_mode and e.message == "timed out":
                            # 	# self._logger.warn("Connection stale but MRBEAM_DEBUG enabled. Continuing....")
                            # 	continue
                            # else:
                            self._logger.warn(
                                "Exception while sockect.recv(): %s (message: %s) - Resetting connection...",
                                e,
                                e.message,
                            )
                            break

                        if not data:
                            self._logger.warn(
                                "Connection ended from other side. Closing connection..."
                            )
                            break

                        # Split all JSON messages by new line character
                        messages = data.split(self.MESSAGE_NEWLINE)

                        if not data.endswith(self.MESSAGE_NEWLINE):
                            # Record remaining part of data into temp buffer, to read messages longer than MESSAGE_LENGTH_MAX
                            temp_buffer = messages.pop()
                        else:
                            temp_buffer = b""
                        my_errors, _ = self._handle_messages(messages)

                        if my_errors > 0:
                            self._errors += my_errors
                            if self._errors >= self.MAX_ERRORS:
                                self._logger.warn(
                                    "Resetting connection... error_count=%s, Resetting connection...",
                                    self._errors,
                                )
                                break
                            else:
                                self._logger.warn(
                                    "Received invalid message, error_count=%s",
                                    self._errors,
                                )
                    except:
                        self._logger.exception(
                            "Exception in socket loop. Not sure what to do, resetting connection..."
                        )

                if self._my_socket is not None:
                    self._logger.debug("Closing socket...")
                    self._my_socket.close()
                    self._my_socket = None

                self._isConnected = False
                self._fireEvent(
                    IoBeamEvents.DISCONNECT
                )  # on shutdown this won't be broadcasted

                if not self._shutdown_signaled:
                    self._logger.debug("Sleeping for a sec before reconnecting...")
                    time.sleep(0.1)

            self._logger.debug("Worker thread stopped.")
        except:
            self._logger.exception("Exception in _work(): ")

    def _handle_messages(self, messages):
        """
        Handles incoming list of messages from the socket.
        :param messages: list of incoming dict messages
        :return: int: number of invalid messages 0 means all messages were handled correctly
        """
        error_count = 0
        message_count = 0
        try:
            for json_data in messages:
                if len(json_data) > 0:

                    message_count = +1

                    try:
                        # self._logger.info("ANDYTEST _handle_messages()  %s", json_data)

                        json_dict = json.loads(json_data)
                        # Now there could be "data" and "response"
                        if "data" in json_dict:
                            _data = json_dict["data"]
                            if self.MESSAGE_ERROR not in _data:
                                # Process all data sets
                                if isinstance(_data, dict):
                                    # We have to process the iobeam dataset first, because we need the iobeam version for analytics
                                    if "iobeam" in _data.keys():
                                        error_count += self._handle_dataset(
                                            "iobeam", _data.pop("iobeam", None)
                                        )

                                    for data_id, dataset in _data.items():
                                        error_count += self._handle_dataset(
                                            data_id, dataset
                                        )
                            else:
                                self._logger.debug(
                                    "Received error in data '%s'",
                                    _data[self.MESSAGE_ERROR],
                                )
                                error_count += 1
                        elif "response" in json_dict:
                            error_count += self._handle_response(json_dict)

                    except ValueError as ve:
                        # Check if we communicate with an older version of iobeam, iobeam:version:0.6.0
                        if isinstance(json_data, basestring) and json_data.startswith(
                            "iobeam:version:"
                        ):
                            tokens = json_data.split(":")
                            try:
                                self.iobeam_version = tokens[2]
                                version_obj = LooseVersion(tokens[2])
                            except ValueError:
                                self.iobeam_version = None
                                version_obj = None
                                self._logger.debug(
                                    "Could not parse iobeam version and data '%s' as JSON",
                                    json_data,
                                )

                            # BACKWARD_COMPATIBILITY:
                            # If there is an iobeam version that does not use
                            # JSON (< v0.7.0), we check the version number here
                            if not self.is_iobeam_version_ok():
                                self.notify_user_old_iobeam()

                        else:
                            self._logger.debug(
                                "Could not parse data '%s' as JSON - err : %s",
                                json_data,
                                ve,
                            )
                    except Exception as e2:
                        self._logger.debug("Some error with data '%s'", json_data)
                        self._logger.error(e2)
                        error_count += 1

        except Exception as e:
            self._logger.exception(e)

        return error_count, message_count

    def _handle_dataset(self, name, dataset):
        """
        Handle dataset
        :param name: name of the dataset
        :param dataset: the contents of the dataset
        :return: error count
        """
        # self._logger.info("ANDYTEST _handle_dataset() %s: %s", name, dataset)
        error_count = 0
        processing_start = time.time()

        err = -1
        try:
            if len(name) <= 0:
                err = self._handle_invalid_dataset(name, dataset)
            elif self.MESSAGE_ERROR in dataset:
                self._logger.debug(
                    "Received %s dataset error: %s", name, dataset[self.MESSAGE_ERROR]
                )
                err += 1
            # # elif len(dataset) == 0:
            # # 	self._logger.debug("Received empty dataset %s", name)
            else:
                if name == self.DATASET_FAN_DYNAMIC:
                    err = self._handle_fan_dynamic(dataset)
                elif name == self.DATASET_FAN_STATIC:
                    err = self._handle_fan_static(dataset)
                elif name == self.DATASET_COMPRESSOR_STATIC:
                    err = self._handle_compressor_static(dataset)
                elif name == self.DATASET_COMPRESSOR_DYNAMIC:
                    err = self._handle_compressor_dynamic(dataset)
                elif name == self.DATASET_LASER:
                    err = self._handle_laser(dataset)
                elif name == self.DATASET_LASERHEAD:
                    err = self._handle_laserhead(dataset)
                elif name == self.DATASET_LASERHEAD_SHORT:
                    pass
                    # err = self._handle_laserhead(dataset)
                elif name == self.DATASET_IOBEAM:
                    err = self._handle_iobeam(dataset)
                elif name == self.DATASET_PCF:
                    err = self._handle_pcf(dataset)
                elif name == self.DATASET_FAN_LINK_QUALITY:
                    err = self._handle_link_quality(dataset)
                elif name == self.DATASET_FAN_EXHAUST:
                    err = self._handle_exhaust(dataset)
                elif name == self.DATASET_HW_MALFUNCTION:
                    err = self._handle_hw_malfunction(dataset)
                elif name == self.DATASET_I2C:
                    err = self._handle_i2c(dataset)
                elif name == self.DATASET_I2C_MONITORING:
                    err = self._handle_i2c_monitoring(dataset)
                elif name == self.DATASET_REED_SWITCH:
                    err = self._handle_reed_switch(dataset)
                elif name == self.DATASET_ANALYTICS:
                    err = self._handle_analytics_dataset(dataset)
                elif name == self.MESSAGE_DEVICE_UNUSED:
                    pass
                elif name == self.MESSAGE_ERROR:
                    err = self._handle_error_message(dataset)
                else:
                    err = self._handle_unknown_dataset(name, dataset)
        except:
            self._logger.exception("Error handling dataset '%s': %s", name, dataset)

        if err >= 0:
            error_count += err

        processing_time = time.time() - processing_start
        self._handle_processing_time(processing_time, dataset, err)

        return error_count

    def _handle_fan_dynamic(self, dataset):
        """
        Handle dynamic fan data
        :param dataset:
        :return: error count
        """
        if isinstance(dataset, dict) and len(dataset) > 3:
            vals = dict(
                state=self._as_number(dataset[self.MESSAGE_ACTION_FAN_STATE]),
                rpm=self._as_number(dataset[self.MESSAGE_ACTION_FAN_RPM]),
                dust=self._as_number(dataset[self.MESSAGE_ACTION_DUST_VALUE]),
                connected=self._get_connected_val(
                    dataset[self.MESSAGE_ACTION_FAN_CONNECTED]
                ),
            )
            # if token[4] == 'error':
            # 	self._logger.warn("Received fan connection error: %s", message)
            self._call_callback(IoBeamValueEvents.DYNAMIC_VALUE, dataset, vals)
            self._call_callback(
                IoBeamValueEvents.STATE_VALUE,
                dataset,
                dict(val=vals[self.MESSAGE_ACTION_FAN_STATE]),
            )
            self._call_callback(
                IoBeamValueEvents.RPM_VALUE,
                dataset,
                dict(val=vals[self.MESSAGE_ACTION_FAN_RPM]),
            )
            self._call_callback(
                IoBeamValueEvents.DUST_VALUE,
                dataset,
                dict(val=vals[self.MESSAGE_ACTION_DUST_VALUE]),
            )
            self._call_callback(
                IoBeamValueEvents.CONNECTED_VALUE,
                dataset,
                dict(val=vals[self.MESSAGE_ACTION_FAN_CONNECTED]),
            )
        else:
            # Handle values one by one
            if self.MESSAGE_ACTION_DUST_VALUE in dataset:
                dust_val = self._as_number(dataset[self.MESSAGE_ACTION_DUST_VALUE])
                if dust_val is not None:
                    self._call_callback(
                        IoBeamValueEvents.DUST_VALUE, dataset, dict(val=dust_val)
                    )

            if self.MESSAGE_ACTION_FAN_RPM in dataset:
                rpm_val = self._as_number(dataset[self.MESSAGE_ACTION_FAN_RPM])
                if rpm_val is not None:
                    self._call_callback(
                        IoBeamValueEvents.RPM_VALUE, dataset, dict(val=rpm_val)
                    )

            if self.MESSAGE_ACTION_FAN_STATE in dataset:
                state = self._as_number(dataset[self.MESSAGE_ACTION_FAN_STATE])
                if state is not None:
                    self._call_callback(
                        IoBeamValueEvents.STATE_VALUE, dataset, dict(val=state)
                    )

            if self.MESSAGE_ACTION_FAN_CONNECTED in dataset:
                self._call_callback(
                    IoBeamValueEvents.CONNECTED_VALUE,
                    dataset,
                    dict(
                        val=self._get_connected_val(
                            dataset[self.MESSAGE_ACTION_FAN_CONNECTED]
                        )
                    ),
                )
                if self.MESSAGE_ERROR in dataset[self.MESSAGE_ACTION_FAN_CONNECTED]:
                    self._logger.warn(
                        "Received fan connection error: %s",
                        dataset[self.MESSAGE_ACTION_FAN_CONNECTED][self.MESSAGE_ERROR],
                    )
        return 0

    def _handle_fan_static(self, dataset):
        """
        Handle static fan data
        :param dataset:
        :return: error count
        """
        if self.MESSAGE_ACTION_FAN_VERSION in dataset:
            self._logger.info(
                "fan_static: fanPCB v%s, factor: %s - %s",
                dataset.get(self.MESSAGE_ACTION_FAN_VERSION, None),
                dataset.get(self.MESSAGE_ACTION_FAN_FACTOR, None),
                dataset,
            )
        return 0

    def _handle_compressor_dynamic(self, dataset):
        self._call_callback(IoBeamValueEvents.COMPRESSOR_DYNAMIC, dataset)
        return 0

    def _handle_compressor_static(self, dataset):
        """
        Handle static compressor data
        :param dataset:
        :return: error count
        """
        # self._logger.info("compressor_static: %s", dataset)
        self._call_callback(IoBeamValueEvents.COMPRESSOR_STATIC, dataset)
        return 0

    def _handle_i2c_monitoring(self, dataset):
        if not dataset.get("state", None) == "ok":
            self._logger.error(
                "i2c_monitoring state change reported: %s", dataset, analytics=False
            )
            if (
                not self._last_i2c_monitoring_dataset is None
                and not self._last_i2c_monitoring_dataset.get("state", None)
                == dataset.get("state", None)
            ):
                dataset_data = dataset.get("data", dict())
                params = dict(
                    state=dataset.get("state", None),
                    method=dataset_data.get("test_mode", None),
                    current_devices=dataset_data.get("current_devices", []),
                    lost_devices=dataset_data.get("lost_devices", []),
                    new_devices=dataset_data.get("new_devices", []),
                )

                self.send_iobeam_analytics(eventname="i2c_monitoring", data=params)
        self._last_i2c_monitoring_dataset = dataset

    def _handle_reed_switch(self, dataset):
        self._logger.info("reed_switch: %s", dataset)
        return 0

    def _handle_laser(self, dataset):
        """
        Handle laser dataset, which may contain laser temperature, serial and power
        :param dataset:
        :return: error count
        """
        if self.MESSAGE_ACTION_LASER_TEMP in dataset:
            if dataset[self.MESSAGE_ACTION_LASER_TEMP]:
                self._call_callback(
                    IoBeamValueEvents.LASER_TEMP,
                    dataset,
                    dict(temp=self._as_number(dataset[self.MESSAGE_ACTION_LASER_TEMP])),
                )

        return 0

    def _handle_laserhead(self, dataset):
        """
        Handle laserhead dataset, iobeam sends the whole laserhead data.
        :param dataset:
        :return: error count
        """
        try:
            self._laserhead_handler.set_current_used_lh_data(dataset)
        except:
            self._logger.exception("laserhead: exception while handling head:data: ")
        return 0

    def _handle_pcf(self, dataset):
        """
        Handle pcf dataset, which includes onbutton, interlocks, lid and steprun
        :param dataset: pcf dataset, e.g. {"intlk": {...}, "lid": {...}, ...}
        :return: error count
        """
        if self.MESSAGE_DEVICE_ONEBUTTON in dataset:
            self._handle_onebutton(dataset[self.MESSAGE_DEVICE_ONEBUTTON])

        if self.MESSAGE_DEVICE_INTERLOCK in dataset:
            self._handle_interlock(dataset[self.MESSAGE_DEVICE_INTERLOCK])

        if self.MESSAGE_DEVICE_LID in dataset:
            self._handle_lid(dataset[self.MESSAGE_DEVICE_LID])

        if self.MESSAGE_DEVICE_STEPRUN in dataset:
            self._handle_steprun(dataset[self.MESSAGE_DEVICE_STEPRUN])
        return 0

    def _handle_onebutton(self, dataset):
        """
        Handle onebtn dataset
        :param dataset: onebtn dataset, e.g. {"state": "dn", "duration": "1.2"}
        :return: error count
        """
        duration = None
        if "state" in dataset and dataset["state"]:
            state = dataset["state"]
            if "duration" in dataset and dataset["duration"]:
                try:
                    duration = self._as_number(dataset["duration"])
                except:
                    self._logger.debug(
                        "Received invalid onebtn duration: %s", dataset["duration"]
                    )
                    return 1
        else:
            return self._handle_invalid_dataset(self.MESSAGE_DEVICE_ONEBUTTON, dataset)

        self._logger.debug(
            "_handle_onebutton() message: %s, state: %s, duration: %s",
            dataset,
            state,
            duration,
        )

        if state == self.MESSAGE_ACTION_ONEBUTTON_PRESSED:
            self._fireEvent(IoBeamEvents.ONEBUTTON_PRESSED)
        elif state == self.MESSAGE_ACTION_ONEBUTTON_DOWN and duration is not None:
            self._fireEvent(IoBeamEvents.ONEBUTTON_DOWN, duration)
        elif state == self.MESSAGE_ACTION_ONEBUTTON_RELEASED and duration is not None:
            self._fireEvent(IoBeamEvents.ONEBUTTON_RELEASED, duration)
        elif state == self.MESSAGE_ACTION_ONEBUTTON_UP:
            return 0
        else:
            return self._handle_invalid_dataset(self.MESSAGE_DEVICE_ONEBUTTON, dataset)
        return 0

    def _handle_interlock(self, dataset):
        """
        Handle interlock message
        :param dataset: interlock dataset, e.g. {"0": "cl", "1": "cl", ...}
        :return: error count
        """
        name = {
            "0": "Lid Right",
            "1": "Lid Left",
            "2": "Bottom Left",
            "3": "Bottom Right",
        }
        if isinstance(dataset, dict):
            before_state = self.open_interlocks()
            for lock_id, lock_state in dataset.items():
                if lock_id is not None:
                    lock_name = name[lock_id]
                    if lock_state == self.MESSAGE_ACTION_INTERLOCK_OPEN:
                        self._interlocks[lock_name] = True
                    elif lock_state == self.MESSAGE_ACTION_INTERLOCK_CLOSED:
                        self._interlocks.pop(lock_name, None)
                    else:
                        return self._handle_invalid_message(dataset)
                else:
                    return self._handle_invalid_message(dataset)

            now_state = self.open_interlocks()
            if now_state != before_state:
                if self.is_interlock_closed():
                    self._fireEvent(IoBeamEvents.INTERLOCK_CLOSED)
                else:
                    self._fireEvent(IoBeamEvents.INTERLOCK_OPEN, now_state)
                self._logger.info("Open interlocks : %s", now_state)
        return 0

    def _handle_lid(self, action):
        """
        Handle lid message
        :param action: lid action, e.g. "cl" or "op"
        :return: error count
        """
        self._logger.debug("_handle_lid() action: %s", action)

        if action == self.MESSAGE_ACTION_LID_OPENED:
            self._fireEvent(IoBeamEvents.LID_OPENED)
        elif action == self.MESSAGE_ACTION_LID_CLOSED:
            self._fireEvent(IoBeamEvents.LID_CLOSED)
        else:
            return self._handle_invalid_message(action)
        return 0

    def _handle_steprun(self, dataset):
        return 0

    def _handle_iobeam(self, dataset):
        """
        Handle iobeam dataset
        :param dataset:
        :return: error count
        """
        if "version" in dataset:
            if dataset["version"]:
                self.iobeam_version = dataset["version"]
                ok = self.is_iobeam_version_ok()
                if ok:
                    self._logger.info(
                        "Received iobeam version: %s - version OK", self.iobeam_version
                    )
                else:
                    self.notify_user_old_iobeam()

                return 0
            else:
                self._logger.warn(
                    "_handle_iobeam(): Received iobeam:version message without version number. Counting as error. Message: %s",
                    dataset,
                )
                return 1

        if "init" in dataset:
            # introduced with iobeam 0.4.2
            # in future versions we could make this requried and only unlock laser functionality once this was ok
            if dataset["init"] and dataset["init"].startswith("ok"):
                self._logger.info("iobeam init ok: '%s'", dataset)
            else:
                # ANDYTEST add analytics=True to next log line
                self._logger.info(
                    "iobeam init error: '%s' - requesting iobeam_debug...", dataset
                )
                # Add request id to the command
                self._send_command(self.get_request_msg(["debug"]))

                self._hw_malfunction_handler.show_hw_malfunction_notification(dataset)
        return 0

    def _handle_hw_malfunction(self, dataset):
        """
        Handle hw malfunction dataset.
        :param dataset:
        :return: error count
        """
        try:
            if dataset:
                self._hw_malfunction_handler.report_hw_malfunction(dataset)
        except:
            self._logger.exception("Exception in _handle_hw_malfunction")
        return 0

    def _handle_i2c(self, dataset):
        self._logger.info("i2c_state: %s", dataset)

    def _handle_analytics_dataset(self, dataset):
        if dataset.get("communication_errors", None):
            self.send_iobeam_analytics(
                eventname="communication_errors",
                data=dataset.get("communication_errors"),
            )
        return 0

    def _handle_debug(self, dataset):
        """
        Handle debug dataset
        :param dataset:
        :return: error count
        """
        self._logger.info("iobeam debug dataset: '%s'", dataset)
        return 0

    def _handle_exhaust(self, dataset):
        """
        Handle exhaust dataset
        :param dataset:
        :return: error count
        """
        self._logger.debug("exhaust dataset: '%s'", dataset)
        # get the pressure sensor reading this will come as dust with the current iobeam version
        if "dust" in dataset:
            vals = {
                "pressure": dataset["dust"],
            }
            self._call_callback(IoBeamValueEvents.EXHAUST_DYNAMIC_VALUE, dataset, vals)
        return 0

    def _handle_link_quality(self, dataset):
        """
        Handle link quality dataset
        :param dataset:
        :return: error count
        """
        # self._logger.info("link quality dataset: '%s'", dataset)
        return 0

    def _handle_invalid_dataset(self, name, dataset):
        """
        Handle datasets of an invalid format, or datasets which have some missing data
        :param name:
        :param dataset:
        :return:
        """
        # self._logger.debug("Received invalid dataset %s: '%s'", name, dataset)
        return 0

    def _handle_unknown_dataset(self, name, dataset):
        """
        Handle dataset which has unknown name
        :param name:
        :param dataset:
        :return:
        """
        if name not in self._unknown_datasets:
            self._unknown_datasets.append(name)
            self._logger.warn("Received unknown dataset %s: %s", name, dataset)
        return 0

    def _handle_invalid_message(self, message):
        """
        Handle invalid message, which could be any unexpected message
        :param message:
        :return:
        """
        self._logger.warn("Received invalid message: '%s'", message)
        return 1

    def _handle_error_message(self, message):
        """
        Handle error message
        :param message:
        :return:
        """
        # TODO: A better way to extract?
        action = message.values()[0]
        if action == "reconnect":
            raise Exception("ioBeam requested to reconnect. Now doing so...")
        return 1

    def _handle_response(self, message):
        """
        Handle response, which is typically a response to a command sent earlier
        :param message: response message, e.g. {"response": {"command": {"device": "fan", ...}, "state": "ok"}}
        :return: error count
        """
        # self._logger.info("ANDYTEST _handle_response(): %s", message)
        error_count = 0
        processing_start = time.time()

        err = -1

        response = message["response"]
        if "request_id" in message:
            message["response"]["request_id"] = message["request_id"]
        if "state" in response:
            value = response["state"]
            # check if OK otherwise it's an error
            success = value == self.MESSAGE_OK
            payload = dict(success=success)
            if not success:
                try:
                    msg = response.get(self.MESSAGE_ERROR).get("msg")
                except:
                    msg = response["state"]
                payload["error"] = msg
                err += 1
                self._logger.warn(
                    "Received error response from iobeam: '%s', full response: %s",
                    msg,
                    message,
                )

            elif self.MESSAGE_COMMAND in response:
                device = response[self.MESSAGE_COMMAND].get("device", None)
                action = response[self.MESSAGE_COMMAND].get("action", None)

                if device == self.MESSAGE_DEVICE_FAN:
                    if action == self.MESSAGE_ACTION_FAN_ON:
                        self._call_callback(
                            IoBeamValueEvents.FAN_ON_RESPONSE, response, payload
                        )
                    elif action == self.MESSAGE_ACTION_FAN_OFF:
                        self._call_callback(
                            IoBeamValueEvents.FAN_OFF_RESPONSE, response, payload
                        )
                    elif action == self.MESSAGE_ACTION_FAN_AUTO:
                        self._call_callback(
                            IoBeamValueEvents.FAN_AUTO_RESPONSE, response, payload
                        )
                    elif action == self.MESSAGE_ACTION_FAN_FACTOR:
                        self._call_callback(
                            IoBeamValueEvents.FAN_FACTOR_RESPONSE, response, payload
                        )
                    else:
                        self._logger.debug("Received response: %s", response)
                elif device == self.MESSAGE_DEVICE_COMPRESSOR:
                    self._logger.debug("handling compressor response: %s", message)
                else:
                    self._logger.debug(
                        "_handle_response() receives response for unknow device: %s",
                        response,
                    )

        if err >= 0:
            error_count += err

        processing_time = time.time() - processing_start
        self._handle_processing_time(processing_time, message, err)

        return error_count

    def _handle_processing_time(self, processing_time, message, err, log_stats=False):
        self.processing_times_log.append(
            dict(
                ts=time.time(),
                processing_time=processing_time,
                message=message,
                error_count=err,
            )
        )
        if processing_time > self.PROCESSING_TIME_WARNING_THRESHOLD:
            self._logger.warn(
                "Message handling time took %ss. (Errors: %s, message: '%s')",
                processing_time,
                err,
                message,
            )
        if log_stats or processing_time > self.PROCESSING_TIME_WARNING_THRESHOLD:
            self.log_debug_processing_stats()

    def log_debug_processing_stats(self):
        """
        Not exactly sure what my idea was with this...
        # TODO: find a way to trigger this manually for debugging and general curiosity.
        :return:
        """
        min = sys.maxint
        max = 0
        sum = 0
        count = 0
        earliest = time.time()
        for entry in self.processing_times_log:
            if entry["processing_time"] < min:
                min = entry["processing_time"]
            if entry["processing_time"] > max:
                max = entry["processing_time"]
            if entry["ts"] < earliest:
                earliest = entry["ts"]
            sum += entry["processing_time"]
            count += 1
        if count <= 0:
            self._logger.error(
                "_handle_processing_time() stats: message count is <= 0, something seems be wrong."
            )
        else:
            avg = sum / count
            time_formatted = datetime.datetime.fromtimestamp(earliest).strftime(
                "%Y-%m-%d %H:%M:%S"
            )
            self._logger.info(
                "Message handling stats: %s message since %s; max: %ss, avg: %ss, min: %ss",
                count,
                time_formatted,
                max,
                avg,
                min,
            )

    def _send_identification(self):
        client_msg = self.get_client_msg()
        return client_msg if self._send_command(client_msg) else False

    def _fireEvent(self, event, payload=None):
        self._event_bus.fire(event, payload)

    def _as_number(self, str):
        if str is None:
            return None
        try:
            return float(str)
        except:
            return None

    def get_command_msg(self, device, action, value=None):
        """
        Make and return command in required format
        :param device: device for which command should be executed
        :param action: action to be executed for given device
        :param value: additional value (optional, but required for some commands like fan:on:50)
        :return: command message
        """
        command = {
            self.MESSAGE_COMMAND: {"device": device, "action": action},
            "request_id": self.next_request_id(),
        }
        if value is not None:
            command[self.MESSAGE_COMMAND]["value"] = value
        return command

    def get_request_msg(self, datasets):
        """
        Make and return data request message in required format
        :param datasets:
        :return: data request message
        """
        return {self.MESSAGE_REQUEST: datasets, "request_id": self.next_request_id()}

    def get_client_msg(self):
        """
        Make and return client identification message in required format
        :return: client identification message
        """
        return {
            "client": {
                "name": self.CLIENT_NAME,
                "version": self._plugin.get_plugin_version(),
                "config": {"send_initial_data": True, "update_interval": True},
            }
        }

    def next_request_id(self):
        """
        Get next request id for a command or data request
        :return: next request id
        """
        with self._request_id_lock:
            self.request_id += 1
            return self.request_id

    def _get_connected_val(self, value):
        connected = None
        if value is None:
            return None

        value = value.lower()
        if value in ("none", "unknown"):
            connected = None
        elif value == "false" or value == "error":
            connected = False
        elif value == "true":
            connected = True
        return connected

    def send_iobeam_analytics(self, eventname, data):
        """
        This will send analytics data using the MrBeam event system, to mimic what the rest of the plugins do.
        Everything will be saved to the type='iobeam'.
        Args:
                eventname: the name of the event for Datastore ('e')
                data: the payload of the event for Datastore ('data')

        Returns:

        """
        payload = dict(
            plugin="iobeam",
            plugin_version=self.iobeam_version,
            eventname=eventname,
            data=data,
        )

        self._plugin.fire_event(MrBeamEvents.ANALYTICS_DATA, payload)
