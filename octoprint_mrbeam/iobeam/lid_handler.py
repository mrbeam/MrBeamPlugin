import time
import threading
from threading import Event
import os
import shutil
import logging

import cv2
from flask.ext.babel import gettext
# from typing import Dict, Any, Union, Callable

from octoprint_mrbeam.mrbeam_events import MrBeamEvents

# don't crash on a dev computer where you can't install picamera
import octoprint_mrbeam.camera
from octoprint_mrbeam.camera import MrbCamera
from octoprint_mrbeam.camera.undistort import prepareImage
from octoprint_mrbeam.camera.undistort import _getCamParams, _getPicSettings, DIST_KEY, MTX_KEY

# TODO mb pic does not rely on picamera, should not use a Try catch.
try:
    import mb_picture_preparation as mb_pic
    PICAMERA_AVAILABLE = True
except ImportError as e:
    PICAMERA_AVAILABLE = False
    logging.getLogger("octoprint.plugins.mrbeam.iobeam.lidhandler").error(
        "Could not import module 'mb_picture_preparation'. Disabling camera integration. (%s: %s)", e.__class__.__name__, e)

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

        self._photo_creator = None
        self.image_correction_enabled = self._settings.get(['cam', 'image_correction_enabled'])

        self._event_bus.subscribe(MrBeamEvents.MRB_PLUGIN_INITIALIZED, self._on_mrbeam_plugin_initialized)

    def _on_mrbeam_plugin_initialized(self, event, payload):
        self._temperature_manager = self._plugin.temperature_manager
        self._iobeam = self._plugin.iobeam
        self._analytics_handler = self._plugin.analytics_handler

        if self.camEnabled:
            imagePath = self._settings.getBaseFolder("uploads") + '/' + self._settings.get(["cam", "localFilePath"])
            self._photo_creator = PhotoCreator(self._plugin, self._plugin_manager, imagePath, self.image_correction_enabled)

        self._subscribe()

    def _subscribe(self):
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
                self._logger.info('Camera stopping...: event: {}, client_opened {}, is_slicing: {}, lid_closed: {}, printer.is_locked(): {}, save_debug_images: {}'.format(
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
                    self._logger.info('Camera starting: event: {}, client_opened {}, is_slicing: {}, lid_closed: {}, printer.is_locked(): {}, save_debug_images: {}, is_initial_calibration: {}'.format(
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
                    self._logger.info('Camera not starting...: event: {}, client_opened {}, is_slicing: {}, lid_closed: {}, printer.is_locked(): {}, save_debug_images: {}'.format(
                        event,
                        self._client_opened,
                        self._is_slicing,
                        self._lid_closed,
                        self._printer.is_locked() if self._printer else None,
                        self._photo_creator.save_debug_images
                    ))

    def _setClientStatus(self,event):
        if self._photo_creator is not None and self.camEnabled:
            if event == OctoPrintEvents.CLIENT_OPENED:
                self._start_photo_worker()
            else:
                self._end_photo_worker()

    def shutdown(self):
        if self._photo_creator is not None:
            self._logger.debug("shutdown() stopping _photo_creator")
            self._end_photo_worker()

    def take_undistorted_picture(self,is_initial_calibration=False):
        from flask import make_response
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
        if not self._photo_creator.active():
            worker = threading.Thread(target=self._photo_creator.work, name='Photo-Worker')
            worker.daemon = True
            worker.start()
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
        self.last_photo = 0
        self.badQualityPicCount = 0
        self.is_initial_calibration = False
        self.undistorted_pic_path = None
        self.save_debug_images = True # self._settings.get(['cam', 'saveCorrectionDebugImages'])
        self.camera = None
        self._logger = logging.getLogger("octoprint.plugins.mrbeam.iobeam.lidhandler.PhotoCreator")
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

    def stop(self):
        return self.stopEvent.set()

    def set_undistorted_path(self):
        self.undistorted_pic_path = self._settings.getBaseFolder("uploads") + '/' + self._settings.get(['cam', 'localUndistImage'])

    def work(self):
        self.stopEvent.clear()
        session_details = dict(
            num_pics=0,
            errors=[],
            detected_markers={},
        )

        # todo find maximum of sleep in beginning that's not affecting UX
        time.sleep(0.8)

        if self.is_initial_calibration:
            self.set_undistorted_path()
            # set_debug_images_to = save_debug_images or self._photo_creator.save_debug_images
            self.save_debug_images = True

        if not PICAMERA_AVAILABLE:
            self._logger.warn("Camera disabled. Not all required modules could be loaded at startup. ")
            self.stopEvent.set()
            return

        self._logger.debug("Starting the camera now.")
        try:
            with MrbCamera(octoprint_mrbeam.camera.MrbPicWorker(maxSize=2),
                           framerate=8,
                           resolution=octoprint_mrbeam.camera.LEGACY_STILL_RES,  # TODO camera.DEFAULT_STILL_RES,
                           stopEvent=self.stopEvent,) as cam:
                self.serve_pictures(cam, session_details)
        except Exception as e:
            if e.__class__.__name__.startswith('PiCamera'):
                self._logger.error("PiCamera Error while preparing camera: %s: %s", e.__class__.__name__, e)
            else:
                self._logger.exception("Exception while preparing camera: %s: %s", e.__class__.__name__, e)
        self.stopEvent.set()

    def serve_pictures(self, cam, session_details):
        path_to_cam_params = self._settings.get(["cam", "lensCalibrationFile"])
        path_to_pic_settings = self._settings.get(["cam", "correctionSettingsFile"])
        path_to_last_markers = self._settings.get(["cam", "correctionTmpFile"])

        mrb_volume = self._laserCutterProfile['volume']
        out_pic_size = int(mrb_volume['width'] * 4), int(mrb_volume['depth'] * 4)
        self._logger.debug("Will send images with size %s", out_pic_size)
        # resize img to be used for the legacy algo
        w = self._settings.get(["cam", "cam_img_width"])
        h = self._settings.get(["cam", "cam_img_height"])

        # load cam_params from file
        cam_params = _getCamParams(path_to_cam_params)
        self._logger.debug('Loaded cam_params: {}'.format(cam_params))

        # load pic_settings json
        pic_settings = _getPicSettings(path_to_pic_settings)
        self._logger.debug('Loaded pic_settings: {}'.format(pic_settings))

        # TODO camera resolution and outpic res are independent
        detection_algo = {'new': lambda raw_pic: prepareImage(input_image=raw_pic,
                                                              path_to_output_image=self.tmp_img_prepared,
                                                              cam_dist=cam_params[DIST_KEY],
                                                              cam_matrix=cam_params[MTX_KEY],
                                                              pic_settings=pic_settings,
                                                              size=out_pic_size,
                                                              quality=100,
                                                              debug_out=True,  #self.save_debug_images,
                                                              stopEvent=self.stopEvent,
                                                              threads=4),
                          'legacy': lambda: mb_pic.prepareImage(self.tmp_img_raw,
                                                                self.tmp_img_prepared,
                                                                path_to_cam_params,
                                                                path_to_pic_settings,
                                                                path_to_last_markers,
                                                                size=out_pic_size,  # (h, w),
                                                                save_undistorted=self.undistorted_pic_path,
                                                                quality=75,
                                                                debug_out=self.save_debug_images,
                                                                stopEvent=self.stopEvent, )}
        self._logger.warning("debug state : %s", self.save_debug_images)
        try:
            if self.active():
                # TODO if first run (after open lid) : preliminary brightness measurement
                cam.start_preview()
                time.sleep(2)
                # bestShutterSpeeds = cam.apply_best_shutter_speed()  # Usually only 1 value, but there could be more
                # TODO keep pic in RAM before saving it (no need to save if it is going to be modified or thrown out before serving)

                cam.async_capture()  # starts capture to the cam.worker
            prev = None
            while self.active():
                cam.wait()  # waits until the next picture is ready
                if not self.active(): break  # check if still active...
                # TODO If difference high -> Correct and serve new picture (will save bandwidth)
                # TODO start capture with different brightness if we think we need it
                #     TODO apply shutter speed adjustment from preliminary measurements

                latest = cam.lastPic() # gets last picture given to cam.worker
                cam.async_capture()  # starts capture with new settings
                if latest is None:
                    self._logger.warning("The last picture is empty :O")
                    continue
                # Compare previous image with the current one.
                # Do not save the new img if too similar
                # prev = prev or cv2.imread(self.tmp_img_raw)
                # # TODO gauss blur Compare new and old raw img.
                # if diff(latest, prev) < 50:
                #     # Discard this picture
                #     continue
                # else:
                #     cv2.imwrite(self.tmp_img_raw, latest)
                #     # Write image to disk and continue
                #     del prev
                #     prev = None # free up RAM ?

                if self.image_correction_enabled:
                    self._logger.debug("Starting with correction...")
                    # TODO Toggle : choose which algo to run first ; only run on bad corners from previous run
                    workspaceCorners, markers = detection_algo['new'](latest)
                    for k, v in markers.items():
                        if v is None: del markers[k]
                    success_1 = workspaceCorners is not None
                    # Conform to the legacy result to be sent to frontend
                    correction_result = {'markers_found':      None if markers is None else list(markers.keys()), # {k: v.astype(int) for k, v in markers.items()},
                                         'markers_recognised': len(markers),
                                         'corners_calculated': None if workspaceCorners is None else list(workspaceCorners), # {k: v.astype(int) for k, v in workspaceCorners.items()},
                                         'successful_correction': success_1}
                    self._logger.info("New image correction result: {}".format(correction_result))
                    # Send result to fronted ASAP
                    if success_1:
                        self._move_img(self.tmp_img_prepared, self.final_image_path)
                        self._send_frontend_picture_metadata(correction_result)
                        self.badQualityPicCount = 0

                    # Write the img to disk for the 2nd algo
                    cv2.imwrite(self.tmp_img_raw, cv2.resize(latest, (w, h)))

                    correction_result2 = detection_algo['legacy']()

                    self._logger.debug("Legacy image correction result: {}".format(correction_result2))
                    success_2 = not correction_result2['error']
                    correction_result2['successful_correction'] = success_2
                    # TODO if this brightness was good enough for all the corner detection for this pic, then only use this for next pic.

                    # TODO tweak bestShutterSpeed if needed.

                    if success_2:
                        if not success_1:
                            self._move_img(self.tmp_img_prepared, self.final_image_path)
                        self.badQualityPicCount = 0
                        # Use this picture
                    else:
                        errorID = correction_result2['error'].split(':')[0]
                        errorString = correction_result2['error'].split(':')[1]
                        if errorID == 'BAD_QUALITY':
                            self.badQualityPicCount += 1
                            self._logger.error(
                                    errorString + ' Number of bad quality pics: {}'.format(self.badQualityPicCount))
                            if self.badQualityPicCount > 10:
                                self._logger.error(
                                        'Too many bad pics! Show bad image now.'.format(self.badQualityPicCount))
                                self._move_img(self.tmp_img_raw, self.final_image_path)
                        elif errorID == 'NO_CALIBRATION' or errorID == 'NO_PICTURE_FOUND':
                            self._logger.error(errorString)
                        else:  # Unknown error
                            self._logger.error(errorID + errorString)
                    if not success_1:
                        self._send_frontend_picture_metadata(correction_result2)
                    # TODO Iratxe tweak analytics
                    # self._save_session_details_for_analytics(session_details, correction_result)
            # TODO compare with new algo result if good enough

            self._analytics_handler.add_camera_session_details(session_details)
            self._logger.debug("PhotoCreator stopping...")
        except Exception as worker_exception:
            self._logger.exception("Exception in worker thread of PhotoCreator: {}".format(worker_exception.message))

    def _save_session_details_for_analytics(self, session_details, correction_result):
        try:
            session_details['num_pics'] += 1

            error = correction_result['error']
            if error:
                session_details['errors'].append(error)

            num_detected = correction_result.get('markers_recognized', None)
            if num_detected in session_details['detected_markers']:
                session_details['detected_markers'][num_detected] += 1
            else:
                session_details['detected_markers'][num_detected] = 1
        except Exception as ex:
            self._logger.exception('Exception in _save_session_details_for_analytics: {}'.format(ex))

    def _send_frontend_picture_metadata(self, meta_data):
        self._plugin_manager.send_plugin_message("mrbeam", dict(beam_cam_new_image=meta_data))

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
