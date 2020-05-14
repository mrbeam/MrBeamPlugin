import copy
import json
import numpy as np
import time
import cv2
import base64
import threading
from threading import Event
import os
import shutil
import logging

from flask.ext.babel import gettext
# from typing import Dict, Any, Union, Callable

from octoprint_mrbeam.mrbeam_events import MrBeamEvents

# don't crash on a dev computer where you can't install picamera
import octoprint_mrbeam.camera
from octoprint_mrbeam.camera import gaussBlurDiff, QD_KEYS, PICAMERA_AVAILABLE
from octoprint_mrbeam.util import json_serialisor, logme
import octoprint_mrbeam.camera.exc as exc
if PICAMERA_AVAILABLE:
	from octoprint_mrbeam.camera.mrbcamera import MrbCamera
	from octoprint_mrbeam.camera.undistort import prepareImage, MAX_OBJ_HEIGHT, \
		CAMERA_HEIGHT, _getCamParams, _getPicSettings, DIST_KEY, MTX_KEY

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

		if PICAMERA_AVAILABLE:
			imagePath = self._settings.getBaseFolder("uploads") + '/' + self._settings.get(["cam", "localFilePath"])
			self._photo_creator = PhotoCreator(self._plugin,
											   self._plugin_manager,
											   imagePath,
											   debug=False)
		else:
			self._photo_creator = None
		self.refresh_pic_settings = Event() # TODO placeholder for when we delete PhotoCreator

		self._analytics_handler = self._plugin.analytics_handler
		self._event_bus.subscribe(MrBeamEvents.MRB_PLUGIN_INITIALIZED, self._subscribe)

	def _subscribe(self, event, payload):
		self._event_bus.subscribe(IoBeamEvents.LID_OPENED, self.onEvent)
		self._event_bus.subscribe(IoBeamEvents.INTERLOCK_OPEN, self.onEvent)
		self._event_bus.subscribe(IoBeamEvents.INTERLOCK_CLOSED, self.onEvent)
		self._event_bus.subscribe(IoBeamEvents.LID_CLOSED, self.onEvent)
		self._event_bus.subscribe(OctoPrintEvents.CLIENT_OPENED, self.onEvent)
		self._event_bus.subscribe(OctoPrintEvents.SHUTDOWN, self.onEvent)
		self._event_bus.subscribe(OctoPrintEvents.CLIENT_CLOSED,self.onEvent)
		self._event_bus.subscribe(OctoPrintEvents.SLICING_STARTED,self._onSlicingEvent)
		self._event_bus.subscribe(OctoPrintEvents.SLICING_DONE,self._onSlicingEvent)
		self._event_bus.subscribe(OctoPrintEvents.SLICING_FAILED,self._onSlicingEvent)
		self._event_bus.subscribe(OctoPrintEvents.SLICING_CANCELLED, self._onSlicingEvent)
		self._event_bus.subscribe(OctoPrintEvents.PRINTER_STATE_CHANGED,self._printerStateChanged)

	def onEvent(self, event, payload):
		self._logger.debug("onEvent() event: %s, payload: %s", event, payload)
		if event == IoBeamEvents.LID_OPENED:
			self._logger.debug("onEvent() LID_OPENED")
			self._lid_closed = False
			self._startStopCamera(event)
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
		elif event == OctoPrintEvents.CLIENT_OPENED:
			self._logger.debug("onEvent() CLIENT_OPENED sending client lidClosed: %s", self._lid_closed)
			self._client_opened = True
			self._startStopCamera(event)
		elif event == OctoPrintEvents.CLIENT_CLOSED:
			self._client_opened = False
			self._startStopCamera(event)
		elif event == OctoPrintEvents.SHUTDOWN:
			self.shutdown()

	def is_lid_open(self):
		return not self._lid_closed

	def on_front_end_pic_received(self):
		self._logger.debug("Front End finished downloading the picture")
		if self._photo_creator is not None:
			self._photo_creator.send_pic_asap()

	def send_camera_image_to_analytics(self):
		if self._photo_creator:
			self._photo_creator.send_last_img_to_analytics()

	def _printerStateChanged(self, event, payload):
		if payload['state_string'] == 'Operational':
			# TODO CHECK IF CLIENT IS CONNECTED FOR REAL, with PING METHOD OR SIMILAR
			self._client_opened = True
			self._startStopCamera(event)

	def _onSlicingEvent(self, event, payload):
		self._is_slicing = (event == OctoPrintEvents.SLICING_STARTED)
		self._startStopCamera(event)

	def _startStopCamera(self, event):
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
			else:
				# TODO get the states from _printer or the global state, instead of having local state as well!
				if self._client_opened and not self._is_slicing and not self._interlock_closed and not self._printer.is_locked():
					self._logger.info('Camera starting' + status)
					self._start_photo_worker()
				elif self._photo_creator.is_initial_calibration:
					# camera is in first init mode
					self._logger.info('Camera starting: initial_calibration. event: {}'.format(event))
					self._start_photo_worker()
				else:
					self._logger.debug('Camera not supposed to start now.' + status)

	def shutdown(self):
		if self._photo_creator is not None:
			self._logger.debug("shutdown() stopping _photo_creator")
			self._end_photo_worker()

	def take_undistorted_picture(self,is_initial_calibration=False):
		from flask import make_response, jsonify
		if self._photo_creator is not None:
			self._photo_creator.is_initial_calibration = is_initial_calibration
			self._startStopCamera("take_undistorted_picture_request")
			# this will be accepted in the .done() method in frontend
			resp_text = {'msg': gettext("Please make sure the lid of your Mr Beam is open and wait a little...")}
			return make_response(jsonify(resp_text), 200)
		else:
			return make_response('Error, no photocreator active, maybe you are developing and dont have a cam?', 503)

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
			self._logger.info("Another PhotoCreator thread is already active! Not starting a new one.")

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
		self.last_correction_result = None
		self.worker = None
		self._flag_send_img_to_analytics = None
		
		if debug:
			self._logger = mrb_logger("octoprint.plugins.mrbeam.iobeam.lidhandler.PhotoCreator", logging.DEBUG)
		else:
			self._logger = mrb_logger("octoprint.plugins.mrbeam.iobeam.lidhandler.PhotoCreator", logging.INFO)
		if self._settings.get(["cam", "keepOriginals"]):
			self.tmp_img_raw = self.final_image_path.replace('.jpg', "-tmp{}.jpg".format(time.time()))
			self.tmp_img_prepared = self.final_image_path.replace('.jpg', '-tmp2.jpg')
		else:
			self.tmp_img_raw = self.final_image_path.replace('.jpg', '-tmp.jpg')
			self.tmp_img_prepared = self.final_image_path.replace('.jpg', '-tmp2.jpg')
		map(self._createFolder_if_not_existing, [self.final_image_path, self.tmp_img_raw, self.tmp_img_prepared])

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
			try:
				with MrbCamera(octoprint_mrbeam.camera.MrbPicWorker(maxSize=2, debug=self.debug),
							   # framerate=8,
							   resolution=octoprint_mrbeam.camera.LEGACY_STILL_RES,  # TODO camera.DEFAULT_STILL_RES,
							   stopEvent=self.stopEvent,) as cam:
					self.serve_pictures(cam, pic_settings=pic_settings, cam_params=cam_params, out_pic_size=out_pic_size)
				if recurse_nb > 0:
					self._logger.info("Camera recovered")
					self._analytics_handler.add_camera_session_details(exc.msgForAnalytics(exc.CAM_CONNRECOVER))
			except exc.CameraConnectionException as e:
				self._logger.warning(" %s, %s : %s" % (e.__class__.__name__, e, exc.msg(exc.CAM_CONN)),
									   analytics=exc.CAM_CONN)
				if recurse_nb < MAX_PIC_THREAD_RETRIES:
					self._logger.info("Restarting work() after some sleep")
					self._plugin.user_notification_system.show_notifications(
						self._plugin.user_notification_system.get_notification(
							notification_id='warn_cam_conn_err',
							replay=True))
					self.stopEvent.clear()
					if not self.stopEvent.wait(5.0):
						self.work(recurse_nb=recurse_nb+1)
				else:
					self._logger.exception(" %s, %s : Recursive restart : too many times, displaying Error message." % (e.__class__.__name__, e),
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
		except:
			self._logger.exception("Exception in PhotoCreator thread: ")
			

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
		# Marker positions detected on the last loop
		markers = None
		# waste the first picture : doesn't matter how long we wait to warm up, the colors will be off.
		cam.wait()
		while self._plugin.lid_handler._lid_closed:
			# Wait for the lid to be completely open
			if self._plugin.lid_handler._interlock_closed or self.stopping:
				return
			time.sleep(.2)
		# The lid didn't open during waiting time
		cam.async_capture()
		while not self.stopping:
			if self.refresh_pic_settings.isSet():
				self.refresh_pic_settings.clear()
				path_to_pic_settings = self._settings.get(["cam", "correctionSettingsFile"])
				self._logger.info("Refreshing picture settings from %s" % path_to_pic_settings)
				pic_settings = _getPicSettings(path_to_pic_settings)
				prev=None # Forces to take a new picture
			cam.wait()  # waits until the next picture is ready
			if self.stopping: break
			
			# ANDY
			if prev is not None and self._flag_send_img_to_analytics:
				self._send_last_img_to_analytics(prev, markers, missed, analytics)
			# else:
			# 	self._logger.info("ANDYTEST NOT sending image: prev: %s, _flag_send_img_to_analytics: %s", None if prev is None else 'smth', self._flag_send_img_to_analytics)
			
			
			latest = cam.lastPic() # gets last picture given by cam.worker
			cam.async_capture()  # starts capture with new settings
			if latest is None:
				# The first picture will be empty, should wait for the 2nd one.
				self._logger.info("The last picture is empty")
				continue
			if self.stopping: break  # check if still active...
			# TODO start capture with different brightness if we think we need it
			#     TODO apply shutter speed adjustment from preliminary measurements

			# Compare previous image with the current one.
			if prev is None or gaussBlurDiff(latest, prev, resize=.5):
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
			# NOTE -- prepareImage is bloat, TODO spill content here
			workspaceCorners, markers, missed, err, analytics = prepareImage(
				input_image=latest,
				path_to_output_image=self.tmp_img_prepared,
				pic_settings=pic_settings,
				cam_dist=dist,
				cam_matrix=mtx,
				last_markers=markers,
				size=scaled_output_size,
				quality=quality,
				zoomed_out=self.zoomed_out,
				debug_out=self.save_debug_images,  # self.save_debug_images,
				undistorted=True,
				stopEvent=self.stopEvent,
				min_pix_amount=self._settings.get(['cam', 'markerRecognitionMinPixel']),
				threads=4
			)
			if self.stopping: return False, None, None, None, None
			success = workspaceCorners is not None
			# Conform to the legacy result to be sent to frontend
			correction_result = {
				'markers_found': list(filter(lambda q: q not in missed, QD_KEYS)),
				# {k: v.astype(int) for k, v in markers.items()},
				'markers_recognised': 4 - len(missed),
				'corners_calculated': None if workspaceCorners is None else list(workspaceCorners),
				# {k: v.astype(int) for k, v in workspaceCorners.items()},
				'markers_pos': {qd: pos.tolist() for qd, pos in markers.items()},
				'successful_correction': success,
				'undistorted_saved': True,
				'workspace_corner_ratio': float(MAX_OBJ_HEIGHT) / CAMERA_HEIGHT / 2,
				'avg_color': color,
				'marker_px_size': marker_size,
				'error': err,
			}
			# Send result to fronted ASAP
			if success:
				self._ready_to_send_pic(correction_result)
			else:
				# Just tell front end that there was an error
				self._send_frontend_picture_metadata(correction_result)
			self._add_result_to_analytics(
				session_details,
				markers,
				increment_pic=True,
				error=err,
				extra=analytics
			)
		cam.stop_preview()
		if session_details['num_pics'] > 0:
			session_details.update(
				{'settings_min_marker_size': self._settings.get(['cam', 'markerRecognitionMinPixel'])}
			)
			self._analytics_handler.add_camera_session_details(session_details)
		self._logger.debug("PhotoCreator_stopping")

	# @logme(True)
	def _add_result_to_analytics(self,
					 session_details,
					 markers,
					 colors={},
					 marker_size={},
					 increment_pic=False,
					 colorspace='hsv',
					 upload_speed=None,
					 error=None,
					 extra=None):
		if extra is None: extra={}
		assert(type(markers) is dict)
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

		_s = session_details
		try:
			if increment_pic: _s['num_pics'] += 1
			for qd in octoprint_mrbeam.camera.QD_KEYS:
				_s_marker = _s['markers'][qd]
				if qd in markers.keys() and markers[qd] is not None:
					_marker = np.asarray(markers[qd])
					_n_avg, _n_std = add_to_stat(_marker,
												 _s_marker['avg_pos'],
												 _s_marker['std_pos'],
												 _s_marker['found'])
					_s_marker['avg_pos'] = _n_avg.tolist()
					_s_marker['std_pos'] = _n_std.tolist()
					_s_marker['found'] += 1
				else:
					_s_marker['missed'] += 1
			if error:
				error = error.replace(".","-").replace(",","-")
				if error in _s['errors']:
					_s['errors'][error] += 1
				else:
					_s['errors'][error] = 1

		except Exception as ex:
			self._logger.exception('Exception_in-_save__s_for_analytics-_{}'.format(ex))
	
	def send_last_img_to_analytics(self):
		self._flag_send_img_to_analytics = True
		
	def _send_last_img_to_analytics(self, img, markers, missed, analytics):
		self._logger.info("ANDYTEST _send_last_img_to_analytics()")
		# self._logger.info("ANDYTEST img: %s, markers: %s, missed: %s, err: %s, analytics: %s, marker_size: %s", img, markers, missed, err, analytics, marker_size)
		self._flag_send_img_to_analytics = False
		t = threading.Thread(target=self._send_last_img_to_analytics_threaded,
							 name='send_last_img_to_analytics',
							 kwargs={'img': img,
									 'markers': markers,
									 'missed': missed,
									 'analytics_data': analytics
									 })
		t.daemon = True
		t.start()
		
		
	def _send_last_img_to_analytics_threaded(self, img, markers, missed, analytics_data):
		try:
			if img is not None:
				img_format = 'jpg'
				_, img = cv2.imencode('.{}'.format(img_format), img, [int(cv2.IMWRITE_JPEG_QUALITY), 80])
				img = base64.b64encode(img)
				
				analytics_str = ''
				try:
					analytics_str = str(analytics_data)
				except:
					self._logger.warn("_send_last_img_to_analytics_threaded() Can not convert analytics_data to json: %s", analytics_data)
				
				dist = ''
				path_to_cam_params = self._settings.get(["cam", "lensCalibrationFile"])
				try:
					with open(path_to_cam_params, 'r') as f:
						dist = base64.b64encode(f.read())
				except:
					self._logger.warn("_send_last_img_to_analytics_threaded() Can not read npz file: %s", path_to_cam_params)
					
				
				payload = {'img_base64': img,
				           'img_type': img_format,
				           'distortion_matrix_base64': dist,
				           'metadata': {
					           'markers_found': ', '.join(markers.keys()),
					           'markers_missed': ', '.join(missed),
					           'analytics': analytics_str},
				           }
				self._logger.info("_send_last_img_to_analytics_threaded() img len: %s, metadata: %s", len(img), payload['metadata'])
				self._analytics_handler.add_camera_image(payload)
				self._analytics_handler.upload()
			else:
				self._logger.info("_send_last_img_to_analytics_threaded() no image available")
		except:
			self._logger.exception("Exception in _send_last_img_to_analytics_threaded()")
	
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

def blank_session_details():
	"""
	Add to these session details when taking the pictures.
	Do not send back as-is (won't convert to JSON)
	"""
	_init_marker = {
		'missed':  0,
		'found':   0,
		'avg_pos': None,
		'std_pos': None,
		# 'colorspace': 'hsv',
		'avg_color': [],
		#'median_color': [],
		'marker_px_size': []
	}
	session_details = {'num_pics': 0,
					   'markers': {'NW': copy.deepcopy(_init_marker),
								   'SE': copy.deepcopy(_init_marker),
								   'SW': copy.deepcopy(_init_marker),
								   'NE': copy.deepcopy(_init_marker)},
					   'errors': {},
					   'avg_upload_speed': None,
					   'settings_min_marker_size': None}
	return session_details
