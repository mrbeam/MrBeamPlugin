#!/usr/bin/env python3
from __future__ import absolute_import, print_function, unicode_literals, division
from collections import Mapping
import datetime
from multiprocessing import Event, Process, Queue, Value
from threading import Thread, RLock
import logging
import cv2
import signal, os
import numpy as np
import time
import queue
from os import path
import numpy as np
from copy import copy
import re

from octoprint_mrbeam.camera.definitions import (
    LEGACY_STILL_RES,
    CB_ROWS,
    CB_COLS,
    CB_SQUARE_SIZE,
    REFRESH_RATE_WAIT_CHECK,
    BOARD_SIZE_MM,
    MIN_BOARDS_DETECTED,
    MAX_PROCS,
    STATE_PENDING_CAMERA,
    STATE_QUEUED,
    STATE_PROCESSING,
    STATE_SUCCESS,
    STATE_FAIL,
    STATE_IGNORED,
    STATE_PENDING,
    STATES,
    TMP_PATH,
    TMP_RAW_FNAME,
    TMP_RAW_FNAME_RE,
    TMP_RAW_FNAME_RE_NPZ,
)
from octoprint_mrbeam.mrbeam_events import MrBeamEvents
from octoprint_mrbeam.util import (
    makedirs,
    get_thread,
    dict_merge,
    dict_map,
    _basestring,
)
from octoprint_mrbeam.util.img import differed_imwrite
from octoprint_mrbeam.util.log import logme, logtime, logExceptions, json_serialisor
from octoprint_mrbeam.mrb_logger import mrb_logger
import yaml
from octoprint_mrbeam.support import check_calibration_tool_mode

# Remote connection for calibration
# SSH_FILE = "/home/pi/.ssh/pi_id_rsa"
# REMOTE_CALIBRATION_FOLDER = "/home/calibrationfiles/"
# REMOTE_CALIBRATE_EXEC = path.join(REMOTE_CALIBRATION_FOLDER, "calibrate2.py")
# MY_HOSTNAME = "MrBeam-8ae9"

_logger = mrb_logger(__name__, lvl=logging.INFO)
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"
FACTORY = "factory"
USER = "user"

### LENS UNDISTORTION FUNCTIONS

# @logtime()
def undistort(img, mtx, dist, calibration_img_size=None, output_img_size=None):
    """Apply the camera calibration matrices to distort the picture back straight.
    @param calibration_img_size: tuple: size of the image when the calibration was occuring.
    @param output_img_size: tuple: desired size of the output image.
    If not declared, the calibration image size and output image are going to be
    assumed the same as the input.
    It is faster to upscale/downscale here than to do it in a 2nd step seperately
    """
    # The camera matrix need to be rescaled if the image size changed
    # in_mtx = adjust_mtx_to_pic(img, mtx, dist, calibration_img_size)
    h, w = img.shape[:2]
    dest_mtx, roi = cv2.getOptimalNewCameraMatrix(mtx, dist, (w, h), 1, output_img_size)
    mapx, mapy = cv2.initUndistortRectifyMap(mtx, dist, None, dest_mtx, (w, h), 5)
    return cv2.remap(img, mapx, mapy, cv2.INTER_LINEAR), dest_mtx

    # undistort image with cam_params
    # return cv2.undistort(img, mtx, dist, dest_mtx)


def adjust_mtx_to_pic(img, mtx, dist, original_img_size=None):
    h, w = img.shape[:2]
    if original_img_size is None:
        original_img_size = (w, h)
    _logger.warning("im in %s, im calib %s", (w, h), original_img_size)
    newcameramtx, _ = cv2.getOptimalNewCameraMatrix(
        mtx, dist, original_img_size, 0, (w, h)
    )
    return newcameramtx


