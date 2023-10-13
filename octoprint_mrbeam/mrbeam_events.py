from octoprint.events import Events as OctoPrintEvents


# NOTICE: This is used by the camera plugin
class MrBeamEvents(object):
    SETTINGS_LOAD = "SettingsLoad"
    MRB_PLUGIN_INITIALIZED = "MrbPluginInitialized"
    BOOT_GRACE_PERIOD_END = "BootGracePeriodEnd"

    PRINT_PROGRESS = "PrintProgress"
    SLICING_PROGRESS = "SlicingProgress"

    READY_TO_LASER_START = "ReadyToLaserStart"
    READY_TO_LASER_CANCELED = "ReadyToLaserCanceled"

    SHUTDOWN_PREPARE_START = "ShutdownPrepareStart"
    SHUTDOWN_PREPARE_CANCEL = "ShutdownPrepareCancel"
    SHUTDOWN_PREPARE_SUCCESS = "ShutdownPrepareSuccess"

    LASER_PAUSE_SAFETY_TIMEOUT_START = "LaserPauseSafetyTimeoutStart"
    LASER_PAUSE_SAFETY_TIMEOUT_END = "LaserPauseSafetyTimeoutEnd"
    LASER_PAUSE_SAFETY_TIMEOUT_BLOCK = "LaserPauseSafetyTimeoutBlock"

    PRINT_CANCELING_DONE = "PrintCancelingDone"
    PRINT_ABORTED = "PrintAborted"

    PRINT_DONE_PAYLOAD = "PrintDonePayload"

    BUTTON_PRESS_REJECT = "ButtonPressReject"

    # After PrintDone we turn up the exhaust system and maybe other things...
    LASER_JOB_DONE = "LaserJobDone"
    LASER_JOB_CANCELLED = "LaserJobCancelled"
    LASER_JOB_FAILED = "LaserJobFailed"
    LASER_JOB_ABORTED = "LaserJobAborted"
    LASER_JOB_ABORT = "LaserJobAbort"  # Abort a laser job

    # events for the laser head
    LASER_HOME = "LaserHome"

    LASER_COOLING_TEMPERATURE_REACHED = "LaserCoolingTemperatureReached"
    LASER_COOLING_PAUSE = "LaserCoolingPause"  # Pause the job for cooling
    LASER_COOLING_RESUME = "LaserCoolingResume"  # Resume laser job after cooling
    LASER_COOLING_TO_SLOW = "LaserCoolingToSlow"
    LASER_COOLING_RE_TRIGGER_FAN = "LaserCoolingReTriggerFan"
    LASER_HIGH_TEMPERATURE = "LaserHighTemperature"

    HIGH_TEMPERATURE_CRITICAL_SHOW = "HighTemperatureCriticalShow"
    HIGH_TEMPERATURE_CRITICAL_HIDE = "HighTemperatureCriticalHide"
    HIGH_TEMPERATURE_CRITICAL_DISMISSED = "HighTemperatureCriticalDismissed"
    HIGH_TEMPERATURE_WARNING_SHOW = "HighTemperatureWarningShow"
    HIGH_TEMPERATURE_WARNING_HIDE = "HighTemperatureWarningHide"
    HIGH_TEMPERATURE_WARNING_DISMISSED = "HighTemperatureWarningDismissed"

    COMPRESSOR_DEACTIVATE = "CompressorDeactivate"

    EXHAUST_DEACTIVATE = "ExhaustDeactivate"

    LED_ERROR_ENTER = "LedErrorEnter"
    LED_ERROR_EXIT = "LedErrorExit"

    ALARM_ENTER = "AlarmEnter"
    ALARM_EXIT = "AlarmExit"

    DUSTING_MODE_START = "DustingModeStart"

    ANALYTICS_DATA = "MrbAnalyticsData"
    MRB_PLUGIN_VERSION = "MrbPluginVersion"
    JOB_TIME_ESTIMATED = "JobTimeEstimated"

    HARDWARE_MALFUNCTION = "HardwareMalfunction"

    LASER_HEAD_READ = "LaserHeadRead"

    # Camera Calibration Screen Events
    RAW_IMAGE_TAKING_START = "RawImageTakingStart"
    RAW_IMAGE_TAKING_DONE = "RawImageTakingDone"
    RAW_IMG_TAKING_LAST = "LensCalibTakingLast"
    RAW_IMG_TAKING_FAIL = "LensCalibTakingFail"
    LENS_CALIB_START = "LensCalibStart"
    LENS_CALIB_PROCESSING_BOARDS = "LensCalibProcessingBoards"
    LENS_CALIB_RUNNING = "LensCalibRunning"
    LENS_CALIB_IDLE = "LensCalibIdle"
    LENS_CALIB_DONE = "LensCalibDone"
    LENS_CALIB_EXIT = "LensCalibExit"
    LENS_CALIB_FAIL = "LensCalibFail"
    BLINK_PRINT_LABELS = "BlinkPrintLabels"
    INITIAL_CALIBRATION = "initial_calibration"

    # Airfilter
    AIRFILTER_CHANGED = "AirfilterChanged"
    HEAVY_DUTY_PREFILTER_CHANGED = "HeavyDutyPrefilterChanged"

    # Usage Data
    USAGE_DATA_RESET_PREFILTER = "UsageDataResetPrefilter"
    USAGE_DATA_RESET_CARBON_FILTER = "UsageDataResetCarbonFilter"
    USAGE_DATA_RESET_LASER_HEAD = "UsageDataResetLaserHead"
    USAGE_DATA_CHANGED = "UsageDataChanged"

    @classmethod
    def register_with_octoprint(cls):
        """this has to be called during plugin's Constructor."""
        for k, v in vars(MrBeamEvents).iteritems():
            if (
                isinstance(k, basestring)
                and isinstance(v, basestring)
                and k[0].isupper()
            ):
                setattr(OctoPrintEvents, k, v)
