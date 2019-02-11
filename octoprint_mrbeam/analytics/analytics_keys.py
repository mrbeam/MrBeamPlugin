class AnalyticsKeys(object):
	ANALYTICS_FOLDER = '/home/pi/.octoprint/analytics/'

	SERIALNUMBER = 'snr'
	TYPE = 't'
	VERSION = 'v'
	EVENT = 'e'
	TIMESTAMP = 'ts'
	NTP_SYNCED = 'ntp'
	TIMESTRING = 'timestring'
	DATA = 'data'
	SOFTWARE_TIER = 'sw_tier'
	VERSION_MRBEAM_PLUGIN = 'version_mrbeam_plugin'
	LASERHEAD_SERIAL = 'laserhead_serial'
	ENV = 'env'
	TOTAL_SPACE = 'total'
	AVAILABLE_SPACE = 'available'
	USED_SPACE = 'used'

	### EVENT TYPES ###
	JOB_EVENT = 'job'
	DEVICE_EVENT = 'device'
	CAM_EVENT = 'cam'
	LOG_EVENT = 'log'

	### DEVICE KEYS ###
	HOSTNAME = 'hostname'
	LASERHEAD_VERSION = 'lh_ver'

	### EVENT KEYS ###
	STARTUP = 'startup'
	SHUTDOWN = 'shutdown'
	INIT = 'init_json'
	FLASH_GRBL = 'flash_grbl'
	ANALYTICS_ENABLED = 'analytics_enabled'
	IPS = 'ips'
	DISK_SPACE = 'disk_space'

	### LOG EVENT KEYS ###
	LOG = 'log'
	EXCEPTION = 'exception'

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
	LASER_JOB = 'laser_job'
	DESIGN_FILE = 'design_file'
	MATERIAL = 'material'

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
	JOB_DURATION = 'dur'

	DUST_START = 'd_start'
	DUST_END = 'd_end'
	DUST_START_TS = 'd_start_ts'
	DUST_END_TS = 'd_end_ts'
	DUST_DURATION = 'd_duration'
	DUST_DIFF = 'd_diff'
	DUST_PER_TIME = 'd_per_time'

	PROGRESS_PERCENT =           'p'
	PROGRESS_LASER_TEMPERATURE = 'lt'
	PROGRESS_LASER_INTENSITY =   'li'
	PROGRESS_DUST_VALUE =        'dv'

	### CAM KEYS ###
	MARKERS = 'markers'
	CORNERS = 'corners'
	CAM_CALIBRATION = 'calibration'
	PIC_EVENT = 'pic'
	PIC_PREP = 'pic_prep'
	CAM_SESSION_ID = 'cs_id'
