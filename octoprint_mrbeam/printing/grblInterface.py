# coding=utf-8

__author__ = "teja philipp"
__date__ = "$29.01.2022 16:11:03$"

import re
import time
from collections import namedtuple

from octoprint_mrbeam.mrb_logger import mrb_logger


class GrblInterface(object):

    RE_WELCOME = re.compile("Grbl (?P<version>\S+)\s.*")
    RE_SETTING = re.compile("\$(?P<id>\d+)=(?P<value>\S+)\s\((?P<comment>.*)\)")

    # GrblHAL 1.1 @ RP2040 produces these status messages
    # <Idle|MPos:0.000,0.000,0.000|Bf:35,1023|FS:0,0|Pn:Z|WCO:0.000,0.000,0.000>
    # <Idle|MPos:0.000,0.000,0.000|Bf:35,1023|FS:0,0|Pn:Z|Ov:100,100,100>
    RE_STATUS_GRBL11 = re.compile(
        "<(?P<status>\w+)"
        + "\|.*(?P<pos_type>[MW])Pos:(?P<pos_x>[0-9.\-]+),(?P<pos_y>[0-9.\-]+),(?P<pos_z>[0-9.\-]+)"
        + "\|.*Bf:(?P<rx>\d+),(?P<plan_buf>\d+)"
        + "\|.*FS:(?P<feedrate>\d+),(?P<laser_intensity>\d+)"
        + "(\|.*Pn:(?P<limit_x>[X]?)(?P<limit_y>[Y]?)(?P<limit_z>[Z]?))?"
        + "(\|.*WCO:(?P<wco_x>[0-9.\-]+),(?P<wco_y>[0-9.\-]+),(?P<wco_z>[0-9.\-]+))?"
        + "(\|.*Ov:(?P<ov_1>\d+),(?P<ov_2>\d+),(?P<ov_3>\d+))?.*>"
    )

    RE_STATUS_GRBL09 = re.compile(
        "<(?P<status>\w+)"
        + ",.*MPos:(?P<mpos_x>[0-9.\-]+),(?P<mpos_y>[0-9.\-]+)"
        + ",.*WPos:(?P<pos_x>[0-9.\-]+),(?P<pos_y>[0-9.\-]+)"
        + ",.*RX:(?P<rx>\d+)"
        + ",.*limits:(?P<limit_x>[x]?)(?P<limit_y>[y]?)z?"
        + ",.*laser (?P<laser_state>\w+):(?P<laser_intensity>\d+).*>"
    )

    RE_STATUS_GRBL_LEGACY = re.compile(
        "<(?P<status>\w+)"
        + ",.*MPos:(?P<mpos_x>[0-9.\-]+),(?P<mpos_y>[0-9.\-]+)"
        + ",.*WPos:(?P<pos_x>[0-9.\-]+),(?P<pos_y>[0-9.\-]+)"
        + ",.*RX:(?P<rx>\d+)"
        + ",.*laser (?P<laser_state>\w+):(?P<laser_intensity>\d+).*>"
    )

    DEFAULT = dict(
        version="default",
        supportsRescueFromHome=False,
        supportsG24Avoided=False,
        supportsChecksums=False,
        supportsBurnmarkPrevention=False,
        supportsCoreXY=False,
        statusRegex=RE_STATUS_GRBL_LEGACY,
    )

    ### GRBL VERSIONs #######################################
    # original grbl
    GRBL_VERSION_20170919_22270fa = dict(DEFAULT, **dict(version="0.9g_22270fa"))

    #
    # adds rescue from home feature
    GRBL_VERSION_20180223_61638c5 = dict(
        DEFAULT,
        **dict(
            version="0.9g_20180223_61638c5",
            supportsRescueFromHome=True,
            statusRegex=RE_STATUS_GRBL09,
        )
    )
    #
    # trial grbl
    # - adds rx-buffer state with every ok
    # - adds alarm mesage on rx buffer overrun
    GRBL_VERSION_20180828_ac367ff = dict(
        DEFAULT,
        **dict(
            version="0.9g_20180828_ac367ff",
            supportsRescueFromHome=True,
            statusRegex=RE_STATUS_GRBL09,
        )
    )
    #
    # adds G24_AVOIDED
    GRBL_VERSION_20181116_a437781 = dict(
        DEFAULT,
        **dict(
            version="0.9g_20181116_a437781",
            supportsRescueFromHome=True,
            supportsG24Avoided=True,
            statusRegex=RE_STATUS_GRBL09,
        )
    )
    #
    # adds checksums
    GRBL_VERSION_2019_MRB_CHECKSUM = dict(
        DEFAULT,
        **dict(
            version="0.9g_20190327_d2868b9",
            supportsRescueFromHome=True,
            supportsG24Avoided=True,
            supportsChecksums=True,
            statusRegex=RE_STATUS_GRBL09,
        )
    )
    #
    # fixes burn marks
    GRBL_VERSION_20210714_d5e31ee = dict(
        DEFAULT,
        **dict(
            version="0.9g_20210714_d5e31ee",
            supportsRescueFromHome=True,
            supportsG24Avoided=True,
            supportsChecksums=True,
            supportsBurnmarkPrevention=True,
            statusRegex=RE_STATUS_GRBL09,
        )
    )

    # grblHAL 1.1f with coreXY, z-Axis, lasermode
    GRBL_VERSION_MB3PROTO = dict(
        DEFAULT,
        **dict(
            version="1.1f",
            supportsCoreXY=True,
            statusRegex=RE_STATUS_GRBL11,
        )
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

    ALARM_CODE_COMMAND_TOO_LONG = "ALARM_CODE_COMMAND_TOO_LONG"

    def __init__(self, versionStr=None):
        self._logger = mrb_logger("octoprint.plugins.mrbeam.printing.grblInterface")
        self.version = versionStr

        self.state = dict(
            status=self.STATE_NONE,
            mpos=(0, 0, 0),
            wpos=(0, 0, 0),
            serialBuffer=-1,
            serialBufferLastUpdated=time.time(),
            plannerBuffer=0,
            feedrate=0,
            laserIntensity=0,
            laserActive=False,
            limitX=-1,
            limitY=-1,
            limitZ=-1,
            wco=(0, 0, 0),
            overrides=(100, 100, 100),
        )

        self.grbl = self._getGrbl(self.version)

    def parseStatus(self, line):
        match = None

        match = self.grbl["statusRegex"].match(line)
        if not match:
            self._logger.warn(
                "GRBL status string did not match pattern. GRBL version: %s, status string: %s",
                self.version,
                line,
            )
            return

        groups = match.groupdict()
        self._logger.info("line: %s\n state: %s", line, groups)
        if self.grbl["statusRegex"] == self.RE_STATUS_GRBL11:
            posType = groups["pos_type"]
            x = self._getFloatOrDefault(groups["pos_x"], None, "pos_x")
            y = self._getFloatOrDefault(groups["pos_y"], None, "pos_y")
            z = self._getFloatOrDefault(groups["pos_z"], None, "pos_z")

            if posType == "M":
                mx = x
                my = y
                mz = z
                wx = x + self.state["wco"][0]
                wy = y + self.state["wco"][1]
                wz = z + self.state["wco"][2]
            else:
                wx = x
                wy = y
                wz = z
                mx = x - self.state["wco"][0]
                my = y - self.state["wco"][1]
                mz = z - self.state["wco"][2]
        else:
            wx = self._getFloatOrDefault(groups["pos_x"], None, "pos_x")
            wy = self._getFloatOrDefault(groups["pos_y"], None, "pos_y")
            wz = 0
            if "pos_z" in groups:
                wz = self._getFloatOrDefault(groups["pos_z"], 0, "pos_z")

            mx = self._getFloatOrDefault(groups["mpos_x"], None, "mpos_x")
            my = self._getFloatOrDefault(groups["mpos_y"], None, "mpos_y")
            mz = 0
            if "mpos_z" in groups:
                mz = self._getFloatOrDefault(groups["mpos_z"], 0, "mpos_z")

        # persist one time reports in state object
        if "status" in groups:
            self.state["status"] = groups["status"]

        self.state["mpos"] = (mx, my, mz)
        self.state["wpos"] = (wx, wy, wz)

        if "rx" in groups:
            rxBuffer = (
                self._getIntOrDefault(
                    groups["rx"], -1, "Can't convert RX value from GRBL status to int."
                ),
            )
            if rxBuffer >= 0:
                self.state["serialBuffer"] = rxBuffer
                self.state["serialBufferLastUpdated"] = time.time()
        if "plan_buf" in groups:
            self.state["plannerBuffer"] = (self._getIntOrDefault(groups["plan_buf"]),)
        if "feedrate" in groups:
            self.state["feedrate"] = (self._getIntOrDefault(groups["feedrate"]),)
        if "laser_intensity" in groups:
            self.state["laserIntensity"] = self._getIntOrDefault(
                groups["laser_intensity"]
            )
            self.state["laserActive"] = "on" if groups["laser_intensity"] > 0 else "off"
        if "limit_x" in groups:
            self.state["limit_x"] = time.time() if groups["limit_x"] else 0
        if "limit_y" in groups:
            self.state["limit_y"] = time.time() if groups["limit_y"] else 0
        if "limit_z" in groups:
            self.state["limit_z"] = time.time() if groups["limit_y"] else 0
        if "wco_x" in groups and groups["wco_x"] is not None:
            self.state["wco"] = (
                self._getFloatOrDefault(groups["wco_x"], 0),
                self._getFloatOrDefault(groups["wco_y"], 0),
                self._getFloatOrDefault(groups["wco_z"], 0),
            )
        if "ov_1" in groups and groups["ov_1"] is not None:
            self.state["overrides"] = (
                self._getFloatOrDefault(groups["ov_1"], 100),
                self._getFloatOrDefault(groups["ov_2"], 100),
                self._getFloatOrDefault(groups["ov_3"], 100),
            )

        return self.state

    def _getGrbl(self, version):
        for v in [
            self.GRBL_VERSION_20170919_22270fa,
            self.GRBL_VERSION_20180223_61638c5,
            self.GRBL_VERSION_20180828_ac367ff,
            self.GRBL_VERSION_20181116_a437781,
            self.GRBL_VERSION_2019_MRB_CHECKSUM,
            self.GRBL_VERSION_20210714_d5e31ee,
            self.GRBL_VERSION_MB3PROTO,
        ]:
            if version == v["version"]:
                # self._logger.info("VVV %s", v)
                return v

        return self.GRBL_VERSION_20210714_d5e31ee  # fallback if no version match

    def _getIntOrDefault(self, value, default=None, failmsg=""):
        try:
            return int(value)
        except ValueError:
            self._logger.error("Can't convert %s to int: %s", value, failmsg)
            return default
        except TypeError:
            self._logger.warn("Can't convert type to int: %s", value)
            return default

    def _getFloatOrDefault(self, value, default=None, failmsg=""):
        try:
            return float(value)
        except ValueError:
            self._logger.error("Can't convert %s to float: %s", value, failmsg)
            return default
        except TypeError:
            self._logger.warn("Can't convert type to float: %s", value)
            return default