def undist_points(inPts, mtx, dist, new_mtx=None, reverse=False):
    # TODO Is it possible to reverse the distortion?
    in_vecs = np.asarray(inPts, dtype=np.float32).reshape((-1, 1, 2))
    if new_mtx is None:
        new_mtx = mtx
    for x, y in cv2.undistortPoints(in_vecs, mtx, dist, P=new_mtx).reshape(-1, 2):
        yield x, y


def undist_dict(dict_pts, *a, **kw):
    keys = dict_pts.keys()
    inPts = [
        dict_pts[k] for k in keys
    ]  # Preserve in the order in which we have the keys
    res_iter = undist_points(inPts, *a, **kw)
    return {keys[i]: np.array(pos) for i, pos in enumerate(res_iter)}


def clean_unexpected_files(tmp_path):
    """
    Removes unexpected files in the directory path
    - .npz files that do not have the corresponding image anymore
    """
    files = os.listdir(tmp_path)
    for f in files:
        _logger.info("File: {} - file[:-4] - {}".format(f, f[:-4]))
        if re.match(TMP_RAW_FNAME_RE_NPZ, f) and not f[:-4] in files:
            _logger.info("Match !")
            os.remove(path.join(tmp_path, f))


### CAMERA LENS CALIBRATION


class BoardDetectorDaemon(Thread):
    """Processes images of chessboards to calibrate the lens used to take the pictures."""

    def __init__(
        self,
        output_calib,
        image_size=LEGACY_STILL_RES,
        procs=1,
        stateChangeCallback=None,
        runCalibrationAsap=False,
        event_bus=None,
        rawImgLock=None,
        state=None,
        factory=False,
    ):
        self._logger = mrb_logger(__name__, lvl=5)
        # runCalibrationAsap : run the lens calibration when we have enough pictures ready
        self.event_bus = event_bus
        self.rawImgLock = rawImgLock

        # State of the detection & calibration
        if state is None:
            self.state = CalibrationState(
                changeCallback=stateChangeCallback,
                npzPath=output_calib,
                rawImgLock=rawImgLock,
            )
        else:
            self.state = state
        self.factory_mode = factory
        self.output_file = output_calib

        # Arrays to store object points and image points from all the images.
        self.objPoints = {}  # 3d point in real world space
        self.imgPoints = {}  # 2d points in image plane.
        self.image_size = image_size

        # processor load
        self.procs = Value("i", 1)

        # Queues for I/O with the process
        # self.inputFiles = Queue()
        self.stopQueue = Queue()
        self.outputFiles = Queue()
        self.tasks = []
        self.images = []

        # Locks
        self._started = Event()
        self._started.clear()
        self.waiting = Event()
        self._stop = Event()
        self._stop.clear()
        self._terminate = Event()
        self._terminate.clear()
        self._pause = Event()
        self._pause.clear()
        self._startWhenIdle = Event()
        if not runCalibrationAsap:
            self._startWhenIdle.clear()
        else:
            self._startWhenIdle.set()
        self.path_inc = 0

        # img_path: process - processes trying to detect a chessboard
        self.runningProcs = {}
        Thread.__init__(self, name=self.__class__.__name__)

        # self.daemon = False
        # catch SIGTERM used by Process.terminate()
        # signal.signal(signal.SIGTERM, signal.SIG_IGN) #self.stopAsap)
        # signal.signal(signal.SIGINT, signal.SIG_IGN) #self.stopAsap)

    def stop(self, signum=signal.SIGTERM, frame=None):
        self._logger.debug("Stopping")
        self._stop.set()

    def stopAsap(self, signum=signal.SIGTERM, frame=None):
        if self.is_alive():
            for path, proc in self.runningProcs.items():
                self._logger.debug("Killing process %s for image: %s", proc, path)
                os.kill(proc.pid, signal.SIGKILL)
            self._logger.info("Terminating board detector")
            self._terminate.set()
            self._stop.set()
        self._logger.debug("Not alive, no need to stop.")

    def start(self):
        self._logger.debug("Starting board detector")
        self._started.set()
        Thread.start(self)

    @property
    def started(self):
        return self._started.is_set()

    def pause(self):
        self._logger.debug("Pausing")
        self._pause.set()

    @property
    def stopping(self):
        return self._stop.is_set() or self._terminate.is_set()

    def add(
        self,
        image,
        chessboardSize=(CB_ROWS, CB_COLS),
        state=STATE_PENDING_CAMERA,
        index=None,
        **kw
    ):  # , rough_location=None, remote=None):
        self.state.add(
            image, chessboardSize, state=state, index=index or self.path_inc, **kw
        )
        self.path_inc += 1

    def load_dir(self, path, chessboardSize=(CB_ROWS, CB_COLS)):
        import re

        dirlist = os.listdir(path)
        found = False
        for fname in dirlist:
            if re.match(TMP_RAW_FNAME_RE, fname):
                found = True
                fullpath = os.path.join(path, fname)
                index = int(fname[slice(*re.search("[0-9]+", fname).span())])
                if self.path_inc <= index:
                    self.path_inc = index + 1
                self.add(fullpath, chessboardSize, STATE_QUEUED, index)
        return found

    def remove(self, path):
        self._logger.info("Removing picture %s" % path)
        if path in self.runningProcs.keys():
            self._logger.debug("Killing process for path %s" % path)
            os.kill(self.runningProcs[path].pid, signal.SIGKILL)
            # termination might cause the pipe to break if it is in use by the process
            self._logger.debug("Sent kill command for path %s" % path)
            self.runningProcs[path].join()
            self._logger.debug("Joined process for path %s" % path)
            try:
                self.runningProcs.pop(path)
            except KeyError:
                self._logger.debug(
                    "Unexpected KeyError %s not in runningProcs - %s",
                    path,
                    self.runningProcs.keys(),
                )
        self.state.remove(path)
        if self.idle:
            self.fire_event(MrBeamEvents.LENS_CALIB_IDLE)

    def __len__(self):
        return len(self.state)

    def __getitem__(self, item):
        return self.state[item]

    def fire_event(self, *args, **kw):
        if self.event_bus is not None:
            self.event_bus.fire(*args, **kw)

    def next_tmp_img_name(self):
        return TMP_RAW_FNAME.format(self.path_inc)

    @property
    def startCalibrationWhenIdle(self):
        return self._startWhenIdle.is_set()

    @startCalibrationWhenIdle.setter
    def startCalibrationWhenIdle(self, value):
        if value:
            self._logger.debug("Start calibration when idle set.")
            self._startWhenIdle.set()
        else:
            self._logger.debug("Start calibration when idle cleared.")
            self._startWhenIdle.clear()

    @property
    def detectedBoards(self):
        # return len(list(filter(lambda x: x.ready() and x.get()[1] is not None, self.tasks)))
        return len(
            list(filter(lambda x: x["state"] == STATE_SUCCESS, self.state.values()))
        )

    @property
    def idle(self):
        return (
            all(
                pic["state"] in [STATE_FAIL, STATE_SUCCESS, STATE_IGNORED]
                for pic in self.state.values()
            )
            and self.state.lensCalibration["state"] != STATE_PROCESSING
        )

    def scaleProcessors(self, number):
        self.procs.value = number
        self._logger.info("Changing to %s simultaneous processes", self.procs.value)

    @get_thread(name="saveCalibration", daemon=True)
    def saveCalibration(self, path=None):
        if self.state.calibrationRunning():
            self._logger.warning("Won't start lens calibration - already processing")
            return False
        self.state.calibrationBusy()
        self._logger.info("Start lens calibration.")
        # self.startCalibrationWhenIdle = False
        self.fire_event(MrBeamEvents.LENS_CALIB_RUNNING)
        self._logger.info("EVENT LENS CALIBRATION RUNNING")
        availableResults = self.state.getSuccesses()
        objPoints = []
        imgPoints = []
        for t in availableResults:
            # TODO add ignored paths list provided by user choice in Front End (could be STATE_IGNORED)
            objPoints.append(get_object_points(*t["board_size"]))
            imgPoints.append(t["found_pattern"])
        self._logger.debug(
            "len patterns : %i and %i " % (len(objPoints), len(imgPoints))
        )

        self.state.updateCalibration(
            *runLensCalibration(
                objPoints,
                imgPoints,
                self.state.imageSize,
            )
        )
        self.fire_event(MrBeamEvents.LENS_CALIB_DONE)
        self._logger.info("EVENT LENS CALIBRATION DONE")
        return True

    # @logtime()
    @logExceptions
    def run(self):
        # state, callback=None, chessboardSize=(CB_COLS, CB_ROWS), rough_location=None, remote=None):
        count = 0
        resultQueue = Queue()
        self._logger.debug("Pool started - %i procs" % MAX_PROCS)
        loopcount = 0
        while not self.stopping:
            loopcount += 1
            # self._logger.info("loopcount %i \r", loopcount)
            if loopcount % 100 == 0:
                self._logger.debug(
                    "Running... %s procs running, stopsignal : %s"
                    % (len(self.runningProcs), self._stop.is_set())
                )
            if (
                self.state.lensCalibration["state"] == STATE_PENDING
                and len(self) >= MIN_BOARDS_DETECTED
            ):
                self.state.refresh()
            else:
                self.state.refresh(
                    imgFoundCallback=self.fire_event,
                    args=(MrBeamEvents.RAW_IMAGE_TAKING_DONE,),
                )
            if self.idle:
                if loopcount % 100 == 0:
                    self._logger.debug(
                        "waiting to be restarted, lens calib : %s",
                        self.state.lensCalibration["state"],
                    )
                if (
                    self.state.lensCalibration["state"] == STATE_PENDING
                    and self.startCalibrationWhenIdle
                    and self.detectedBoards >= MIN_BOARDS_DETECTED
                ):
                    self.saveCalibration()
                elif len(self) >= MIN_BOARDS_DETECTED > self.detectedBoards:
                    if self.idle and self.detectedBoards < MIN_BOARDS_DETECTED:
                        self.fire_event(MrBeamEvents.LENS_CALIB_FAIL)
                    if loopcount % 20 == 0:
                        self._logger.debug(
                            "Only %i boards detected yet, %i necessary"
                            % (self.detectedBoards, MIN_BOARDS_DETECTED)
                        )
            # self.runningProcs = self.state.runningProcs() #len(list(filter(lambda x: not x.ready(), self.tasks)))
            if (
                len(self.runningProcs.keys()) < self.procs.value
                and self.state.getPending()
                and not self.stopping
            ):
                path = self.state.getPending()
                self.state.update(
                    path,
                    STATE_PROCESSING,
                    origin=FACTORY if self.factory_mode else USER,
                )
                count += 1
                self._logger.debug(
                    "%i / %i processes running, adding Process of image %s"
                    % (len(self.runningProcs.keys()), self.procs.value, path)
                )
                # self._logger.info("current state :\n%s" % self.state)
                board_size = self.state[path]["board_size"]
                args = (path, count, board_size, resultQueue)
                self.runningProcs[path] = Process(target=handleBoardPicture, args=args)
                self.runningProcs[path].start()
            while not resultQueue.empty():
                # Need to clean the queue before joining processes
                self._logger.info("Getting result from board detection.")
                r = resultQueue.get()
                self._logger.info("Got result from board detection.")
                try:
                    self.state.update(
                        origin=FACTORY if self.factory_mode else USER, **r
                    )
                except KeyError:
                    # can happen if a picture is removed from the state
                    # as the detection is about to finish
                    if self.idle:
                        self.fire_event(MrBeamEvents.LENS_CALIB_IDLE)
                    continue
                if r["state"] == STATE_SUCCESS:
                    self.state.lensCalibration["state"] = STATE_PENDING
                if self.idle:
                    self.fire_event(MrBeamEvents.LENS_CALIB_IDLE)

            for path, proc in self.runningProcs.items():
                if proc.exitcode is not None:
                    if proc.exitcode < 0 and not self._terminate.is_set():
                        self._logger.warning(
                            "Something went wrong with the process for path\n%s." % path
                        )
                    else:
                        self._logger.debug("Process exited for path %s." % path)
                    self.runningProcs.pop(path)
            if self._stop.wait(0.1):
                break
        self._logger.warning("Stop signal intercepted")
        resultQueue.close()
        for path, proc in self.runningProcs.items():
            self._logger.debug("Joining process %p for path: %s", proc, path)
            proc.join()
            self.runningProcs.pop(path)
        self.fire_event(MrBeamEvents.LENS_CALIB_EXIT)
        self._logger.info("Lens calibration exited")


