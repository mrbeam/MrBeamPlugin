from itertools import chain

from octoprint_mrbeam.mrb_logger import mrb_logger
from octoprint_mrbeam.camera import Camera
from . import exc
try:
	from picamera import PiCamera
	import picamera
except OSError:
	# TODO Teja : uninstall picamera on your device :D
	raise ImportError("Could not import PiCamera")

import time
import threading
import logging

DEFAULT_SHUTTER_SPEED = 2 * 10**5 # (microseconds)


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
		self.__args = args if args is not None else ()
		self.__kw = kwargs if kwargs is not None else {}

	# def run(self):
	# 	try:
	# 		threading.Thread.run(self)
	# 	except Exception as e:
	# 		self._logger.exception("mrbeam.loopthread : %s, %s", e.__class__.__name__, e)
	# 		raise

	def _loop(self):
		self.running.set()
		while not self.stopFlag.isSet():
			try:
				self.ret = self.t(*self.__args, **self.__kw)
			except Exception as e:
				self._logger.error("Handled exception in picamera: %s, %s", e.__class__.__name__, e)
				raise
			self.running.clear()
			while not self.stopFlag.isSet() and not self.running.isSet():
				self.running.wait(.2)

	def async_next(self, **kw):
		self._logger.debug("captureLoop running %s, stopFlag %s",
		                   self.running.isSet(),
		                   self.stopFlag.isSet())
		time.sleep(.1)

		self.__kw.update(kw)
		self.running.set()  # Asks the loop to continue running, see LoopThread


