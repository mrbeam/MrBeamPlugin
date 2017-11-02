class AnalyticsKeys(object):
	SERIALNUMBER = 'snr'
	TYPE = 't'
	VERSION = 'v'
	EVENT = 'e'
	TIMESTAMP = 'ts'
	TIMESTRING = 'timestring'
	DATA = 'data'

	### EVENT TYPES ###
	JOB_EVENT = 'job'
	DEVICE_EVENT = 'device'
	CAM_EVENT = 'cam'

	### DEVICE KEYS ###
	HOSTNAME = 'hostname'
	LASERHEAD_VERSION = 'lh_ver'

	### EVENT KEYS ###
	STARTUP = 'startup'
	SHUTDOWN = 'shutdown'
	INIT = 'init_json'



	### JOB KEYS ###
	JOB_ID = 'job_id'
	FILENAME = 'filename'
	PRINT_STARTED = 'p_started'
	PRINT_PROGRESS = 'p_progress'
	PRINT_DONE = 'p_done'
	LASERJOB_DONE = 'laserjob_done'
	PRINT_PAUSED = 'p_paused'
	PRINT_RESUMED = 'p_resumed'
	PRINT_CANCELLED = 'p_cancelled'
	PRINT_FAILED = 'p_failed'
	DUST_SUM = 'dust_summary'
	INTENSITY_SUM = 'intensity_summary'
	LASERTEMP = 'lasertemp'
	LASERTEMP_SUM = 'lasertemp_summary'
	FINAL_DUST = 'final_dust'
	COOLING_START = 'cooling_start'
	COOLING_DONE = 'cooling_done'
	CONV_ENGRAVE = 'conv_eng'
	CONV_CUT = 'conv_cut'
	PRINT_EVENTS = [
						PRINT_STARTED,
						PRINT_PROGRESS,
						PRINT_DONE,
						PRINT_CANCELLED,
						PRINT_PAUSED,
						PRINT_RESUMED,
						PRINT_FAILED,
						CONV_CUT,
						CONV_ENGRAVE
					]
	FAILED_PRINT_EVENTS = [PRINT_CANCELLED,PRINT_FAILED]

	DUST_START = 'dust_start'
	DUST_END = 'dust_end'
	DUST_START_TS = 'dust_start_ts'
	DUST_END_TS = 'dust_end_ts'


	### CAM KEYS ###
	MARKERS = 'markers'
	CORNERS = 'corners'
	CAM_CALIBRATION = 'calibration'
	PIC_EVENT = 'pic'
	CAM_SESSION_ID = 'cs_id'
