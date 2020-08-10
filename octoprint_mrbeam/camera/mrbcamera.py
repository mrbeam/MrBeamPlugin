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

DEFAULT_SHUTTER_SPEED = int(1.5 * 10**5) # (microseconds)


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

	def _loop(self):
		self.running.set()
		while not self.stopFlag.isSet():
			try:
				self.ret = self.t(*self.__args, **self.__kw)
			except AttributeError as e:
				connectionErrMsg = "'NoneType' object has no attribute 'outputs'"
				if connectionErrMsg in str(e):
					self._logger.warning("Camera was not ready yet, it should restart by itself.")
				else:
					raise e
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

	def __init__(self, worker, stopEvent=None, shutter_speed=None, *args, **kwargs):
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
		self.captureLoop = LoopThread(
			target=self.capture,
			stopFlag=self.stopEvent,
			args=(self.worker,),
			kwargs={'format': 'jpeg'},)
		if shutter_speed is not None:
			self.shutter_speed = shutter_speed
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



	def anti_rolling_shutter_banding(self):
		### Experimental & unused ###
		"""mitigates the horizontal banding due to rolling shutter interaction with 50Hz/60Hz lights"""
		# TODO 60Hz countries
		self._logger.debug("Shutter speed : %i", self.shutter_speed)
		self._logger.debug("Exposure speed : %i", self.exposure_speed)
		autoShutterSpeed = self.exposure_speed
		# self.shutter_speed = 10

	def compensate_shutter_speed(self, img):
		from octoprint_mrbeam.camera import TARGET_AVG_ROI_BRIGHTNESS, BRIGHTNESS_TOLERANCE
		# self._logger.info(
		# 	"sensor : "+ str(self.sensor_mode)+
		# 	"\n iso : "+ str(self.iso)+
		# 	"\n gain : "+ str(self.analog_gain)+
		# 	"\n digital gain : "+ str(self.digital_gain)+
		# 	"\n brightness : "+ str(self.worker.avg_roi_brightness)+
		# 	"\n exposure_speed : "+ str(self.exposure_speed))
		min_bright = TARGET_AVG_ROI_BRIGHTNESS - BRIGHTNESS_TOLERANCE
		max_bright = TARGET_AVG_ROI_BRIGHTNESS + BRIGHTNESS_TOLERANCE
		brightness = self.worker.avg_roi_brightness
		_minb, _maxb = min(brightness.values()), max(brightness.values())
		compensate = 1
		self._logger.debug("Brightnesses: \nMin %s  Max %s\nCurrent %s" % (min_bright, max_bright, brightness))
		if  _minb < min_bright and _maxb > max_bright:
			self._logger.debug("Outside brightness bounds.")
			compensate = float(max_bright) / _maxb
		elif _minb >= min_bright and _maxb > max_bright:
			self._logger.debug("Brghtness over compensated")
			compensate = float(max_bright) / _maxb
		elif _minb < min_bright and _maxb <= max_bright:
			self._logger.debug("Brightness under compensated")
			compensate = float(min_bright) / _minb
		else:
			return
		# change the speed of compensation
		#     smoothe > 1 : aggressive, smoothe < 1 : slow
		#     /!\ Can add instability in the case of smoothe > 1
		# smoothe = 1.4/2
		# compensate = compensate ** smoothe
		if self.shutter_speed == 0 and self.exposure_speed > 0:
			self.shutter_speed = self.exposure_speed
		elif self.shutter_speed == 0:
			self.shutter_speed = DEFAULT_SHUTTER_SPEED
		self.shutter_speed = int(self.shutter_speed * compensate)

	def apply_best_shutter_speed(self):
		"""
		Use the corners of the image to do the auto-brightness adjustment.
		:param fpsAvgDelta:
		:param shutterSpeedDeltas:
		:return:
		"""
		self.start_preview()
		time.sleep(1)
		autoShutterSpeed = self.exposure_speed
		self.exposure_mode = 'off'
		self._logger.info("exposure_speed: %s" % self.exposure_speed)
		self.shutter_speed = autoShutterSpeed + 1

		# Always takes the first picture with the auto calibrated mode
		for i, img in enumerate(self.capture_continuous(self.worker, format='jpeg',
								quality=100, use_video_port=True)):
			if i % 2 == 1: continue # The values set are only applied for the following picture
			self.compensate_shutter_speed(img)
			if i > 13: break
