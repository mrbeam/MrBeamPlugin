# coding=utf-8
from __future__ import absolute_import

__author__ = (
    "Florian Becker <florian@mr-beam.org> based on work by Gina Häußge and David Braam"
)
__license__ = "GNU Affero General Public License http://www.gnu.org/licenses/agpl.html"
__copyright__ = (
    "Copyright (C) 2013 David Braam - Released under terms of the AGPLv3 License"
)

import os
import threading
import glob
import time
import serial
import re
import Queue
import random

from flask.ext.babel import gettext

import octoprint.plugin

from octoprint.settings import settings, default_settings
from octoprint.events import eventManager, Events as OctoPrintEvents
from octoprint.filemanager.destinations import FileDestinations
from octoprint.util import (
    get_exception_string,
    RepeatedTimer,
    CountedEvent,
    sanitize_ascii,
)

from octoprint_mrbeam.printing.profile import laserCutterProfileManager
from octoprint_mrbeam.mrb_logger import mrb_logger
from octoprint_mrbeam.printing.acc_line_buffer import AccLineBuffer
from octoprint_mrbeam.printing.acc_watch_dog import AccWatchDog
from octoprint_mrbeam.util import dict_get
from octoprint_mrbeam.util.cmd_exec import exec_cmd_output
from octoprint_mrbeam.mrbeam_events import MrBeamEvents

