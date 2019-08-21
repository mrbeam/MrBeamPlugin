
from octoprint_mrbeam.mrb_logger import mrb_logger
from octoprint.events import Events as OctoPrintEvents



class MrBeamEvents(object):
	PRINT_PROGRESS             = "PrintProgress"
	SLICING_PROGRESS           = "SlicingProgress"

	READY_TO_LASER_START       = "ReadyToLaserStart"
	READY_TO_LASER_CANCELED    = "ReadyToLaserCanceled"

	SHUTDOWN_PREPARE_START     = "ShutdownPrepareStart"
	SHUTDOWN_PREPARE_CANCEL    = "ShutdownPrepareCancel"
	SHUTDOWN_PREPARE_SUCCESS   = "ShutdownPrepareSuccess"

	LASER_PAUSE_SAFETY_TIMEOUT_START  = "LaserPauseSafetyTimeoutStart"
	LASER_PAUSE_SAFETY_TIMEOUT_END    = "LaserPauseSafetyTimeoutEnd"
	LASER_PAUSE_SAFETY_TIMEOUT_BLOCK  = "LaserPauseSafetyTimeoutBlock"

	PRINT_CANCELING_DONE       = "PrintCancelingDone"

	PRINT_DONE_PAYLOAD		   = "PrintDonePayload"

	BUTTON_PRESS_REJECT        = "ButtonPressReject"

	# After PrintDone we turn up the exhaus system and maybe other things...
	LASER_JOB_DONE             = "LaserJobDone"
	LASER_JOB_CANCELLED        = "LaserJobCancelled"
	LASER_JOB_FAILED           = "LaserJobFailed"

	LASER_COOLING_PAUSE        = "LaserCoolingPause"
	LASER_COOLING_RESUME       = "LaserCoolingResume"

	DUSTING_MODE_START         = "DustingModeStart"

	ANALYTICS_DATA             = "MrbAnalyticsData"
	MRB_PLUGIN_VERSION         = "MrbPluginVersion"
	JOB_TIME_ESTIMATED         = "JobTimeEstimated"

	HARDWARE_MALFUNCTION       = "HardwareMalfunction"

	LASER_HEAD_READ             = "LaserHeadRead"


	@classmethod
	def register_with_octoprint(cls):
		"""
		this has to be called during plugin's Constructor
		"""
		for k,v in vars(MrBeamEvents).iteritems():
			if isinstance(k, basestring) and isinstance(v, basestring) and k[0].isupper():
				setattr(OctoPrintEvents, k, v)

