import time
import threading
import os
import shutil
import logging
from os.path import isfile

# don't crash on a dev computer where you can't install picamera
try:
	from picamera import PiCamera
	PICAMERA_AVAILABLE = True
except Exception as e:
	PICAMERA_AVAILABLE = False
	logging.getLogger("octoprint.plugins.mrbeam.iobeam.lidhandler").warn(
		"Could not import module 'picamera'. Disabling camera integration. (%s: %s)", e.__class__.__name__, e)
try:
	import mb_picture_preparation as mb_pic
except ImportError as e:
	PICAMERA_AVAILABLE = False
	logging.getLogger("octoprint.plugins.mrbeam.iobeam.lidhandler").warn(
		"Could not import module 'mb_picture_preparation'. Disabling camera integration. (%s: %s)", e.__class__.__name__, e)

from octoprint_mrbeam.iobeam.iobeam_handler import IoBeamEvents
from octoprint.events import Events as OctoPrintEvents
from octoprint_mrbeam.mrb_logger import mrb_logger

# singleton
_instance = None

def lidHandler(plugin):
	global _instance
	if _instance is None:
		_instance = LidHandler(plugin._event_bus,
							   plugin._plugin_manager)
	return _instance


# This guy handles lid Events
class LidHandler(object):
	def __init__(self, event_bus, plugin_manager):
		self._event_bus = event_bus
		self._settings = _mrbeam_plugin_implementation._settings
		self._plugin_manager = plugin_manager
		self._logger = mrb_logger("octoprint.plugins.mrbeam.iobeam.lidhandler")

		self.lidClosed = True
		self.camEnabled = self._settings.get(["cam", "enabled"])

		self._photo_creator = None
		self.image_correction_enabled = self._settings.get(['cam', 'image_correction_enabled'])
		if self.camEnabled:
			#imagePath = self._settings.getBaseFolder("uploads") + '/' + self._settings.get(["cam", "localFilePath"])
			imagePath = self._settings.getBaseFolder("uploads") + '/' + self._settings.get(["cam", "localFilePath"])
			self._photo_creator = PhotoCreator(self._plugin_manager, imagePath, self.image_correction_enabled)

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
			self._write_lid_analytics('LID_OPENED')
			self.lidClosed = False
			if self._photo_creator and self.camEnabled:
				if not self._photo_creator.active:
					self._start_photo_worker()
				else:
					self._logger.error("Another PhotoCreator thread is already active! Not starting a new one. Why am I here...??? "
					                   "Looks like LID_OPENED was triggered several times. Maybe iobeam is reconnecting constantly?")
			self._send_frontend_lid_state()
		elif event == IoBeamEvents.LID_CLOSED:
			self._logger.debug("onEvent() LID_CLOSED")
			self._write_lid_analytics('LID_CLOSED')
			self.lidClosed = True
			self._end_photo_worker()
			self._send_frontend_lid_state()
		elif event == OctoPrintEvents.CLIENT_OPENED:
			self._logger.debug("onEvent() CLIENT_OPENED sending client lidClosed: %s", self.lidClosed)
			self._send_frontend_lid_state()
		elif event == OctoPrintEvents.SHUTDOWN:
			self.shutdown()

	def shutdown(self):
		if self._photo_creator is not None:
			self._logger.debug("shutdown() stopping _photo_creator")
			self._end_photo_worker()

	def set_save_undistorted(self):
		from flask import make_response
		if self._photo_creator is not None:
			self._photo_creator.save_undistorted = self._settings.getBaseFolder("uploads") + '/' + self._settings.get(['cam','localUndistImage'])
			# todo make_response, so that it will be accepted in the .done() method in frontend
			return make_response('Should save Image soon, please wait.',200)
		else:
			return make_response('Error, no photocreator active, maybe you are developing and dont have a cam?',503)

	def _start_photo_worker(self):
		worker = threading.Thread(target=self._photo_creator.work,name='Photo-Worker')
		worker.daemon = True
		worker.start()


	def _end_photo_worker(self):
		if self._photo_creator:
			self._photo_creator.active = False

	def _send_frontend_lid_state(self, closed=None):
		lid_closed = closed if closed is not None else self.lidClosed
		self._plugin_manager.send_plugin_message("mrbeam", dict(lid_closed=lid_closed))

	def _write_lid_analytics(self, eventname):
		typename = 'lid_handler'
		# todo get lid version
		lid_version = 1
		_mrbeam_plugin_implementation._analytics_handler.write_event(typename,eventname,lid_version)