class MrbCamera(PiCamera, Camera):

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
		self.sensor_mode = 2
		self.vflip = True
		self.hflip = True
		self.iso = 150
		self.awb_mode = 'auto'
		self.meter_mode='matrix'
		# self.exposure_mode = ''
		self.stopEvent = stopEvent or threading.Event()  # creates an unset event if not given
		self.start_preview()
		self._logger = mrb_logger("octoprint.plugins.mrbeam.util.camera.mrbcamera", lvl=logging.INFO)
		self.busy = threading.Event()
		self.worker = worker
		# self.apply_best_shutter_speed()
		self.captureLoop = LoopThread(
			target=self.capture,
			stopFlag=self.stopEvent,
			args=(self.worker,),
			kwargs={'format': 'jpeg'},)
		# TODO load the default settings

	def start(self):
		if not self.captureLoop.isAlive() and not self.stopEvent.isSet():
			self._logger.debug("capture loop not alive, starting now")
			self.captureLoop.start()
		else:
			self._logger.debug("Camera already running or stopEvent set")

	def stop(self, timeout=None):
		if self.captureLoop.is_alive() and not self.stopEvent.isSet():
			self.stopEvent.set()
			self.captureLoop.running.clear()
			self.captureLoop.join(timeout)

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
		return self.captureLoop.async_next(*args, **kw)

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

	# def capture(self, *args, **kwargs):
	# 	"""
	# 	Take consecutive pictures in rapid succession.

	# 	If arguments are given as lists, will take as many pictures as
	# 	there are elements. Single values are applied for all pics, and
	# 	shorter lists will be cycled through.
	# 	"""
	# 	zip_args = []
	# 	max_len_arg = max(map(len, filter(lambda o: isinstance(o, Sized), chain(args, kwargs.values())))
	# 	for a in args:


	### Experimental & unused ###

	def anti_rolling_shutter_banding(self):
		"""mitigates the horizontal banding due to rolling shutter interaction with 50Hz/60Hz lights"""
		# TODO 60Hz countries
		self._logger.debug("Shutter speed : %i", self.shutter_speed)
		self._logger.debug("Exposure speed : %i", self.exposure_speed)
		autoShutterSpeed = self.exposure_speed
		# self.shutter_speed = 10

	def compensate_shutter_speed(self, img):
		from octoprint_mrbeam.camera import TARGET_AVG_ROI_BRIGHTNESS, BRIGHTNESS_TOLERANCE
		self._logger.info(
			"sensor : "+ str(self.sensor_mode)+
			"\n iso : "+ str(self.iso)+
			"\n gain : "+ str(self.analog_gain)+
			"\n digital gain : "+ str(self.digital_gain)+
			"\n brightness : "+ str(self.worker.avg_roi_brightness)+
			"\n exposure_speed : "+ str(self.exposure_speed))
		# print(self.framerate_delta)
		# out.times.append(1 / (self.framerate + self.framerate_delta))
		# Then change the shutter speed

		# TODO is shutter speed setting for this img set at i - 1 or i - 2 ?

		# The MrbPicWorker already does the brightness measurements in the picture corners for us
		min_bright = TARGET_AVG_ROI_BRIGHTNESS - BRIGHTNESS_TOLERANCE
		max_bright = TARGET_AVG_ROI_BRIGHTNESS + BRIGHTNESS_TOLERANCE
		# smoothe = 1.4/2
		brightness = self.worker.avg_roi_brightness
		_minb, _maxb = min(brightness.values()), max(brightness.values())
		compensate = 1
		self._logger.info("Brightnesses: \nMin %s  Max %s\nCurrent %s" % (min_bright, max_bright, brightness))
		if  _minb < min_bright and _maxb > max_bright:
			self._logger.info("Outside brightness bound.")
			compensate = float(max_bright) / _maxb
		elif _minb >= min_bright and _maxb > max_bright:
			self._logger.info("Over compensated")
			compensate = float(max_bright) / _maxb
		elif _minb < min_bright and _maxb <= max_bright:
			self._logger.info("Under compensated")
			compensate = float(min_bright) / _minb
		else:
			self._logger.info("Well compensated")
			return
		# compensate = compensate ** smoothe
		if self.shutter_speed == 0 and self.exposure_speed > 0:
			self.shutter_speed = self.exposure_speed
		elif self.shutter_speed == 0:
			self.shutter_speed = DEFAULT_SHUTTER_SPEED
		self._logger.info("Applying compensation alpha : %s to shutter speed: %s" % (compensate, self.shutter_speed))
		self.shutter_speed = int(self.shutter_speed * compensate)
		self._logger.info("result shutter speed: %s" % self.shutter_speed)

	def apply_best_shutter_speed(self, shutterSpeedMultDelta=2, shutterSpeedDeltas=None):
		"""
		Applies to the camera the best shutter speed to detect all the markers
		:param fpsAvgDelta:
		:param shutterSpeedDeltas:
		:return:
		"""
		self.start_preview()
		time.sleep(1)
		autoShutterSpeed = self.exposure_speed
		self.exposure_mode = 'off'
		# Capture at the given cam fps and resolution

		self._logger.info("exposure_speed: %s" % self.exposure_speed)
		self.shutter_speed = autoShutterSpeed + 1
		lastDeltas = [1]  # List of shutter speed offsets used (1 = 1 * normal shutter speed)
		# if shutterSpeedDeltas is None: # Creates default behavior
		# 	construct fpsDeltas from fpsAvgDelta
		# 	Go for 3 pics around the given average
		# 	shutterSpeedDeltas = [shutterSpeedMultDelta ** i for i in [-2, 1, ]]  # new shutter speed = shutterSpeedDelta * auto_shutter_speed

		# Always takes the first picture with the auto calibrated mode
		for i, img in enumerate(self.capture_continuous(self.worker, format='jpeg',
								quality=100, use_video_port=True)):
			if i % 2 == 1: continue # The values set are only applied for the following picture
			self.compensate_shutter_speed(img)
			# time.sleep(.4)
			if i > 13: break
			# elif not self.worker.allCornersCovered():
			# 	# TODO take darker or brighter pic
			# 	for qd, brightnessDiff in self.worker.detectedBrightness[-1].items():
			# 		if qd in chain(self.worker.good_corner_bright):
			# 			# ignore if a previous picture managed to capture it well
			# 			pass
			# 		else:
			# 			# add a new delta brightness
			# 			delta = int(shutterSpeedMultDelta ** (brightnessDiff // BRIGHTNESS_TOLERANCE)) * lastDeltas[-1]
			# 			if delta not in shutterSpeedDeltas or delta not in lastDeltas:
			# 				shutterSpeedDeltas.append(delta)

			# if len(shutterSpeedDeltas) == 0:
			# 	print("This last image was good enough")
			# 	break
			# elif len(shutterSpeedDeltas) > 0:
			# 	# remember the previous shutter speeds
			# 	lastDeltas.append(int(autoShutterSpeed * shutterSpeedDeltas.pop()))
			# 	# Set shutter speed for the next pic
			# 	self.shutter_speed = int(autoShutterSpeed * lastDeltas[-1])
			# 	# Need to wait for the shutter speed to take effect ??
			# 	time.sleep(.5)  # self.shutter_speed / 10**6 * 10 # transition to next shutter speed