### MachineCom #########################################################################################################
class MachineCom(object):

    DEBUG_PRODUCE_CHECKSUM_ERRORS = False
    DEBUG_PRODUCE_CHECKSUM_ERRORS_RND = 2000
    DEBUG_PRODUCE_FAKE_SYNC_ERRORS = False

    ### GRBL VERSIONs #######################################
    # original grbl
    GRBL_VERSION_20170919_22270fa = "0.9g_22270fa"
    #
    # adds rescue from home feature
    GRBL_VERSION_20180223_61638c5 = "0.9g_20180223_61638c5"
    GRBL_FEAT_BLOCK_VERSION_LIST_RESCUE_FROM_HOME = GRBL_VERSION_20170919_22270fa
    #
    # trial grbl
    # - adds rx-buffer state with every ok
    # - adds alarm mesage on rx buffer overrun
    GRBL_VERSION_20180828_ac367ff = "0.9g_20180828_ac367ff"
    #
    # adds G24_AVOIDED
    GRBL_VERSION_20181116_a437781 = "0.9g_20181116_a437781"
    #
    # adds checksums
    GRBL_VERSION_2019_MRB_CHECKSUM = "0.9g_20190327_d2868b9"
    #
    # fixes burn marks
    GRBL_VERSION_20210714_d5e31ee = "0.9g_20210714_d5e31ee"

    GRBL_FEAT_BLOCK_CHECKSUMS = (
        GRBL_VERSION_20170919_22270fa,
        GRBL_VERSION_20180223_61638c5,
        GRBL_VERSION_20180828_ac367ff,
        GRBL_VERSION_20181116_a437781,
    )
    #
    #
    GRBL_DEFAULT_VERSION = GRBL_VERSION_20210714_d5e31ee
    ##########################################################

    GRBL_SETTINGS_READ_WINDOW = 10.0
    GRBL_SETTINGS_CHECK_FREQUENCY = 0.5

    GRBL_RX_BUFFER_SIZE = 127
    GRBL_WORKING_RX_BUFFER_SIZE = GRBL_RX_BUFFER_SIZE - 5
    GRBL_LINE_BUFFER_SIZE = 80

    STATE_NONE = 0
    STATE_OPEN_SERIAL = 1
    STATE_DETECT_SERIAL = 2
    STATE_DETECT_BAUDRATE = 3
    STATE_CONNECTING = 4
    STATE_OPERATIONAL = 5
    STATE_PRINTING = 6
    STATE_PAUSED = 7
    STATE_CLOSED = 8
    STATE_ERROR = 9
    STATE_CLOSED_WITH_ERROR = 10
    STATE_TRANSFERING_FILE = 11
    STATE_LOCKED = 12
    STATE_HOMING = 13
    STATE_FLASHING = 14

    GRBL_STATE_QUEUE = "Queue"
    GRBL_STATE_IDLE = "Idle"
    GRBL_STATE_RUN = "Run"

    COMMAND_STATUS = "?"
    COMMAND_HOLD = "!"
    COMMAND_RESUME = "~"
    COMMAND_RESET = b"\x18"
    COMMAND_FLUSH = "FLUSH"
    COMMAND_SYNC = "SYNC"
    COMMAND_RESET_ALARM = "$X"

    STATUS_POLL_FREQUENCY_OPERATIONAL = 2.0
    STATUS_POLL_FREQUENCY_PRINTING = 1.0  # set back top 1.0 if it's not causing gcode24
    STATUS_POLL_FREQUENCY_PAUSED = 0.2
    STATUS_POLL_FREQUENCY_DEFAULT = STATUS_POLL_FREQUENCY_PRINTING

    GRBL_SYNC_COMMAND_WAIT_STATES = (GRBL_STATE_RUN, GRBL_STATE_QUEUE)
    GRBL_SYNC_COMMAND_IDLE_STATES = (GRBL_STATE_IDLE,)

    GRBL_HEX_FOLDER = "files/grbl/"

    pattern_grbl_status_legacy = re.compile(
        "<(?P<status>\w+),.*MPos:(?P<mpos_x>[0-9.\-]+),(?P<mpos_y>[0-9.\-]+),.*WPos:(?P<pos_x>[0-9.\-]+),(?P<pos_y>[0-9.\-]+),.*RX:(?P<rx>\d+),.*laser (?P<laser_state>\w+):(?P<laser_intensity>\d+).*>"
    )
    pattern_grbl_status = re.compile(
        "<(?P<status>\w+),.*MPos:(?P<mpos_x>[0-9.\-]+),(?P<mpos_y>[0-9.\-]+),.*WPos:(?P<pos_x>[0-9.\-]+),(?P<pos_y>[0-9.\-]+),.*RX:(?P<rx>\d+),.*limits:(?P<limit_x>[x]?)(?P<limit_y>[y]?)z?,.*laser (?P<laser_state>\w+):(?P<laser_intensity>\d+).*>"
    )
    pattern_grbl_version = re.compile("Grbl (?P<version>\S+)\s.*")
    pattern_grbl_setting = re.compile(
        "\$(?P<id>\d+)=(?P<value>\S+)\s\((?P<comment>.*)\)"
    )

    ALARM_CODE_COMMAND_TOO_LONG = "ALARM_CODE_COMMAND_TOO_LONG"

    pattern_get_x_coord_from_gcode = re.compile("^G.*X(\d{1,3}\.?\d{0,3})\D.*")
    pattern_get_y_coord_from_gcode = re.compile("^G.*Y(\d{1,3}\.?\d{0,3})\D.*")

    def __init__(
        self, port=None, baudrate=None, callbackObject=None, printerProfileManager=None
    ):
        self._logger = mrb_logger("octoprint.plugins.mrbeam.printing.comm_acc2")

        if port is None:
            port = settings().get(["serial", "port"])
        elif isinstance(port, list):
            port = port[0]
        if baudrate is None:
            settingsBaudrate = settings().getInt(["serial", "baudrate"])
            if settingsBaudrate is None:
                baudrate = 0
            else:
                baudrate = settingsBaudrate
        if callbackObject is None:
            callbackObject = MachineComPrintCallback()

        self._port = port
        self._baudrate = baudrate
        self._callback = callbackObject
        self._laserCutterProfile = laserCutterProfileManager().get_current_or_default()

        self._state = self.STATE_NONE
        self._grbl_state = None
        self._grbl_version = None
        self._grbl_settings = dict()
        self._errorValue = "Unknown Error"
        self._serial = None
        self._currentFile = None
        self._status_polling_timer = None
        self._status_polling_next_ts = 0
        self._status_polling_interval = self.STATUS_POLL_FREQUENCY_DEFAULT
        self._status_last_ts = 0
        self._acc_line_buffer = AccLineBuffer()
        self._current_feedrate = None
        self._current_intensity = None
        self._current_pos_x = None
        self._current_pos_y = None
        self._current_laser_on = False
        self._cmd = None
        self._recovery_lock = False
        self._recovery_ignore_further_alarm_responses = False
        self._lines_recoverd_total = 0
        self._pauseWaitStartTime = None
        self._pauseWaitTimeLost = 0.0
        self._commandQueue = Queue.Queue()
        self._send_event = CountedEvent(max=50)
        self._finished_currentFile = False
        self._pause_delay_time = 0
        self._passes = 1
        self._finished_passes = 0
        self._flush_command_ts = -1
        self._sync_command_ts = -1
        self._sync_command_state_sent = False
        self.limit_x = -1
        self.limit_y = -1
        # from GRBL status RX value: Number of characters queued in Grbl's serial RX receive buffer.
        self._grbl_rx_status = -1
        self._grbl_rx_last_change = -1
        self._grbl_settings_correction_ts = 0

        self.g24_avoided_message = []

        self.grbl_auto_update_enabled = _mrbeam_plugin_implementation._settings.get(
            ["dev", "grbl_auto_update_enabled"]
        )
        self._terminal_show_checksums = _mrbeam_plugin_implementation._settings.get(
            ["terminal_show_checksums"]
        )

        # grbl features
        self.grbl_feat_rescue_from_home = False
        self.grbl_feat_checksums = False

        # regular expressions
        self._regex_command = re.compile("^\s*\*?\d*\s*\$?([GM]\d+|[THFSX])")
        self._regex_feedrate = re.compile("F\d+", re.IGNORECASE)
        self._regex_intensity = re.compile("S\d+", re.IGNORECASE)
        self._regex_compressor = re.compile("M100\w*P(\d+)", re.IGNORECASE)
        self._regex_gcode = re.compile("([XY])(\d+\.?\d*)", re.IGNORECASE)

        self._real_time_commands = {
            "poll_status": False,
            "feed_hold": False,
            "cycle_start": False,
            "soft_reset": False,
        }

        # hooks
        self._pluginManager = octoprint.plugin.plugin_manager()
        self._serial_factory_hooks = self._pluginManager.get_hooks(
            "octoprint.comm.transport.serial.factory"
        )

        # laser power correction
        self._power_correction_settings = (
            _mrbeam_plugin_implementation.laserhead_handler.get_correction_settings()
        )
        self._current_lh_data = (
            _mrbeam_plugin_implementation.laserhead_handler.get_current_used_lh_data()
        )
        self._intensity_upper_bound = int(
            self._laserCutterProfile["laser"]["intensity_upper_bound"]
        )

        self._power_correction_factor = 1
        if self._power_correction_settings["correction_enabled"]:
            lh_info = self._current_lh_data["info"]
            if self._power_correction_settings["correction_factor_override"]:
                self._power_correction_factor = self._power_correction_settings[
                    "correction_factor_override"
                ]
            else:
                if lh_info and "correction_factor" in lh_info:
                    self._power_correction_factor = lh_info["correction_factor"]

        self._logger.info(
            "Power correction factor: {}".format(self._power_correction_factor)
        )

        self.watch_dog = AccWatchDog(self)

        # threads
        self.monitoring_thread = None
        self.sending_thread = None
        self.recovery_thread = None
        self._start_monitoring_thread()
        self._start_status_polling_timer()

    def _start_monitoring_thread(self):
        self._monitoring_active = True
        self.monitoring_thread = threading.Thread(
            target=self._monitor_loop, name="comm._monitoring_thread"
        )
        self.monitoring_thread.daemon = True
        self.monitoring_thread.start()

    def _start_sending_thread(self):
        self._sending_active = True
        self.sending_thread = threading.Thread(
            target=self._send_loop, name="comm._sending_thread"
        )
        self.sending_thread.daemon = True
        self.sending_thread.start()

    def _start_status_polling_timer(self):
        if self._status_polling_timer is not None:
            self._status_polling_timer.cancel()
        self._status_polling_timer = RepeatedTimer(0.1, self._poll_status)
        self._status_polling_timer.start()

    def set_terminal_show_checksums(self, enabled):
        self._terminal_show_checksums = bool(enabled)
        self._logger.info(
            "Show checksums: %s",
            "on" if self._terminal_show_checksums else "off",
            terminal_as_comm=True,
        )

    def get_home_position(self):
        """
        Returns the home position which usually where the head is after homing. (Except in C series)
        :return: Tuple of (x, y) position
        """
        if (
            dict_get(self._laserCutterProfile, ["legacy", "job_done_home_position_x"])
            is not None
        ):
            return (
                self._laserCutterProfile["legacy"]["job_done_home_position_x"],
                self._laserCutterProfile["volume"]["depth"]
                + self._laserCutterProfile["volume"]["working_area_shift_y"],
            )
        return (
            self._laserCutterProfile["volume"]["width"]
            + self._laserCutterProfile["volume"]["working_area_shift_x"],
            self._laserCutterProfile["volume"]["depth"]
            + self._laserCutterProfile["volume"]["working_area_shift_y"],
        )

    def _monitor_loop(self):
        try:
            # Open the serial port.
            if not self._openSerial():
                self._logger.critical(
                    "_monitor_loop() Serial not open, leaving monitoring loop."
                )
                return

            self._logger.info(
                "Connected to: %s, starting monitor" % self._serial,
                terminal_as_comm=True,
            )
            self._changeState(self.STATE_CONNECTING)

            if (
                self.grbl_auto_update_enabled
                and self._laserCutterProfile["grbl"]["auto_update_file"]
            ):
                self._logger.info(
                    "GRBL auto updating to version: %s, file: %s",
                    self._laserCutterProfile["grbl"]["auto_update_version"],
                    self._laserCutterProfile["grbl"]["auto_update_file"],
                )
                self.flash_grbl(
                    grbl_file=self._laserCutterProfile["grbl"]["auto_update_file"],
                    is_connected=False,
                )

            # reset on connect
            if self._laserCutterProfile["grbl"]["resetOnConnect"]:
                self._serial.flushInput()
                self._serial.flushOutput()
                self._sendCommand(self.COMMAND_RESET)
            self._timeout = get_new_timeout("communication")

            while self._monitoring_active:
                try:
                    line = self._readline()
                    if line is None:
                        break
                    if line.strip() is not "":
                        self._timeout = get_new_timeout("communication")
                    if line.startswith("<"):  # status report
                        self._handle_status_report(line)
                    elif line.startswith("ok"):  # ok message :)
                        self._handle_ok_message(line)
                    elif line.startswith("err"):  # error message
                        self._handle_error_message(line)
                    elif line.startswith("ALA"):  # ALARM message
                        self._handle_alarm_message(line)
                    elif line.startswith("["):  # feedback message
                        self._handle_feedback_message(line)
                    elif line.startswith("Grb"):  # Grbl startup message
                        self._handle_startup_message(line)
                    elif line.startswith("Corru"):  # Corrupted line:
                        self._handle_g24avoided_corrupted_line(line)
                    elif line.startswith("$"):  # Grbl settings
                        self._handle_settings_message(line)
                    elif not line and (
                        self._state is self.STATE_CONNECTING
                        or self._state is self.STATE_OPEN_SERIAL
                        or self._state is self.STATE_DETECT_SERIAL
                    ):
                        self._logger.warning(
                            "Empty line received during STATE_CONNECTION, starting soft-reset",
                            terminal_as_comm=True,
                            analytics=True,
                        )
                        self._sendCommand(self.COMMAND_RESET)  # Serial-Connection Error
                except Exception as e:
                    self._logger.exception(
                        "Exception in _monitor_loop: {}".format(e),
                        terminal_dump=True,
                        analytics=True,
                    )
                    errorMsg = gettext(
                        "Please contact Mr Beam support team and attach octoprint.log."
                    )
                    self._log(errorMsg)
                    self._errorValue = errorMsg
                    self._fire_print_failed()
                    self._changeState(self.STATE_ERROR)
                    eventManager().fire(
                        OctoPrintEvents.ERROR,
                        dict(error=self.getErrorString(), analytics=False),
                    )
            self._logger.info(
                "Connection closed, closing down monitor", terminal_as_comm=True
            )
        except:
            self._logger.exception("Exception in _monitor_loop() thread: ")

    def _send_loop(self):
        while self._sending_active:
            try:
                self._process_rt_commands()
                # if self.isPrinting() and self._commandQueue.empty():
                if (
                    self.isPrinting()
                    and self._commandQueue.empty()
                    and not self._recovery_lock
                ):
                    cmd = self._getNext()  # get next cmd form file
                    if cmd is not None:
                        self.sendCommand(cmd)
                        self._callback.on_comm_progress()
                    else:
                        # TODO: this code is about lasering the same file several times. not gonna happen in mrbII
                        if self._finished_passes >= self._passes:
                            if self._acc_line_buffer.is_empty():
                                self.watch_dog.do_regular_check()
                                self.watch_dog.log_state(
                                    trigger="before_set_print_finished"
                                )
                                self._set_print_finished()
                                self.watch_dog.log_state(
                                    trigger="after_set_print_finished"
                                )
                        self._currentFile.resetToBeginning()
                        cmd = self._getNext()  # get next cmd form file
                        if cmd is not None:
                            self.sendCommand(cmd)
                            self._callback.on_comm_progress()

                self._sendCommand()
                self._send_event.wait(1)
                self._send_event.clear()
            except Exception as e:
                self._logger.exception(
                    "Exception in _send_loop: {}".format(e), terminal_dump=True
                )
                errorMsg = gettext(
                    "Please contact Mr Beam support team and attach octoprint.log."
                )
                self._log(errorMsg)
                self._errorValue = errorMsg
                self._fire_print_failed()
                self._changeState(self.STATE_ERROR)
                eventManager().fire(
                    OctoPrintEvents.ERROR,
                    dict(error=self.getErrorString(), analytics=False),
                )
        # self._logger.info("ANDYTEST Leaving _send_loop()")

    def _sendCommand(self, cmd=None):
        """
        Takes command from:
         - parameter passed to this function, (!! treated as real time command)
         - self._cmd or
         - self._commandQueue.get()
        and writes it onto serial.
        If command is passed as parameter it's treated as a real time command,
        which means there are no checks if it will exceed grbl buffer current capacity.
        :param cmd: treated as real time command

        All commands can be either a plain string or an dict object.
        Object-Commands can have the following keys and are executed in this order:
        - flush: a FLUSH is performed before any other step is executed. FLUSH waits until we're no longer waiting for any OKs from GRBL
        - sync: a SYNC is performed before any other step is executed. SYNC is like FLUSH but waits until GRBL reports IDLE state.
        - compressor: Set the compressor (if present) to the given value. usually in combination with flush.
        - cmd: a command string (sam as if cmd is a plain string)
        """
        if cmd is None:
            if self._cmd is None and self._commandQueue.empty():
                return
            elif self._cmd is None:
                tmp = self._commandQueue.get()
                if isinstance(tmp, basestring):
                    self._cmd = {"cmd": tmp}
                elif isinstance(tmp, dict):
                    self._cmd = tmp
                else:
                    self._logger.error(
                        "_sendCommand() command is of unexpected type: %s", type(tmp)
                    )

            # FLUSH
            if self._cmd.get("cmd", None) == self.COMMAND_FLUSH or self._cmd.get(
                "flush", False
            ):
                # FLUSH waits until we're no longer waiting for any OKs from GRBL
                if self._flush_command_ts <= 0:
                    self._flush_command_ts = time.time()
                    self._logger.debug(
                        "FLUSHing (grbl_state: {}, acc_line_buffer: {}, grbl_rx: {})".format(
                            self._grbl_state,
                            self._acc_line_buffer.get_char_len(),
                            self._grbl_rx_status,
                        ),
                        terminal_as_comm=True,
                    )
                    if self.DEBUG_PRODUCE_FAKE_SYNC_ERRORS and self._grbl_rx_status > 0:
                        self._acc_line_buffer.add(
                            "DUMMY\n",
                            intensity=self._current_intensity,
                            feedrate=self._current_feedrate,
                            pos_x=self._current_pos_x,
                            pos_y=self._current_pos_y,
                            laser=self._current_laser_on,
                        )
                        self._logger.debug(
                            "FLUSHing DEBUG_PRODUCE_FAKE_SYNC_ERRORS added fake command (grbl_state: {}, acc_line_buffer: {}, grbl_rx: {})".format(
                                self._grbl_state,
                                self._acc_line_buffer.get_char_len(),
                                self._grbl_rx_status,
                            ),
                            terminal_as_comm=True,
                        )
                    return
                elif self._acc_line_buffer.is_empty():
                    self._cmd.pop("flush", None)
                    if self._cmd.get("cmd", None) == self.COMMAND_FLUSH:
                        self._cmd.pop("cmd", None)
                    self._logger.debug(
                        "FLUSHed ({}ms)".format(
                            int(1000 * (time.time() - self._flush_command_ts))
                        ),
                        terminal_as_comm=True,
                    )
                    self._flush_command_ts = -1
                elif (
                    (time.time() - self._flush_command_ts) > 3.0
                    and (self._status_last_ts > self._flush_command_ts)
                    and self._grbl_rx_status == 0
                    and (
                        time.time() - self._grbl_rx_last_change
                        > self.STATUS_POLL_FREQUENCY_PRINTING * 2 + 0.1
                    )
                    and not self._acc_line_buffer.is_empty()
                ):
                    # We used generous timing here to be sure that this state is persistent.
                    self._logger.warn(
                        "FLUSHing clogged! Clearing commands in %s",
                        self._acc_line_buffer,
                        terminal_as_comm=True,
                        analytics=True,
                    )
                    self._acc_line_buffer.reset_clogged()
                else:
                    # still flushing. do nothing else for now...
                    return

            # SYNC
            if self._cmd.get("cmd", None) == self.COMMAND_SYNC or self._cmd.get(
                "sync", False
            ):
                # As FLUSH but wait for GRBL going IDLE before we continue
                if self._sync_command_ts <= 0:
                    self._sync_command_ts = time.time()
                    self._sync_command_state_sent = False
                    self._logger.debug(
                        "SYNCing (grbl_state: {}, acc_line_buffer: {}, grbl_rx: {})".format(
                            self._grbl_state,
                            self._acc_line_buffer.get_char_len(),
                            self._grbl_rx_status,
                        ),
                        terminal_as_comm=True,
                    )
                    if self.DEBUG_PRODUCE_FAKE_SYNC_ERRORS and self._grbl_rx_status > 0:
                        self._acc_line_buffer.add(
                            "DUMMY\n",
                            intensity=self._current_intensity,
                            feedrate=self._current_feedrate,
                            pos_x=self._current_pos_x,
                            pos_y=self._current_pos_y,
                            laser=self._current_laser_on,
                        )
                        self._logger.debug(
                            "SYNCing DEBUG_PRODUCE_FAKE_SYNC_ERRORS added fake command (grbl_state: {}, acc_line_buffer: {}, grbl_rx: {})".format(
                                self._grbl_state,
                                self._acc_line_buffer.get_char_len(),
                                self._grbl_rx_status,
                            ),
                            terminal_as_comm=True,
                        )
                    return
                elif self._acc_line_buffer.is_empty() and not (
                    self._grbl_state in self.GRBL_SYNC_COMMAND_WAIT_STATES
                ):
                    # Successfully synced, let's move on
                    self._cmd.pop("sync", None)
                    if self._cmd.get("cmd", None) == self.COMMAND_SYNC:
                        self._cmd.pop("cmd", None)
                    self._logger.debug(
                        "SYNCed ({}ms)".format(
                            int(1000 * (time.time() - self._sync_command_ts))
                        ),
                        terminal_as_comm=True,
                    )
                    self._sync_command_ts = -1
                    self._sync_command_state_sent = False
                elif (
                    self._acc_line_buffer.is_empty()
                    and (self._grbl_state in self.GRBL_SYNC_COMMAND_WAIT_STATES)
                    and not self._sync_command_state_sent
                ):
                    # Request a status update from GRBL to see if it's really ready.
                    self._sync_command_state_sent = True
                    self._logger.debug(
                        "SYNCing ({}ms) - Sending '?'".format(
                            int(1000 * (time.time() - self._sync_command_ts))
                        ),
                        terminal_as_comm=True,
                    )
                    self._sendCommand(self.COMMAND_STATUS)
                    return
                elif (
                    (time.time() - self._sync_command_ts) > 3.0
                    and (self._status_last_ts > self._sync_command_ts)
                    and self._grbl_rx_status == 0
                    and (
                        time.time() - self._grbl_rx_last_change
                        > self.STATUS_POLL_FREQUENCY_PRINTING * 2 + 0.1
                    )
                    and not self._acc_line_buffer.is_empty()
                ):
                    # We used generous timing here to be sure that this state is persistent.
                    self._logger.warn(
                        "SYNCing clogged! Clearing commands in %s",
                        self._acc_line_buffer,
                        terminal_as_comm=True,
                        analytics=True,
                    )
                    self._acc_line_buffer.reset_clogged()
                else:
                    # still syncing. do nothing else for now...
                    return

            # COMPRESSOR
            if "compressor" in self._cmd:
                comp_val = self._cmd.pop("compressor")
                self._set_compressor(comp_val)
                self._logger.debug("Compressor: %s", comp_val, terminal_as_comm=True)

            # CMD
            if "cmd" in self._cmd:
                my_cmd = self._cmd.get("cmd", None)  # to avoid race conditions
                if my_cmd is None:
                    self._cmd.pop("cmd", None)
                elif not (len(my_cmd) + 1 < self.GRBL_LINE_BUFFER_SIZE):
                    msg = "Error: Command too long. max: {}, cmd length: {}, cmd: {}... (shortened)".format(
                        self.GRBL_LINE_BUFFER_SIZE - 1,
                        len(my_cmd),
                        my_cmd[0 : self.GRBL_LINE_BUFFER_SIZE - 1],
                    )
                    self._logger.error(msg, analytics=True)
                    self._handle_alarm_message(
                        "Command too long to send to GRBL.",
                        code=self.ALARM_CODE_COMMAND_TOO_LONG,
                    )
                    self._cmd.pop("cmd", None)
                elif (
                    my_cmd
                    and self._acc_line_buffer.get_char_len() + len(my_cmd) + 1
                    < self.GRBL_WORKING_RX_BUFFER_SIZE
                ):
                    # In recovery: if acc_line_buffer is marked dirty we must check if it is set to clean again.
                    if (
                        self._acc_line_buffer.is_dirty()
                        and self.COMMAND_RESET_ALARM in my_cmd
                    ):
                        self._acc_line_buffer.set_clean()
                    self._log("Send: %s" % (my_cmd), is_command=True)
                    self._acc_line_buffer.add(
                        my_cmd + "\n",
                        intensity=self._current_intensity,
                        feedrate=self._current_feedrate,
                        pos_x=self._current_pos_x,
                        pos_y=self._current_pos_y,
                        laser=self._current_laser_on,
                    )

                    if self.DEBUG_PRODUCE_CHECKSUM_ERRORS:
                        if (
                            random.randint(0, self.DEBUG_PRODUCE_CHECKSUM_ERRORS_RND)
                            == 1
                        ):
                            orig_command = my_cmd
                            rnd = random.randint(0, len(my_cmd) - 1)
                            my_cmd = (
                                my_cmd[: rnd - 1]
                                + chr(random.randint(0, 255))
                                + my_cmd[rnd:]
                            )
                            self._logger.warn(
                                "DEBUG Randomly changed '%s' to '%s' to cause checksum error.",
                                orig_command,
                                my_cmd,
                                terminal_as_comm=True,
                            )
                    try:
                        self._serial.write(bytes(my_cmd + "\n"))
                        self._process_command_phase("sent", my_cmd)
                        self._cmd.pop("cmd", None)
                    # except serial.SerialException:
                    except Exception:
                        self._logger.exception(
                            "Exception while writing to serial: cmd: %s - %s"
                            % (my_cmd, get_exception_string())
                        )
                        self._errorValue = get_exception_string()
                        self.close(True)

            if len(self._cmd) <= 0:
                # ok, we're done with this command
                self._cmd = None
                self._send_event.set()
        else:
            cmd_obj = self._process_command_phase("sending", cmd)
            my_cmd = cmd_obj.get("cmd", "")
            self._log("Send: %s" % my_cmd)
            try:
                self._serial.write(bytes(my_cmd))
                self._process_command_phase("sent", my_cmd)
            except serial.SerialException:
                self._logger.info(
                    "Unexpected error while writing serial port: %s"
                    % (get_exception_string()),
                    terminal_as_comm=True,
                )
                self._errorValue = get_exception_string()
                self.close(True)

    def _calc_checksum(self, cmd):
        checksum = 0
        for c in list(cmd):
            # whitespaces are ignored for checksum!
            if c != " ":
                checksum += ord(c)
        checksum = checksum % 256
        return checksum

    def _add_checksum_to_cmd(self, cmd):
        if cmd is None:
            return None
        if cmd.find("*") < 0 and cmd not in (self.COMMAND_FLUSH, self.COMMAND_SYNC):
            cmd = "{cmd}*{chk}".format(cmd=cmd, chk=self._calc_checksum(cmd))
        return cmd

    def _process_rt_commands(self):
        if self._real_time_commands["poll_status"]:
            self._sendCommand(self.COMMAND_STATUS)
            self._real_time_commands["poll_status"] = False
        elif self._real_time_commands["feed_hold"]:
            self._sendCommand(self.COMMAND_HOLD)
            self._real_time_commands["feed_hold"] = False
        elif self._real_time_commands["cycle_start"]:
            self._sendCommand(self.COMMAND_RESUME)
            self._real_time_commands["cycle_start"] = False
        elif self._real_time_commands["soft_reset"]:
            self._sendCommand(self.COMMAND_RESET)
            self._real_time_commands["soft_reset"] = False

    def _handle_rt_command(self, cmd):
        """
        If cmd is a RT command, the RT command is sent and True is returned, False otherwise.
        :param cmd:
        :return:
        """
        cmd = cmd.strip()
        if cmd == self.COMMAND_STATUS:
            self._sendCommand(self.COMMAND_STATUS)
        elif cmd == self.COMMAND_HOLD:
            self._sendCommand(self.COMMAND_HOLD)
        elif cmd == self.COMMAND_RESUME:
            self._sendCommand(self.COMMAND_RESUME)
        elif cmd == self.COMMAND_RESET:
            self._sendCommand(self.COMMAND_RESET)
        else:
            return False
        return True

    def _openSerial(self):
        self._grbl_version = None
        self._grbl_settings = dict()

        def default(_, port, baudrate, read_timeout):
            if port is None or port == "AUTO":
                # no known port, try auto detection
                self._changeState(self.STATE_DETECT_SERIAL)
                ser = self._detectPort(True)
                if ser is None:
                    self._errorValue = (
                        "Failed to autodetect serial port, please set it manually."
                    )
                    self._changeState(self.STATE_ERROR)
                    eventManager().fire(
                        OctoPrintEvents.ERROR,
                        dict(error=self.getErrorString(), analytics=False),
                    )
                    self._logger.warn(
                        "Failed to autodetect serial port, please set it manually.",
                        terminal_dump=True,
                        serial=True,
                        analytics=True,
                    )
                    return None
                port = ser.port

            # connect to regular serial port
            self._logger.info("Connecting to: %s" % port, terminal_as_comm=True)
            if baudrate == 0:
                baudrates = baudrateList()
                ser = serial.Serial(
                    str(port),
                    115200 if 115200 in baudrates else baudrates[0],
                    timeout=read_timeout,
                    writeTimeout=10000,
                    parity=serial.PARITY_ODD,
                )
            else:
                ser = serial.Serial(
                    str(port),
                    baudrate,
                    timeout=read_timeout,
                    writeTimeout=10000,
                    parity=serial.PARITY_ODD,
                )
            ser.close()
            ser.parity = serial.PARITY_NONE
            ser.open()
            return ser

        serial_factories = self._serial_factory_hooks.items() + [("default", default)]
        for name, factory in serial_factories:
            try:
                serial_obj = factory(
                    self,
                    self._port,
                    self._baudrate,
                    settings().getFloat(["serial", "timeout", "connection"]),
                )
            except (OSError, serial.SerialException):
                exception_string = get_exception_string()
                self._errorValue = "Connection error, see Terminal tab"
                self._changeState(self.STATE_ERROR)
                eventManager().fire(
                    OctoPrintEvents.ERROR,
                    dict(error=self.getErrorString(), analytics=False),
                )
                self._logger.warn(
                    "Unexpected error while connecting to serial port: %s %s (hook %s)",
                    self._port,
                    exception_string,
                    name,
                    serial=True,
                    terminal_dump=True,
                    analytics=True,
                )
                if "failed to set custom baud rate" in exception_string.lower():
                    self._log(
                        "Your installation does not support custom baudrates (e.g. 250000) for connecting to your printer. This is a problem of the pyserial library that OctoPrint depends on. Please update to a pyserial version that supports your baudrate or switch your printer's firmware to a standard baudrate (e.g. 115200). See https://github.com/foosel/OctoPrint/wiki/OctoPrint-support-for-250000-baud-rate-on-Raspbian"
                    )
                return False
            if serial_obj is not None:
                # first hook to succeed wins, but any can pass on to the next
                self._changeState(self.STATE_OPEN_SERIAL)
                self._serial = serial_obj
                return True
        return False

    def _readline(self):
        if self._serial is None:
            return None
        ret = None
        cmd = None
        recovery_str = (
            "RECOVERY" if self._recovery_ignore_further_alarm_responses else ""
        )
        try:
            ret = self._serial.readline()
            self._send_event.set()
            if "ok" in ret:
                cmd = self._acc_line_buffer.acknowledge_cmd()
                if self._recovery_ignore_further_alarm_responses:
                    recovery_str = "RECOVERY END"
            elif (
                "err" in ret or "ALARM" in ret
            ):  # TODO: are all ALARM messages to be counted?
                cmd = self._acc_line_buffer.decline_cmd()
            cmd = AccLineBuffer.get_cmd_from_item(cmd)
        except serial.SerialException:
            self._logger.error(
                "Unexpected error while reading serial port: %s"
                % (get_exception_string()),
                terminal_as_comm=True,
            )
            self._errorValue = get_exception_string()
            self.close(True)
            return None
        except TypeError as e:
            # While closing or reopening sometimes we get this exception:
            # 	File "build/bdist.linux-armv7l/egg/serial/serialposix.py", line 468, in read
            #     buf = os.read(self.fd, size-len(read))
            self._logger.exception(
                "TypeError in _readline. Did this happen while closing or re-opening serial?: {e}".format(
                    e=e
                ),
                terminal_as_comm=True,
            )
            pass
        if ret is None or ret == "":
            return ""
        try:
            if cmd:
                self._log(
                    "Recv: %s  // %s  %s" % (sanitize_ascii(ret), cmd, recovery_str),
                    is_command=True,
                )
            else:
                self._log("Recv: %s" % (sanitize_ascii(ret)), is_command=True)
        except ValueError as e:
            # self._log("WARN: While reading last line: %s" % e)
            self._logger.warn(
                "Exception while sanitizing ascii input from grbl. Excpetion: '%s', original string from grbl: '%s'",
                e,
                ret,
            )
            self._log("Recv: %r" % ret)
        return ret

    def _getNext(self):
        if self._finished_currentFile is False:
            line = self._currentFile.getNext()
            if line is None:
                self._finished_passes += 1
                if self._finished_passes >= self._passes:
                    self._finished_currentFile = True
            return line
        else:
            return None

    def _set_print_finished(self):
        self._logger.debug("_set_print_finished() called")
        self._callback.on_comm_print_job_done()
        self._changeState(self.STATE_OPERATIONAL)
        payload = self._get_printing_file_state()
        self.watch_dog.stop()
        self._move_home()
        _mrbeam_plugin_implementation.fire_event(
            MrBeamEvents.PRINT_DONE_PAYLOAD, payload
        )

    def _move_home(self):
        self._logger.debug("_move_home() called")
        self.sendCommand("M5")
        h_pos = self.get_home_position()
        command = "G0X{x}Y{y}".format(x=h_pos[0], y=h_pos[1])
        self.sendCommand(command)
        self.sendCommand("M9")

    def _handle_status_report(self, line):
        match = None
        if self._grbl_version == self.GRBL_VERSION_20170919_22270fa:
            match = self.pattern_grbl_status_legacy.match(line)
        else:
            match = self.pattern_grbl_status.match(line)
        if not match:
            self._logger.warn(
                "GRBL status string did not match pattern. GRBL version: %s, status string: %s",
                self._grbl_version,
                line,
            )
            return

        groups = match.groupdict()
        self._grbl_state = groups["status"]

        #  limit (end stops) not supported in legacy GRBL version
        if "limit_x" in groups:
            self.limit_x = time.time() if groups["limit_x"] else 0
        if "limit_y" in groups:
            self.limit_y = time.time() if groups["limit_y"] else 0

        # grbl_character_buffer
        if "rx" in groups:
            rx = -1
            try:
                rx = int(groups["rx"])
            except ValueError:
                self._logger.error(
                    "Can't convert RX value from GRBL status to int. RX value: %s",
                    groups["rx"],
                )
            if not rx == self._grbl_rx_status:
                self._grbl_rx_status = rx
                self._grbl_rx_last_change = time.time()

        # positions
        try:
            self.MPosX = float(groups["mpos_x"])
            self.MPosY = float(groups["mpos_y"])
            wx = float(groups["pos_x"])
            wy = float(groups["pos_y"])
            self._callback.on_comm_pos_update([self.MPosX, self.MPosY, 0], [wx, wy, 0])
        except:
            self._logger.exception(
                "Exception while handling position updates from GRBL."
            )

        # laser
        self._handle_laser_intensity_for_analytics(
            groups["laser_state"], groups["laser_intensity"]
        )

        # unintended pause....
        if self._grbl_state == self.GRBL_STATE_QUEUE:
            if time.time() - self._pause_delay_time > 0.3:
                if not self.isPaused():
                    if (
                        _mrbeam_plugin_implementation
                        and _mrbeam_plugin_implementation.onebutton_handler
                        and not _mrbeam_plugin_implementation.onebutton_handler.is_intended_pause()
                    ):
                        self._logger.warn(
                            "_handle_status_report() Override pause since we got status '%s' from grbl. (_flush_command_ts: %s, _sync_command_ts: %s)",
                            self._grbl_state,
                            self._flush_command_ts,
                            self._sync_command_ts,
                            analytics=True,
                        )
                        self.setPause(
                            False,
                            send_cmd=True,
                            force=True,
                            trigger="GRBL_QUEUE_OVERRIDE",
                        )
                    else:
                        self._logger.warn(
                            "_handle_status_report() Pausing since we got status '%s' from grbl. (_flush_command_ts: %s, _sync_command_ts: %s)",
                            self._grbl_state,
                            self._flush_command_ts,
                            self._sync_command_ts,
                            terminal_dump=True,
                            analytics=True,
                        )
                        self.setPause(True, send_cmd=False, trigger="GRBL_QUEUE")
        elif (
            self._grbl_state == self.GRBL_STATE_RUN
            or self._grbl_state == self.GRBL_STATE_IDLE
        ):
            if time.time() - self._pause_delay_time > 0.3:
                if self.isPaused():
                    self._logger.warn(
                        "_handle_status_report() Unpausing since we got status '%s' from grbl. (_flush_command_ts: %s, _sync_command_ts: %s)",
                        self._grbl_state,
                        self._flush_command_ts,
                        self._sync_command_ts,
                        analytics=True,
                    )
                    self.setPause(False, send_cmd=False, trigger="GRBL_RUN")

        self._status_last_ts = time.time()

    def _handle_laser_intensity_for_analytics(self, laser_state, laser_intensity):
        if (
            laser_state == "on"
            and _mrbeam_plugin_implementation.mrbeam_plugin_initialized
        ):
            _mrbeam_plugin_implementation.analytics_handler.collect_laser_intensity_value(
                int(laser_intensity)
            )

    def _handle_ok_message(self, line):
        item = self._acc_line_buffer.get_last_responded()

        ## RECOVERY ##
        if (
            self._recovery_ignore_further_alarm_responses
            and self.COMMAND_RESET_ALARM in AccLineBuffer.get_cmd_from_item(item)
        ):
            # the empty line we're sending before $X is also responded with an 'ok', even though it does not unlock the alarm.
            # That's why it's important to check if $X is really the command that got acknowledged.
            self._recovery_alarm_reset_confirmed = True
        # during a recovery the first ok proves that alarm state was cleared
        self._recovery_ignore_further_alarm_responses = False

        ## HOMING ##
        if self._state == self.STATE_HOMING:
            self._changeState(self.STATE_OPERATIONAL)

        # # update working pos from acknowledged gcode
        # if item and item['cmd'].startswith('G'):
        # 	self._callback.on_comm_pos_update(None, [item['x'], item['y'], 0])
        # 	# since we just got a postion update we can reset the wait time for the next status poll
        # 	# ideally we never poll statuses during engravings
        # 	self._reset_status_polling_waittime()

    def _handle_error_message(self, line):
        """
        Handles error messages from GRBL
        :param line: GRBL error respnse
        """
        line = line.rstrip() if line else line
        # grbl repots an error if there was never any data written to it's eeprom.
        # it's going to write default values to eeprom and everything is fine then....
        if "EEPROM read fail" in line:
            self._logger.debug(
                "_handle_error_message() Ignoring this error message: '%s'", line
            )
            return
        if "Alarm lock" in line and self._recovery_ignore_further_alarm_responses:
            # During a recovery we can simply ignore these.
            return
        if "Line overflow" in line:
            # If we get this from grbl we can assume that some newline-characters got lost
            # and we can treat this as an MRB_CHECKSUM_ERROR.
            # We can safely assume this because we filter too long commands before sending them.
            self._start_recovery_thread()
            return

        my_cmd = AccLineBuffer.get_cmd_from_item(
            self._acc_line_buffer.get_last_responded()
        )
        self._errorValue = "GRBL: {} in {}".format(line, my_cmd)
        eventManager().fire(
            OctoPrintEvents.ERROR, dict(error=self.getErrorString(), analytics=True)
        )
        self._fire_print_failed()
        self._changeState(self.STATE_LOCKED)

    def _handle_alarm_message(self, line, code=None):
        line = line.rstrip() if line else line
        errorMsg = None
        throwErrorMessage = True
        dumpTerminal = True
        if "MRB_CHECKSUM_ERROR" in line:
            self._start_recovery_thread()
            # no need to stop lasering and report it to the user, we want to recover this
            return
        elif code == self.ALARM_CODE_COMMAND_TOO_LONG:
            # this is not really a GRBL alarm state. Hackey to have it handled as one...
            errorMsg = line or str(self.ALARM_CODE_COMMAND_TOO_LONG)
            dumpTerminal = False
        elif "Hard/soft limit" in line:
            errorMsg = "GRBL: Machine Limit Hit. Please reset the machine and do a homing cycle"
        elif "Abort during cycle" in line:
            errorMsg = "GRBL: Soft-reset detected. Please do a homing cycle"
            throwErrorMessage = False
        elif "Probe fail" in line:
            errorMsg = "GRBL: Probing has failed. Please reset the machine and do a homing cycle"
        else:
            errorMsg = "GRBL: alarm message: '{}'".format(line)

        if errorMsg:
            self._logger.warn(
                errorMsg, serial=True, terminal_dump=dumpTerminal, analytics=True
            )
            self._errorValue = errorMsg
            if throwErrorMessage:
                eventManager().fire(
                    OctoPrintEvents.ERROR,
                    dict(error=self.getErrorString(), analytics=False),
                )

        with self._commandQueue.mutex:
            self._commandQueue.queue.clear()
        self._acc_line_buffer.reset()
        self._send_event.clear(completely=True)
        self._fire_print_failed()
        self._changeState(self.STATE_LOCKED)

        # close and open serial port to reset arduino
        self._serial.close()
        self._openSerial()

    def _handle_feedback_message(self, line):
        if line[1:].startswith("Res"):  # [Reset to continue]
            # send ctrl-x back immediately '\x18' == ctrl-x
            self._serial.write(list(bytearray("\x18")))
            pass
        elif line[1:].startswith("'$H"):  # ['$H'|'$X' to unlock]
            self._changeState(self.STATE_LOCKED)
            if self.isOperational():
                errorMsg = "GRBL: Machine reset."
                self._cmd = None
                self._acc_line_buffer.reset()
                self._pauseWaitStartTime = None
                self._pauseWaitTimeLost = 0.0
                self._send_event.clear(completely=True)
                with self._commandQueue.mutex:
                    self._commandQueue.queue.clear()
                self._log(errorMsg)
                self._logger.error(
                    errorMsg, serial=True, analytics=True, terminal_dump=True
                )
                self._errorValue = errorMsg
                eventManager().fire(
                    OctoPrintEvents.ERROR,
                    dict(error=self.getErrorString(), analytics=False),
                )
                self._fire_print_failed()
        elif line[1:].startswith("G24"):  # [G24_AVOIDED]
            self.g24_avoided_message = []
            self._logger.warn("G24_AVOIDED (Corrupted line data will follow)")
        elif line[1:].startswith("Cau"):  # [Caution: Unlocked]
            pass
        elif line[1:].startswith("Ena"):  # [Enabled]
            pass
        elif line[1:].startswith("Dis"):  # [Disabled]
            pass

    def _handle_startup_message(self, line):
        match = self.pattern_grbl_version.match(line)
        if match:
            self._grbl_version = match.group("version")
        else:
            self._logger.error(
                "Unable to parse GRBL version from startup message: %s", line
            )

        self.grbl_feat_rescue_from_home = (
            self._grbl_version not in self.GRBL_FEAT_BLOCK_VERSION_LIST_RESCUE_FROM_HOME
        )
        self.grbl_feat_checksums = (
            self._grbl_version not in self.GRBL_FEAT_BLOCK_CHECKSUMS
        )
        self.reset_grbl_auto_update_config()

        self._logger.info(
            "GRBL version: %s, rescue_from_home: %s, auto_update: %s, checksums: %s",
            self._grbl_version,
            self.grbl_feat_rescue_from_home,
            self.grbl_auto_update_enabled,
            self.grbl_feat_checksums,
        )

        if self.DEBUG_PRODUCE_CHECKSUM_ERRORS:
            self._logger.warn(
                "DEBUG_PRODUCE_CHECKSUM_ERRORS is active! Do not use in PROD",
                terminal_as_comm=True,
            )

        self._onConnected(self.STATE_LOCKED)
        self.correct_grbl_settings()

    def _handle_g24avoided_corrupted_line(self, line):
        """
        @deprecated: new grbl versions with checksum support do not send G24_AVOIDED anymore
        #
        So far this 'Corrupted line' is sent only in combination with G24_AVOIDED

        > 11:39:15,866 _COMM_: Send: G1X58.32Y338.49G1X56.78Y338.57
        > ...
        > 11:39:16,786 _COMM_: Recv: [G24_AVOIDED]
        > 11:39:16,789 _COMM_: Recv: Corrupted line: G1X58.32Y338.49
        > ...
        > 11:39:17,221 _COMM_: Recv: Corrupted line: G1X56.78Y338.57

        Results in this output:
        # WARNING - G24_AVOIDED line: 'G1X58.32Y338.49G1X56.78Y338.57' (hex: [47 31 58 35 38 2E 33 32 59 33 33 38 2E 34 39][47 31 58 35 36 2E 37 38 59 33 33 38 2E 35 37])
        :param line:
        """
        data = line[len("Corrupted line: ") :]
        self.g24_avoided_message.append(data)
        if len(self.g24_avoided_message) >= 2:
            self.send_g24_avoided_message()
            self.g24_avoided_message = []

    def send_g24_avoided_message(self):
        try:
            data_str = ""
            data_hex = ""
            for i in self.g24_avoided_message:
                if i.endswith("\n"):
                    # A line always ends with a \n which is added by GRBL to evey line sent back to us.
                    i = i[:-1]
                data_str += i
                data_hex += "[{}]".format(self.get_hex_str_from_str(i))

            self._logger.warn(
                "G24_AVOIDED line: '%s' (hex: %s)", data_str, data_hex, analytics=True
            )
        except:
            self._logger.exception(
                "G24_AVOIDED Exception in _handle_g24_avoided_message(): "
            )

    def _handle_settings_message(self, line):
        """
        Handles grbl settings message like '$130=515.1'
        :param line:
        """
        match = self.pattern_grbl_setting.match(line)
        # there are a bunch of responses that do not match and it's ok.
        if match:
            id = int(match.group("id"))
            comment = match.group("comment")
            v_str = match.group("value")
            v = float(v_str)
            try:
                i = int(v)
            except ValueError:
                pass
            value = v
            if i == v and v_str.find(".") < 0:
                value = i
            self._grbl_settings[id] = dict(value=value, comment=comment)

    def _start_recovery_thread(self):
        """
        This starts a recovery process in another thread.
        Recovery is when GRBL reported an MRB_CHECKSUM_ERROR.
        In this case:
        GRBL switches to ALARM state and does not process any commands in it's serial buffer
        however it will proceed with all commands already in the planning buffer.
        Now our job is to resend all commands that were skipped by GRBL.
        First we need to send a ALARM_RESET command ($X) to end grbl's alarm state.
        Then we send all commands which got declined beginning with the one which caused the checksum error.
        It's important that there are now new commands from the file put into the sending pipeling
        once we sent the ALARM_RESET until e sent all commands the need to be resent (marked dirty).
        self._recovery_lock blocks the sending-queue from reading new commands from the file.
        Once the lock is set and we waited some time for the sending queue to clear (this timeout mechanism should
        be improved e.g. by using a lock), we can feed the recovery commands lead by a ALARM_RESET into the sending queue.
        All commands that have been sent after the error are marked as 'dirty', ALARM_RESET is the first 'clean' command
        after the error. We have to make sure that we re-send all dirty commands before we re-open the sending-queue for
        new commands from the file.
        """
        if self._recovery_lock and not self._recovery_ignore_further_alarm_responses:
            # Already in recovery
            # Another checksum error doesn't matter until the ALARM_RESET was processed
            # Here it was already processes and the checksum error happened afterwards.
            # This we need to handle.
            # We stop the running recovery thread, send anotherALARM_RESET, mark everything dirty again
            # and keep processing all commands in the order as they come.
            # I hope that this produces correct results.
            self._recovery_thread_kill = True
            self.recovery_thread.join(0.5)

        self._logger.info("RECOVERY START", terminal_as_comm=True)
        self._recovery_lock = True
        self._recovery_ignore_further_alarm_responses = True
        self._recovery_alarm_reset_confirmed = False
        self._acc_line_buffer.set_dirty()

        self._recovery_thread_kill = False
        self.recovery_thread = threading.Thread(
            target=self.__recovery_thread, name="comm.__recovery_thread"
        )
        self.recovery_thread.daemon = True
        self.recovery_thread.start()

    def __recovery_thread(self):
        try:
            self._recovery_lock = True
            self._recovery_ignore_further_alarm_responses = True
            # TODO: would be good if we can be sure that the regular sending pipeline is really empty
            #  instead of simply waiting potentially too long or too short and then just hoping that it is empty.
            time.sleep(1.0)
            cmd_obj = self._acc_line_buffer.get_last_responded()
            restart_commands = [
                " ",  # send a new line before $X to make sure, grbl regards it as a new command.
                self._add_checksum_to_cmd(self.COMMAND_RESET_ALARM),
            ]
            if cmd_obj and cmd_obj["i"] is not None:
                # grbl internally adds a "S0" in case of a checksum error. (This "S0" is NOT acknowledged by grbl.)
                # Therefor we need to turn the laser power back on.
                # This is the intensity value which was current BEFORE this command. It might be different from
                # a S-value within the command causing the checksum error.
                restart_commands.append(
                    self._add_checksum_to_cmd("S{}".format(int(cmd_obj["i"])))
                )

            recover_cmd = restart_commands.pop(0)
            while not self._recovery_thread_kill and self._acc_line_buffer.is_dirty():
                if recover_cmd:
                    self._logger.info(
                        "Re-queue: %s  RECOVERY", recover_cmd, terminal_as_comm=True
                    )
                    self._lines_recoverd_total += 1
                    self.sendCommand(recover_cmd, processed=True)
                else:
                    # the we did'nt get a command let's wait a bit. there might be a new one shortly
                    # because grbl might still process commands on it's serial buffer.
                    time.sleep(0.001)
                # get next command either from our static restart_commands or a dirty command from _acc_line_buffer
                recover_cmd = (
                    restart_commands.pop(0)
                    if restart_commands
                    else self._acc_line_buffer.recover_next_command()
                )

            if self._recovery_thread_kill:
                self._logger.info(
                    "_send_recovery_commands() Recovery: Starting over..."
                )
            else:
                self._recovery_lock = False
                self._logger.info("_send_recovery_commands() Recovery: Done")
        except:
            self._logger.exception("Exception in recovery thread: ")

    def correct_grbl_settings(self, retries=3):
        """
        This triggers a reload of GRBL settings and does a validation and correction afterwards.
        """
        if (
            time.time() - self._grbl_settings_correction_ts
            > self.GRBL_SETTINGS_READ_WINDOW
        ):
            self._grbl_settings_correction_ts = time.time()
            self._refresh_grbl_settings()
            self._verify_and_correct_loaded_grbl_settings(
                retries=retries,
                timeout=self.GRBL_SETTINGS_READ_WINDOW,
                force_thread=True,
            )
        else:
            self._logger.warn(
                "correct_grbl_settings() got called more than once withing %s s. Ignoring this call.",
                self.GRBL_SETTINGS_READ_WINDOW,
            )

    def _refresh_grbl_settings(self):
        self._grbl_settings = dict()
        self.sendCommand("$$")

    def _get_string_loaded_grbl_settings(self, settings=None):
        my_grbl_settings = (
            settings or self._grbl_settings.copy()
        )  # to avoid race conditions
        log = []
        for id, data in sorted(my_grbl_settings.iteritems()):
            log.append(
                "${id}={val} ({comment})".format(
                    id=id, val=data["value"], comment=data["comment"]
                )
            )
        return "({count}) [{data}]".format(count=len(log), data=", ".join(log))

    def _verify_and_correct_loaded_grbl_settings(
        self, retries=0, timeout=0.0, force_thread=False
    ):
        settings_count = self._laserCutterProfile["grbl"]["settings_count"]
        settings_expected = self._laserCutterProfile["grbl"]["settings"]
        self._logger.debug(
            "GRBL Settings waiting... timeout: %s, settings count: %s",
            timeout,
            len(self._grbl_settings),
        )

        if force_thread or (
            timeout > 0.0 and len(self._grbl_settings) < settings_count
        ):
            timeout = timeout - self.GRBL_SETTINGS_CHECK_FREQUENCY
            myThread = threading.Timer(
                self.GRBL_SETTINGS_CHECK_FREQUENCY,
                self._verify_and_correct_loaded_grbl_settings,
                kwargs=dict(retries=retries, timeout=timeout),
            )
            myThread.daemon = True
            myThread.name = "CommAcc2_GrblSettings"
            myThread.start()
        else:
            my_grbl_settings = self._grbl_settings.copy()  # to avoid race conditions

            log = self._get_string_loaded_grbl_settings(settings=my_grbl_settings)

            commands = []
            if len(my_grbl_settings) != settings_count:
                self._logger.error(
                    "GRBL Settings count incorrect!! %s settings but should be %s. Writing all settings to grbl.",
                    len(my_grbl_settings),
                    settings_count,
                )
                for id, value in sorted(settings_expected.iteritems()):
                    commands.append("${id}={val}".format(id=id, val=value))
            else:
                for id, value in sorted(settings_expected.iteritems()):
                    if not id in my_grbl_settings:
                        self._logger.error(
                            "GRBL Settings $%s - Missing entry! Should be: %s",
                            id,
                            value,
                        )
                        commands.append("${id}={val}".format(id=id, val=value))
                    elif my_grbl_settings[id]["value"] != value:
                        self._logger.error(
                            "GRBL Settings $%s=%s (%s) - Incorrect value! Should be: %s",
                            id,
                            my_grbl_settings[id]["value"],
                            my_grbl_settings[id]["comment"],
                            value,
                        )
                        commands.append("${id}={val}".format(id=id, val=value))

            if len(commands) > 0:
                msg = "GRBL Settings - Verification: FAILED"
                self._logger.warn(msg + " - " + log)
                self._log(msg)
                self._logger.warn(
                    "GRBL Settings correcting: %s values",
                    len(commands),
                    terminal_as_comm=True,
                )
                for c in commands:
                    self._logger.warn(
                        "GRBL Settings correcting value: %s", c, terminal_as_comm=True
                    )
                    # flush before and after to make sure grbl can really handle the settings command
                    self.sendCommand(self.COMMAND_FLUSH)
                    self.sendCommand(c)
                    self.sendCommand(self.COMMAND_FLUSH)
                if retries > 0:
                    retries -= 1
                    wait_time = 2.0
                    self._logger.warn(
                        "GRBL Settings corrections done. Restarting verification in %s s",
                        wait_time,
                        terminal_as_comm=True,
                    )
                    time.sleep(wait_time)
                    self._logger.warn(
                        "GRBL Settings Restarting verification...",
                        terminal_as_comm=True,
                    )
                    self.correct_grbl_settings(retries=retries)
                else:
                    self._logger.warn(
                        "GRBL Settings corrections done. No more retries.",
                        terminal_as_comm=True,
                    )

            else:
                msg = "GRBL Settings - Verification: OK"
                self._logger.info(msg + " - " + log)
                self._log(msg)

    def _process_command_phase(self, phase, command, command_type=None, gcode=None):
        cmd_obj = command
        if isinstance(command, basestring):
            cmd_obj = {"cmd": command}
        if phase not in ("queuing", "queued", "sending", "sent"):
            return cmd_obj

        if gcode is None:
            gcode = self._gcode_command_for_cmd(command)

        # if it's a gcode command send it through the specific handler if it exists
        if gcode is not None:
            gcodeHandler = "_gcode_" + gcode + "_" + phase
            if hasattr(self, gcodeHandler):
                handler_result = getattr(self, gcodeHandler)(
                    command, cmd_type=command_type
                )
                if handler_result is None:
                    cmd_obj = {"cmd": command}
                elif isinstance(handler_result, basestring):
                    cmd_obj["cmd"] = handler_result
                elif isinstance(handler_result, dict):
                    cmd_obj = handler_result

        # finally return whatever we resulted on
        return cmd_obj

    # TODO CLEM Inject color
    def setColors(self, currentFileName, colors):
        print(
            ">>>>>>>>>>>>>>>>>>>|||||||||||||||<<<<<<<<<<<<<<<<<<<<",
            currentFileName,
            colors,
        )

    def _gcode_command_for_cmd(self, cmd):
        """
        Tries to parse the provided ``cmd`` and extract the GCODE command identifier from it (e.g. "G0" for "G0 X10.0").

        Arguments:
            cmd (str): The command to try to parse.

        Returns:
            str or None: The GCODE command identifier if it could be parsed, or None if not.
        """
        if not cmd:
            return None

        if cmd == self.COMMAND_HOLD:
            return "Hold"
        if cmd == self.COMMAND_RESUME:
            return "Resume"

        gcode = self._regex_command.search(cmd)
        if not gcode:
            return None

        return gcode.group(1)

    # internal state management
    def _changeState(self, newState):
        if self._state == newState:
            return

        self._set_status_polling_interval_for_state(state=newState)

        if newState == self.STATE_CLOSED or newState == self.STATE_CLOSED_WITH_ERROR:
            if self._currentFile is not None:
                self._currentFile.close()
            self._log(
                "entered state closed / closed with error. reseting character counter."
            )
            self.acc_line_lengths = []

        oldState = self.getStateString()
        self._state = newState
        self._logger.debug(
            "Changing monitoring state from '%s' to '%s'"
            % (oldState, self.getStateString()),
            terminal_as_comm=True,
        )
        self._callback.on_comm_state_change(newState)

    def _onConnected(self, nextState):
        self._serial.timeout = settings().getFloat(
            ["serial", "timeout", "communication"]
        )

        if nextState is None:
            self._changeState(self.STATE_LOCKED)
        else:
            self._changeState(nextState)

        if self.sending_thread is None or not self.sending_thread.isAlive():
            self._start_sending_thread()

        payload = dict(
            grbl_version=self._grbl_version, port=self._port, baudrate=self._baudrate
        )
        eventManager().fire(OctoPrintEvents.CONNECTED, payload)

    def _detectPort(self, close):
        self._log("Serial port list: %s" % (str(serialList())))
        for p in serialList():
            try:
                self._log("Connecting to: %s" % (p))
                serial_obj = serial.Serial(p)
                if close:
                    serial_obj.close()
                return serial_obj
            except (OSError, serial.SerialException) as e:
                self._log("Error while connecting to %s: %s" % (p, str(e)))
        return None

    def _poll_status(self):
        """
        Called by RepeatedTimer self._status_polling_timer every 0.1 secs
        We need to descide here if we should send a status request
        """
        try:
            if self.isOperational():
                if time.time() >= self._status_polling_next_ts:
                    self._real_time_commands["poll_status"] = True
                    self._send_event.set()
                    self._status_polling_next_ts = (
                        time.time() + self._status_polling_interval
                    )
        except:
            self._logger.exception("Exception in status polling call: ")

    def _reset_status_polling_waittime(self):
        """
        Resets wait time till we should do next status polling
        This is typically called after we received an ok with a position
        """
        self._status_polling_next_ts = time.time() + self._status_polling_interval

    def _set_status_polling_interval_for_state(self, state=None):
        """
        Sets polling interval according to current state
        :param state: (optional) state, if None, self._state is used
        """
        state = state or self._state
        if state == self.STATE_PRINTING:
            self._status_polling_interval = self.STATUS_POLL_FREQUENCY_PRINTING
        elif state == self.STATE_OPERATIONAL:
            self._status_polling_interval = self.STATUS_POLL_FREQUENCY_OPERATIONAL
        elif state == self.STATE_PAUSED:
            self._status_polling_interval = self.STATUS_POLL_FREQUENCY_PAUSED

    def _soft_reset(self):
        if self.isOperational():
            self._real_time_commands["soft_reset"] = True
            self._send_event.set()

    def _log(self, message, is_command=False):
        """
        deprecated. use mrb_logger with flag serial=True instead
        :param message:
        """
        if is_command and not self._terminal_show_checksums:
            checksum = re.compile("\*\d{1,3}\s?")
            message = re.sub(checksum, "", message)
        self._logger.comm(message, serial=True)

    def _fire_print_failed(self, err_msg=None):
        """
        Tests it printer is in printing state and fire PRINT_FAILED event if so.
        :param err_msg:
        :return:
        """
        printing = self.isPrinting() or self.isPaused()
        err_msg = err_msg or self.getErrorString()
        if printing:
            payload = {}
            if self._currentFile is not None:
                payload = self._get_printing_file_state()
                payload["error_msg"] = err_msg
            eventManager().fire(OctoPrintEvents.PRINT_FAILED, payload)

    def flash_grbl(self, grbl_file=None, verify_only=False, is_connected=True):
        """
        Flashes the specified grbl file (.hex). This file must not contain a bootloader.
        :param grbl_file: (optional) if not provided the default grbl file is used.
        :param verify_only: If true, nothing is written, current grbl is verified only
        :param is_connected: If True, serial connection to grbl is closed before flashing and reconnected afterwards.
                Auto updates is executed before connection to grbl is established so in this case this param should be set to False.
        """
        log_verb = "verifying" if verify_only else "flashing"

        if self._state in (self.STATE_FLASHING, self.STATE_PRINTING, self.STATE_PAUSED):
            msg = "{} GRBL not possible in current printer state.".format(
                log_verb.capitalize()
            )
            self._logger.warn(msg, terminal_as_comm=True)
            return

        grbl_file = grbl_file or self.get_grbl_file_name()

        if grbl_file.startswith("..") or grbl_file.startswith("/"):
            msg = "ERROR {} GRBL '{}': Invalid filename.".format(log_verb, grbl_file)
            self._logger.warn(msg, terminal_as_comm=True)
            return

        from_version = self._grbl_version

        grbl_path = os.path.join(__package_path__, self.GRBL_HEX_FOLDER, grbl_file)
        if not os.path.isfile(grbl_path):
            msg = "ERROR {} GRBL '{}': File not found".format(log_verb, grbl_file)
            self._logger.warn(msg, terminal_as_comm=True)
            return

        self._logger.info("{} grbl: '%s'", log_verb.capitalize(), grbl_path)

        if is_connected:
            self.close(isError=False, next_state=self.STATE_FLASHING)
            time.sleep(1)

        # FYI: Fuses can't be changed from over srial
        params = [
            "avrdude",
            "-patmega328p",
            "-carduino",
            "-b{}".format(self._baudrate),
            "-P{}".format(self._port),
            "-u",
            "-q",  # non inter-active and quiet
            "-Uflash:{}:{}:i".format("v" if verify_only else "w", grbl_path),
        ]
        self._logger.debug("flash_grbl() avrdude command:  %s", " ".join(params))
        output, code = exec_cmd_output(params)

        if output is not None:
            output = output.replace("strace: |autoreset: Broken pipe\n", "")
            output = output.replace("done with autoreset\n", "")

        if not verify_only:
            try:
                if _mrbeam_plugin_implementation.mrbeam_plugin_initialized:
                    _mrbeam_plugin_implementation.analytics_handler.add_grbl_flash_event(
                        from_version=from_version,
                        to_version=grbl_file,
                        successful=(code == 0),
                        err=None if (code == 0) else output,
                    )
            except:
                self._logger.exception(
                    "Exception while writing GRBL-flashing to analytics: "
                )

        # error case
        if code != 0 and not verify_only:
            msg_short = "ERROR flashing GRBL '{}': FAILED (See Avrdude output above for details.)".format(
                grbl_file
            )
            msg_long = "{}:\n{}".format(msg_short, output)
            self._logger.error(msg_long, terminal_as_comm=True)
            self._logger.error(msg_short, terminal_as_comm=True)

            try:
                msg = "The update of the internal component GRBL failed.{br}It is still safe to use your Mr Beam. However, if this error persists consider to contact the {opening_tag}Mr Beam support team{closing_tag}.{br}{br}{strong_opening_tag}Error:{strong_closing_tag}{br}{error}".format(
                    opening_tag='<a href="http://mr-beam.org/support" target="_blank">',
                    closing_tag="</a>",
                    error="GRBL update '{}' failed: {}...".format(
                        grbl_file, output[:120]
                    ),
                    br="<br/>",
                    strong_opening_tag="<strong>",
                    strong_closing_tag="</strong>",
                )
                _mrbeam_plugin_implementation.user_notification_system.show_notifications(
                    _mrbeam_plugin_implementation.user_notification_system.get_legacy_notification(
                        title="GRBL Update failed", text=msg, is_err=True
                    )
                )
            except Exception:
                self._logger.exception(
                    "Exception while notifying frontend after failed flash_grbl: "
                )

        elif code != 0 and verify_only:
            msg_short = "Verification GRBL '{}': FAILED (See Avrdude output above for details.)".format(
                grbl_file
            )
            msg_long = "{}:\n{}".format(msg_short, output)
            self._logger.info(msg_long, terminal_as_comm=True)
            self._logger.info(msg_short, terminal_as_comm=True)
        elif code == 0 and verify_only:
            msg_short = "Verification GRBL '{}': OK".format(grbl_file)
            msg_long = "{}:\n{}".format(msg_short, output)
            self._logger.info(msg_long, terminal_as_comm=True)
            self._logger.info(msg_short, terminal_as_comm=True)
        elif code == 0 and not verify_only:
            # ok case
            msg_short = "OK flashing GRBL '{}'".format(grbl_file)
            msg_long = "{}:\n{}".format(msg_short, output)
            self._logger.debug(msg_long, terminal_as_comm=True)
            self._logger.info(msg_short, terminal_as_comm=True)

        time.sleep(1.0)

        # reconnect
        if is_connected:
            timeout = 60
            self._logger.info(
                "Waiting before reconnect. (max %s secs)",
                timeout,
                terminal_as_comm=True,
            )
            if (
                self.monitoring_thread is not None
                and threading.current_thread() != self.monitoring_thread
            ):
                self.monitoring_thread.join(timeout)

            if (
                self.monitoring_thread is not None
                and not self.monitoring_thread.isAlive()
            ):
                # will open serial connection
                self._start_monitoring_thread()
            else:
                self._logger.info(
                    "Can't reconnect automacically. Try to reconnect manually or reboot system."
                )

    @staticmethod
    def get_grbl_file_name(grbl_version=None):
        """
        Gets you the filename according to the given grbl version.
        :param grbl_version: (optional) grbl version - If no grbl version is provided it returns you the filename of the default version for this release.
        :return: filename
        """
        grbl_version = grbl_version or MachineCom.GRBL_DEFAULT_VERSION
        grbl_file = "grbl_{}.hex".format(grbl_version)
        if (
            grbl_version == MachineCom.GRBL_VERSION_20170919_22270fa
        ):  # legacy version string
            grbl_file = "grbl_0.9g_20170919_22270fa.hex"
        return grbl_file

    def reset_grbl_auto_update_config(self):
        """
        Resets grbl auto update configuration in octoprint settings if current grbl version is expected version.
        This makes sure that once the auto update got executed sucessfully it's not done again and again.
        Only has effect IF:
         - grbl_auto_update_enabled in config.yaml is True (default)
        """
        if (
            self.grbl_auto_update_enabled
            and self._laserCutterProfile["grbl"]["auto_update_version"] is not None
        ):
            if (
                self._grbl_version
                == self._laserCutterProfile["grbl"]["auto_update_version"]
            ):
                self._logger.info(
                    "Removing grbl auto update flags from octoprint settings..."
                )
                try:
                    self._laserCutterProfile["grbl"]["auto_update_file"] = None
                    self._laserCutterProfile["grbl"]["auto_update_version"] = None
                    laserCutterProfileManager().save(
                        self._laserCutterProfile, allow_overwrite=True
                    )
                except Exception:
                    self._logger.exception(
                        "Exception while saving Mr Beam settings changes for auto update controls"
                    )
            else:
                self._logger.warn(
                    "GRBL auto update still set: auto_update_file: %s, auto_update_version: %s, current grbl version: %s",
                    self._laserCutterProfile["grbl"]["auto_update_file"],
                    self._laserCutterProfile["grbl"]["auto_update_version"],
                    self._grbl_version,
                )

    def rescue_from_home_pos(self, retry=0):
        """
        In case the laserhead is pushed deep into homing corner and constantly keeps endstops/limit switches pushed,
        this is going to rescue it from there before homing cycle is started.

        This method tests:
        - If GRBL version supports rescue (means reports limit data)
        - If laserhead needs to be rescued
        And then rescues aka moves the laserhead out of the critical zone.

        Requires GRBL v '0.9g_20180223_61638c5' because we need limit data reported.
        """
        if retry <= 0:
            if self._grbl_version is None:
                self._logger.warn("rescue_from_home_pos() No GRBL version yet.")
                return

            if not self.grbl_feat_rescue_from_home:
                self._logger.info(
                    "rescue_from_home_pos() Rescue from home not supported by current GRBL version. GRBL version: %s",
                    self._grbl_version,
                )
                return
            else:
                self._logger.info(
                    "rescue_from_home_pos() GRBL version: %s", self._grbl_version
                )

        elif retry > 3:
            params = dict(
                x="X" if self.limit_x > 0 else "",
                y="Y" if self.limit_y > 0 else "",
                none="None" if self.limit_x == 0 and self.limit_y == 0 else "",
                retries=retry,
            )
            msg = (
                "Can not do homing cycle. Limits:{x}{y}{none}, reties:{retries}".format(
                    **params
                )
            )
            self._errorValue = msg
            self._logger.error(
                "rescue_from_home_pos() Max retries reached! Error: %s", msg
            )
            self._changeState(self.STATE_ERROR)
            eventManager().fire(
                OctoPrintEvents.ERROR,
                dict(error=self.getErrorString(), analytics=False),
            )
            raise Exception(msg)

        self._wait_for_limits_status_update(force=True)

        if self.limit_x < 0 or self.limit_y < 0:
            self._logger.warn(
                "rescue_from_home_pos() Can't get status with limit data. Returning."
            )
            return

        if self.limit_x == 0 and self.limit_y == 0:
            self._logger.debug(
                "rescue_from_home_pos() Not in home pos. nothing to rescue."
            )
            return

        self._logger.info(
            "rescue_from_home_pos() Rescuing laserhead from home position... (retry: %s)",
            retry,
        )
        self.sendCommand("$X")
        self.sendCommand(self.COMMAND_FLUSH)
        self.sendCommand("G91")
        self.sendCommand(
            "G1X{x}Y{y}F500S0".format(
                x="-5" if self.limit_x > 0 else "0", y="-5" if self.limit_y > 0 else "0"
            )
        )
        self.sendCommand("G90")
        self.sendCommand(self.COMMAND_FLUSH)
        time.sleep(1)  # turns out we need this :-/

        self._wait_for_limits_status_update(force=True)
        if self.limit_x > 0 or self.limit_y > 0:
            retry += 1
            self.rescue_from_home_pos(retry=retry)

    def _wait_for_limits_status_update(self, force=False):
        if force:
            self.limit_x = -1
            self.limit_y = -1
        if self.limit_x < 0 or self.limit_y < 0:
            ts = time.time()
            self._logger.debug(
                "_wait_for_limits_status_update() No limit data yet. Requesting status update from GRBL..."
            )
            self._sendCommand(self.COMMAND_STATUS)
            i = 0
            while i < 200 and (self.limit_x < 0 or self.limit_y < 0):
                i += 1
                time.sleep(0.01)
            self._logger.debug(
                "_wait_for_limits_status_update() Limits: limit_x=%s, limit_y=%s (took %.3fms)",
                self.limit_x,
                self.limit_y,
                time.time() - ts,
            )

    # def _handle_command_handler_result(self, command, command_type, gcode, handler_result):
    # 	original_tuple = (command, command_type, gcode)
    #
    # 	if handler_result is None:
    # 		# handler didn't return anything, we'll just continue
    # 		return original_tuple
    #
    # 	if isinstance(handler_result, basestring):
    # 		# handler did return just a string, we'll turn that into a 1-tuple now
    # 		handler_result = (handler_result,)
    # 	elif not isinstance(handler_result, (tuple, list)):
    # 		# handler didn't return an expected result format, we'll just ignore it and continue
    # 		return original_tuple
    #
    # 	hook_result_length = len(handler_result)
    # 	if hook_result_length == 1:
    # 		# handler returned just the command
    # 		command, = handler_result
    # 	elif hook_result_length == 2:
    # 		# handler returned command and command_type
    # 		command, command_type = handler_result
    # 	else:
    # 		# handler returned a tuple of an unexpected length
    # 		return original_tuple
    #
    # 	gcode = self._gcode_command_for_cmd(command)
    # 	return command, command_type, gcode

    def _replace_feedrate(self, cmd):
        obj = self._regex_feedrate.search(cmd)
        if obj is not None:
            feedrate_cmd = cmd[obj.start() : obj.end()]
            self._current_feedrate = int(feedrate_cmd[1:])

            # Limit if necessary
            if self._current_feedrate > 5000:  # The frontend limits to 3000
                self._current_feedrate = 5000
            elif self._current_feedrate < 30:  # The frontend limits to 100
                self._current_feedrate = 30

            return cmd.replace(feedrate_cmd, "F%d" % self._current_feedrate)

        return cmd

    def _replace_intensity(self, cmd):
        obj = self._regex_intensity.search(cmd)
        if obj is not None:
            intensity_limit = int(self._laserCutterProfile["laser"]["intensity_limit"])
            max_correction_factor = float(
                self._laserCutterProfile["laser"]["max_correction_factor"]
            )
            intensity_cmd = cmd[obj.start() : obj.end()]
            parsed_intensity = int(intensity_cmd[1:])

            # Limit GCode input (in case users enter a too high value in the gcode)
            self._current_intensity = parsed_intensity
            if self._current_intensity > intensity_limit:
                self._logger.debug(
                    "gcode intensity higher as allowed max, will limit to max value - %s => %s",
                    self._current_intensity,
                    intensity_limit,
                )
            self._current_intensity = min(intensity_limit, self._current_intensity)

            # Apply power correction factor and limit again (in case there is something wrong with the calculation of
            # the correction factor)
            if self._power_correction_factor > max_correction_factor:
                self._logger.debug(
                    "Power correction factor higher as allowed max, will limit to max value - %s => %s",
                    self._power_correction_factor,
                    max_correction_factor,
                )
            self._power_correction_factor = min(
                self._power_correction_factor, max_correction_factor
            )
            self._current_intensity = int(
                round(self._current_intensity * self._power_correction_factor)
            )
            if (
                self._intensity_upper_bound
                and self._current_intensity > self._intensity_upper_bound
            ):
                self._logger.debug(
                    "Intensity higher as allowed max, will limit to max value - %s => %s",
                    self._current_intensity,
                    self._intensity_upper_bound,
                )
            self._current_intensity = min(
                self._current_intensity, self._intensity_upper_bound
            )

            # self._logger.info('Intensity command changed from S{old} to S{new} (correction factor {factor} and '
            # 				  'intensity limit {limit})'.format(old=parsed_intensity, new=self._current_intensity,
            # 													factor=self._power_correction_factor,
            # 													limit=self._intensity_upper_bound))

            return cmd.replace(intensity_cmd, "S%d" % self._current_intensity)
        return cmd

    def get_hex_str_from_str(self, data):
        res = []
        for i in range(len(data)):
            tmp = hex(ord(data[i]))[2:].upper()
            res.append("0" + tmp if len(tmp) <= 1 else tmp)
        return " ".join(res)

    def _parse_vals_from_gcode(self, cmd):
        data = dict(
            x=None,
            y=None,
            # can easily be extended to also find S and F: simply add these letters to the regexp...
            # i=None,
            # f=None
        )
        matches = self._regex_gcode.findall(cmd)
        if matches:
            for group in matches:
                try:
                    data[group[0].lower()] = float(group[1])
                except:
                    raise Exception(
                        "Invalid coordinate in gcode command: %s:%s in %s",
                        group[0].lower(),
                        group[1],
                        cmd,
                    )
        return data

    def _remember_pos(self, data):
        x = data.get("x", None)
        if x is not None:
            self._current_pos_x = x
        y = data.get("y", None)
        if y is not None:
            self._current_pos_y = y

    ##~~ command handlers
    # hooks are called by self._process_command_phase()
    ##~~
    def _gcode_G0_sending(self, cmd, cmd_type=None):
        self._remember_pos(self._parse_vals_from_gcode(cmd))
        return cmd

    def _gcode_G1_sending(self, cmd, cmd_type=None):
        self._remember_pos(self._parse_vals_from_gcode(cmd))
        cmd = self._replace_feedrate(cmd)
        cmd = self._replace_intensity(cmd)
        return cmd

    def _gcode_G2_sending(self, cmd, cmd_type=None):
        self._remember_pos(self._parse_vals_from_gcode(cmd))
        cmd = self._replace_feedrate(cmd)
        cmd = self._replace_intensity(cmd)
        return cmd

    def _gcode_G3_sending(self, cmd, cmd_type=None):
        self._remember_pos(self._parse_vals_from_gcode(cmd))
        cmd = self._replace_feedrate(cmd)
        cmd = self._replace_intensity(cmd)
        return cmd

    def _gcode_M3_sending(self, cmd, cmd_type=None):
        self._current_laser_on = True
        cmd = self._replace_feedrate(cmd)
        cmd = self._replace_intensity(cmd)
        return cmd

    def _gcode_M5_sending(self, cmd, cmd_type=None):
        self._current_laser_on = False
        return cmd

    def _gcode_M100_sending(self, cmd, cmd_type=None):
        val = None
        matches = self._regex_compressor.findall(cmd)
        if matches:
            try:
                val = int(matches[0])
            except:
                raise Exception(
                    "Invalid value in gcode compressor command: %s, matches: %s",
                    cmd,
                    matches,
                )
        if val is None:
            return {}
        else:
            nu_cmd = {"compressor": val, "sync": True, "cmd": None}
            return nu_cmd

    def _gcode_G01_sending(self, cmd, cmd_type=None):
        return self._gcode_G1_sending(cmd, cmd_type)

    def _gcode_G02_sending(self, cmd, cmd_type=None):
        return self._gcode_G2_sending(cmd, cmd_type)

    def _gcode_G03_sending(self, cmd, cmd_type=None):
        return self._gcode_G3_sending(cmd, cmd_type)

    def _gcode_M03_sending(self, cmd, cmd_type=None):
        return self._gcode_M3_sending(cmd, cmd_type)

    def _gcode_M05_sending(self, cmd, cmd_type=None):
        return self._gcode_M5_sending(cmd, cmd_type)

    def _gcode_X_sent(self, cmd, cmd_type=None):
        # since we use $X to rescue from homeposition, we don't want this to trigger homing
        # self._changeState(self.STATE_HOMING)  # TODO: maybe change to seperate $X mode
        return cmd

    def _gcode_H_sent(self, cmd, cmd_type=None):
        self._changeState(self.STATE_HOMING)
        return cmd

    def _gcode_Hold_sent(self, cmd, cmd_type=None):
        self._changeState(self.STATE_PAUSED)
        return cmd

    def _gcode_Resume_sent(self, cmd, cmd_type=None):
        self._changeState(self.STATE_PRINTING)
        return cmd

    def _gcode_F_sending(self, cmd, cmd_type=None):
        return self._replace_feedrate(cmd)

    def _gcode_S_sending(self, cmd, cmd_type=None):
        return self._replace_intensity(cmd)

    def sendCommand(self, cmd, cmd_type=None, processed=False):
        if cmd is not None and cmd.strip().startswith("/"):
            self._handle_user_command(cmd)
        elif self._handle_rt_command(cmd):
            pass
        else:
            if processed:
                cmd_obj = {"cmd": cmd}
            else:
                cmd.encode("ascii", "replace")
                cmd = process_gcode_line(cmd)
                if not cmd:
                    return

                cmd_obj = self._process_command_phase("sending", cmd)
                if cmd_obj is None or len(cmd_obj) <= 0:
                    return

                if self.grbl_feat_checksums:
                    cmd_obj["cmd"] = self._add_checksum_to_cmd(cmd_obj["cmd"])

            if cmd_obj.get("cmd", None) is not None:
                eepromCmd = re.search("^\$[0-9]+=.+$", cmd_obj.get("cmd"))
                if eepromCmd and self.isPrinting():
                    self._log(
                        "Warning: Configuration changes during print are not allowed!"
                    )
                    return

            self._commandQueue.put(cmd_obj)
            self._send_event.set()
            self.watch_dog.notify_command(cmd_obj)

    def _handle_user_command(self, cmd):
        """
        Handles commands the user can enter on the terminal starting with /
        """
        try:
            cmd = cmd.strip()
            self._log("Command: %s" % cmd)
            self._logger.info("Terminal user command: %s", cmd)
            tokens = cmd.split(" ")
            specialcmd = tokens[0].lower()
            if specialcmd.startswith("/togglestatusreport"):
                if self._status_polling_interval <= 0:
                    self._set_status_polling_interval_for_state()
                else:
                    self._status_polling_interval = 0
            elif specialcmd.startswith("/setstatusfrequency"):
                try:
                    self._status_polling_interval = float(tokens[1])
                except ValueError:
                    self._log("No frequency setting found! No change")
            elif specialcmd.startswith("/disconnect"):
                self.close()
            elif specialcmd.startswith("/feedrate"):
                if len(tokens) > 1:
                    self._set_feedrate_override(int(tokens[1]))
                else:
                    self._log("no feedrate given")
            elif specialcmd.startswith("/intensity"):
                if len(tokens) > 1:
                    data = specialcmd[8:]
                    self._set_intensity_override(int(tokens[1]))
                else:
                    self._log("no intensity given")
            elif specialcmd.startswith("/reset"):
                self._log("Reset initiated")
                self._serial.write(list(bytearray("\x18")))
            elif specialcmd.startswith("/flash_grbl"):
                # if no file given: flash default grbl version
                file = self.get_grbl_file_name()
                if len(tokens) > 1:
                    file = tokens[1]
                if file in (None, "?", "-h", "--help"):
                    grbl_path = os.path.join(__package_path__, self.GRBL_HEX_FOLDER)
                    grbl_files = [
                        f
                        for f in os.listdir(grbl_path)
                        if (
                            os.path.isfile(os.path.join(grbl_path, f))
                            and not f.startswith(".")
                        )
                    ]
                    self._log("Available GRBL files:")
                    for f in grbl_files:
                        self._log("    %s" % f)
                else:
                    self._log("Flashing GRBL '%s'..." % file)
                    self.flash_grbl(file)
            elif specialcmd.startswith("/verify_grbl"):
                # if no file given: verify to currently installed
                file = self.get_grbl_file_name(self._grbl_version)
                if len(tokens) > 1:
                    file = tokens[1]
                if file in (None, "?", "-h", "--help"):
                    grbl_path = os.path.join(__package_path__, self.GRBL_HEX_FOLDER)
                    grbl_files = [
                        f
                        for f in os.listdir(grbl_path)
                        if (
                            os.path.isfile(os.path.join(grbl_path, f))
                            and not f.startswith(".")
                        )
                    ]
                    self._log("Available GRBL files:")
                    for f in grbl_files:
                        self._log("    %s" % f)
                else:
                    self._log("Verifying GRBL '%s'..." % file)
                    self.flash_grbl(file, verify_only=True)
            elif specialcmd.startswith("/correct_settings"):
                self._log("Correcting GRBL settings...")
                self.correct_grbl_settings()
            elif specialcmd.startswith("/power_correction"):
                if len(tokens) > 1:
                    token = int(tokens[1])
                    if token == 1:
                        self._log("Enabling power correction...")
                        lh_data = (
                            _mrbeam_plugin_implementation.laserhead_handler.get_current_used_lh_data()
                        )
                        if lh_data["info"] and "correction_factor" in lh_data["info"]:
                            self._power_correction_factor = lh_data["info"][
                                "correction_factor"
                            ]
                        else:
                            self._log(
                                "Couldn't enable power correction, there is no correction factor for laser head {}.".format(
                                    lh_data["serial"]
                                )
                            )

                    elif token == 0:
                        self._log("Disabling power correction...")
                        self._power_correction_factor = 1

                    self._log(
                        "Power correction set to {}".format(
                            self._power_correction_factor
                        )
                    )
                else:
                    self._log("No parameter given (0 or 1)")
            elif specialcmd.startswith("/show_checksums"):
                if len(tokens) > 1:
                    token = int(tokens[1])
                    if token == 1:
                        self._log("Checksums will be shown in the terminal")
                        _mrbeam_plugin_implementation._settings.set_boolean(
                            ["terminal_show_checksums"], True, force=True
                        )
                        _mrbeam_plugin_implementation._settings.save()
                    elif token == 0:
                        self._log("Checksums will not be shown in the terminal")
                        _mrbeam_plugin_implementation._settings.set_boolean(
                            ["terminal_show_checksums"], False, force=True
                        )
                        _mrbeam_plugin_implementation._settings.save()
                else:
                    self._log("No parameter given (0 or 1)")

            else:
                self._log("Command not found.")
                self._log("Available commands are:")
                self._log("   /togglestatusreport")
                self._log("   /setstatusfrequency <interval secs>")
                self._log("   /feedrate <f>")
                self._log("   /intensity <s>")
                self._log("   /disconnect")
                self._log("   /reset")
                self._log("   /correct_settings")
                self._log("   /power_correction <x>		--> Enable: x = 1; Disable: x = 0")
                self._log("   /show_checksums <x>		--> Enable: x = 1; Disable: x = 0")
                self._log(
                    "   /verify_grbl [? | <file>] // ?: list of available files; If omitted default grbl version will be verified ."
                )
                self._log(
                    "   /flash_grbl [? | <file>] // ?: list of available files; If omitted current grbl version will be flashed."
                )
        except:
            self._logger.exception(
                "Exception while executing terminal command '%s'",
                cmd,
                terminal_as_comm=True,
            )

    def selectFile(self, filename, sd):
        if self.isBusy():
            return

        self._currentFile = PrintingGcodeFileInformation(filename)
        eventManager().fire(
            OctoPrintEvents.FILE_SELECTED,
            {
                "file": self._currentFile.getFilename(),
                "filename": os.path.basename(self._currentFile.getFilename()),
                "origin": self._currentFile.getFileLocation(),
            },
        )
        self._callback.on_comm_file_selected(
            filename, self._currentFile.getFilesize(), False
        )

    def selectGCode(self, gcode):
        if self.isBusy():
            return

        self._currentFile = PrintingGcodeFromMemoryInformation(gcode)
        eventManager().fire(
            OctoPrintEvents.FILE_SELECTED,
            {
                "file": self._currentFile.getFilename(),
                "filename": os.path.basename(self._currentFile.getFilename()),
                "origin": self._currentFile.getFileLocation(),
            },
        )
        self._callback.on_comm_file_selected(
            "In_Memory_GCode", len(gcode), True
        )  # Hack: set SD-Card to true to avoid Octoprint os.stats check (which will fail of course).

    def unselectFile(self):
        if self.isBusy():
            return

        self._currentFile = None
        eventManager().fire(OctoPrintEvents.FILE_DESELECTED)
        self._callback.on_comm_file_selected(None, None, False)

    def startPrint(self, *args, **kwargs):
        # TODO implement pos kw argument for resuming prints
        if not self.isOperational():
            return

        if self._currentFile is None:
            raise ValueError("No file selected for printing")

        # reset feedrate in case they where changed in a previous run
        self._finished_passes = 0
        self._pauseWaitTimeLost = 0.0
        self._pauseWaitStartTime = None

        try:
            self.watch_dog.reset()
            self.watch_dog.start(self._currentFile)

            # ensure fan is on whatever gcode follows.
            self.sendCommand("M08")

            self._currentFile.start()
            self._finished_currentFile = False

            payload = self._get_printing_file_state()
            eventManager().fire(OctoPrintEvents.PRINT_STARTED, payload)

            self._changeState(self.STATE_PRINTING)
        except Exception as e:
            self._logger.exception(
                "Error while trying to start printing: {}".format(e), terminal_dump=True
            )
            self._errorValue = get_exception_string()
            self._changeState(self.STATE_ERROR)
            eventManager().fire(
                OctoPrintEvents.ERROR,
                dict(error=self.getErrorString(), analytics=False),
            )

    def cancelPrint(self, failed=False, error_msg=False):
        if not self.isOperational():
            return

        # first pause (feed hold) before doing the soft reset in order to retain machine pos.
        self._sendCommand(self.COMMAND_HOLD)
        time.sleep(0.5)

        with self._commandQueue.mutex:
            self._commandQueue.queue.clear()
        self._cmd = None

        self.watch_dog.stop()
        self._sendCommand(self.COMMAND_RESET)
        self._acc_line_buffer.reset()
        self._send_event.clear(completely=True)
        self._changeState(self.STATE_LOCKED)

        payload = self._get_printing_file_state()

        if failed:
            if not payload.get("error_msg", None):
                payload["error_msg"] = error_msg

            eventManager().fire(OctoPrintEvents.PRINT_FAILED, payload)
        else:
            eventManager().fire(OctoPrintEvents.PRINT_CANCELLED, payload)

    def setPause(
        self, pause, send_cmd=True, pause_for_cooling=False, trigger=None, force=False
    ):
        if not self._currentFile:
            return

        payload = self._get_printing_file_state()
        payload["trigger"] = trigger

        if not pause and (self.isPaused() or force):
            if self._pauseWaitStartTime:
                self._pauseWaitTimeLost = self._pauseWaitTimeLost + (
                    time.time() - self._pauseWaitStartTime
                )
                self._pauseWaitStartTime = None
            self._pause_delay_time = time.time()
            payload[
                "time"
            ] = self.getPrintTime()  # we need the pasue time to be removed from time
            self.watch_dog.start()
            if send_cmd is True:
                self._real_time_commands["cycle_start"] = True
            self._send_event.set()
            eventManager().fire(OctoPrintEvents.PRINT_RESUMED, payload)
        elif pause and (self.isPrinting() or force):
            if not self._pauseWaitStartTime:
                self._pauseWaitStartTime = time.time()
            self._pause_delay_time = time.time()
            self.watch_dog.stop()
            if send_cmd is True:
                self._real_time_commands["feed_hold"] = True
            self._send_event.set()
            eventManager().fire(OctoPrintEvents.PRINT_PAUSED, payload)

        if self.getPrintTime() < 0.0:
            self._logger.warn(
                "setPause() %s: print time is negative! print time: %s, _pauseWaitStartTime: %s, _pauseWaitTimeLost: %s",
                "pausing" if pause else "resuming",
                self.getPrintTime(),
                self._pauseWaitStartTime,
                self._pauseWaitTimeLost,
            )

    def increasePasses(self):
        self._passes += 1
        self._logger.info(
            "increased Passes to %d" % self._passes, terminal_as_comm=True
        )

    def decreasePasses(self):
        self._passes -= 1
        self._logger.info("decrease Passes to %d" % self._passes, terminal_as_comm=True)

    def setPasses(self, value):
        self._passes = value
        self._logger.info("set Passes to %d" % self._passes, terminal_as_comm=True)

    def sendGcodeScript(self, scriptName, replacements=None):
        pass

    def getStateId(self, state=None):
        if state is None:
            state = self._state

        possible_states = filter(
            lambda x: x.startswith("STATE_"), self.__class__.__dict__.keys()
        )
        for possible_state in possible_states:
            if getattr(self, possible_state) == state:
                return possible_state[len("STATE_") :]

        return "UNKNOWN"

    def getStateString(self, state=None):
        if state is None:
            state = self._state
        if state == self.STATE_NONE:
            return "Offline"
        if state == self.STATE_OPEN_SERIAL:
            return "Opening serial port"
        if state == self.STATE_DETECT_SERIAL:
            return "Detecting serial port"
        if state == self.STATE_DETECT_BAUDRATE:
            return "Detecting baudrate"
        if state == self.STATE_CONNECTING:
            return "Connecting"
        if state == self.STATE_OPERATIONAL:
            return "Operational"
        if state == self.STATE_PRINTING:
            # return "Printing"
            return "Lasering"
        if state == self.STATE_PAUSED:
            return "Paused"
        if state == self.STATE_CLOSED:
            return "Closed"
        if state == self.STATE_ERROR:
            return "Error: %s" % (self.getErrorString())
        if state == self.STATE_CLOSED_WITH_ERROR:
            return "Error: %s" % (self.getErrorString())
        if state == self.STATE_TRANSFERING_FILE:
            return "Transfering file to SD"
        if self._state == self.STATE_LOCKED:
            return "Locked"
        if self._state == self.STATE_HOMING:
            return "Homing"
        if self._state == self.STATE_FLASHING:
            return "Flashing"
        return "Unknown State (%d)" % (self._state)

    def getPrintProgress(self):
        if self._currentFile is None:
            return None
        return self._currentFile.getProgress()

    def getPrintFilepos(self):
        if self._currentFile is None:
            return None
        return self._currentFile.getFilepos()

    def getCleanedPrintTime(self):
        printTime = self.getPrintTime()
        if printTime is None:
            return None
        return printTime

    def getConnection(self):
        return self._port, self._baudrate

    def isOperational(self):
        return (
            self._state == self.STATE_OPERATIONAL
            or self._state == self.STATE_PRINTING
            or self._state == self.STATE_PAUSED
        )

    def isPrinting(self):
        return self._state == self.STATE_PRINTING

    def isPaused(self):
        return self._state == self.STATE_PAUSED

    def isLocked(self):
        return self._state == self.STATE_LOCKED

    def isHoming(self):
        return self._state == self.STATE_HOMING

    def isFlashing(self):
        return self._state == self.STATE_FLASHING

    def isBusy(self):
        return self.isPrinting() or self.isPaused()

    def isError(self):
        return (
            self._state == self.STATE_ERROR
            or self._state == self.STATE_CLOSED_WITH_ERROR
        )

    def isClosedOrError(self):
        return (
            self._state == self.STATE_ERROR
            or self._state == self.STATE_CLOSED_WITH_ERROR
            or self._state == self.STATE_CLOSED
        )

    def isSdReady(self):
        return False

    def isStreaming(self):
        return False

    def getErrorString(self):
        return self._errorValue

    def getPrintTime(self):
        if self._currentFile is None or self._currentFile.getStartTime() is None:
            return None
        else:
            return (
                time.time() - self._currentFile.getStartTime() - self._pauseWaitTimeLost
            )

    def getGrblVersion(self):
        return self._grbl_version

    def _get_printing_file_state(self):
        file_state = {
            "file": self._currentFile.getFilename(),
            "filename": os.path.basename(self._currentFile.getFilename()),
            "origin": self._currentFile.getFileLocation(),
            "time": self.getPrintTime(),
            "mrb_state": _mrbeam_plugin_implementation.get_mrb_state(),
            "file_lines_total": self._currentFile.getLinesTotal(),
            "file_lines_read": self._currentFile.getLinesRead(),
            "file_lines_remaining": self._currentFile.getLinesRemaining(),
            "lines_recovered": self._lines_recoverd_total,
        }

        return file_state

    def close(self, isError=False, next_state=None):
        self._monitoring_active = False
        self._sending_active = False
        self._status_polling_interval = 0

        printing = self.isPrinting() or self.isPaused()
        if self._serial is not None:
            if isError:
                self._changeState(self.STATE_CLOSED_WITH_ERROR)
            elif next_state:
                self._changeState(next_state)
            else:
                self._changeState(self.STATE_CLOSED)
            self._serial.close()
        self._serial = None

        if printing:
            payload = None
            if self._currentFile is not None:
                payload = self._get_printing_file_state()
            eventManager().fire(OctoPrintEvents.PRINT_FAILED, payload)
        eventManager().fire(OctoPrintEvents.DISCONNECTED)

    def _set_compressor(self, value):
        try:
            _mrbeam_plugin_implementation.compressor_handler.set_compressor(value)
        except:
            self._logger.exception("Exception in _set_air_pressure() ")

    def _set_compressor_pause(self, paused):
        try:
            if paused:
                _mrbeam_plugin_implementation.compressor_handler.set_compressor_pause()
            else:
                _mrbeam_plugin_implementation.compressor_handler.set_compressor_pause()
        except:
            self._logger.exception("Exception in _set_air_pressure() ")


