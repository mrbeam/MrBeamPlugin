# coding=utf-8

__author__ = "teja philipp"
__date__ = "$29.01.2022 16:11:03$"

import re
import time

from octoprint_mrbeam.mrb_logger import mrb_logger


class GrblInterface(object):
    SETTING_CODES = dict(
        SETTING0="Step pulse time, microseconds",
        SETTING1="Step idle delay, milliseconds",
        SETTING2="Step pulse invert, mask",
        SETTING3="Step direction invert, mask",
        SETTING4="Invert step enable pin, boolean",
        SETTING5="Invert limit pins, boolean",
        SETTING6="Invert probe pin, boolean",
        SETTING10="Status report options, mask",
        SETTING11="Junction deviation, millimeters",
        SETTING12="Arc tolerance, millimeters",
        SETTING13="Report in inches, boolean",
        SETTING20="Soft limits enable, boolean",
        SETTING21="Hard limits enable, boolean",
        SETTING22="Homing cycle enable, boolean",
        SETTING23="Homing direction invert, mask",
        SETTING24="Homing locate feed rate, mm/min",
        SETTING25="Homing search seek rate, mm/min",
        SETTING26="Homing switch debounce delay, milliseconds",
        SETTING27="Homing switch pull-off distance, millimeters",
        SETTING30="Maximum spindle speed, RPM",
        SETTING31="Minimum spindle speed, RPM",
        SETTING32="Laser-mode enable, boolean",
        SETTING100="X-axis steps per millimeter",
        SETTING101="Y-axis steps per millimeter",
        SETTING102="Z-axis steps per millimeter",
        SETTING110="X-axis maximum rate, mm/min",
        SETTING111="Y-axis maximum rate, mm/min",
        SETTING112="Z-axis maximum rate, mm/min",
        SETTING120="X-axis acceleration, mm/sec^2",
        SETTING121="Y-axis acceleration, mm/sec^2",
        SETTING122="Z-axis acceleration, mm/sec^2",
        SETTING130="X-axis maximum travel, millimeters",
        SETTING131="Y-axis maximum travel, millimeters",
        SETTING132="Z-axis maximum travel, millimeters",
    )

    SETTING_CODES2 = dict(
        SETTING10="<report mask> default from INVERT_CONTROL_PIN_MASK.",
        SETTING14="<control mask> default from INVERT_CONTROL_PIN_MASK. Invert control input signals. Bits 4 - 7 cannot be set with $14 when COMPATIBILITY_LEVEL > 1 or the driver does not support the input.",
        SETTING15="<coolant mask> default from INVERT_COOLANT_FLOOD_PIN and INVERT_COOLANT_MIST_PIN. Invert coolant output signals.",
        SETTING16="<spindle mask> default from INVERT_SPINDLE_ENABLE_PIN, INVERT_SPINDLE_CCW_PIN and INVERT_SPINDLE_PWM_PIN. Invert spindle output signals.",
        SETTING17="<control mask> default from DISABLE_CONTROL_PINS_PULL_UP_MASK. Disable control signal pullup, replaces #define DISABLE_CONTROL_PIN_PULL_UP.",
        SETTING18="<axis mask> default from DISABLE_LIMIT_PINS_PULL_UP_MASK. Disable limit signals pull up, replaces #define DISABLE_LIMIT_PIN_PULL_UP. Driver may apply pull down instead.",
        SETTING19="<boolean> default from DISABLE_PROBE_PIN_PULL_UP. Disable probe pull up. Driver may apply pull down instead.",
        SETTING21="<mask> Changed from original boolean for enabling hard limits. bit0 - enable hard limits. bit1 - enable strict mode when hard limits enabled, this bit cannot be changed when COMPATIBILITY_LEVEL > 1. bit 1 default to #define CHECK_LIMITS_AT_INIT setting. NOTE: In strict mode switches will also be checked when $X is issued, if still engaged error 45 will be reported. Homing is still possible, but for $X to work limit switches has to be disengaged or overridden.",
        SETTING28="<float> default from DEFAULT_G73_RETRACT. Specifies G73 retract distance in mm.",
        SETTING29="<n> : default from DEFAULT_STEP_PULSE_DELAY, range 0 - 10. Stepper pulse delay in microseconds, replaces #define STEP_PULSE_DELAY.",
        SETTING31="<n> default value derived from DEFAULT_LASER_MODE and DEFAULT_LATHE_MODE. Changed from original boolean for enabling laser mode. 0 - normal mode. 1 - laser mode. 2 - lathe mode.",
        SETTING33="<float> : default from DEFAULT_SPINDLE_PWM_FREQ, range driver dependent. Spindle PWM frequency i Hz (from LPC port).",
        SETTING34="<n> : default from DEFAULT_SPINDLE_PWM_OFF_VALUE, range 0 - 100. Spindle off PWM duty cycle in percent (from LPC port).",
        SETTING35="<n> : default from DEFAULT_SPINDLE_PWM_MIN_VALUE, range 0 - 100. Spindle minimum PWM duty cycle in percent.",
        SETTING36="<n> : default from DEFAULT_SPINDLE_PWM_MAX_VALUE, range 0 - 100. Spindle maximum PWM duty cycle in percent (from LPC port).",
        SETTING37="<axis mask> : defaults to all axes. Defines which steppers is to be deenergized when motion completes. Driver/hardware dependent which are supported. At least X should be, disables all motors.",
        SETTING38="<n> : default driver dependent. Spindle encoder pulses per revolution. Usage is driver dependent (for spindle synchronized motion).",
        SETTING39="<n> : default 1, enable printable realtime command characters. Set to 0 to disable, when disabled these characters (?, ! and ~) are ignored as realtime commands and added to the input instead when part of a comment or a $-setting. NOTE: top bit set alternatives are provided as a safer alternative, see config.h.",
        SETTING40="<boolean> default 0 (off). Enable soft limits for jogging. When enabled jog targets will be limited to machine travel limits for homed axes.",
        SETTING43="<n> : default from DEFAULT_N_HOMING_LOCATE_CYCLE, range 0 - 255. Number of homing locate cycles",
        SETTING44="<axis mask> : default 0.",
        SETTING45="<axis mask> : default 0.",
        SETTING46="<axis mask> : default 0.",
        SETTING47="<axis mask> : default 0.",
        SETTING48="<axis mask> : default 0.",
        SETTING49="<axis mask> : default 0. Axis priority for homing lowest numbered executed first, number of available settings is same as number of supported axes. Replaces #define HOMING_CYCLE_0 etc.",
        SETTING50="<float> : default plugin dependent. Jogging step speed in mm/min. Not used by core, indended use by driver and/or sender. Senders may query this for keyboard jogging modified by CTRL key.",
        SETTING51="<float> : default plugin dependent. Jogging slow speed in mm/min. Not used by core, indended use by driver and/or sender. Senders may query this for keyboard jogging.",
        SETTING52="<float> : default plugin dependent. Jogging fast speed in mm/min. Not used by core, indended use by driver and/or sender. Senders may query this for keyboard jogging modified by SHIFT key.",
        SETTING53="<float> : default plugin dependent. Jogging step distance in mm. Not used by core, indended use by driver and/or sender. Senders may query this for keyboard jogging modified by CTRL key.",
        SETTING54="<float> : default plugin dependent. Jogging slow distance in mm. Not used by core, indended use by driver and/or sender. Senders may query this for keyboard jogging.",
        SETTING55="<float> : default plugin dependent. Jogging fast distance in mm. Not used by core, indended use by driver and/or sender. Senders may query this for keyboard jogging modified by SHIFT key.",
        SETTING60="<boolean> : default 1 (on). Restore default overrides when program ends. Replaces #define RESTORE_OVERRIDES_AFTER_PROGRAM_END.",
        SETTING61="<boolean> : default 0 (off). Ignore safety door signal when idle. If on only the spindle (laser) will be switched off. May be useful if positioning a laser head with the lid open is needed.",
        SETTING62="<boolean> : default 0 (off). Enable sleep function. Replaces #define SLEEP_ENABLE (ATMega port)",
        SETTING63="<boolean> : default 0 (on). Disable laser during hold. Replaces #define DISABLE_LASER_DURING_HOLD.",
        SETTING64="<boolean> : default 0 (off). Force grbl to enter alarm mode on startup. Replaces #define FORCE_INITIALIZATION_ALARM.",
        SETTING65="<boolean> : default 0 (off). Require homing sequence to be executed at startup(?). Replaces #define HOMING_INIT_LOCK.",
        # PID (closed loop control) settings
        SETTING80="<float> : default driver dependent. Spindle PID regulator proportional gain. Usage is driver dependent.",
        SETTING81="<float> : default driver dependent. Spindle PID regulator integral gain. Usage is driver dependent.",
        SETTING82="<float> : default driver dependent. Spindle PID regulator derivative gain. Usage is driver dependent.",
        SETTING84="<float> : default driver dependent. Spindle PID max output error. Usage is driver dependent.",
        SETTING85="<float> : default driver dependent. Spindle PID regulator max integral error. Usage is driver dependent.",
        SETTING90="<float> : default driver dependent. Spindle synced motion PID regulator proportional gain. Usage is driver dependent.",
        SETTING91="<float> : default driver dependent. Spindle synced motion PID regulator integral gain. Usage is driver dependent.",
        SETTING92="<float> : default driver dependent. Spindle synced motion PID regulator derivative gain. Usage is driver dependent.",
        # Spindle related settings:
        SETTING340="<n> : Spindle at speed tolerance, default 0 percent. Available for drivers and plugins that supports spindle at speed functionality. If set to a value > 0 then alarm 14 will be issued if the spindle speed is not within tolerance during a timeout delay. The timeout delay defaults to 4 seconds and is currently set from the SAFETY_DOOR_SPINDLE_DELAY symbol.",
        # Manual tool change settings:
        # Available for drivers that supports manual tool change. Requires machine to be homed. The controlled point (tool tip) will be moved to the original position after touch off for modes 1 - 3.
        # $TPW command is a shorthand for Tool Probe Workpiece. This command is only available in mode 1 and 2 and when a tool change is pending.
        SETTING341="<n> : Manual tool change mode, default value 0. 0: Normal. Manual tool change and touch off via jogging. 1: Manual touch off. Initial move to linear axis home position for tool change, manual or automatic touch off with $TPW command. 2: Manual touch off @ G59.3. Initial move to linear axis home position then to G59.3 position for tool change, manual or automatic touch off with $TPW command. 3: Manual touch off @ G59.3. Initial move to linear axis home position for tool change then to G59.3 position for automatic touch off. 4: Ignore M6. Note: Mode 1 and 2 requires initial tool offset set when $TPW command is used for touch off. In mode 2 a successful touch off will automatically Note: Mode 3 requires initial tool offset set.",
        SETTING342="<n> : Probing distance, default 30 mm. Used in mode 1 and 2 when $TPW command is issued and in mode 3.",
        SETTING343="<n> : Probing slow feed rate, default 25 mm/min. Used in mode 1 and 2 when $TPW command is issued and in mode 3 to obtain an accurate tool offset.",
        SETTING344="<n> : Probing seek feed rate, default 200 mm/min. Used in mode 1 and 2 when $TPW command is issued and in mode 3 to obtain an initial tool offset. If successful tool is backed off a bit and probing is redone with the slow feed rate from $343.",
    )

    RE_WELCOME = re.compile("Grbl (?P<version>\S+)\s.*")
    RE_SETTING = re.compile("\$(?P<id>\d+)=(?P<value>\S+)(\s\((?P<comment>.*)\))?")

    # GrblHAL 1.1 @ RP2040 produces these status messages (https://github.com/grblHAL/core/wiki/Report-extensions#realtime-report)
    # <Idle|MPos:0.000,0.000,0.000|Bf:35,1023|FS:0,0|Pn:Z|WCO:0.000,0.000,0.000>
    # <Idle|MPos:0.000,0.000,0.000|Bf:35,1023|FS:0,0|Pn:Z|Ov:100,100,100>
    # <Alarm:8|MPos:0.000,0.000,-5.000|Bf:35,1023|FS:0,0>
    # [<Idle|Run|Hold|Jog|Alarm|Door|Check|Home|Sleep|Tool>{:<substatus>}
    #  |<WPos:|MPos:><axis positions>
    # {|Bf:<block buffers free>,<RX characters free>}
    # {|Ln:<line number>}
    # {|FS:<feed rate>,<programmed rpm>{,<actual rpm>}}
    # {|PN:<signals>}
    # {|WCO:<axis offsets>}
    # {|WCS:G<coordinate system>}

    RE_STATUS_GRBL11 = re.compile(
        "<(?P<status>\w+)(:(?P<substatus>\w+))?"
        + "\|(?P<pos_type>[MW])Pos:(?P<pos_x>[0-9.\-]+),(?P<pos_y>[0-9.\-]+),(?P<pos_z>[0-9.\-]+)"
        + "("
        + "|(\|Bf:(?P<plan_buf>\d+),(?P<rx>\d+))?"
        + "|(\|Ln:(?P<lineNr>\d+))?"
        + "|(\|FS:(?P<feedrate>\d+),(?P<laser_intensity>\d+)(,(?P<current_laser_intensity>\d+))?)?"
        # + "|(\|Pn:(?P<limit_x>[X]?)(?P<limit_y>[Y]?)(?P<limit_z>[Z]?))?"
        # P - probe triggered
        # O - probe disconnected, new
        # X - X limit switch asserted
        # Y - Y limit switch asserted
        # Z - Z limit switch asserted
        # A - A limit switch asserted, new
        # B - B limit switch asserted, new
        # C - C limit switch asserted, new
        # D - Door switch asserted
        # R - Reset switch asserted
        # H - Feed hold switch asserted
        # S - Cycle start switch asserted
        # E - E-Stop switch asserted, new
        # L - Block delete switch asserted, new
        # T - Optional program stop switch asserted, new
        # W - Motor warning, new
        # M - Motor fault, new
        + "|(\|Pn:(?P<signals>[POXYZABCDRHSELTWM]+?))?"
        + "|(\|WCO:(?P<wco_x>[0-9.\-]+),(?P<wco_y>[0-9.\-]+),(?P<wco_z>[0-9.\-]+))?"
        # {|Ov:<overrides>}
        + "|(\|Ov:(?P<ov_1>\d+),(?P<ov_2>\d+),(?P<ov_3>\d+))?"
        # {|A:<accessory status>}
        + "|(\|A:(?P<accessory_status>\w+))?"
        # {|MPG:<0|1>}
        + "|(\|MPG:(?P<mpg_enable>[01]))?"
        # {|H:<0|1>{,<axis bitmask>}}
        + "|(\|H:(?P<homing_complete>[01])(,(?P<busy_axes>\w+)?))?"
        # {|D:<0|1>}
        # + "(\|.*D:(?P<_complete>[01]))?"
        # {|Sc:<axisletters>}
        # {|TLR:<0|1>}
        + "|(\|TLR:(?P<tool_length>\w+))?"
        # {|FW:<firmware>}
        + "|(\|FW:(?P<firmware>\w+))?"
        # {|In:<result>}]
        + ")*?>",
    )

    # <Idle,MPos:-1.000,-1.000,0.000,WPos:507.000,390.000,0.000,Buf:0,RX:0,limits:,laser off:0>
    RE_STATUS_GRBL09 = re.compile(
        "<(?P<status>\w+)"
        + ",.*MPos:(?P<mpos_x>[0-9.\-]+),(?P<mpos_y>[0-9.\-]+)"
        + ",.*WPos:(?P<pos_x>[0-9.\-]+),(?P<pos_y>[0-9.\-]+)"
        + ",.*Buf:(?P<plan_buf>\d+)"
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
        self.settings = dict()

    def parseStatus(self, line):
        match = None
        isGrbl11 = self.grbl["statusRegex"] == self.RE_STATUS_GRBL11

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
        if isGrbl11:
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

        if "rx" in groups and groups["rx"] is not None:
            rxBuffer = (
                self._getIntOrDefault(
                    groups["rx"], -1, "Can't convert RX value from GRBL status to int."
                ),
            )
            if rxBuffer >= 0:
                self.state["serialBuffer"] = rxBuffer
                self.state["serialBufferLastUpdated"] = time.time()
        if "plan_buf" in groups and groups["plan_buf"] is not None:
            self.state["plannerBuffer"] = (self._getIntOrDefault(groups["plan_buf"]),)
        if "feedrate" in groups and groups["feedrate"] is not None:
            self.state["feedrate"] = (self._getIntOrDefault(groups["feedrate"]),)
            if "laser_intensity" in groups and groups["laser_intensity"] is not None:
                self.state["laserIntensity"] = self._getIntOrDefault(
                    groups["laser_intensity"]
                )
                if isGrbl11:
                    self.state["laserActive"] = (
                        "on" if groups["laser_intensity"] > 0 else "off"
                    )
                else:
                    self.state["laserActive"] = (
                        "on" if groups["laser_state"] == "on" else "off"
                    )

        if isGrbl11:
            if "signals" in groups and groups["signals"] is not None:
                signalStr = groups["signals"]
                self.state["limit_x"] = time.time() if "X" in signalStr else 0
                self.state["limit_y"] = time.time() if "Y" in signalStr else 0
                self.state["limit_z"] = time.time() if "Z" in signalStr else 0
        else:
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

    def parseSettings(self, line):
        match = self.RE_SETTING.match(line)
        # there are a bunch of responses that do not match and it's ok.
        if match:
            id = int(match.group("id"))
            v_str = match.group("value")
            v = float(v_str)
            try:
                i = int(v)
            except ValueError:
                pass
            value = v
            if i == v and v_str.find(".") < 0:
                value = i

            comment = match.group("comment")
            if comment is None or comment is "":
                key = "SETTING" + str(id)
                if key in self.SETTING_CODES:
                    comment = self.SETTING_CODES[key]
                if key in self.SETTING_CODES2:
                    comment = self.SETTING_CODES2[key]

                self.settings[id] = dict(value=value, comment=comment)
            self._logger.info("parseSettings: $%s=%s %s", id, value, comment)
        else:
            self._logger.info("parseSettings: NO IDEA %s", line)

    def refreshSettings(self):
        self.settings = dict()

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
