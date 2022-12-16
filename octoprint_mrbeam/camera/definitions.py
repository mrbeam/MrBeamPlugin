#!/usr/bin/env python3
from fractions import Fraction
import logging
import numpy as np

########################
### General camera
########################

RESOLUTIONS = {
    "1000x780": (1000, 780),
    "1920x1080": (1920, 1080),
    "2000x1440": (2000, 1440),
    "2048x1536": (2048, 1536),
    "2592x1944": (2592, 1944),
    "2592x1952": (2592, 1952),
}

LEGACY_STILL_RES = RESOLUTIONS[
    "2048x1536"
]  # from octoprint_mrbeam __init___ : get_settings_defaults
DEFAULT_STILL_RES = RESOLUTIONS[
    "2592x1944"
]  # Be careful : Resolutions accepted as increments of 32 horizontally and 16 vertically
DEFAULT_SHUTTER_SPEED = int(1.5 * 10**5)  # (microseconds)
MAX_SHUTTER_SPEED = 400000  # limits the shutter speed to this value

N, W, S, E = "N", "W", "S", "E"
NW, NE, SW, SE = N + W, N + E, S + W, S + E
QD_KEYS = [NW, NE, SW, SE]

# threshold; 2 consecutive pictures need to have a minimum difference
# before being undistorted and served
DIFF_TOLERANCE = 50

TARGET_AVG_ROI_BRIGHTNESS = 170
BRIGHTNESS_TOLERANCE = 40  # TODO Keep the brightness of the images tolerable

VERSION_KEY = "version"
DIST_KEY = "dist"
MTX_KEY = "mtx"

# Height (mm) from the bottom of the work area to the camera lens.
CAMERA_HEIGHT = 582
# Height (mm) - max height at which the Mr Beam II can laser an object.
MAX_OBJ_HEIGHT = 38

SUCCESS_WRITE_RETVAL = 1  # successful retval for cv2.imwrite

########################
### MARKER DETECTION
########################
# Size of the corner search area
RATIO_W, RATIO_H = Fraction(1, 6), Fraction(1, 4)
# Padding distance from the edges of the image (The markers are never pressed against the border)
OFFSET_W, OFFSET_H = Fraction(0, 36), Fraction(0, 20)

RATIO_W_KEY = "ratioW"
RATIO_H_KEY = "ratioH"

STOP_EVENT_ERR = "StopEvent_was_raised"
ERR_NEED_CALIB = "Camera_calibration_is_needed"

HUE_BAND_LB_KEY = "hue_lower_bound"
HUE_BAND_LB = 105
HUE_BAND_UB = 200  # if value > 180 : loops back to 0

# Minimum and Maximum number of pixels a marker should have
# as seen on the edge detection masks
# TODO make scalable with picture resolution
MIN_MARKER_PIX = 350
MAX_MARKER_PIX = 1500


########################
### CORNER CALIBRATION
########################

# Calibration file :
# Position of the pink circles, as found during calibration
UNDIST_CALIB_MARKERS_KEY = "user_undist_calibMarkers"
RAW_CALIB_MARKERS_KEY = "raw_calibMarkers"
FACT_UNDIST_CALIB_MARKERS_KEY = "calibMarkers"  # legacy
FACT_RAW_CALIB_MARKERS_KEY = "factory_raw_calibMarkers"

# Calibration file :
# Position of the corners (arrow tips), as found during the calibration
UNDIST_CORNERS_KEY = "user_undist_cornersFromImage"
RAW_CORNERS_KEY = "raw_cornersFromImage"
FACT_UNDIST_CORNERS_KEY = "cornersFromImage"  # legacy
FACT_RAW_CORNERS_KEY = "factory_raw_cornersFromImage"

# Empty settings config
PIC_SETTINGS = {
    UNDIST_CALIB_MARKERS_KEY: None,
    UNDIST_CORNERS_KEY: None,
}
CALIB_REFS = dict(
    markers=dict(
        user=dict(raw=RAW_CALIB_MARKERS_KEY, undistorted=UNDIST_CALIB_MARKERS_KEY),
        factory=dict(
            raw=FACT_RAW_CALIB_MARKERS_KEY,
            undistorted=FACT_UNDIST_CALIB_MARKERS_KEY,
        ),
    ),
    corners=dict(
        user=dict(raw=RAW_CORNERS_KEY, undistorted=UNDIST_CORNERS_KEY),
        factory=dict(
            raw=FACT_RAW_CORNERS_KEY,
            undistorted=FACT_UNDIST_CORNERS_KEY,
        ),
    ),
)

########################
### LENS CALIBRATION
########################
# Chessboard size
CB_ROWS = 5
CB_COLS = 6
CB_SQUARE_SIZE = 30  # mm
# Chessboard size in mm
BOARD_SIZE_MM = np.array([220, 190])
MIN_BOARDS_DETECTED = 9
MAX_PROCS = 4

# Frequency to check presence of a file
REFRESH_RATE_WAIT_CHECK = 0.2  # TODO: use OctoPrint.mrbeam/venv/lib/python2.7/site-packages/watchdog-0.8.3-py2.7.egg/watchdog/observers/fsevents.py

# Progress of the lens calibration and the pictures taken.
STATE_PENDING_CAMERA = "camera_processing"
STATE_QUEUED = "queued"
STATE_PROCESSING = "processing"
STATE_SUCCESS = "success"
STATE_FAIL = "fail"
STATE_IGNORED = "ignored"
STATE_PENDING = "pending"
STATES = [
    STATE_QUEUED,
    STATE_PROCESSING,
    STATE_SUCCESS,
    STATE_FAIL,
    STATE_IGNORED,
    STATE_PENDING,
    STATE_PENDING_CAMERA,
]

# Lens calibration files
LENS_CALIBRATION = {
    "path": "cam",  # extra path after the base folder (usually ~/.octoprint/)
    "legacy": "lens_correction_2048x1536.npz",
    "user": "lens_correction.npz",
    "factory": "factory_lens_correction.npz",
}


# Filenames for calibration board pictures
TMP_PATH = "/tmp/chess_img_{}.jpg"

# Formated and Regex filenames for calibration board pictures
TMP_RAW_FNAME = "tmp_raw_img_{0:0>3}.jpg"
TMP_RAW_FNAME_RE = "tmp_raw_img_[0-9]+.jpg$"
TMP_RAW_FNAME_RE_NPZ = "tmp_raw_img_[0-9]+.jpg.npz$"
