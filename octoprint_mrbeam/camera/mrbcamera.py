from itertools import chain

from octoprint_mrbeam.mrb_logger import mrb_logger
from octoprint_mrbeam.camera import Camera

try:
	from picamera import PiCamera
	import picamera
except OSError:
	# TODO Teja : uninstall picamera on your device :D
	raise ImportError("Could not import PiCamera")

import time
import threading
import logging

BRIGHTNESS_TOLERANCE = 80 # TODO Keep the brightness of the images tolerable


class LoopThread(threading.Thread):
	"""Loops over the target function instead of stopping"""

	def __init__(self, target, stopFlag, args=(), kwargs=None):
		"""
		Loops over the target function instead of stopping
		At the end of each loop, the self.running Event is cleared.
		To start a new loop, set the Event again ( loopThread.running.set() )

		:param target: target function
		:type target: Callable
		:param stopFlag: set this flag to break the loop
		:type stopFlag: threading.Event
		:param args: args passed to the target
		:type args: tuple, NoneType
		:param kwargs: kwargs passed to the target
		:type kwargs: Map, NoneType
		"""
		threading.Thread.__init__(self, target=self._loop,)
		# self.daemon = False
		self.running = threading.Event()
		self.running.clear()
		self.stopFlag = stopFlag
		self._logger = mrb_logger('octoprint.plugins.mrbeam.loopthread', lvl=logging.INFO)
		self.ret = None
		self.t = target
		self._logger.debug("Loopthread initialised")
		self.__args = args or ()
		self.__kw = kwargs or {}

	def run(self):
		try:
			threading.Thread.run(self)
		except Exception as e:
			self._logger.warning("mrbeam.loopthread : %s, %s", e.__class__.__name__, e)

	def _loop(self):
		self.running.set()
		while not self.stopFlag.isSet():
			try:
				self.ret = self.t(*self.__args, **self.__kw)
			except picamera.exc.PiCameraMMALError as e:
				self.running.clear()
				self.stopFlag.set()
				self._logger.exception(" %s, %s", e.__class__.__name__, e)
				return
			except Exception as e:
				self._logger.exception(" %s, %s", e.__class__.__name__, e)
			self.running.clear()
			self.running.wait()