def get_object_points(rows, cols):
    # prepare object points, like (0,0,0), (1,0,0), (2,0,0) ....,(6,5,0)
    objp = np.zeros((rows * cols, 3), np.float32)
    grid = np.mgrid[
        0 : rows * CB_SQUARE_SIZE : CB_SQUARE_SIZE,
        0 : cols * CB_SQUARE_SIZE : CB_SQUARE_SIZE,
    ].T  # .reshape(-1, 2)
    grid_copy = copy(grid)
    grid[:, :, 0], grid[:, :, 1] = grid_copy[:, :, 1], grid_copy[:, :, 0]
    objp[:, :2] = grid.reshape(-1, 2)
    return objp


# @logtime
# @logme(True)
@logExceptions
def handleBoardPicture(image, count, board_size, q_out=None):
    # logger = logging.getLogger()
    # if self._stop.is_set(): return
    # signal.signal(signal.SIGTERM, signal.SIG_DFL)
    if isinstance(image, _basestring):
        # self._logger.info("Detecting board in %s" % image)
        img = cv2.imread(image)
        if img is None:
            raise ValueError("Could not read image %s" % image)
        path = image
    elif isinstance(image, np.ndarray):
        # self._logger.info("Detecting board...")
        img = image
        path = TMP_PATH.format(count)
    else:
        raise ValueError(
            "Expected an image or a path to an image in inputFiles, not %s", repr(image)
        )

    logging.info("Finding board")
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    success, found_pattern = findBoard(gray, board_size)
    if success and found_pattern is not None:
        _pattern = found_pattern.reshape(-1, 2)

    center = None
    bbox = None
    try:
        if success:
            _c = np.average(_pattern, axis=0).tolist()
            center = tuple(_c)
        else:
            center = None
    except:
        center = None
        # TODO log this
    try:
        if success:
            bbox = (tuple(np.min(_pattern, axis=0)), tuple(np.max(_pattern, axis=0)))
        else:
            bbox = None
    except:
        bbox = None
        # TODO log this

    if success:
        drawnImg = cv2.drawChessboardCorners(
            img,
            board_size,
            found_pattern,
            success,
        )
        height, width, _ = drawnImg.shape
        differed_imwrite(path, drawnImg)
    else:
        height, width = None, None
    if q_out is not None:
        q_out.put(
            dict(
                path=path,
                state=STATE_SUCCESS if success else STATE_FAIL,
                board_size=board_size,
                found_pattern=found_pattern,
                board_center=center,
                board_bbox=bbox,
                width=width,
                height=height,
            )
        )
    if success:
        # if callback != None: callback(path, STATE_SUCCESS, board_size=board_size, found_pattern=found_pattern)
        return found_pattern
    else:
        # if callback != None: callback(path, STATE_FAIL, board_size=board_size)
        return None