### MachineCom callback ################################################################################################
class MachineComPrintCallback(object):
    def on_comm_log(self, message):
        pass

    def on_comm_temperature_update(self, temp, bedTemp):
        pass

    def on_comm_state_change(self, state):
        pass

    def on_comm_message(self, message):
        pass

    def on_comm_progress(self):
        pass

    def on_comm_print_job_done(self):
        pass

    def on_comm_z_change(self, newZ):
        pass

    def on_comm_file_selected(self, filename, filesize, sd):
        pass

    def on_comm_sd_state_change(self, sdReady):
        pass

    def on_comm_sd_files(self, files):
        pass

    def on_comm_file_transfer_started(self, filename, filesize):
        pass

    def on_comm_file_transfer_done(self, filename):
        pass

    def on_comm_force_disconnect(self):
        pass

    def on_comm_pos_update(self, MPos, WPos):
        pass


class PrintingFileInformation(object):
    """
    Encapsulates information regarding the current file being printed: file name, current position, total size and
    time the print started.
    Allows to reset the current file position to 0 and to calculate the current progress as a floating point
    value between 0 and 1.
    """

    def __init__(self, filename):
        self._logger = mrb_logger(
            "octoprint.plugins.mrbeam.comm_acc2.PrintingFileInformation"
        )
        self._filename = filename
        self._pos = 0
        self._size = None
        self._comment_size = None
        self._start_time = None

    def getStartTime(self):
        return self._start_time

    def getFilename(self):
        return self._filename

    def getFilesize(self):
        return self._size

    def getFilepos(self):
        return self._pos - self._comment_size

    def getFileLocation(self):
        return FileDestinations.LOCAL

    def getProgress(self):
        """
        The current progress of the file, calculated as relation between file position and absolute size. Returns -1
        if file size is None or < 1.
        """
        if self._size is None or not self._size > 0:
            return -1
        return float(self._pos - self._comment_size) / float(
            self._size - self._comment_size
        )

    def reset(self):
        """
        Resets the current file position to 0.
        """
        self._pos = 0

    def start(self):
        """
        Marks the print job as started and remembers the start time.
        """
        self._start_time = time.time()

    def close(self):
        """
        Closes the print job.
        """
        pass


