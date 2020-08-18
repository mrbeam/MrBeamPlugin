import copy
import json
import numpy as np
import time
import cv2
import base64
import threading
from threading import Event, Timer, Lock
import os
from os import path
import shutil
import logging
import re
import yaml


from flask.ext.babel import gettext
# from typing import Dict, Any, Union, Callable

from octoprint_mrbeam.mrbeam_events import MrBeamEvents

# don't crash on a dev computer where you can't install picamera
from octoprint_mrbeam.camera import gaussBlurDiff, QD_KEYS, PICAMERA_AVAILABLE, MrbPicWorker, LEGACY_STILL_RES, save_debug_img
from octoprint_mrbeam.camera import calibration as calibration
from octoprint_mrbeam.camera import exc as exc
if PICAMERA_AVAILABLE:
	from octoprint_mrbeam.camera.mrbcamera import MrbCamera
	from octoprint_mrbeam.camera.undistort import prepareImage, MAX_OBJ_HEIGHT, \
		CAMERA_HEIGHT, _getCamParams, _getPicSettings, DIST_KEY, MTX_KEY
from octoprint_mrbeam.camera.calibration import BoardDetectorDaemon, MIN_BOARDS_DETECTED
from octoprint_mrbeam.util import dict_merge, get_thread, makedirs
from octoprint_mrbeam.util.log import json_serialisor, logme

SIMILAR_PICS_BEFORE_UPSCALE = 1
LOW_QUALITY = 65 # low JPEG quality for compressing bigger pictures
OK_QUALITY = 75 # default JPEG quality served to the user
TOP_QUALITY = 90 # best compression quality we want to serve the user
DEFAULT_MM_TO_PX = 1 # How many pixels / mm is used for the output image

SIMILAR_PICS_BEFORE_REFRESH = 20
MAX_PIC_THREAD_RETRIES = 2


from octoprint_mrbeam.iobeam.iobeam_handler import IoBeamEvents
from octoprint.events import Events as OctoPrintEvents
from octoprint_mrbeam.mrb_logger import mrb_logger
import octoprint_mrbeam

# singleton
_instance = None


def lidHandler(plugin):
	global _instance
	if _instance is None:
		_instance = LidHandler(plugin)
	return _instance