class MrbCamera(PiCamera, Camera):
	# TODO do stuff here, like the calibration algo
	def __init__(self, worker, stopEvent=None, *args, **kwargs):
		"""
		Record pictures asynchronously in order to perform corrections
		simultaneously on the previous images.
		:param worker: The pictures are recorded into this
		:type worker: str, "writable", filename or class with a write function (see PiCamera.capture input)
		:param stopEvent: will exit gracefully when this Event is set
		:type stopEvent: threading.Event
		:param args: passed on to Picamera.__init__()
		:type args: tuple
		:param kwargs: passed on to Picamera.__init__()
		:type kwargs: Map
		"""
		# TODO set sensor mode and framerate etc...
		super(MrbCamera, self).__init__(*args, **kwargs)
		self.vflip = True
		self.hflip = True
		self.awb_mode = 'auto'
		self.stopEvent = stopEvent or threading.Event()  # creates an unset event if not given
		self.start_preview()
		self._logger = mrb_logger("octoprint.plugins.mrbeam.util.camera.mrbcamera", lvl=logging.INFO)
		self.busy = threading.Event()
		self.worker = worker
		self.captureLoop = LoopThread(
			target=self.capture,
			stopFlag=stopEvent,
			args=(self.worker,),
			kwargs={'format': 'jpeg'},)
		# TODO load the default settings

	def anti_rolling_shutter_banding(self):
		"""mitigates the horizontal banding due to rolling shutter interaction with 50Hz/60Hz lights"""
		# TODO 60Hz countries
		self._logger.debug("Shutter speed : %i", self.shutter_speed)
		self._logger.debug("Exposure speed : %i", self.exposure_speed)
		autoShutterSpeed = self.exposure_speed
		# self.shutter_speed = 10

	def apply_best_shutter_speed(self, shutterSpeedMultDelta=2, shutterSpeedDeltas=None):
		"""
		Applies to the camera the best shutter speed to detect all the markers
		:param fpsAvgDelta:
		:param shutterSpeedDeltas:
		:return:
		"""
		self.framerate = 4
		self.sensor_mode = 2
		self.iso = 100
		self.exposure_mode = 'off'
		# Capture at the given cam fps and resolution

		autoShutterSpeed = self.exposure_speed
		lastDeltas = [1]  # List of shutter speed offsets used (1 = 1 * normal shutter speed)
		# if shutterSpeedDeltas is None: # Creates default behavior
		# 	construct fpsDeltas from fpsAvgDelta
		# 	Go for 3 pics around the given average
		# 	shutterSpeedDeltas = [shutterSpeedMultDelta ** i for i in [-2, 1, ]]  # new shutter speed = shutterSpeedDelta * auto_shutter_speed

		# Always takes the first picture with the auto calibrated mode
		for i, img in enumerate(self.capture_continuous(self.worker, format='jpeg',
														quality=100, use_video_port=True)):
			self._logger.info(
				"sensor : ", self.sensor_mode, " iso : ", self.iso,
				" gain : ", self.analog_gain, " digital gain : ", self.digital_gain,
				" brightness : ", self.brightness, " exposure_speed : ", self.exposure_speed)
			# print(self.framerate_delta)
			# out.times.append(1 / (self.framerate + self.framerate_delta))
			# Then change the shutter speed

			# TODO is shutter speed setting for this img set at i - 1 or i - 2 ?

			# The MrbPicWorker already does the brightness measurements in the picture corners for us
			if len(self.worker.good_corner_bright[-1]) == 4:
				self.shutter_speed = int(autoShutterSpeed * lastDeltas[-1])
				return int(autoShutterSpeed * lastDeltas[-1])
			elif not self.worker.allCornersCovered():
				# TODO take darker or brighter pic
				for qd, brightnessDiff in self.worker.detectedBrightness[-1].items():
					if qd in chain(self.worker.good_corner_bright):
						# ignore if a previous picture managed to capture it well
						pass
					else:
						# add a new delta brightness
						delta = int(shutterSpeedMultDelta ** (brightnessDiff // BRIGHTNESS_TOLERANCE)) * lastDeltas[-1]
						if delta not in shutterSpeedDeltas or delta not in lastDeltas:
							shutterSpeedDeltas.append(delta)

			if len(shutterSpeedDeltas) == 0:
				print("This last image was good enough")
				break
			elif len(shutterSpeedDeltas) > 0:
				# remember the previous shutter speeds
				lastDeltas.append(int(autoShutterSpeed * shutterSpeedDeltas.pop()))
				# Set shutter speed for the next pic
				self.shutter_speed = int(autoShutterSpeed * lastDeltas[-1])
				# Need to wait for the shutter speed to take effect ??
				time.sleep(.5)  # self.shutter_speed / 10**6 * 10 # transition to next shutter speed

	def start(self):
		if not self.captureLoop.isAlive() and not self.stopEvent.isSet():
			self._logger.debug("capture loop not alive, starting now")
			self.captureLoop.start()
		else:
			self._logger.debug("Camera already running or stopEvent set")

	def async_capture(self, *args, **kw):
		"""
		Starts or signals the camera to start taking a new picture.
		The new picture can be retrieved with MrbCamera.lastPic()
		Wait for the picture to be taken with MrbCamera.wait()
		:param args:
		:type args:
		:param kw:
		:type kw:
		:return:
		:rtype:
		"""
		self._logger.debug("captureLoop running %s, stopFlag %s, shutter speed %s",
		                  self.captureLoop.running.isSet(),
		                  self.captureLoop.stopFlag.isSet(),
		                  self.shutter_speed)
		time.sleep(.1)
		self.captureLoop.running.set()  # Asks the loop to continue running, see LoopThread

	def wait(self):
		"""
		Wait for the camera to be done capturing a picture. Blocking call.
		It is ignored when stopEvent is set.
		"""
		while self.captureLoop.running.isSet() or self.worker.busy.isSet():
			if self.stopEvent.isSet(): return
			time.sleep(.02)
		return

	def lastPic(self):
		"""Returns the last picture taken"""
		return self.worker.latest