class PrintingGcodeFileInformation(PrintingFileInformation):
    """
    Encapsulates information regarding an ongoing direct print. Takes care of the needed file handle and ensures
    that the file is closed in case of an error.
    """

    def __init__(self, filename, offsets_callback=None, current_tool_callback=None):
        PrintingFileInformation.__init__(self, filename)

        self._handle = None

        self._first_line = None

        self._offsets_callback = offsets_callback
        self._current_tool_callback = current_tool_callback

        if not os.path.exists(self._filename) or not os.path.isfile(self._filename):
            raise IOError("File %s does not exist" % self._filename)

        self._size = os.stat(self._filename).st_size
        self._pos = 0
        self._comment_size = 0
        self._lines_total = self._calc_total_lines()
        self._lines_read = 0
        self._lines_read_bak = 0

    def start(self):
        """
        Opens the file for reading and determines the file size.
        """
        PrintingFileInformation.start(self)
        self._handle = open(self._filename, "r")
        self._lines_read = 0
        self._lines_read_bak = 0

    def close(self):
        """
        Closes the file if it's still open.
        """
        PrintingFileInformation.close(self)
        if self._handle is not None:
            try:
                self._handle.close()
            except:
                pass
        self._handle = None

    def resetToBeginning(self):
        """
        resets the file handle so you can read from the beginning again.
        """
        self._logger.debug(
            "resetToBeginning() self._lines_read %s, self._lines_read_bak: %s",
            self._lines_read,
            self._lines_read_bak,
        )
        self._handle = open(self._filename, "r")
        self._lines_read = 0

    def getNext(self):
        """
        Retrieves the next line for printing.
        """
        if self._handle is None:
            raise ValueError("File %s is not open for reading" % self._filename)

        try:
            processed = None
            while processed is None:
                if self._handle is None:
                    # file got closed just now
                    self._logger.debug(
                        "getNext() self._handle is None -> returning None"
                    )
                    return None
                line = self._handle.readline()
                if not line:
                    self._logger.debug(
                        "getNext() read line is None -> closing self._handle"
                    )
                    self.close()
                else:
                    self._lines_read += 1
                    self._lines_read_bak += 1
                    # self._logger.debug("getNext() increased self._lines_read to %s", self._lines_read)
                processed = process_gcode_line(line)
                if processed is None:
                    self._comment_size += len(line)
            self._pos = self._handle.tell()

            return processed
        except Exception as e:
            self.close()
            self._logger.exception("Exception while processing line")
            raise e

    def getLinesTotal(self):
        return self._lines_total

    def getLinesRead(self):
        return self._lines_read or self._lines_read_bak

    def getLinesRemaining(self):
        return self.getLinesTotal() - self.getLinesRead()

    def _calc_total_lines(self):
        res = -1
        try:
            tmp, code = exec_cmd_output(
                "wc -l \"{}\" | cut -f1 -d' '".format(self._filename), shell=True
            )
            if code == 0:
                res = int(tmp)
            else:
                self._logger.error(
                    "Can't convert _lines_total to int: command returned exit code %s, output: %s",
                    code,
                    tmp,
                )
        except ValueError:
            self._logger.error("Can't convert _lines_total to int: value is %s", tmp)
        return res


