



class MrBeamEvents(object):
	PRINT_PROGRESS             = "PrintProgress"
	SLICING_PROGRESS           = "SlicingProgress"

	READY_TO_LASER_START       = "ReadyToLaserStart"
	READY_TO_LASER_CANCELED    = "ReadyToLaserCanceled"

	SHUTDOWN_PREPARE_START     = "ShutdownPrepareStart"
	SHUTDOWN_PREPARE_CANCEL    = "ShutdownPrepareCancel"
	SHUTDOWN_PREPARE_SUCCESS   = "ShutdownPrepareSuccess"

	LASER_PAUSE_SAFTEY_TIMEOUT_START  = "LaserPauseSafetyTimeoutStart"
	LASER_PAUSE_SAFTEY_TIMEOUT_END    = "LaserPauseSafetyTimeoutEnd"
	LASER_PAUSE_SAFTEY_TIMEOUT_BLOCK  = "LaserPauseSafetyTimeoutBlock"

    PRINT_CANCELING_DONE       = "PrintCancelingDone"

	LASER_COOLING_PAUSE        = "LaserCoolingPause"
	LASER_COOLING_RESUME       = "LaserCoolingResume"
