import copy
import json
import numpy as np
import time
import threading
from math import sqrt
from threading import Event
import os
import shutil
import logging

import cv2
from flask.ext.babel import gettext
# from typing import Dict, Any, Union, Callable

from octoprint_mrbeam.mrbeam_events import MrBeamEvents

# don't crash on a dev computer where you can't install picamera
try:
	import octoprint_mrbeam.camera
	from octoprint_mrbeam.camera import MrbCamera, gaussBlurDiff, QD_KEYS, PICAMERA_AVAILABLE
	from octoprint_mrbeam.camera.undistort import prepareImage
	from octoprint_mrbeam.camera.undistort import _getCamParams, _getPicSettings, DIST_KEY, MTX_KEY
	from octoprint_mrbeam.util import json_serialisor, logme
	# TODO mb pic does not rely on picamera, should not use a Try catch.
	import mb_picture_preparation as mb_pic
	PICAMERA_AVAILABLE = True
except ImportError as e:
	PICAMERA_AVAILABLE = False
	logging.getLogger("octoprint.plugins.mrbeam.iobeam.lidhandler").error(
		"Could not import module 'mb_picture_preparation'. Disabling camera integration. (%s: %s)", e.__class__.__name__, e)

SIMILAR_PICS_BEFORE_UPSCALE = 3
LOW_QUALITY = 65 # low JPEG quality for compressing bigger pictures
OK_QUALITY = 75 # default JPEG quality served to the user
TOP_QUALITY = 90 # best compression quality we want to serve the user
DEFAULT_MM_TO_PX = 1 # How many pixels / mm is used for the output image

SIMILAR_PICS_BEFORE_REFRESH = 20

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
        self._logger = mrb_logger("octoprint.plugins.mrbeam.iobeam.lidhandler")

        self._lid_closed = True
        self._is_slicing = False
        self._client_opened = False

        self.camEnabled = self._settings.get(["cam", "enabled"])

        self.image_correction_enabled = self._settings.get(['cam', 'image_correction_enabled'])

        if self.camEnabled and PICAMERA_AVAILABLE:
            imagePath = self._settings.getBaseFolder("uploads") + '/' + self._settings.get(["cam", "localFilePath"])
            self._photo_creator = PhotoCreator(self._plugin,
                                               self._plugin_manager,
                                               imagePath,
                                               self.image_correction_enabled,
                                               debug=False)
        else:
            self._photo_creator = None
        self._analytics_handler = self._plugin.analytics_handler
        self._event_bus.subscribe(MrBeamEvents.MRB_PLUGIN_INITIALIZED, self._subscribe)

    def _subscribe(self, event, payload):
        self._event_bus.subscribe(IoBeamEvents.LID_OPENED, self.onEvent)
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

    def _printerStateChanged(self, event, payload):
        if payload['state_string'] == 'Operational':
            # TODO CHECK IF CLIENT IS CONNECTED FOR REAL, with PING METHOD OR SIMILAR
            self._client_opened = True
            self._startStopCamera(event)

    def _onSlicingEvent(self, event, payload):
        self._is_slicing = (event == OctoPrintEvents.SLICING_STARTED)
        self._startStopCamera(event)

    def _startStopCamera(self, event):
        if self._photo_creator is not None and self.camEnabled:
            if event in (IoBeamEvents.LID_CLOSED, OctoPrintEvents.SLICING_STARTED, OctoPrintEvents.CLIENT_CLOSED):
                self._logger.info('Camera stopping - event: {}, client_opened {}, is_slicing: {}\nlid_closed: {}, printer.is_locked(): {}, save_debug_images: {}'.format(
                        event,
                        self._client_opened,
                        self._is_slicing,
                        self._lid_closed,
                        self._printer.is_locked() if self._printer else None,
                        self._photo_creator.save_debug_images
                    ))
                self._end_photo_worker()
            else:
                # TODO get the states from _printer or the global state, instead of having local state as well!
                if self._client_opened and not self._is_slicing and not self._lid_closed and not self._printer.is_locked():
                    self._logger.info('Camera starting - event: {}, client_opened {}, is_slicing: {}\nlid_closed: {}, printer.is_locked(): {}, save_debug_images: {}, is_initial_calibration: {}'.format(
                            event,
                            self._client_opened,
                            self._is_slicing,
                            self._lid_closed,
                            self._printer.is_locked() if self._printer else None,
                            self._photo_creator.save_debug_images,
                            self._photo_creator.is_initial_calibration
                        ))
                    self._start_photo_worker()
                elif self._photo_creator.is_initial_calibration:
                    # camera is in first init mode
                    self._logger.info('Camera starting: initial_calibration. event: {}'.format(event))
                    self._start_photo_worker()
                else:
                    self._logger.debug('Camera not supposed to start now. event: {}, client_opened {}, is_slicing: {}\nlid_closed: {}, printer.is_locked(): {}, save_debug_images: {}'.format(
                        event,
                        self._client_opened,
                        self._is_slicing,
                        self._lid_closed,
                        self._printer.is_locked() if self._printer else None,
                        self._photo_creator.save_debug_images
                    ))

    def shutdown(self):
        if self._photo_creator is not None:
            self._logger.debug("shutdown() stopping _photo_creator")
            self._end_photo_worker()

    def take_undistorted_picture(self,is_initial_calibration=False):
        from flask import make_response, jsonify
        if self._photo_creator is not None:
            if is_initial_calibration:
                self._photo_creator.is_initial_calibration = True
            else:
                self._photo_creator.set_undistorted_path()
            self._startStopCamera("take_undistorted_picture_request")
            # this will be accepted in the .done() method in frontend
            resp_text = {'msg': gettext("Please make sure the lid of your Mr Beam II is open and wait a little...")}
            return make_response(jsonify(resp_text), 200)
        else:
            return make_response('Error, no photocreator active, maybe you are developing and dont have a cam?', 503)

    def _start_photo_worker(self):
        if not (self._photo_creator.active() or self._photo_creator.worker.isAlive()):
            self._photo_creator.start()
        else:
            self._logger.info("Another PhotoCreator thread is already active! Not starting a new one.")

    def _end_photo_worker(self):
        if self._photo_creator:
            self._photo_creator.stop()
            self._photo_creator.save_debug_images = False
            self._photo_creator.undistorted_pic_path = None


