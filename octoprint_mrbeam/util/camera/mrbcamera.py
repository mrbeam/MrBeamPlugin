from itertools import chain

import picamera # The official picamera package
import time
import threading
import numpy as np
import cv2
from octoprint_mrbeam.util.camera import getRois, MrbPicWorker
from octoprint_mrbeam.util.camera import BRIGHTNESS_TOLERANCE
from multiprocessing import Pool
import octoprint_mrbeam.util.camera

class LoopThread(threading.Thread):

	def __init__(self, target, stopFlag, *args, **kwargs):
		self.running = threading.Event()
		self.stopFlag = stopFlag

		super(LoopThread, self).__init__(target=target, *args, **kwargs)
		self.ret = None

	def run(self):
		self.stopFlag.unset()
		self.running.set()
		while not self.stopFlag.isSet():
			self.ret = self.target(*self.__args, **self.__kwargs)
			self.running.unset()
			self.running.wait()


class MrbCamera(picamera.Picamera):
	# TODO do stuff here, like the calibration algo
	def __init__(self, stopEvent=None, *args, **kwargs):
		now = time.time()
		# TODO set sensor mode and framerate etc...
		super(MrbCamera, self).__init__(*args, **kwargs)
		self.camera.vflip = True
		self.camera.hflip = True
		self.camera.awb_mode = 'auto'
		self.stopEvent = stopEvent or threading.Event() # creates an unset event if not given
		if not self.image_correction_enabled:
			# self.camera.brightness = 70
			self.camera.color_effects = (128, 128)
		self.camera.start_preview()
		self._logger.debug("_prepare_cam() prepared in %ss", time.time() - now)
		self.picReady = threading.Event()
		self.busy = threading.Event()
		self.worker = MrbPicWorker(maxSize=2)
		self.captureLoop = LoopThread(target=self.capture, stopFlag=stopEvent, args=(self.worker,))
		# TODO load the default settings

	def apply_best_shutter_speed(self, shutterSpeedMultDelta=2, shutterSpeedDeltas=None):
		"""
		Applies to the camera the best shutter speed to detect all the markers
		:param outputs: path to save merged picture. If None : Does not merge and save
		:type outputs: None or str
		:param fpsAvgDelta:
		:param shutterSpeedDeltas:
		:return:
		"""
		self.framerate = 4
		self.sensor_mode = 2
		self.iso = 100
		self.exposure_mode = 'off'
		# Capture at the given cam fps and resolution

		# Take 3 captures
		autoShutterSpeed = self.exposure_speed
		lastDeltas = [1]
		if shutterSpeedDeltas is None: # Creates default behavior
			# construct fpsDeltas from fpsAvgDelta
			# Go for 3 pics around the given average
			shutterSpeedDeltas = [shutterSpeedMultDelta ** i for i in [-2, 1, ]]  # [self.framerate + i * fpsAvgDelta for i in range(-1, 2)]

		# Always take the first picture with the auto calibrated mode
		for i, img in enumerate(self.capture_continuous(self.worker, format='jpeg',
														quality=100, use_video_port=True)):
			print("sensor : ", self.sensor_mode, " iso : ", self.iso,
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

	def async_capture(self, *args, **kw):
		# TODO asynchronously produce img, return None when done
		if not self.captureLoop.isAlive():
			self.captureLoop.start()
		else:
			self.captureLoop.running.set() # Asks the loop to continue running, see LoopThread

	def wait(self):
		while self.captureLoop.running.isSet():
			# TODO return something special to know it has been killed
			if self.stopEvent.isSet(): return
			time.sleep(.2)
		return

	def lastPic(self):
		return self.worker.images[-1]