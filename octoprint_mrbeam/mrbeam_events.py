from octoprint.events import Events as OctoPrintEvents


class MrBeamEvents(object):
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

    PRINT_DONE_PAYLOAD = "PrintDonePayload"

    BUTTON_PRESS_REJECT = "ButtonPressReject"

    # After PrintDone we turn up the exhaus system and maybe other things...
    LASER_JOB_DONE = "LaserJobDone"
    LASER_JOB_CANCELLED = "LaserJobCancelled"
    LASER_JOB_FAILED = "LaserJobFailed"

    LASER_COOLING_PAUSE = "LaserCoolingPause"
    LASER_COOLING_RESUME = "LaserCoolingResume"

    DUSTING_MODE_START = "DustingModeStart"

    ANALYTICS_DATA = "MrbAnalyticsData"
    MRB_PLUGIN_VERSION = "MrbPluginVersion"
    JOB_TIME_ESTIMATED = "JobTimeEstimated"

    HARDWARE_MALFUNCTION = "HardwareMalfunction"

    LASER_HEAD_READ = "LaserHeadRead"

    # Camera Calibration Screen Events
    RAW_IMAGE_TAKING_START = "RawImageTakingStart"
    RAW_IMAGE_TAKING_DONE = "RawImageTakingDone"
    RAW_IMG_TAKING_LAST = "lensCalibTakingLast"
    RAW_IMG_TAKING_FAIL = "lensCalibTakingFail"
    LENS_CALIB_START = "lensCalibStart"
    LENS_CALIB_PROCESSING_BOARDS = "lensCalibProcessingBoards"
    LENS_CALIB_RUNNING = "lensCalibRunning"
    LENS_CALIB_IDLE = "lensCalibIdle"
    LENS_CALIB_DONE = "lensCalibDone"
    LENS_CALIB_EXIT = "lensCalibExit"
    LENS_CALIB_FAIL = "lensCalibFail"
    BLINK_PRINT_LABELS = "blinkPrintLabels"

    @classmethod
    def register_with_octoprint(cls):
        """
        this has to be called during plugin's Constructor
        """
        for k, v in vars(MrBeamEvents).iteritems():
            if (
                isinstance(k, basestring)
                and isinstance(v, basestring)
                and k[0].isupper()
            ):
                setattr(OctoPrintEvents, k, v)