class PhotoCreator(object):
    def __init__(self, _plugin, _plugin_manager, path, image_correction_enabled, debug=False):
        self._plugin = _plugin
        self._plugin_manager = _plugin_manager
        self.final_image_path = path
        self.image_correction_enabled = image_correction_enabled
        self._settings = _plugin._settings
        self._analytics_handler = _plugin.analytics_handler
        self._laserCutterProfile = _plugin.laserCutterProfileManager.get_current_or_default()
        self.stopEvent = Event()
        self.stopEvent.set()
        self._pic_available = Event()
        self._pic_available.clear()
        self.last_photo = 0
        self.badQualityPicCount = 0
        self.is_initial_calibration = False
        self.undistorted_pic_path = None
        self.save_debug_images = self._settings.get(['cam', 'saveCorrectionDebugImages'])
        self._logger = logging.getLogger("octoprint.plugins.mrbeam.iobeam.lidhandler.PhotoCreator")
        self.debug = debug
        self._front_ready = Event()
        self.last_correction_result = None
        self.worker = threading.Thread()
        if debug: self._logger.setLevel(logging.DEBUG)
        else:     self._logger.setLevel(logging.INFO)
        if self._settings.get(["cam", "keepOriginals"]):
            self.tmp_img_raw = self.final_image_path.replace('.jpg', "-tmp{}.jpg".format(time.time()))
            self.tmp_img_prepared = self.final_image_path.replace('.jpg', '-tmp2.jpg')
        else:
            self.tmp_img_raw = self.final_image_path.replace('.jpg', '-tmp.jpg')
            self.tmp_img_prepared = self.final_image_path.replace('.jpg', '-tmp2.jpg')
        map(self._createFolder_if_not_existing, [self.final_image_path, self.tmp_img_raw, self.tmp_img_prepared])

    def active(self):
        return not self.stopEvent.isSet()

    def start(self):
        if self.active():
            self.stop()
        self.stopEvent.clear()
        self.worker = threading.Thread(target=self.work, name='Photo-Worker')
        self.worker.daemon = True
        self.worker.start()

    def stop(self):
        self.stopEvent.set()
        if self.worker.isAlive():
            return self.worker.join()
        else:
            return

    def set_undistorted_path(self):
        self.undistorted_pic_path = self._settings.getBaseFolder("uploads") + '/' + self._settings.get(['cam', 'localUndistImage'])

    def work(self):
        # todo find maximum of sleep in beginning that's not affecting UX
        time.sleep(0.8)

        if self.is_initial_calibration:
            self.set_undistorted_path()
            # set_debug_images_to = save_debug_images or self._photo_creator.save_debug_images
            # TODO save marker colors
            self.save_debug_images = True

        if not PICAMERA_AVAILABLE:
            self._logger.warn("Camera disabled. Not all required modules could be loaded at startup. ")
            self.stopEvent.set()
            return

        self._logger.debug("Starting the camera now.")
        try:
            with MrbCamera(octoprint_mrbeam.camera.MrbPicWorker(maxSize=2, debug=self.debug),
                           framerate=8,
                           resolution=octoprint_mrbeam.camera.LEGACY_STILL_RES,  # TODO camera.DEFAULT_STILL_RES,
                           stopEvent=self.stopEvent,) as cam:
                self.serve_pictures(cam)
        except Exception as e:
            if e.__class__.__name__.startswith('PiCamera'):
                self._logger.error("PiCamera_Error_while_preparing_camera_%s_%s", e.__class__.__name__, e)
            else:
                self._logger.exception("Exception_while_preparing_camera_%s_%s", e.__class__.__name__, e)
        self.stopEvent.set()

    def serve_pictures(self, cam):
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
        path_to_cam_params = self._settings.get(["cam", "lensCalibrationFile"])
        path_to_pic_settings = self._settings.get(["cam", "correctionSettingsFile"])
        path_to_last_markers = self._settings.get(["cam", "correctionTmpFile"])

        mrb_volume = self._laserCutterProfile['volume']
        out_pic_size = mrb_volume['width'], mrb_volume['depth']
        self._logger.debug("Will send images with size %s", out_pic_size)

        # load cam_params from file
        cam_params = _getCamParams(path_to_cam_params)
        self._logger.debug('Loaded cam_params: {}'.format(cam_params))

        # load pic_settings json
        pic_settings = _getPicSettings(path_to_pic_settings)
        self._logger.debug('Loaded pic_settings: {}'.format(pic_settings))
        try:
            if self.active():
                cam.start_preview()
                time.sleep(2)
                # bestShutterSpeeds = cam.apply_best_shutter_speed()  # Usually only 1 value, but there could be more

                # TODO cam.anti_rolling_shutter_banding()
                cam.start()  # starts capture to the cam.worker
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
            while self.active():
                cam.wait()  # waits until the next picture is ready
                if not self.active(): break
                latest = cam.lastPic() # gets last picture given by cam.worker
                cam.async_capture()  # starts capture with new settings
                if latest is None:
                    # The first picture will be empty, should wait for the 2nd one.
                    self._logger.info("The last picture is empty")
                    continue
                if not self.active(): break  # check if still active...
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
                        time.sleep(1.5) # Let the raspberry breathe a bit (prevent overheating)
                        continue
                # Get the desired scale and quality of the picture to serve
                upscale_factor , quality = pic_qualities[pic_qual_index]
                scaled_output_size = tuple(int(upscale_factor * i) for i in out_pic_size)
                # --- Correct captured image ---
                self._logger.debug("Starting with correction...")
                # TODO Toggle : choose which algo to run first
                success_1, correction_result, markers, missed, err = self._new_detect_algo(latest, cam_params,
                                                                                           pic_settings,
                                                                                           scaled_output_size,
                                                                                           last_markers=markers,
                                                                                           quality=quality)
                if not self.active(): break
                # Send result to fronted ASAP
                if success_1:
                    self._ready_to_send_pic(correction_result)
                    self.badQualityPicCount = 0

                success_2, correction_result2 = self._legacy_detect_algo(latest,
                                                                         path_to_cam_params,
                                                                         path_to_pic_settings,
                                                                         path_to_last_markers,
                                                                         scaled_output_size,
                                                                         quality=quality)
                if not self.active(): break

                self._logger.debug("correct result 2 %s", correction_result2)
                if not success_2:
                    errorID = correction_result2['error'].split(':')[0]
                    errorString = correction_result2['error'].split(':')[1]
                    if errorID == 'BAD_QUALITY':
                        self.badQualityPicCount += 1
                        self._logger.error(
                                errorString + '_Number_of_bad_quality_pics_{}'.format(self.badQualityPicCount))
                        if self.badQualityPicCount > 10:
                            self._logger.error('Too_many_bad_pics-_Show_bad_image_now'.format(self.badQualityPicCount))
                            self._ready_to_send_pic(correction_result2)
                    elif errorID == 'NO_CALIBRATION' or errorID == 'NO_PICTURE_FOUND':
                        self._logger.error(errorString)
                    else:  # Unknown error
                        self._logger.error(errorID + errorString)
                if success_2 and not success_1:
                    self._ready_to_send_pic(correction_result2)
                    self.badQualityPicCount = 0
                    # Use this picture
                elif not success_1:
                    # Just tell front end that there was an error
                    self._send_frontend_picture_metadata(correction_result2)
                self._add_result_to_analytics(session_details,
                                              'new',
                                              markers,
                                              increment_pic=True,
                                              error=err)
                self._add_result_to_analytics(session_details,
                                              'legacy',
                                              correction_result2['markers_found'],
                                              increment_pic=False,
                                              error=correction_result2['error'])
                # self._logger.debug("Analytics: %s", json.dumps(session_details,
                #                                                    indent=2,
                #                                                    default=json_serialisor))
            cam.stop_preview()
            if session_details['num_pics'] > 0:
                self._analytics_handler.add_camera_session_details(session_details)
            self._logger.debug("PhotoCreator_stopping")
        except Exception as worker_exception:
            self._logger.exception("Exception_in_worker_thread_of_PhotoCreator-_{}".format(worker_exception.message))

    def _new_detect_algo(self, pic, cam_params, pic_settings, out_pic_size, last_markers=None, quality=OK_QUALITY):
        # Only for the purpose of the transition of 1 detection type to the other.
        # This should otherwise just be part of serve_pictures()
        workspaceCorners, markers, missed, err = prepareImage(input_image=pic,
                                                              path_to_output_image=self.tmp_img_prepared,
                                                              cam_dist=cam_params[DIST_KEY],
                                                              cam_matrix=cam_params[MTX_KEY],
                                                              pic_settings=pic_settings,
                                                              last_markers=last_markers,
                                                              size=out_pic_size,
                                                              quality=quality,
                                                              debug_out=self.save_debug_images,  # self.save_debug_images,
                                                              undistorted=True,
                                                              stopEvent=self.stopEvent,
                                                              threads=4)
        if not self.active(): return False, None, None, None, None
        success_1 = workspaceCorners is not None
        # Conform to the legacy result to be sent to frontend
        correction_result = {'markers_found':         list(filter(lambda q: q not in missed, QD_KEYS)),
                             # {k: v.astype(int) for k, v in markers.items()},
                             'markers_recognised':    4 - len(missed),
                             'corners_calculated':    None if workspaceCorners is None else list(workspaceCorners),
                             # {k: v.astype(int) for k, v in workspaceCorners.items()},
                             'markers_pos':           {qd: pos.tolist() for qd, pos in markers.items()},
                             'successful_correction': success_1,
                             'undistorted_saved':     True,
                             'error': err}
        return success_1, correction_result, markers, missed, err

    def _legacy_detect_algo(self, pic,
                            path_to_cam_params,
                            path_to_pic_settings,
                            path_to_last_markers,
                            out_pic_size,
                            quality=OK_QUALITY):
        # Write the img to disk for the 2nd algo
        w = self._settings.get(["cam", "cam_img_width"])
        h = self._settings.get(["cam", "cam_img_height"])
        cv2.imwrite(self.tmp_img_raw, cv2.resize(pic, (w, h)))
        correction_result2 = mb_pic.prepareImage(self.tmp_img_raw,
                                              self.tmp_img_prepared,
                                              path_to_cam_params,
                                              path_to_pic_settings,
                                              path_to_last_markers,
                                              size=out_pic_size,  # (h, w),
                                              save_undistorted=self.undistorted_pic_path,
                                              quality=quality,
                                              debug_out=self.save_debug_images,
                                              stopEvent=self.stopEvent, )

        success_2 = not correction_result2['error']
        correction_result2['successful_correction'] = success_2
        return success_2, correction_result2

    # @logme(True)
    def _add_result_to_analytics(self,
                                 session_details,
                                 algo,
                                 markers,
                                 increment_pic=False,
                                 colorspace='hsv',
                                 avg_colors=None,
                                 med_colors=None,
                                 upload_speed=None,
                                 error=None):
        assert(algo in ['new', 'legacy'])
        # Legacy algo only gives us a list of found corners
        assert(type(markers) is dict or type(markers) is list)
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
                _s_marker = _s[algo]['markers'][qd]
                _marker = None
                if algo == 'new' and qd in markers.keys() and markers[qd] is not None:
                    _marker = np.asarray(markers[qd])
                elif algo == 'legacy' and qd in markers.keys() and markers[qd]['x'] is not None:
                    _marker = np.asarray([markers[qd]['y'], markers[qd]['x']])
                if _marker is not None:
                    _success_mass = _s_marker['found']
                    _n_avg, _n_std = add_to_stat(_marker,
                                                 _s_marker['avg_pos'],
                                                 _s_marker['std_pos'],
                                                 _success_mass)
                    _s_marker['avg_pos'] = _n_avg.tolist()
                    _s_marker['std_pos'] = _n_std.tolist()
                    _s_marker['found'] += 1
                else:
                    _s_marker['missed'] += 1

            if error:
                error = error.replace(".","-").replace(",","-")
                if error in _s[algo]['errors']:
                    _s[algo]['errors'][error] += 1
                else:
                    _s[algo]['errors'][error] = 1

        except Exception as ex:
            self._logger.exception('Exception_in-_save__s_for_analytics-_{}'.format(ex))

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
        try:
            path = os.path.dirname(filename)
            if not os.path.exists(path):
                os.makedirs(path)
                self._logger.debug("Created folder '%s' for camera images.", path)
        except:
            self._logger.exception("Exception_while_creating_folder_'%s'_for_camera_images-_", filename)

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
    session_details = { 'new': {'markers': {'NW': {'missed': int,
                                                   'found': int,
                                                   'avg_pos': [float, float],
                                                   'std_pos': float,
                                                   'colorspace': str,
                                                   'avg_color_when_missed': [[int, int, int], ...],
                                                   'median_color_when_missed': [[int, int, int], ...]}
                                            'SE': {...},
                                            'SW': {...},
                                            'NE': {...}},
                                'errors': list(dict)},
                        'legacy': {...},
                        'mean_upload_speed': int}
    """
    _init_marker = {'missed':  0,
                    'found':   0,
                    'avg_pos': None,
                    'std_pos': None,
                    # The following fields are unused for now
                    # 'colorspace': 'hsv',
                    # 'avg_color_when_missed': [],
                    # 'median_color_when_missed': []
                    }
    _init_result = {'markers': {'NW': copy.deepcopy(_init_marker),
                                'SE': copy.deepcopy(_init_marker),
                                'SW': copy.deepcopy(_init_marker),
                                'NE': copy.deepcopy(_init_marker)},
                    'errors':  {}}
    session_details = {'num_pics':           0,
                       'new':               copy.deepcopy(_init_result),
                       'legacy':            copy.deepcopy(_init_result),
                       'avg_upload_speed': None}
    return session_details