class PrintingGcodeFromMemoryInformation(PrintingGcodeFileInformation):
    def __init__(self, gcode):
        PrintingFileInformation.__init__(self, "in_memory_gcode")
        self._gcode = gcode.split("\n")
        self._size = len(gcode)
        self._first_line = None
        self._offsets_callback = None
        self._current_tool_callback = None
        self._pos = 0
        self._comment_size = 0
        self._lines_total = len(self._gcode)
        self._lines_read = 0
        self._lines_read_bak = 0

    def start(self):
        PrintingFileInformation.start(self)
        self._lines_read = 0
        self._lines_read_bak = 0

    def close(self):
        PrintingFileInformation.close(self)
        self._gcode = None

    def resetToBeginning(self):
        self._logger.debug(
            "resetToBeginning() self._lines_read %s, self._lines_read_bak: %s",
            self._lines_read,
            self._lines_read_bak,
        )
        self._lines_read = 0
        self._pos = 0
        self._comment_size = 0

    def getNext(self):
        """
        Retrieves the next line for printing.
        """
        if self._gcode is None:
            raise ValueError("Line buffer is not filled")

        try:
            processed = None
            while processed is None:
                if self._gcode is None:
                    # file got closed just now
                    self._logger.debug(
                        "getNext() self._gcode is None -> returning None"
                    )
                    return None

                line = None
                try:
                    line = self._gcode[self._lines_read]
                    self._lines_read += 1
                    self._lines_read_bak += 1
                    self._pos += len(line)
                except IndexError:
                    self._logger.debug(
                        "getNext() read line raised IndexError -> closing self._gcode"
                    )
                    self.close()

                if line != None:
                    processed = process_gcode_line(line)
                    if processed is None:
                        self._comment_size += len(line)

            return processed
        except Exception as e:
            self.close()
            self._logger.exception("Exception while processing line")
            raise e