class PhotoCreator(object):
	def __init__(self, _plugin_manager, path, image_correction_enabled):
		self._plugin_manager = _plugin_manager
		self.final_image_path = path
		self.image_correction_enabled = image_correction_enabled
		self._settings = _mrbeam_plugin_implementation._settings
		self._laserCutterProfile = _mrbeam_plugin_implementation.laserCutterProfileManager.get_current_or_default()
		self.keepOriginals = self._settings.get(["cam", "keepOriginals"])
		self.active = False
		self.last_photo = 0
		self.badQualityPicCount = 0
		self.save_undistorted = None
		self.camera = None
		self._logger = logging.getLogger("octoprint.plugins.mrbeam.iobeam.lidhandler.PhotoCreator")

		self._init_filenames()
		self._createFolder_if_not_existing(self.final_image_path)
		self._createFolder_if_not_existing(self.tmp_img_raw)
		self._createFolder_if_not_existing(self.tmp_img_prepared)

	def work(self):
		try:
			self.active = True
			# todo find maximum of sleep in beginning that's not affecting UX
			time.sleep(0.8)

			if not PICAMERA_AVAILABLE:
				self._logger.warn("Camera disabled. Not all required modules could be loaded at startup. ")
				self.active = False
				return

			self._logger.debug("Taking picture now.")
			self._prepare_cam()
			while self.active and self.camera:
				if self.keepOriginals:
					self._init_filenames()
				self._capture()
				# check if still active...
				if self.active:
					# todo QUESTION: should the tmp_img_raw ever be showed in frontend?
					move_from = self.tmp_img_raw
					correction_result = dict(successful_correction=False)
					if self.image_correction_enabled:
						correction_result = self.correct_image(self.tmp_img_raw, self.tmp_img_prepared)
						self._write_cam_analytics(correction_result)
						# todo ANDY concept of what should happen with good and bad pictures etc....
						if correction_result['successful_correction']:
							move_from = self.tmp_img_prepared
							self._move_img(move_from, self.final_image_path)
							self.badQualityPicCount = 0
						else:
							errorID = correction_result['error'].split(':')[0]
							errorString = correction_result['error'].split(':')[1]
							if errorID == 'BAD_QUALITY':
								self.badQualityPicCount += 1
								self._logger.error(errorString+' Number of bad quality pics: {}'.format(self.badQualityPicCount))
								# todo get the maximum for badquality pics from settings
								if self.badQualityPicCount > 10:
									self._logger.error('Too many bad pics! Show bad image now.'.format(self.badQualityPicCount))
									self._move_img(move_from, self.final_image_path)
							elif errorID == 'NO_CALIBRATION':
								self._logger.error(errorString)
							elif errorID == 'NO_PICTURE_FOUND':
								self._logger.error(errorString)
							else: # Unknown error
								self._logger.error(errorID+errorString)
					self._send_frontend_picture_metadata(correction_result)
					time.sleep(1.5)

			self._logger.debug("PhotoCreator stopping...")
		except Exception as worker_exception:
			self._logger.exception("Exception in worker thread of PhotoCreator: {}".format(worker_exception.message))
		finally:
			self.active = False
			self._close_cam()

	def _send_frontend_picture_metadata(self, meta_data):
		self._plugin_manager.send_plugin_message("mrbeam", dict(beam_cam_new_image=meta_data))

	def _init_filenames(self):
		if self.keepOriginals:
			self.tmp_img_raw = self.final_image_path.replace('.jpg', "-tmp{}.jpg".format(time.time()))
			self.tmp_img_prepared = self.final_image_path.replace('.jpg', '-tmp2.jpg')
		else:
			self.tmp_img_raw = self.final_image_path.replace('.jpg', '-tmp.jpg')
			self.tmp_img_prepared = self.final_image_path.replace('.jpg', '-tmp2.jpg')

	def _prepare_cam(self):
		try:
			w = self._settings.get(["cam", "cam_img_width"])
			h = self._settings.get(["cam", "cam_img_height"])
			now = time.time()

			self.camera = PiCamera()
			# Check with Clemens about best default values here....
			self.camera.resolution = (w, h)
			self.camera.vflip = True
			self.camera.hflip = True
			self.camera.awb_mode = 'sunlight'
			if not self.image_correction_enabled:
				# self.camera.brightness = 70
				self.camera.color_effects = (128, 128)
			self.camera.start_preview()

			self._logger.debug("_prepare_cam() prepared in %ss", time.time() - now)
		except Exception as e:
			if e.__class__.__name__.startswith('PiCamera'):
				self._logger.error("PiCamera Error while preparing camera: %s: %s", e.__class__.__name__, e)
			else:
				self._logger.exception("Exception while preparing camera:")

	def _capture(self):
		try:
			now = time.time()
			# self.camera.capture(self.tmpPath, format='jpeg', resize=(1000, 800))
			self.camera.capture(self.tmp_img_raw, format='jpeg')

			self._logger.debug("_capture() captured picture in %ss", time.time() - now)
		except Exception as e:
			if e.__class__.__name__.startswith('PiCamera'):
				self._logger.error("PiCamera Error while capturing picture: %s: %s", e.__class__.__name__, e)
			else:
				self._logger.exception("Exception while taking picture from camera:")

	def _createFolder_if_not_existing(self, filename):
		try:
			path = os.path.dirname(filename)
			if not os.path.exists(path):
				os.makedirs(path)
				self._logger.debug("Created folder '%s' for camera images.", path)
		except:
			self._logger.exception("Exception while creating folder '%s' for camera images:", filename)

	def _move_img(self, src, dest):
		try:
			if os.path.exists(dest):
				os.remove(dest)
			shutil.move(src, dest)
		except Exception as e:
			self._logger.warn("exception while moving file: %s", e)