# @logExceptions
def findBoard(image, pattern):
    """Finds the chessboard pattern of a given size in the image"""
    # TODO Add 8-way connected label filtering for small elements
    corners_found, corners = cv2.findChessboardCorners(
        image,
        patternSize=pattern,
        flags=cv2.CALIB_CB_ADAPTIVE_THRESH
        + cv2.CALIB_CB_NORMALIZE_IMAGE
        + cv2.CALIB_CB_FAST_CHECK,
    )
    if not corners_found:
        return corners_found, corners
    cornerSubPix = cv2.cornerSubPix(
        image,
        corners,
        (11, 11),
        (-1, -1),
        (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 30, 0.001),
    )
    return corners_found, cornerSubPix


@logExceptions
def runLensCalibration(objPoints, imgPoints, imgRes, q_out=None):
    """
    None the distortion of the lens given the detected chessboards.
    N.B. is supposed to run after the main process has been joined,
    but can also run in parallel (only uses the available results)
    """
    # signal.signal(signal.SIGTERM, signal.SIG_DFL)
    ret, mtx, dist, rvecs, tvecs = cv2.calibrateCamera(
        np.asarray(objPoints, dtype=np.float32),
        np.asarray(imgPoints, dtype=np.float32),
        imgRes,
        None,
        None,
    )
    # if callback: callback()
    if q_out:
        q_out.put(dict(ret=ret, mtx=mtx, dist=dist, rvecs=rvecs, tvecs=tvecs))
    if ret == 0:
        # TODO save to file here?

        return ret, mtx, dist, rvecs, tvecs
    else:
        return ret, mtx, dist, rvecs, tvecs


