#!/usr/bin/env python3
from multiprocessing import Event, Pool, Process, Queue, Value
import logging
import cv2
import signal, os
import numpy as np
import time
from octoprint_mrbeam.util import logtime, logExceptions
import octoprint_mrbeam.camera as camera
import queue
from os import path

CB_ROWS = 5
CB_COLS = 6
CB_SQUARE_SIZE = 30  # mm

REFRESH_RATE_WAIT_CHECK = .2

# Chessboard size in mm
BOARD_SIZE_MM = np.array([220, 190])
MIN_BOARDS_DETECTED = 1
MAX_PROCS = 4

# Remote connection for calibration
# SSH_FILE = "/home/pi/.ssh/pi_id_rsa"
# REMOTE_CALIBRATION_FOLDER = "/home/calibrationfiles/"
# REMOTE_CALIBRATE_EXEC = path.join(REMOTE_CALIBRATION_FOLDER, "calibrate2.py")
# MY_HOSTNAME = "MrBeam-8ae9"

class BoardDetectorDaemon(Process):
	"""Processes images of chessboards to calibrate the lens used to take the pictures."""

	def __init__(self, output_calib, image_size=camera.LEGACY_STILL_RES, procs=1, callback=None, runCalibrationAsap=False):
		# runCalibrationAsap : run the lens calibration when we have enough pictures ready
		self._logger = logging.getLogger(__name__ + '.' + self.__class__.__name__)
		self._logger.setLevel(logging.DEBUG)
		self._logger.warning("Initiating the Board Detector Daemon")

		self.output_file = output_calib

		# Arrays to store object points and image points from all the images.
		self.objPoints = {}  # 3d point in real world space
		self.imgPoints = {}  # 2d points in image plane.
		self.image_size = image_size

		# processor load
		self.procs = Value('i', 2)

		# Queues for I/O with the process
		self.inputFiles = Queue()
		self.successfullFiles = Queue()
		self.failedFiles = Queue()
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
		self._startWhenIdle.clear()

		Process.__init__(self, target=self.processInputImages, name=self.__class__.__name__)

		# self.daemon = False
		# catch SIGTERM used by Process.terminate()
		signal.signal(signal.SIGTERM, self.stop)
		signal.signal(signal.SIGINT, self.stop)

	def stop(self, signum=signal.SIGTERM, frame=None):
		self._logger.info("Stopping")
		self._stop.set()

	def stopAsap(self, signum=signal.SIGTERM, frame=None):
		self._logger.warning("Terminating")
		self._terminate.set()
		self._stop.set()

	def start(self):
		self._logger.info("Starting")
		self._started.set()
		super(self.__class__, self).start()

	@property
	def started(self):
		return self._started.is_set()

	def pause(self):
		self._logger.info("Pausing")
		self._pause.set()

	@property
	def stopping(self):
		return self._stop.is_set() or self._terminate.is_set()

	def add(self, image, chessboardSize=(CB_ROWS, CB_COLS)): #, rough_location=None, remote=None):
		self.inputFiles.put(
			{'path': image,
			 'chessboardSize': chessboardSize
			})

	def __getitem__(self, item):
		if self.tasks[item].ready():
			return self.tasks[item].get()
		else: return False

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
		return len(list(filter(lambda x: x.ready() and x.get()[1] is not None, self.tasks)))

	def scaleProcessors(self, number):
		self.procs = number
		self._logger.info("Changing to %i simultaneous processes" % self.procs)

	# @logtime
	# @logExceptions
	def processInputImages(self):
		try:
			# state, callback=None, chessboardSize=(CB_COLS, CB_ROWS), rough_location=None, remote=None):
			self._logger.warning("Starting the Board Detector Daemon")
			if not self.inputFiles.empty():
				self._logger.warning("Inputfiles not empty")
				self.waiting.clear()
			count = 0
			self._logger.warning("Starting pool")
			pool = Pool(MAX_PROCS)
			self._logger.warning("Pool started - %i procs" % MAX_PROCS)
			while not self._stop.is_set():
				if self.waiting.is_set():
					self._logger.debug("waiting to be restarted")
					if self.startCalibrationWhenIdle and self.detectedBoards >= MIN_BOARDS_DETECTED:
						self._logger.warning("Start lens calibration.")
						self.startCalibrationWhenIdle = False
						if self.runLensCalibration():
							self._logger.warning("Lens calibration succesful")
						else:
							self._logger.error("Lens calibration failed")
					elif self.detectedBoards < MIN_BOARDS_DETECTED:
						self._logger.debug("Only %i boards detected yet, %i necessary" % (self.detectedBoards , MIN_BOARDS_DETECTED))

					if self._stop.is_set():
						self._logger.warning("STOP")
						break
					time.sleep(1)
					# set the wait flags to signal the process to restart processing incoming files

					continue
				if len(list(filter(lambda x: not x.ready(), self.tasks))) < self.procs:
					try :
						_input = self.inputFiles.get(timeout=.1)
						img, size = _input['path'], _input['chessboardSize']
						count += 1
					except queue.Empty:
						self._logger.warning("no image?")
						self.waiting.set()
						continue
					self._logger.warning("apply stuff async")
					self.images.append(img)
					self.tasks.append(pool.apply_async(handleBoardPicture,
									(img, count, size)))
				else:
					if self._stop.wait(.2):
						self._logger.warning("Stop signal intercepted")
						pool.close()
						break
					else:
						self._logger.debug("Dicking around ; procs set to : %i " % self.procs)
			self._logger.info("Pool joining")
			pool.close()
			if self._terminate.is_set():
				self._logger.warning("Pool terminating")
				pool.terminate()
			pool.join()
			self._logger.info("Pool exited")
		except Exception as e:
			self._logger.exception(str(e))

	def runLensCalibration(self, remote=None):
		"""
		None the distortion of the lens given the detected chessboards.
		N.B. is supposed to run after the main process has been joined,
		but can also run in parallel (only uses the available results)
		"""
		availableResults = list(filter(lambda _t: _t.ready(), self.tasks))
		if len(availableResults) == 0: return None
		objPoints = []
		imgPoints = []
		for t in availableResults:
			expected_pattern, found_pattern = t.get()
			if found_pattern is not None:
				# TODO add ignored paths list provided by user choice in Front End
				objPoints.append(get_object_points(*expected_pattern))
				imgPoints.append(found_pattern)

		if remote is not None:
			raise NotImplementedError
			# retval = call(["ssh", '-i', SSH_FILE, remote, "--", "python3", REMOTE_CALIBRATE_EXEC, "-f", MY_HOSTNAME , "SomeOtherInput" ])
			# if retval == 0:
			# 	remote_loc = remote + ":" + path.join(REMOTE_CALIBRATION_FOLDER, MY_HOSTNAME, "/lens_*.npz")
			# 	retval = call(["scp", '-i', SSH_FILE, remote_loc, "~/.octoprint/cam/"])

			# if retval != 0:
			# 	raise ValueError("Remote failed to calibrate my camera")
		else:
			ret, mtx, dist, rvecs, tvecs = cv2.calibrateCamera(objPoints,
									   imgPoints,
									   self.image_size,
									   None, None)
			if ret == 0:
				np.savez(self.output_file, mtx=mtx, dist=dist, rvecs=rvecs, tvecs=tvecs, ret=ret)
				self._logger.info("File with camera parameters has been saved to {}".format(self.output_file))
				return True
			else:
				return False


