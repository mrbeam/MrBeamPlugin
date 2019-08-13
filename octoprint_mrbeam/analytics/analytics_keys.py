class AnalyticsKeys(object):
	SERIALNUMBER = 'snr'
	TYPE = 't'
	VERSION = 'v'
	EVENT = 'e'
	TIMESTAMP = 'ts'
	NTP_SYNCED = 'ntp'
	SESSION_ID = 'sid'
	DATA = 'data'
	SOFTWARE_TIER = 'sw_tier'
	VERSION_MRBEAM_PLUGIN = 'version_mrbeam_plugin'
	LASERHEAD_SERIAL = 'laserhead_serial'
	ENV = 'env'

	### EVENT TYPES ###
	TYPE_JOB_EVENT = 'job'
	TYPE_DEVICE_EVENT = 'device'
	TYPE_CAM_EVENT = 'cam'
	TYPE_LOG_EVENT = 'log'
	TYPE_CONNECTIVITY_EVENT = 'connectivity'
	TYPE_FRONTEND = 'frontend'

	### DEVICE KEYS ###
	HOSTNAME = 'hostname'
	LASERHEAD_VERSION = 'lh_ver'
	OLD_CHANNEL = 'old_channel'
	NEW_CHANNEL = 'new_channel'
	TOTAL_SPACE = 'total'
	AVAILABLE_SPACE = 'available'
	USED_SPACE = 'used_percent'
	MRBEAM_USAGE = 'mrbeam_usage'
	CORRECTION_FACTOR = 'correction_factor'
	CORRECTION_ENABLED = 'correction_enabled'
	CORRECTION_OVERRIDE = 'correction_override'
	POWER_65 = 'p_65'
	POWER_75 = 'p_75'
	POWER_85 = 'p_85'
	USERS = 'users'

	### EVENT KEYS ###
	STARTUP = 'startup'
	SHUTDOWN = 'shutdown'
	INIT = 'init_json'
	FLASH_GRBL = 'flash_grbl'
	ANALYTICS_ENABLED = 'analytics_enabled'
	IPS = 'ips'
	HTTP_SELF_CHECK = 'http_self_check'
	INTERNET_CONNECTION = 'internet_connection'
	DISK_SPACE = 'disk_space'
	SW_CHANNEL_SWITCH = 'sw_channel_switch'
	LASERHEAD_INFO = 'laserhead_info'

	### LOG EVENT KEYS ###
	EVENT_LOG = 'log_event'
	EXCEPTION = 'exception'
	IOBEAM =    'iobeam'
	LOG_CPU = 'cpu'
	CAMERA = 'camera'
	CAMERA_SESSION = 'camera_session'
	OS_HEALTH = 'os_health'

	### JOB KEYS ###
	JOB_ID = 'job_id'
	FILENAME = 'filename'
	SLICING_STARTED = 's_started'
	SLICING_DONE = 's_done'
	PRINT_STARTED = 'p_started'
	PRINT_PROGRESS = 'p_progress'
	PRINT_DONE = 'p_done'
	LASERJOB_STARTED = 'laserjob_started'
	LASERJOB_DONE = 'laserjob_done'
	PRINT_PAUSED = 'p_paused'
	PRINT_RESUMED = 'p_resumed'
	PRINT_CANCELLED = 'p_cancelled'
	PRINT_FAILED = 'p_failed'
	DUST_SUM = 'dust_summary'
	INTENSITY_SUM = 'intensity_summary'
	LASERTEMP = 'lasertemp'
	LASERTEMP_SUM = 'lasertemp_summary'
	CPU_DATA = 'cpu'
	FINAL_DUST = 'final_dust'
	COOLING_START = 'cooling_start'
	COOLING_DONE = 'cooling_done'
	CONV_ENGRAVE = 'conv_eng'
	CONV_CUT = 'conv_cut'
	LASER_JOB = 'laser_job'
	DESIGN_FILE = 'design_file'
	MATERIAL = 'material'
	FAN_RPM_TEST = 'fan_rpm_test'
	FAN_RPM = 'fan_rpm'
	FAN_STATE = 'fan_state'

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
	JOB_TIME_ESTIMATION = 'dur_est'

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


	### CONNECTIVITY ###
	EVENT_UI_RENDER_CALL =          'ui_render_call'
	EVENT_CLIENT_OPENED =           'client_opened'
	VERSION_FINDMYMRBEAM_PLUGIN =   'version_findmymrbeam_plugin'
	CONNECTIONS_STATE = 			'connections_state'