#		returncode = call(['mv', src, dest])
#		if returncode != 0:
#			self._logger.warn("_move_img() returncode is %s (sys call, should be 0)", returncode)

	def _close_cam(self):
		if self.camera is not None:
			self.camera.close()
			self._logger.debug("_close_cam() Camera closed ")

	def correct_image(self,pic_path_in,pic_path_out):
		"""
		:param pic_path_in:
		:param pic_path_out:
		:return: result dict with informations about picture preparation
		"""
		self._logger.debug("Starting with correction...")
		path_to_input_image = pic_path_in
		path_to_output_img = pic_path_out

		path_to_cam_params = self._settings.get(["cam", "lensCalibrationFile"])
		path_to_pic_settings = self._settings.get(["cam", "correctionSettingsFile"])
		path_to_last_markers = self._settings.get(["cam", "correctionTmpFile"])

		# todo implement high-precision feedback to frontend
		# todo implement pixel2MM setting in _laserCutterProfile (the magic number 2 below)
		outputImageWidth = int(2 * self._laserCutterProfile['volume']['width'])
		outputImageHeight = int(2 * self._laserCutterProfile['volume']['depth'])
		correction_result = mb_pic.prepareImage(path_to_input_image,
												path_to_output_img,
												path_to_cam_params,
												path_to_pic_settings,
												path_to_last_markers,
												size=(outputImageWidth,outputImageHeight),
												save_undistorted=self.save_undistorted,
												quality=75,
												debug_out=False)

		if correction_result['undistorted_saved']:
			self.save_undistorted = None
			self._logger.debug("Undistorted Image saved.")

		self._logger.info("Image correction result: {}".format(correction_result))
		# check if there was an error or not.
		if not correction_result['error']:
			correction_result['successful_correction'] = True
		else:
			correction_result['successful_correction'] = False

		return correction_result

	def _write_cam_analytics(self,cam_data):
		typename = 'cam'
		eventname = 'picture_preparation'
		# todo get cam version
		cam_version = 1
		_mrbeam_plugin_implementation._analytics_handler.write_event(typename,eventname,cam_version,payload=dict(cam_data=cam_data))
