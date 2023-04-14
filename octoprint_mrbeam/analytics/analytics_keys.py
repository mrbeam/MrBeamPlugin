class AnalyticsKeys:
    class Header:
        SNR = "snr"
        TYPE = "t"
        ENV = "env"
        VERSION = "v"
        EVENT = "e"
        TIMESTAMP = "ts"
        NTP_SYNCED = "ntp"
        SESSION_ID = "sid"
        DATA = "data"
        SOFTWARE_TIER = "sw_tier"
        VERSION_MRBEAM_PLUGIN = "version_mrbeam_plugin"
        UPTIME = "uptime"
        MODEL = "model"
        FEATURE_ID = "feature_id"

    class EventType:
        JOB = "job"
        DEVICE = "device"
        LOG = "log"
        CONNECTIVITY = "connectivity"
        FRONTEND = "frontend"

    class Job:
        ID = "job_id"
        ERROR = "err"
        STATUS = "status"
        TRIGGER = "trigger"

        class Event:
            LASERJOB_STARTED = "laserjob_started"
            LASERJOB_FINISHED = "laserjob_finished"
            CPU = "cpu"  # This comes both in the slicing and the print
            JOB_TIME_ESTIMATED = "job_time_estimated"  # This comes after the slicing but before the printing
            NTP_SYNC = "ntp_sync"

            class Slicing:
                STARTED = "s_started"
                MATERIAL = "material"
                CONV_ENGRAVE = "conv_eng"
                CONV_CUT = "conv_cut"
                DESIGN_FILE = "design_file"
                DONE = "s_done"
                FAILED = "s_failed"
                CANCELLED = "s_cancelled"

            class Print:
                STARTED = "p_started"
                PROGRESS = "p_progress"
                FAN_RPM_TEST = "fan_rpm_test"
                PAUSED = "p_paused"
                RESUMED = "p_resumed"
                CANCELLED = "p_cancelled"
                FAILED = "p_failed"
                ABORTED = "p_aborted"
                DONE = "p_done"

            class Cooling:
                START = "cooling_start"
                DONE = "cooling_done"
                DIFFERENCE = "cooling_difference"
                TIME = "cooling_time"
                COOLING_FAN_RETRIGGER = "cooling_fan_retrigger"

            class Summary:
                DUST = "dust_summary"
                INTENSITY = "intensity_summary"
                LASERTEMP = "lasertemp_summary"

        class Dust:
            START = "d_start"
            END = "d_end"
            START_TS = "d_start_ts"
            END_TS = "d_end_ts"
            DURATION = "d_duration"
            DIFF = "d_diff"
            PER_TIME = "d_per_time"

        class Fan:
            RPM = "fan_rpm"
            STATE = "fan_state"

        class Duration:
            CURRENT = "dur"
            ESTIMATION = "dur_est_v1_backend"
            ESTIMATION_V2 = "dur_est_v2_frontend"
            CALC_DURATION_TOTAL = "calc_duration_total"
            CALC_DURATION_WOKE = "calc_duration_woke"
            CALC_LINES = "calc_lines"

        class Progress:
            PERCENT = "p"
            LASER_TEMPERATURE = "lt"
            LASER_INTENSITY = "li"
            DUST_VALUE = "dv"
            COMPRESSOR = "compressor"

        class LaserHead:
            TEMP = "lasertemp"

    class Device:
        HOSTNAME = "hostname"
        ERROR = "err"
        SUCCESS = "success"

        class Event:
            ANALYTICS_ENABLED = "analytics_enabled"
            STARTUP = "startup"
            SHUTDOWN = "shutdown"
            DISK_SPACE = "disk_space"
            SOFTWARE_VERSIONS = "software_versions"
            IPS = "ips"
            FLASH_GRBL = "flash_grbl"
            LASERHEAD_INFO = "laserhead_info"
            SW_CHANNEL_SWITCH = "sw_channel_switch"
            HTTP_SELF_CHECK = "http_self_check"
            INTERNET_CONNECTION = "internet_connection"
            MRBEAM_USAGE = "mrbeam_usage"
            COMPRESSOR = "compressor"
            NUM_FILES = "num_files"
            CAMERA_IMAGE = "camera_image"
            LASERHEAD_CHANGED = "laserhead_changed"
            LASER_HIGH_TEMPERATURE = "laser_high_temperature"

        class HighTemp:
            WARNING_SHOWN = "high_temp_warning_shown"
            WARNING_DISMISSED = "high_temp_warning_dismissed"
            CRITICAL_SHOWN = "high_temp_critical_shown"
            CRITICAL_DISMISSED = "high_temp_critical_dismissed"

        class SoftwareChannel:
            OLD = "old_channel"
            NEW = "new_channel"

        class Usage:
            TOTAL_SPACE = "total"
            AVAILABLE_SPACE = "available"
            USED_SPACE = "used_percent"
            USERS = "users"
            FILES = "files"

        class LaserHead:
            SERIAL = "laserhead_serial"
            VERSION = "lh_ver"
            POWER_65 = "p_65"
            POWER_75 = "p_75"
            POWER_85 = "p_85"
            TARGET_POWER = "target_power"
            HEAD_MODEL_ID = "laserhead_model_id"
            CORRECTION_FACTOR = "correction_factor"
            CORRECTION_ENABLED = "correction_enabled"
            CORRECTION_OVERRIDE = "correction_override"
            LAST_USED_HEAD_MODEL_ID = "last_used_laserhead_model_id"
            LAST_USED_SERIAL = "last_used_laserhead_serial"

        class Grbl:
            FROM_VERSION = "from_version"
            TO_VERSION = "to_version"

        class Request:
            RESPONSE = "response"
            CONNECTION = "connection"
            IP = "ip"
            ELAPSED_S = "elapsed_s"

        class Cpu:
            THROTTLE_ALERTS = "throttle_alerts"

    class Log:
        TERMINAL_DUMP = "terminal_dump"
        ERROR = "err"
        SUCCESS = "success"

        class Event:
            EVENT_LOG = "log_event"
            CPU = "cpu"
            CAMERA = "camera"
            OS_HEALTH = "os_health"
            ANALYTICS_FILE_CROP = "analytics_file_crop"

        class Level:
            EXCEPTION = "exception"

        class Component:
            NAME = "component"
            VERSION = "component_version"

        class Caller:
            HASH = "hash"
            FILE = "file"
            LINE = "line"
            FUNCTION = "function"

        class Cpu:
            TEMP = "temp"
            THROTTLE_ALERTS = "throttle_alerts"

        class AnalyticsFile:
            PREV_SIZE = "prev_size"
            NEW_SIZE = "new_size"
            NUM_LINES = "num_lines"

    class Connectivity:
        class Event:
            UI_RENDER_CALL = "ui_render_call"
            CLIENT_OPENED = "client_opened"
            VERSION_FINDMYMRBEAM_PLUGIN = "version_findmymrbeam_plugin"
            CONNECTIONS_STATE = "connections_state"

        class Call:
            HOST = "host"
            REMOTE_IP = "remote_ip"
            REFERRER = "referrer"
            LANGUAGE = "language"
            USER_AGENT = "user_agent"

    class HighTemperatureWarning:
        class Event:
            STATE_TRANSITION = "state_transition"

        class State:
            STATE_BEFORE = "state_before"
            STATE_AFTER = "state_after"
            EVENT = "event"
            FEATURE_DISABLED = "feature_disabled"