class CalibrationState(dict):
    def __init__(
        self,
        imageSize=LEGACY_STILL_RES,
        changeCallback=None,
        npzPath=None,
        rawImgLock=None,
        *args,
        **kw
    ):
        self._logger = mrb_logger(
            __name__ + "." + self.__class__.__name__, lvl=logging.DEBUG
        )
        self.changeCallback = changeCallback
        self.imageSize = imageSize
        self.output_file = npzPath
        self.output_file_ts = -1
        self.rawImgLock = rawImgLock
        self.setOutpuFileTimestamp()
        self.lock = RLock()
        if os.path.isfile(str(self.output_file)):
            self.loadCalibration()
        else:
            self.lensCalibration = dict(state=STATE_PENDING)
        dict.__init__(self, *args, **kw)

    def onChange(self):
        returnState = dict(
            imageSize=self.imageSize,
            lensCalibration=self.lensCalibration["state"],
            lensCalibrationNpzFileTs=self.output_file_ts,
            pictures=self.clean(),
        )
        self._logger.debug("State updated")
        if self.changeCallback != None:
            self.changeCallback(returnState)

    def add(
        self,
        path,
        board_size=(CB_ROWS, CB_COLS),
        state=STATE_PENDING_CAMERA,
        index=-1,
        extra_kw=None,
    ):
        with self.lock:
            self.lensCalibration["state"] = STATE_PENDING
            if path in self.keys():
                # was already added
                return
            if not isinstance(extra_kw, Mapping):
                extra_kw = {}
            default = dict(
                tm_added=time.time(),  # when picture was taken
                state=state,
                tm_proc=None,  # when processing started
                tm_end=None,  # when processing ended
                board_size=board_size,
                index=index,
                **extra_kw
            )
            dirlist = os.listdir(os.path.dirname(path))
            if os.path.basename(path) + ".npz" in dirlist:
                self._logger.debug("Found previous npz file for %s" % path)
                self[path] = dict_merge(default, CalibrationState._load(path))
            else:
                self[path] = default
        self.onChange()

    def remove(self, path):
        with self.lock:
            if self.pop(path, None):  # deletes without checking if the key exists
                for f in [path, path + ".npz"]:
                    if os.path.isfile(f):
                        try:
                            os.remove(f)
                        except OSError:
                            pass
        self.onChange()

    def ignore(self, path):
        with self.lock:
            self.update(path, STATE_IGNORED)

    def update(self, path, state, date=None, origin=USER, **kw):
        date = date or datetime.datetime.now()
        if state in STATES:
            with self.lock:
                _data = dict(state=state, date=date, origin=origin, **kw)
                _t = time.time()
                if state == STATE_SUCCESS or state == STATE_FAIL:
                    _data["tm_end"] = _t
                if state == STATE_PROCESSING:
                    _data["tm_proc"] = _t
                self[path].update(_data)
                if state == STATE_SUCCESS or state == STATE_FAIL:
                    self.save(path)
            self.onChange()
        else:
            raise ValueError("Not a valid state: {}", state)

    def updateCalibration(self, ret, mtx, dist, rvecs, tvecs):
        if ret != 0.0:
            with self.lock:
                self.lensCalibration.update(
                    dict(
                        state=STATE_SUCCESS,
                        err=ret,
                        mtx=mtx,
                        dist=dist,
                        rvecs=rvecs,
                        tvecs=tvecs,
                        date=datetime.datetime.now(),
                        # read with datetime.datetime.strptime(date, DATE_FORMAT)
                        resolution=self.imageSize,
                    )
                )
                self.saveCalibration()
        # elif state in STATES:
        # 	self.lastLensCalibrationState = state
        # else:
        # 	raise ValueError("Not a valid state: {}", state)
        else:
            with self.lock:
                self.lensCalibration.update(dict(state=STATE_FAIL))
        self.onChange()

    def calibrationBusy(self):
        with self.lock:
            self.lensCalibration.update(dict(state=STATE_PROCESSING))
        self.onChange()

    def calibrationRunning(self):
        ret = self.lensCalibration["state"] == STATE_PROCESSING
        self.onChange()
        return ret

    def refresh(self, imgFoundCallback=None, args=(), kwargs={}):
        """Check if a pending image was taken and saved by the camera"""
        # self._logger.debug("### REFRESH ###")
        changed = False
        for path, elm in self.items():
            with self.lock:
                if elm["state"] == STATE_PENDING_CAMERA and os.path.exists(path):
                    if self.rawImgLock is not None:
                        self.rawImgLock.acquire()
                        self.rawImgLock.release()
                    self.update(path, STATE_QUEUED)
                    changed = True
                    if imgFoundCallback is not None:
                        imgFoundCallback(*args, **kwargs)
                        self._logger.debug(
                            "CALLBACK : %s (*%s, **%s)"
                            % (imgFoundCallback.__name__, args, kwargs)
                        )
        if changed:
            self._logger.debug("something changed")
            self.onChange()
        return changed

    def getElmInState(self, state):
        with self.lock:
            return dict(filter(lambda _s: _s[1]["state"] == state, self.items()))

    def get_from_timestamp(self, timestamp):
        with self.lock:
            return dict(
                filter(
                    lambda _s: _s[1]["timestamp"].strftime(DATE_FORMAT) == timestamp,
                    self.items(),
                )
            )

    def getSuccesses(self):
        return self.getElmInState(STATE_SUCCESS).values()

    def getAll(self):
        return self

    def getPending(self):
        for path, imgState in self.items():
            if imgState["state"] == STATE_QUEUED:
                return path

    def getAllPending(self):
        return self.getElmInState(STATE_QUEUED).keys()

    def getProcessing(self):
        return list(filter(lambda _s: _s["state"] == STATE_PROCESSING, self.values()))

    def setOutpuFileTimestamp(self):
        ts = -1
        try:
            ts = int(os.path.getmtime(self.output_file))
        except:
            pass
        self.output_file_ts = ts
        return ts

    def save(self, path):
        """Save the results of the detected chessboard in given path"""
        with self.lock:
            np.savez(path + ".npz", **self[path])

    def load(self, path):
        """Load the results of the detected chessboard in given path"""
        with self.lock:
            self[path].update(CalibrationState._load(path))
        self.onChange()

    @staticmethod
    # @logme(False, True)
    def _load(path):
        return dict(np.load(path + ".npz", allow_pickle=True))

    def saveCalibration(self, path=None):
        """Load the calibration to path"""
        with self.lock:
            makedirs(path or self.output_file, parent=True)
            np.savez(path or self.output_file, **self.lensCalibration)
        self.setOutpuFileTimestamp()

    def loadCalibration(self, path=None):
        """Load the calibration from path (defaults to self.lensCalibration default path)"""
        with self.lock:
            self.lensCalibration = dict(
                np.load(path or self.output_file, allow_pickle=True)
            )
            if (
                "mtx" in self.lensCalibration.keys()
                and self.lensCalibration["mtx"] is not None
            ):
                self.lensCalibration["state"] = STATE_SUCCESS
            else:
                self.lensCalibration["state"] = STATE_FAIL
            if not "resolution" in self.lensCalibration.keys():
                self.lensCalibration["resolution"] = LEGACY_STILL_RES
        self.onChange()

    def rm_unused_images(self):
        for path, item in self.items():
            with self.lock:
                is_used = (
                    item["state"] == STATE_SUCCESS
                    and "date" in item
                    and "date" in self.lensCalibration
                    and datetime.datetime.strptime(
                        str(item["date"]), DATE_FORMAT
                    )  # str convert from np array
                    < datetime.datetime.strptime(
                        str(self.lensCalibration["date"]), DATE_FORMAT
                    )
                )
                if not is_used:
                    self.remove(path)
        self.onChange()

    def rm_from_origin(self, origin=USER):
        for path, item in self.items():
            if "origin" not in item or item["origin"] == origin:
                self.remove(path)
        self.onChange()

    def clean(self, maxlen=None, flatten=False):
        "Allows to be pickled"

        def _isClean(elm):
            return type(elm) in [basestring, str, int, float, bool]

        def make_clean(elm):
            if isinstance(elm, float) or type(elm) in [
                np.float32,
                np.float64,
                np.float16,
                np.double,
            ]:
                return float(elm)
            if isinstance(elm, int) or type(elm) in [
                np.int8,
                np.int16,
                np.int32,
                np.uint8,
                np.uint16,
                np.uint32,
            ]:
                return int(elm)
            if isinstance(elm, np.ndarray) and (
                maxlen is None or len(elm.flat) < maxlen
            ):
                if flatten:
                    return list(elm.flat)
                else:
                    return elm.tolist()
            elif isinstance(elm, datetime.datetime):
                return elm.strftime(DATE_FORMAT)
            else:
                return None

        def _clean(d):
            if isinstance(d, Mapping):
                ret = {}
                for k, v in d.items():
                    res = _clean(v)
                    # if res is not None: ret[k]=res
                    ret[k] = res
                return ret
            elif type(d) in [list, tuple]:
                ret = []
                for elm in d:
                    res = _clean(elm)
                    # if res is not None:
                    ret.append(res)
                return type(d)(ret)
            else:
                if _isClean(d):
                    return d
                else:
                    return make_clean(d)

        return _clean(self)

    def analytics_friendly(self):

        return self.clean(maxlen=6, flatten=True)


if __name__ == "__main__":
    import argparse, textwrap

    parser = argparse.ArgumentParser(
        description="Detect the markers in the pictures provided or from the camera",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=textwrap.dedent(
            """\
	Find the chessboards in the .jpg pictures contained in given path and
	calculate the lens distortion from given chessboards.

	"""
        ),
    )
    # parser.add_argument('outfolder', nargs='?',# type=argparse.FileType('w'),
    #                     default='markers_out')
    #
    parser.add_argument("out_file", metavar="OUT")
    parser.add_argument("images", metavar="IMG", nargs="+")

    args = parser.parse_
    b = BoardDetectorDaemon(args.out_file, runCalibrationAsap=True)
    for path in args.images:
        b.add(path)
    # Detect boards
    if not b.is_alive():
        b.start()
    else:
        b.waiting.clear()

    # Start calibration
    b.startCalibrationWhenIdle = True
    b.scaleProcessors(4)