# This guy handles lid Events
class LidHandler(object):
	def __init__(self, plugin):
		self._plugin = plugin
		self._event_bus = plugin._event_bus
		self._settings = plugin._settings
		self._printer = plugin._printer
		self._plugin_manager = plugin._plugin_manager
		self._laserCutterProfile = plugin.laserCutterProfileManager.get_current_or_default()
		self._logger = mrb_logger("octoprint.plugins.mrbeam.iobeam.lidhandler",
								  logging.INFO)
		self._lid_closed = True
		self._interlock_closed = True
		self._is_slicing = False
		self._client_opened = False
		self.lensCalibrationStarted = False
		self.force_taking_picture = Event()
		self.force_taking_picture.clear()
		self.board_calibration_number_pics_taken_in_session = 0
		self.saveRawImgThread = None

		if PICAMERA_AVAILABLE:
			self.imagePath = self._settings.getBaseFolder("uploads") + '/' + self._settings.get(["cam", "localFilePath"])
			makedirs(self.imagePath, parent=True)
			makedirs(self.debugFolder)
			self._photo_creator = PhotoCreator(self._plugin,
			                                   self._plugin_manager,
			                                   self.imagePath,
			                                   debug=False)
		else:
			self._photo_creator = None
			self.imagePath = None
		self.refresh_pic_settings = Event() # TODO placeholder for when we delete PhotoCreator

		self._analytics_handler = self._plugin.analytics_handler
		self._event_bus.subscribe(MrBeamEvents.MRB_PLUGIN_INITIALIZED, self._subscribe)

		# TODO carefull if photocreator is None
		self.boardDetectorDaemon = BoardDetectorDaemon(self._settings.get(["cam", "lensCalibrationFile"]),
							       runCalibrationAsap=True,
							       stateChangeCallback=self.updateFrontendCC,
		                                               event_bus = self._event_bus,
							       rawImgLock = self._photo_creator.rawLock)
		# self.removeAllTmpPictures() # clean up from the latest calibraton session

	def _subscribe(self, event, payload):
		self._event_bus.subscribe(IoBeamEvents.LID_OPENED, self.onEvent)
		self._event_bus.subscribe(IoBeamEvents.INTERLOCK_OPEN, self.onEvent)
		self._event_bus.subscribe(IoBeamEvents.INTERLOCK_CLOSED, self.onEvent)
		self._event_bus.subscribe(IoBeamEvents.LID_CLOSED, self.onEvent)
		self._event_bus.subscribe(IoBeamEvents.ONEBUTTON_RELEASED, self.onEvent)
		self._event_bus.subscribe(OctoPrintEvents.CLIENT_OPENED, self.onEvent)
		self._event_bus.subscribe(OctoPrintEvents.SHUTDOWN, self.onEvent)
		self._event_bus.subscribe(OctoPrintEvents.CLIENT_CLOSED,self.onEvent)
		self._event_bus.subscribe(OctoPrintEvents.SLICING_STARTED,self._onSlicingEvent)
		self._event_bus.subscribe(OctoPrintEvents.SLICING_DONE,self._onSlicingEvent)
		self._event_bus.subscribe(OctoPrintEvents.SLICING_FAILED,self._onSlicingEvent)
		self._event_bus.subscribe(OctoPrintEvents.SLICING_CANCELLED, self._onSlicingEvent)
		self._event_bus.subscribe(OctoPrintEvents.PRINTER_STATE_CHANGED,self._printerStateChanged)
		self._event_bus.subscribe(OctoPrintEvents.LENS_CALIB_START,self._startStopCamera)

	def onEvent(self, event, payload):
		self._logger.debug("onEvent() event: %s, payload: %s", event, payload)
		if event == IoBeamEvents.LID_OPENED:
			self._logger.debug("onEvent() LID_OPENED")
			self._lid_closed = False
			self._startStopCamera(event)
			self.send_mrb_state()
		if event == IoBeamEvents.INTERLOCK_OPEN:
			self._logger.debug("onEvent() INTERLOCK_OPEN")
			self._interlock_closed = False
		if event == IoBeamEvents.INTERLOCK_CLOSED:
			self._logger.debug("onEvent() INTERLOCK_CLOSED")
			self._interlock_closed = True
		elif event == IoBeamEvents.LID_CLOSED:
			self._logger.debug("onEvent() LID_CLOSED")
			self._lid_closed = True
			self._startStopCamera(event)
			self.send_mrb_state()
		elif event == OctoPrintEvents.CLIENT_OPENED:
			self._logger.debug("onEvent() CLIENT_OPENED sending client lidClosed: %s", self._lid_closed)
			self._client_opened = True
			self._startStopCamera(event)
		elif event == OctoPrintEvents.CLIENT_CLOSED:
			self._client_opened = False
			self._startStopCamera(event)
		elif event == OctoPrintEvents.SHUTDOWN:
			self.shutdown()
		elif event == IoBeamEvents.ONEBUTTON_RELEASED \
		     and self.lensCalibrationStarted \
		     and payload < 5.0:
			self._logger.info("onEvent() ONEBUTTON_RELEASED - payload : %s" % payload)
			if self.saveRawImgThread is not None and self.saveRawImgThread.is_alive():
				self._logger.info("save Img Thread still alive, ignoring request")
			else:
				self.saveRawImgThread = get_thread(daemon=True)(self.saveRawImg)()

	def is_lid_open(self):
		return not self._lid_closed

	def on_front_end_pic_received(self):
		self._logger.debug("Front End finished downloading the picture")
		if self._photo_creator is not None:
			self._photo_creator.send_pic_asap()

	def send_camera_image_to_analytics(self):
		if self._photo_creator:
			if self._plugin.is_dev_env():
				user='dev'
			else:
				user='user'
			self._photo_creator.send_last_img_to_analytics(
				force_upload=True, trigger=user, notify_user=True
			)

	def _printerStateChanged(self, event, payload):
		if payload['state_string'] == 'Operational':
			# TODO CHECK IF CLIENT IS CONNECTED FOR REAL, with PING METHOD OR SIMILAR
			self._client_opened = True
			self._startStopCamera(event)

	def _onSlicingEvent(self, event, payload):
		self._is_slicing = (event == OctoPrintEvents.SLICING_STARTED)
		self._startStopCamera(event)

	def _startStopCamera(self, event, payload=None):
		if self._photo_creator is not None:
			status = ' - event: {}\nclient_opened {}, is_slicing: {}\nlid_closed: {}, printer.is_locked(): {}, save_debug_images: {}'.format(
						event,
						self._client_opened,
						self._is_slicing,
						self._lid_closed,
						self._printer.is_locked() if self._printer else None,
						self._photo_creator.save_debug_images
					)
			if event in (IoBeamEvents.LID_CLOSED, OctoPrintEvents.SLICING_STARTED, OctoPrintEvents.CLIENT_CLOSED):
				self._logger.info('Camera stopping' + status)
				self._end_photo_worker()
			elif event in ["initial_calibration", MrBeamEvents.LENS_CALIB_START]:
				# See self._photo_creator.is_initial_calibration if it used from /plugin/mrbeam/calibration
				self._logger.info('Camera starting: initial_calibration. event: {}'.format(event))
				self._start_photo_worker()
			else:
				# TODO get the states from _printer or the global state, instead of having local state as well!
				if self._plugin.calibration_tool_mode or \
				   (self._client_opened and not self._is_slicing and not self._interlock_closed and not self._printer.is_locked()):
					self._logger.info('Camera starting' + status)
					self._start_photo_worker()
				else:
					self._logger.debug('Camera not supposed to start now.' + status)

	def shutdown(self):
		self._logger.info("Shutting down")
		self.boardDetectorDaemon.stopAsap()
		if self.boardDetectorDaemon.started:
			self._logger.info("shutdown() stopping board detector daemon")
			self.boardDetectorDaemon.join()
		if self._photo_creator is not None:
			self._logger.debug("shutdown() stopping _photo_creator")
			self._end_photo_worker()

	def _start_photo_worker(self):
		path_to_cam_params = self._settings.get(["cam", "lensCalibrationFile"])
		path_to_pic_settings = self._settings.get(["cam", "correctionSettingsFile"])

		mrb_volume = self._laserCutterProfile['volume']
		out_pic_size = mrb_volume['width'], mrb_volume['depth']
		self._logger.debug("Will send images with size %s", out_pic_size)

		# load cam_params from file
		cam_params = _getCamParams(path_to_cam_params)
		self._logger.debug('Loaded cam_params: {}'.format(cam_params))

		# load pic_settings json
		pic_settings = _getPicSettings(path_to_pic_settings)
		self._logger.debug('Loaded pic_settings: {}'.format(pic_settings))
		if not self._photo_creator.active:
			if self._photo_creator.stopping:
				self._photo_creator.restart(pic_settings=pic_settings, cam_params=cam_params, out_pic_size=out_pic_size)
			else:
				self._photo_creator.start(pic_settings=pic_settings, cam_params=cam_params, out_pic_size=out_pic_size)
		else:
			self._logger.debug("Another PhotoCreator thread is already active! Not starting a new one.")

	def _end_photo_worker(self):
		if self._photo_creator is not None:
			self._photo_creator.stop()
			self._photo_creator.save_debug_images = False
			self._photo_creator.undistorted_pic_path = None

	def restart_worker(self):
		raise NotImplementedError()
		# if self._photo_creator:
		# 	self._photo_creator.restart()

	def refresh_settings(self):
		# Let's the worker know to refresh the picture settings while running
		self._photo_creator.refresh_pic_settings.set()

	def compensate_for_obj_height(self, compensate=False):
		if self._photo_creator is not None:
			self._photo_creator.zoomed_out = compensate

	def onLensCalibrationStart(self):
		"""
		When pressing the button 'start lens calibration'
		Doesn't run the cv2 lens calibration at that point.
		"""
		self.getRawImg()
		self._photo_creator.is_initial_calibration = True
		self._start_photo_worker()
		if not self.lensCalibrationStarted and \
		   self.boardDetectorDaemon.load_dir(self.debugFolder):
			self._logger.info("Found pictures from previous session")
		self.lensCalibrationStarted = True
		self._event_bus.fire(MrBeamEvents.LENS_CALIB_START)
		self._logger.warning("EVENT LENS CALIBRATION STARTING")
		self._logger.warning("Lens calibration Started : %s" % self.lensCalibrationStarted)

	def getRawImg(self):
		# Sends the current state to the front end
		self.boardDetectorDaemon.state.onChange()

	def saveRawImg(self):
		# TODO debug/raw.jpg -> copy image over
		# TODO careful when deleting pic + setting new name -> hash
		if self._photo_creator and \
			self._photo_creator.active and \
			not self._photo_creator.stopping:
			# take a new picture and save to the specific path
			if len(self.boardDetectorDaemon) == MIN_BOARDS_DETECTED - 1:
				self._logger.info("Last picture to be taken")
				self._event_bus.fire(MrBeamEvents.RAW_IMG_TAKING_LAST)
			elif len(self.boardDetectorDaemon) >= MIN_BOARDS_DETECTED:
				# TODO Only fail for Waterott
				self._event_bus.fire(MrBeamEvents.RAW_IMG_TAKING_FAIL)
				self._logger.info("Ignoring this picture")
				return
			else:
				self._event_bus.fire(MrBeamEvents.RAW_IMAGE_TAKING_START)
			imgName = self.boardDetectorDaemon.next_tmp_img_name()
			self._photo_creator.saveRaw = imgName
			self._logger.warning("Saving new picture %s" % imgName)
			self.takeNewPic()
			imgPath = path.join(self.debugFolder, imgName)
			# Tell the boardDetector to listen for this file
			self.boardDetectorDaemon.add(imgPath)
			_s = self.boardDetectorDaemon.state
			# n = len(_s.getAllPending()) + len(_s.getSuccesses()) + len(_s.getProcessing()) # Does not include STATE_PENDING_CAMERA
			# if n >= MIN_BOARDS_DETECTED - 1: # not suitable for waterott
			if not self.boardDetectorDaemon.is_alive():
				self.boardDetectorDaemon.start()
			else:
				self.boardDetectorDaemon.waiting.clear()
			# if n >= MIN_BOARDS_DETECTED - 1:
			if len(self.boardDetectorDaemon) >= MIN_BOARDS_DETECTED:
				self.startLensCalibration()
				# TODO If possible, ask the led cli to chain two LED states
				t = Timer(1.2, self._event_bus.fire, args=(MrBeamEvents.LENS_CALIB_PROCESSING_BOARDS,))
				t.start()
		# except:
		# 	self._logger.exception("Exception in _saveRawImgThreaded(): ")
		# self._logger.info("ANDYTEST _saveRawImgThreaded() thread started")

	@logme(True)
	def delRawImg(self, path):
		try:
			os.remove(path)
		except OSError as e:
			self._logger.warning("Error trying to delete file: %s\n%s" % (path, e))
		finally:
			self.boardDetectorDaemon.remove(path)
		return self.boardDetectorDaemon.state.keys() # TODO necessary? Frontend update now happens via plugin message

	def removeAllTmpPictures(self):
		if os.path.isdir(self.debugFolder):
			for filename in os.listdir(self.debugFolder):
				if re.match(calibration.TMP_RAW_FNAME_RE, filename):
					my_path = path.join(self.debugFolder, filename)
					self._logger.debug("Removing tmp calibration file %s" % my_path)
					os.remove(my_path)

	def stopLensCalibration(self):
		self.boardDetectorDaemon.stopAsap()
		try:
			self.boardDetectorDaemon.join()
		except RuntimeError:
			self._logger.debug("Board Detector wasn't started or had already exited.")
		self.boardDetectorDaemon = BoardDetectorDaemon(self._settings.get(["cam", "lensCalibrationFile"]),
							       runCalibrationAsap=True,
							       stateChangeCallback=self.updateFrontendCC,
		                                               event_bus = self._event_bus)
		# self.removeAllTmpPictures()

	def ignoreCalibrationImage(self, path):
		myPath  = path.join(self.debugFolder, "debug", path)
		if myPath in self.boardDetectorDaemon.state.keys():
			self.boardDetectorDaemon.state.ignore(path)

	def takeNewPic(self):
		"""Forces agent to take a new picture."""
		if self.force_taking_picture.isSet():
			self._logger.info("Already analysing a picture, please wait")
			return False
		else:
			if self._photo_creator and \
			   self._photo_creator.active and \
			   not self._photo_creator.stopping:
				self._photo_creator.forceNewPic.set()
				self._logger.info("Force take new picture.")
				return True
			else:
				return False

	def startLensCalibration(self):
		if not self.boardDetectorDaemon.is_alive() and not self.boardDetectorDaemon.stopping:
			self._logger.info("Board detector not alive, starting now")
			self.boardDetectorDaemon.start()

		self.boardDetectorDaemon.startCalibrationWhenIdle = True
		self.boardDetectorDaemon.scaleProcessors(4)
		return True

	def updateFrontendCC(self, data):
		if data['lensCalibration'] == calibration.STATE_SUCCESS:
			self.refresh_settings()
		self._plugin_manager.send_plugin_message("mrbeam", dict(chessboardCalibrationState=data))

	def send_mrb_state(self):
		self._plugin_manager.send_plugin_message("mrbeam", dict(
			mrb_state=self._plugin.get_mrb_state()))


	@property
	def debugFolder(self):
		return path.join(path.dirname(self.imagePath),"debug")