def get_object_points(rows, cols):
    # prepare object points, like (0,0,0), (1,0,0), (2,0,0) ....,(6,5,0)
    objp = np.zeros((rows * cols, 3), np.float32)
    objp[:, :2] = np.mgrid[0:cols * CB_SQUARE_SIZE:CB_SQUARE_SIZE,
                           0:rows * CB_SQUARE_SIZE:CB_SQUARE_SIZE].T.reshape(-1, 2)
    return objp

# @logtime
# @logExceptions
def handleBoardPicture(image, count, expected_pattern):
	# if self._stop.is_set(): return
	if isinstance(image, str):
		# self._logger.info("Detecting board in %s" % image)
		img = cv2.imread(image)
		if img is None:
			raise ValueError("Could not read image %s" % image)
		path = image
	elif isinstance(image, np.ndarray):
		# self._logger.info("Detecting board...")
		img = image
		path = "/tmp/chess_img_{}.jpg".format(count)
	else:
		raise ValueError("Expected an image or a path to an image in inputFiles.")

	# if remote is not None:
	# 	location = path.join(REMOTE_CALIBRATION_FOLDER, MY_HOSTNAME)
	# 	remote_loc = remote + ":" + location
	# 	call(["ssh", "-i", SSH_FILE, remote, "--", "mkdir", "-p", location])
	# 	call(["scp", '-i', SSH_FILE, state['image_path'], remote_loc])
	# 	retcode = call(["ssh", '-i', SSH_FILE, remote, "--", "python3", REMOTE_CALIBRATE_EXEC, path.join(location, path.basename(state['image_path']))])
	# 	if retcode == 0:
	# 		self.valid_images += 1
	# 		state['state'] = self.STATE_DONE_OK
	# 		state['valid'] = True
	# 	else:
	# 		state['state'] = self.STATE_DONE_FAIL
	# 		state['valid'] = False
	# 		self._logger.warning("Could not calibrate the file :O")
	# 	return

	gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
	success, found_pattern = findBoard(gray, expected_pattern)

	if success:
		# self.successfullFiles.put(path)
		return expected_pattern, found_pattern
	else:
		# self.failedFiles.put(path)
		return None, None

def findBoard(image, pattern):
	"""Finds the chessboard pattern of a given size in the image"""
	# TODO Add 8-way connected label filtering for small elements
	corners_found, corners = cv2.findChessboardCorners(
		image,
		patternSize=pattern,
		flags=cv2.CALIB_CB_ADAPTIVE_THRESH + cv2.CALIB_CB_NORMALIZE_IMAGE + cv2.CALIB_CB_FAST_CHECK)
	if not corners_found: return corners_found, corners
	cornerSubPix = cv2.cornerSubPix(image, corners, (11, 11), (-1, -1), (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 30, 0.001))
	return corners_found, cornerSubPix

def _save_results(path, found_pattern, expected_pattern):
	np.savez(path + ".npz", expected_pattern=expected_pattern, found_pattern=found_pattern)
