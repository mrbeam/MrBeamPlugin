import logging
import time
import threading
import os
from subprocess import call
# import mb_picture_preparation

# don't crash on a dev computer where you can't install picamera
try:
	from picamera import PiCamera

	PICAMERA_AVAILABLE = True
except:
	PICAMERA_AVAILABLE = False
	logging.getLogger("octoprint.plugins.mrbeam.iobeam.lidhandler").warn(
		"Could not import module 'picamera'. Disabling camera integration.")

from octoprint_mrbeam.iobeam.iobeam_handler import IoBeamEvents
from octoprint.events import Events as OctoPrintEvents


# singleton
_instance = None

def lidHandler(plugin):
	global _instance
	if _instance is None:
		_instance = LidHandler(plugin._event_bus,
							   plugin._settings,
							   plugin._plugin_manager)
	return _instance


# This guy handles lid Events
class LidHandler(object):
	def __init__(self, event_bus, settings, plugin_manager):
		self._event_bus = event_bus
		self._settings = settings
		self._plugin_manager = plugin_manager
		self._logger = logging.getLogger("octoprint.plugins.mrbeam.iobeam.lidhandler")

		self.lidClosed = True;
		self.camEnabled = self._settings.get(["cam", "enabled"])

		self._photo_creator = None
		if self.camEnabled:
			imagePath = self._settings.getBaseFolder("uploads") + '/' + self._settings.get(["cam", "localFilePath"])
			self._photo_creator = PhotoCreator(imagePath)

		self._subscribe()

	def _subscribe(self):
		self._event_bus.subscribe(IoBeamEvents.LID_OPENED, self.onEvent)
		self._event_bus.subscribe(IoBeamEvents.LID_CLOSED, self.onEvent)
		self._event_bus.subscribe(OctoPrintEvents.CLIENT_OPENED, self.onEvent)
		self._event_bus.subscribe(OctoPrintEvents.SHUTDOWN, self.onEvent)

	def onEvent(self, event, payload):
		self._logger.debug("onEvent() event: %s, payload: %s", event, payload)
		if event == IoBeamEvents.LID_OPENED:
			self._logger.debug("onEvent() LID_OPENED")
			self.lidClosed = False;
			if self._photo_creator and self.camEnabled:
				self._start_photo_worker()
			self._send_frontend_lid_state()
		elif event == IoBeamEvents.LID_CLOSED:
			self._logger.debug("onEvent() LID_CLOSED")
			self.lidClosed = True;
			self._end_photo_worker()
			self._send_frontend_lid_state()
		elif event == OctoPrintEvents.CLIENT_OPENED:
			self._logger.debug("onEvent() CLIENT_OPENED sending client lidClosed:%s", self.lidClosed)
			self._send_frontend_lid_state()
			# apparently the socket connection isn't yet established.
			# Hack: wait a seconden and send it again, it works.
			threading.Timer(1, self._send_frontend_lid_state).start()
		elif event == OctoPrintEvents.SHUTDOWN:
			self._logger.debug("onEvent() SHUTDOWN stopping _photo_creator")
			self._photo_creator.active = False

	def _start_photo_worker(self):
		worker = threading.Thread(target=self._photo_creator.work)
		worker.daemon = True
		worker.start()

	def _end_photo_worker(self):
		if self._photo_creator:
			self._photo_creator.active = False

	def _send_frontend_lid_state(self, closed=None):
		lid_closed = closed if closed is not None else self.lidClosed
		self._plugin_manager.send_plugin_message("mrbeam", dict(lid_closed=lid_closed))


class PhotoCreator(object):
	def __init__(self, path):
		self.imagePath = path
		self.tmpPath = self.imagePath + ".tmp"
		self.tmpPath2 = self.imagePath + ".tmp2"
		self.active = True
		self.last_photo = 0
		self.camera = None
		self._logger = logging.getLogger("octoprint.plugins.mrbeam.iobeam.lidhandler.PhotoCreator")

		self._createFolder_if_not_existing(self.imagePath)
		self._createFolder_if_not_existing(self.tmpPath)
		self._createFolder_if_not_existing(self.tmpPath2)

	def work(self):
		try:
			self.active = True
			if not PICAMERA_AVAILABLE:
				self._logger.warn("PiCamera is not available, not able to capture pictures.")
				self.active = False
				return

			self._prepare_cam()
			while self.active and self.camera:
				self._capture()
				# check if still active...
				if self.active:
					# self.correct_image()
					self._move_tmp_image()
					time.sleep(1)

			self._close_cam()
		except:
			self._logger.exception("Exception in worker thread of PhotoCreator:")

	def _prepare_cam(self):
		try:
			now = time.time()

			self.camera = PiCamera()
			# Check with Clemens about best default values here....
			# self.camera.resolution = (2592, 1944)
			self.camera.resolution = (1024, 768)
			self.camera.vflip = True
			self.camera.hflip = True
			self.camera.brightness = 70
			self.camera.color_effects = (128, 128)
			self.camera.start_preview()

			self._logger.debug("_prepare_cam() prepared in %ss", time.time() - now)
		except:
			self._logger.exception("_prepare_cam() Exception while preparing camera:")

	def _capture(self):
		try:
			now = time.time()
			self.camera.capture(self.tmpPath, format='jpeg', resize=(1000, 800))
			self._logger.debug("_capture() captured picture in %ss", time.time() - now)
		except:
			self._logger.exception("Exception while taking picture from camera:")

	def _createFolder_if_not_existing(self, filename):
		try:
			path = os.path.dirname(filename)
			if not os.path.exists(path):
				os.makedirs(path)
				self._logger.debug("Created folder '%s' for camera images.", path)
		except:
			self.logger.exception("Exception while creating folder '%s' for camera images:", filename)


	def _move_tmp_image(self):
		returncode = call(['mv', self.tmpPath, self.imagePath])
		if returncode != 0:
			self._logger.warn("_move_tmp_image() returncode is %s (sys call, should be 0)", returncode)

	def _close_cam(self):
		if self.camera is not None:
			self.camera.close()
			self._logger.debug("_close_cam() Camera closed ")

	# draft
	def correct_image(self):
		self._logger.debug("correct_image()")
		path_to_input_image = self.tmpPath
		path_to_output_img = self.tmpPath2
		path_to_cam_params = '/home/pi/cam_calibration_output/cam_calibration_output.npz'
		path_to_markers_file = '/home/pi/cam_calibration_output/cam_markers.npz'

		is_high_precision = mb_picture_preparation.prepareImage(path_to_input_image,
																path_to_output_img,
																path_to_cam_params,
																path_to_markers_file)

		self._logger.debug("correct_image() is_high_precision:%s", is_high_precision)