class PhotoCreator(object):
	def __init__(self, _plugin, _plugin_manager, path, debug=False):
		self._plugin = _plugin
		self._plugin_manager = _plugin_manager
		self.final_image_path = path
		self._settings = _plugin._settings
		self._analytics_handler = _plugin.analytics_handler
		self.stopEvent = Event()
		self.stopEvent.set()
		self.activeFlag = Event()
		self.pause = Event()
		self.pause.clear()
		self._pic_available = Event()
		self._pic_available.clear()
		self.refresh_pic_settings = Event()
		self.zoomed_out = True
		self.last_photo = 0
		self.is_initial_calibration = False
		self.undistorted_pic_path = None
		self.save_debug_images = self._settings.get(['cam', 'saveCorrectionDebugImages'])
		self.undistorted_pic_path = self._settings.getBaseFolder("uploads") + '/' + self._settings.get(['cam', 'localUndistImage'])
		self.debug = debug
		self._front_ready = Event()
		self.forceNewPic = Event()
		self.last_correction_result = None
		self.worker = None
		self.saveRaw = True
		self.rawLock = Lock()
		self._flag_send_img_to_analytics = None
		self.cam = None
		self.analytics = None

		if debug:
			self._logger = mrb_logger("octoprint.plugins.mrbeam.iobeam.lidhandler.PhotoCreator", logging.DEBUG)
		else:
			self._logger = mrb_logger("octoprint.plugins.mrbeam.iobeam.lidhandler.PhotoCreator", logging.INFO)

		self.last_markers, self.last_shutter_speed = self.load_camera_settings()
		if self._settings.get(["cam", "keepOriginals"]):
			self.tmp_img_prepared = self.final_image_path.replace('.jpg', '-tmp2.jpg')
		else:
			self.tmp_img_prepared = self.final_image_path.replace('.jpg', '-tmp2.jpg')
		map(self._createFolder_if_not_existing, [self.final_image_path, self.tmp_img_prepared])

	@property
	def active(self):
		return not self.stopEvent.isSet()

	@active.setter
	def active(self, val):
		# @type val: bool
		if val: self.activeFlag.set()
		else:   self.activeFlag.clear()

	def start(self, pic_settings=None, cam_params=None, out_pic_size=None, blocking=True):
		if self.active and not self.stopping:
			self._logger.debug("PhotoCreator worker already running.")
			return
		elif self.active:
			self._logger.debug("worker shutting down but still active, waiting for it to stop before restart.")
			self.stop(blocking)
		self.stopEvent.clear()
		self.active = True
		self.worker = threading.Thread(target=self.work, name='Photo-Worker',
									   kwargs={'pic_settings': pic_settings,
											   'cam_params': cam_params,
											   'out_pic_size': out_pic_size})
		self.worker.daemon = True
		self.worker.start()

	def stop(self, blocking=True):
		if not self.active: self._logger.debug("Worker already stopped")
		self.stopEvent.set()
		if blocking and self.worker is not None and self.worker.is_alive():
			self.worker.join()
		self.active = False
		self._flag_send_img_to_analytics = None

	@property
	def stopping(self):
		return self.stopEvent.isSet()

	def restart(self, pic_settings=None, cam_params=None, out_pic_size=None, blocking=True):
		if self.active:
			self.stop(blocking)
		self.start(pic_settings=pic_settings, cam_params=cam_params, out_pic_size=out_pic_size, blocking=blocking)

	def work(self, pic_settings=None, cam_params=None, out_pic_size=None, recurse_nb=0):
		try:
			if self.is_initial_calibration:
				self.save_debug_images = True

			if not PICAMERA_AVAILABLE:
				self._logger.warn("Camera disabled. Not all required modules could be loaded at startup. ")
				self.stopEvent.set()
				return

			self._logger.debug("Starting the camera now.")
			camera_worker = MrbPicWorker(maxSize=2, debug=self.debug)
			with MrbCamera(camera_worker,
			               framerate=0.8,
			               shutter_speed=self.last_shutter_speed,
			               resolution=LEGACY_STILL_RES,  # TODO camera.DEFAULT_STILL_RES,
			               stopEvent=self.stopEvent,) as self.cam:
				try:
					self.serve_pictures(self.cam, pic_settings=pic_settings, cam_params=cam_params, out_pic_size=out_pic_size)
				except Exception:
					cam.close()
					raise
			if recurse_nb > 0:
				self._logger.info("Camera recovered")
				self._analytics_handler.add_camera_session_details(exc.msgForAnalytics(exc.CAM_CONNRECOVER))
		except exc.CameraConnectionException as e:
			self._logger.warning(" %s : %s" % (e.__class__.__name__, exc.msg(exc.CAM_CONN)),
			                       analytics=exc.CAM_CONN)
			if recurse_nb < MAX_PIC_THREAD_RETRIES:
				self._logger.info("Restarting work() after some sleep")
				self._plugin.user_notification_system.show_notifications(
					self._plugin.user_notification_system.get_notification(
						notification_id='warn_cam_conn_err',
						replay=True))
				self.stopEvent.clear()
				if not self.stopEvent.wait(2.0):
					self.work(recurse_nb=recurse_nb+1)
			else:
				self._logger.error(" %s : Recursive restart : too many times, displaying Error message.\n%s, %s" % (exc.msg(exc.CAM_CONN), e.__class__.__name__, e),
				                       analytics=exc.CAM_CONN)
				self._plugin.user_notification_system.show_notifications(
					self._plugin.user_notification_system.get_notification(
						notification_id='err_cam_conn_err',
						replay=True))
			return
		except Exception as e:
			if e.__class__.__name__.startswith('PiCamera'):
				self._logger.exception("PiCamera_Error_while_preparing_camera_%s_%s", e.__class__.__name__, e)
			else:
				self._logger.exception("Exception_while_preparing_camera_%s_%s", e.__class__.__name__, e)
		self.stopEvent.set()

	def serve_pictures(self, cam, pic_settings=None, cam_params=None, out_pic_size=None):
		"""
		Takes pictures, isolates the work area and serves it to the user at progressively better resolutions.
		After a certain number of similar pictures, Mr Beam serves a better quality pictures
		As of writing this doc, it will go through these settings:
		# 500 x 390, 75% JPEG quality ~ 60 kB
		1000 x 780, 65% JPEG quality ~ 45 kB
		# 1000 x 780, 75% JPEG quality ~ 200 kB
		2000 x 1560, 65% JPEG quality ~ 400 kB
		# 2000 x 1560, 75% JPEG quality ~ 600 kB
		# 2000 x 1560, 90% JPEG quality (lossless) ~ 1 MB

		Data used to compare the two algorithms is also retrieved and sent over at the end of this session

		:param cam: The camera that will record
		:type cam: MrbCamera
		:return: None
		:rtype: NoneType
		"""

		cam.start_preview()
		time.sleep(1.5) # camera warmup + prevent quick switch to pic capture

		session_details = blank_session_details()
		self._front_ready.set()
		try:
			cam.start()  # starts capture to the cam.worker
		except exc.CameraConnectionException as e:
			self._logger.exception(" %s, %s", e.__class__.__name__, e)
			cam.stop(1)
			raise
		# --- Decide on the picture quality to give to the user and whether the pic is different ---
		prev = None # previous image
		nb_consecutive_similar_pics = 0
		# Output image has a resolution based on the physical size of the workspace
		# JPEG compression quality of output image
		# Doubling the upscale factor will quadruple the image resolution while and
		# multiply file size by around 2.8 (depending on image quality)
		pic_qualities = [
			[1 * DEFAULT_MM_TO_PX, LOW_QUALITY],
			[4 * DEFAULT_MM_TO_PX, LOW_QUALITY]
		]
		pic_qual_index = 0
		# waste the first picture : doesn't matter how long we wait to warm up, the colors will be off.
		cam.wait()
		while self._plugin.lid_handler._lid_closed:
			# Wait for the lid to be completely open
			if self._plugin.lid_handler._interlock_closed or self.stopping:
				return
			time.sleep(.2)
		remember_markers = self._settings.get(['cam', 'remember_markers_across_sessions'])
		if not remember_markers:
			self._logger.debug("Camera mode: Accuracy > forgetting markers from last camera session.")
			self.last_markers = None

		# The lid didn't open during waiting time
		cam.async_capture()
		saveNext = False # Lens calibration : save the next picture instead of this one
		min_pix_amount = self._settings.get(['cam', 'markerRecognitionMinPixel'])
		pic_counter = 0
		while not self.stopping:
			while self.pause.isSet():
				time.sleep(.5)
			if self.refresh_pic_settings.isSet():
				self.refresh_pic_settings.clear()
				path_to_pic_settings = self._settings.get(["cam", "correctionSettingsFile"])
				path_to_lens_calib = self._settings.get(["cam", "lensCalibrationFile"])
				self._logger.debug("Refreshing picture settings from %s" % path_to_pic_settings)
				pic_settings = _getPicSettings(path_to_pic_settings)
				cam_params = _getCamParams(path_to_lens_calib)
				prev=None # Forces to take a new picture
			cam.wait()  # waits until the next picture is ready
			if self.stopping: break

			latest = cam.lastPic() # gets last picture given by cam.worker
			cam.async_capture()  # starts capture with new settings
			if latest is None:
				# The first picture will be empty, should wait for the 2nd one.
				self._logger.debug("The last picture is empty")
				continue
			if self.stopping: break  # check if still active...

			cam.compensate_shutter_speed(latest) # Change exposure if needed
			curr_shutter_speed = cam.exposure_speed
			curr_brightness = copy.deepcopy(cam.worker.avg_roi_brightness)

			if self.saveRaw:
				if isinstance(self.saveRaw, str) and not saveNext:
					saveNext = True
					rawSaved = False
				elif isinstance(self.saveRaw, str) and saveNext:
					# FIXME Not perfect. This is the case during the lens calibration where
					# a new raw picture is requested. Do the save during the next round.
					self.rawLock.acquire()
					if save_debug_img(
							latest,
							self.saveRaw,
							folder=path.join(path.dirname(self.final_image_path),"debug")):
						rawSaved = self.saveRaw
					else:
						rawSaved = False
					self.rawLock.release()
					saveNext = False
				else:
					self.rawLock.acquire()
					rawSaved = save_debug_img(latest,
									 "raw.jpg",
									 folder=path.join(path.dirname(self.final_image_path),"debug"))
					self.rawLock.release()

			# Compare previous image with the current one.
			if self.forceNewPic.isSet() or prev is None \
			   or gaussBlurDiff(latest, prev, resize=.5):
				self.forceNewPic.clear()
				# The 2 images are different, try to work on this one.
				prev = latest # no need to copy because latest should be immutable
				nb_consecutive_similar_pics = 0
				pic_qual_index = 0
				# TODO change the upscale factor depending on how fast the connection is
			else:
				# Picture too similar to the previous, discard or upscale it
				nb_consecutive_similar_pics += 1
				if nb_consecutive_similar_pics % SIMILAR_PICS_BEFORE_UPSCALE == 0 \
						and pic_qual_index < len(pic_qualities) - 1:
					# TODO don't upscale if the connection is too bad
					# TODO check connection through netconnectd ?
					# TODO use response from front-end
					pic_qual_index += 1
					prev = latest
				elif nb_consecutive_similar_pics % SIMILAR_PICS_BEFORE_REFRESH == 0 \
						and not self._front_ready.isSet():
					# Try to send a picture despite the client not responding / being ready
					prev = latest
					self._front_ready.set()
				else:
					time.sleep(.8) # Let the raspberry breathe a bit (prevent overheating)
					continue

			# Get the desired scale and quality of the picture to serve
			upscale_factor , quality = pic_qualities[pic_qual_index]
			scaled_output_size = tuple(int(upscale_factor * i) for i in out_pic_size)
			# --- Correct captured image ---
			self._logger.debug("Starting with correction...")
			if cam_params is not None:
				dist, mtx = cam_params[DIST_KEY], cam_params[MTX_KEY]
			else:
				dist, mtx = None, None
			color = {}
			marker_size = {}
			min_pix_amount = self._settings.get(['cam', 'markerRecognitionMinPixel'])
			# NOTE -- prepareImage is bloat, TODO spill content here
			saveLensCorrected = True
			workspaceCorners, self.last_markers, missed, err, analytics, savedPics = prepareImage(
				input_image=latest,
				path_to_output_image=self.tmp_img_prepared,
				pic_settings=pic_settings,
				cam_dist=dist,
				cam_matrix=mtx,
				last_markers=self.last_markers,
				size=scaled_output_size,
				quality=quality,
				zoomed_out=self.zoomed_out,
				debug_out=self.save_debug_images,  # self.save_debug_images,
				undistorted=saveLensCorrected,
				stopEvent=self.stopEvent,
				min_pix_amount=min_pix_amount,
				threads=4
			)
			if self.stopping: return False, None, None, None, None
			success = workspaceCorners is not None
			# Conform to the legacy result to be sent to frontend
			savedPics['raw'] = rawSaved
			correction_result = {
				'markers_found': list(filter(lambda q: q not in missed, QD_KEYS)),
				# {k: v.astype(int) for k, v in markers.items()},
				'markers_recognised': 4 - len(missed),
				'corners_calculated': None if workspaceCorners is None else list(workspaceCorners),
				# {k: v.astype(int) for k, v in workspaceCorners.items()},
				'markers_pos': {qd: list(pos) for qd, pos in self.last_markers.items()},
				'successful_correction': success,
				'undistorted_saved': True,
				'workspace_corner_ratio': float(MAX_OBJ_HEIGHT) / CAMERA_HEIGHT / 2,
				'avg_color': color,
				'marker_px_size': marker_size,
				'error': err,
				'available': savedPics
			}
			# revert to normal debug path
			if isinstance(self.saveRaw, str) and self.saveRaw == savedPics['raw']:
				self.saveRaw=True
			# Send result to fronted ASAP
			if success:
				self._ready_to_send_pic(correction_result)
			else:
				# Just tell front end that there was an error
				self._send_frontend_picture_metadata(correction_result)

			self.analytics = dict_merge(analytics, dict(
				{qd: {'brightness': val} for qd, val in curr_brightness.items()},
				avg_shutter_speed = curr_shutter_speed,
				success=success,
			))
			self._add_result_to_analytics(
				session_details,
				missed=missed,
				increment_pic=True,
				error=err,
				extra=self.analytics
			)

			# upload image to analytics
			pic_counter += 1
			if self._plugin.is_dev_env() \
			        and self._settings.get(['dev', 'automatic_camera_image_upload']) \
			        and (pic_counter <= 10 \
			             or pic_counter % 10 == 0):
				self.send_last_img_to_analytics(
					trigger='dev_auto', force_upload=(pic_counter%10==0)
				)
			self.save_camera_settings(markers=self.last_markers, shutter_speed=self.last_shutter_speed)

		self.last_shutter_speed = cam.shutter_speed
		cam.stop_preview()
		if session_details['num_pics'] > 0:
			session_details.update({
				'settings_min_marker_size': self._settings.get(['cam', 'markerRecognitionMinPixel']),
				'remember_markers_across_sessions': self._settings.get(['cam', 'remember_markers_across_sessions']),
			})
			self._analytics_handler.add_camera_session_details(session_details)
		self._logger.debug("PhotoCreator_stopping")

	# @logme(True)
	def _add_result_to_analytics(
		self,
		session_details,
		missed=[],
		colors={},
		marker_size={},
		increment_pic=False,
		colorspace='hsv',
		upload_speed=None,
		error=None,
		extra=None
	):
		if extra is None: extra={}
		def add_to_stat(pos, avg, std, mass):
			# gives a new avg value and approximate std when merging the new position value.
			# mass is the weight given to the previous avg and std.
			if avg is not None and std is not None:
				avg, std = np.asarray(avg), np.asarray(std)
				_new_avg = (mass * avg + pos) / (mass + 1)
				_new_std = np.sqrt((mass * std) ** 2 + (pos - _new_avg) ** 2) / (mass + 1)
			else:
				_new_avg = np.array(pos, dtype=float)
				_new_std = np.zeros(2, dtype=float)
			return _new_avg, _new_std

		# @logme(True, True)
		def updt(val_prev, val_new, func=np.average, **kw):
			# necessary to phrase it that way if val_prev is a numpy array
			if isinstance(val_prev, np.ndarray) or val_prev or val_prev == 0 :
				return func([val_prev, val_new], **kw)
			else:
				return copy.deepcopy(val_new)

		_s = session_details
		try:
			if increment_pic: _s['num_pics'] += 1
			tot_pics = _s['num_pics']
			for qd in QD_KEYS:
				_s_marker = _s['markers'][qd]
				if qd in self.last_markers.keys() \
				   and qd not in missed \
				   and self.last_markers[qd] is not None:
					_marker = np.asarray(self.last_markers[qd])
					# Position : Avg & Std Deviation
					_n_avg, _n_std = add_to_stat(
						_marker,
						_s_marker['avg_pos'],
						_s_marker['std_pos'],
						_s_marker['found']
					)
					_s_marker['avg_pos'] = _n_avg.tolist()
					_s_marker['std_pos'] = _n_std.tolist()
					_s_marker['found'] += 1
					if all(k in _s_marker.keys() for k in ['avg_hsv', 'pix_size']):
						# Color : Avg hue value
						_s_marker['avg_color'] = updt(_s_marker['avg_color'], extra[qd]['avg_hsv'], weights=[tot_pics, 1], axis=0)
						# Size of the marker (surface area in pixels)
						_s_marker['marker_px_size'] = updt(_s_marker['marker_px_size'], extra[qd]['pix_size'], weights=[tot_pics, 1])
				else:
					_s_marker['missed'] += 1

				# Brightness : Avg & Min, Max
				_s_marker['avg_brightness'] = updt(_s_marker['avg_brightness'], extra[qd]['brightness'], weights=[tot_pics, 1])
				_s_marker['min_brightness'] = updt(_s_marker['min_brightness'], extra[qd]['brightness'], func = np.min)
				_s_marker['max_brightness'] = updt(_s_marker['max_brightness'], extra[qd]['brightness'], func = np.max)
			if extra['success']:
				_s['num_success_pics'] += 1
			if error:
				error = error.replace(".","-").replace(",","-")
				if error in _s['errors']:
					_s['errors'][error] += 1
				else:
					_s['errors'][error] = 1
			_s['avg_shutter_speed'] = updt(_s['avg_shutter_speed'], extra['avg_shutter_speed'], weights=[tot_pics, 1])
			if len(missed) == 0:
				_s['num_all_markers_detected'] += 1
		except Exception as ex:
			self._logger.exception('Exception_in-_save__s_for_analytics-_{}'.format(ex))

	@get_thread(name='send_last_img_to_analytics',)
	def send_last_img_to_analytics(self, force_upload=False, trigger='user', notify_user=False):
		raw_path = os.path.join(os.path.dirname(self.final_image_path), 'debug/raw.jpg')
		latest = cv2.imread(raw_path)
		img_format = 'jpg'
		_, img = cv2.imencode('.{}'.format(img_format), latest, [int(cv2.IMWRITE_JPEG_QUALITY), 80])
		img = base64.b64encode(img)

		analytics_str = ''
		try:
			analytics_str = json.dumps(self.analytics, default=json_serialisor)
		except:
			self._logger.warning("_send_last_img_to_analytics_threaded() Can not convert analytics_data to json: %s", self.analytics)

		dist = ''
		path_to_cam_params = self._settings.get(["cam", "lensCalibrationFile"])
		try:
			with open(path_to_cam_params, 'r') as f:
				dist = base64.b64encode(f.read())
		except:
			self._logger.warning("_send_last_img_to_analytics_threaded() Can not read npz file: %s", path_to_cam_params)

		payload = {'img_base64': img,
					'img_type': img_format,
					'distortion_matrix_base64': dist,
					'trigger': trigger,
					'metadata': {
						'min_pix_amount': self._settings.get(['cam', 'markerRecognitionMinPixel']),
						'analytics': analytics_str,
						'trigger': trigger},
					}
		self._logger.debug("_send_last_img_to_analytics_threaded() trigger: %s, img_base64 len: %s, force_upload: %s, metadata: %s",
							trigger, len(img), force_upload, payload['metadata'])
		self._analytics_handler.add_camera_image(payload)
		if force_upload:
			self._analytics_handler.upload()

		if notify_user:
			self._plugin.user_notification_system.show_notifications(
				self._plugin.user_notification_system.get_notification(
					notification_id='msg_cam_image_analytics_sent'))

	def _ready_to_send_pic(self, correction_result, force=False):
		self.last_correction_result = correction_result
		self._pic_available.set()
		self.send_pic_asap(force=force)

	def send_pic_asap(self, force=False):
		if force or self._pic_available.isSet() and self._front_ready.isSet():
			# Both front and backend sould be ready to send/receive a new picture
			self._move_img(self.tmp_img_prepared, self.final_image_path)
			self._send_frontend_picture_metadata(self.last_correction_result)
			self._pic_available.clear()
			self._front_ready.clear()
		else:
			# Front end finished loading the picture
			self._front_ready.set()

	def _send_frontend_picture_metadata(self, meta_data):
		self._logger.debug("Sending results to front-end :\n%s" % json.dumps(dict(beam_cam_new_image=meta_data), default=json_serialisor))
		self._plugin_manager.send_plugin_message("mrbeam", dict(beam_cam_new_image=meta_data))

	def _createFolder_if_not_existing(self, filename):
		path = os.path.dirname(filename)
		if not os.path.exists(path):
			os.makedirs(path)
			self._logger.debug("Created folder '%s' for camera images.", path)

	def _move_img(self, src, dest):
		try:
			if os.path.exists(dest):
				os.remove(dest)
			shutil.move(src, dest)
		except Exception as e:
			self._logger.warn("exception_while_moving_file-_%s", e)

	def load_camera_settings(self, path='/home/pi/.octoprint/cam/last_session.yaml'):
		"""
		Loads the settings saved from the last session.
		The file is located by default at .octoprint/cam/pic_settings.yaml
		"""
		backup = '/home/pi/.octoprint/cam/last_markers.json'
		if os.path.isfile(path):
			_path = path
		else:
			self._logger.info("last_session.yaml does not exist, using legacy backup (last_markers.json)")
			_path = backup
		try:
			ret = []
			with open(_path) as f:
				settings = yaml.load(f) or {}
				if _path == backup:
					# No shutter speed info
					settings = {k: v[-1] for k, v in settings.items()}
					ret = [settings, None]
				else:
					for k in ['calibMarkers', 'shutter_speed']:
						ret.append(settings.get(k, None))
			return ret
		except (IOError,OSError) as e:
			self._logger.warning("New or Legacy marker memory not found.")
			return [None]*2

	# @logme(True)
	def save_camera_settings(
		self,
		path='/home/pi/.octoprint/cam/last_session.yaml',
		markers = None,
		shutter_speed = None
	):
		"""
		Save the settings given for the next sesison.
		The file is located by default at .octoprint/cam/pic_settings.yaml
		"""
		if markers is None and shutter_speed is None:
			# Nothing to save
			return
		_markers = copy.deepcopy(markers)
		if type(_markers) is dict:
			for k, v in _markers.items():
				if type(v) is np.ndarray:
					_markers[k] = v.tolist()
		else:
			_markers={}

		settings = {}
		try:
			with open(path) as f:
				settings = yaml.load(f)
		except (OSError, IOError) as e:
			self._logger.warning("file %s does not exist or could not be read. Overwriting..." % path)

		settings = dict_merge(settings, {'calibMarkers': _markers,
						 'shutter_speed': shutter_speed})
		try:
			with open(path, 'w') as f:
				f.write(yaml.dump(settings))
		except (OSError, IOError) as e:
			self._logger.error(e)
		except TypeError as e:
			self._logger.warning("Data that I tried writing to %s :\n%s" % (path, settings))