def convert_pause_triggers(configured_triggers):
    triggers = {"enable": [], "disable": [], "toggle": []}
    for trigger in configured_triggers:
        if not "regex" in trigger or not "type" in trigger:
            continue

        try:
            regex = trigger["regex"]
            t = trigger["type"]
            if t in triggers:
                # make sure regex is valid
                re.compile(regex)
                # add to type list
                triggers[t].append(regex)
        except re.error:
            # invalid regex or something like this, we'll just skip this entry
            pass

    result = dict()
    for t in triggers.keys():
        if len(triggers[t]) > 0:
            result[t] = re.compile(
                "|".join(
                    map(
                        lambda pattern: "({pattern})".format(pattern=pattern),
                        triggers[t],
                    )
                )
            )
    return result


def process_gcode_line(line):
    line = strip_comment(line).strip()
    line = line.replace(" ", "")
    if not len(line):
        return None
    return line


def strip_comment(line):
    if not ";" in line:
        # shortcut
        return line
    escaped = False
    result = []
    for c in line:
        if c == ";" and not escaped:
            break
        result += c
        escaped = (c == "\\") and not escaped
    return "".join(result)


def get_new_timeout(t):
    now = time.time()
    return now + get_interval(t)


def get_interval(t):
    if t not in default_settings["serial"]["timeout"]:
        return 0
    else:
        return settings().getFloat(["serial", "timeout", t])


def serialList():
    baselist = []
    baselist = (
        baselist
        + glob.glob("/dev/ttyUSB*")
        + glob.glob("/dev/ttyACM*")
        + glob.glob("/dev/ttyAMA*")
        + glob.glob("/dev/tty.usb*")
        + glob.glob("/dev/cu.*")
        + glob.glob("/dev/cuaU*")
        + glob.glob("/dev/rfcomm*")
    )

    additionalPorts = settings().get(["serial", "additionalPorts"])
    for additional in additionalPorts:
        baselist += glob.glob(additional)

    prev = settings().get(["serial", "port"])
    if prev in baselist:
        baselist.remove(prev)
        baselist.insert(0, prev)
    if settings().getBoolean(["devel", "virtualPrinter", "enabled"]):
        baselist.append("VIRTUAL")
    return filter(None, baselist)


def baudrateList():
    ret = [250000, 230400, 115200, 57600, 38400, 19200, 9600]
    prev = settings().getInt(["serial", "baudrate"])
    if prev in ret:
        ret.remove(prev)
        ret.insert(0, prev)
    return ret