def blank_session_details():
	"""
	Add to these session details when taking the pictures.
	Do not send back as-is (won't convert to JSON)
	example analytics output:
	{
	"num_pics": 8,
	"num_success_pics": 0,
	"errors": {},
	"num_all_markers_detected": 0,
	"avg_upload_speed": null,
	"settings_min_marker_size": null,
	"avg_shutter_speed": 75870.666666666672,
	"markers": {
		"SW": {
			"avg_color": [
			153.83132956630604,
			96.65563641216431,
			157.33211938180796
			],
			"avg_pos": [
			1415.0,
			191.375
			],
			"missed": 0,
			"max_brightness": 222.36003612238798,
			"avg_brightness": 191.76418726204039,
			"min_brightness": 132.54071417672597,
			"found": 8,
			"std_pos": [
			0.0,
			0.14498973996560857
			],
			"marker_px_size": 852.88888888888891
		},
		"NE": {
			"avg_color": [
			145.245669380652,
			107.38059013940135,
			87.4850645317796
			],
			"avg_pos": [
			218.875,
			1952.875
			],
			"missed": 0,
			"max_brightness": 133.5580481163187,
			"avg_brightness": 103.754267896564,
			"min_brightness": 61.796808673120474,
			"found": 8,
			"std_pos": [
			0.09077978610301556,
			0.09077978610301436
			],
			"marker_px_size": 872.77777777777783
		},
		"SE": {
			"avg_color": [
			151.05255352255705,
			92.30664293555843,
			176.65584827724854
			],
			"avg_pos": [
			1385.125,
			1983.0
			],
			"missed": 0,
			"max_brightness": 236.57588634316892,
			"avg_brightness": 210.56778508779132,
			"min_brightness": 154.62930727850451,
			"found": 8,
			"std_pos": [
			0.109375,
			0.0
			],
			"marker_px_size": 934.66666666666663
		},
		"NW": {
			"avg_color": [
			132.75216912060495,
			113.9216832961036,
			75.47599677659782
			],
			"avg_pos": [
			267.375,
			151.125
			],
			"missed": 0,
			"max_brightness": 112.99359963534337,
			"avg_brightness": 85.321787444997511,
			"min_brightness": 46.601849096959924,
			"found": 8,
			"std_pos": [
			0.15655504520228197,
			0.10683497845024859
			],
			"marker_px_size": 887.0
		}
	},
	}
	"""
	_init_marker = {
		'missed':  0,
		'found':   0,
		'avg_pos': None,
		'std_pos': None,
		# 'colorspace': 'hsv',
		'avg_color': [],
		'avg_brightness': None,
		'min_brightness': None,
		'max_brightness': None,
		#'median_color': [],
		'marker_px_size': []
	}
	session_details = {
		'num_pics': 0,
		'num_success_pics': 0,
		'num_all_markers_detected': 0,
		'markers': {
			'NW': copy.deepcopy(_init_marker),
			'SE': copy.deepcopy(_init_marker),
			'SW': copy.deepcopy(_init_marker),
			'NE': copy.deepcopy(_init_marker),
		},
		'errors': {},
		'avg_shutter_speed': None,
		'avg_upload_speed': None,
		'settings_min_marker_size': None,
	}
	return session_details
