from contextlib import contextmanager
from itertools import chain

from octoprint_mrbeam.mrb_logger import mrb_logger
from octoprint_mrbeam.camera.camera import BaseCamera, DummyCamera, __camera__
from exc import MrbCameraError
from .definitions import (
    DEFAULT_SHUTTER_SPEED,
    TARGET_AVG_ROI_BRIGHTNESS,
    BRIGHTNESS_TOLERANCE,
)
from . import exc

try:
    import picamera

    PICAMERA_AVAILABLE = True
except (ImportError, OSError) as e:
    PICAMERA_AVAILABLE = False
    logging.getLogger("octoprint.plugins.mrbeam.util.camera").error(
        "Could not import module 'mrbcamera'. Disabling camera integration. (%s: %s)",
        e.__class__.__name__,
        e,
    )

import time
import threading
from threading import Thread, Event
import logging


def mrbCamera():
    global __camera__
    if not isinstance(__camera__, mrbCamera):
        if isinstance(__camera__, BaseCamera):
            raise MrbCameraError(
                "Could not create a specialised mrbCamera because an other camera is running."
            )
        __camera__ = MrbCamera()
    return __camera__


CameraClass = PiCamera if PICAMERA else DummyCamera


class MrbCamera(CameraClass, BaseCamera):
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
        # This is a bit hacky but it makes sure that we don't try using PiCamera in case it's not imported
        # might need to change if inheriting from multiple classes
        BaseCamera.__init__(self, worker, shutter_speed=shutter_speed)
        CameraClass.__init__(self, worker, shutter_speed=shutter_speed, *args, **kwargs)
        if PICAMERA:
            self.sensor_mode = 2
            self.vflip = True
            self.hflip = True
            self.iso = 150
            self.awb_mode = "auto"
            self.meter_mode = "matrix"
            self.start_preview()
        # self.exposure_mode = ''
        self.stopEvent = stopEvent or Event()  # creates an unset event if not given
        self._logger = mrb_logger(
            "octoprint.plugins.mrbeam.util.camera.mrbcamera", lvl=logging.INFO
        )
        self.busy = threading.Event()

        if shutter_speed is not None:
            self.shutter_speed = shutter_speed
        # TODO load the default settings

    def capture(self, output=None, format="jpeg", *args, **kwargs):
        if output is None:
            output = self.worker
        if self._busy.is_set():
            raise MrbCameraError("Camera already busy taking a picture")
        self._busy.set()
        try:
            super(MrbCamera, self).capture(self, output, format=format, *args, **kwargs)
        finally:
            self._busy.clear()

    def compensate_shutter_speed(self, img):
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
        self._logger.debug(
            "Brightnesses: \nMin %s  Max %s\nCurrent %s"
            % (min_bright, max_bright, brightness)
        )
        if _minb < min_bright and _maxb > max_bright:
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
        self.exposure_mode = "off"
        self._logger.info("exposure_speed: %s" % self.exposure_speed)
        self.shutter_speed = autoShutterSpeed + 1

        # Always takes the first picture with the auto calibrated mode
        for i, img in enumerate(
            self.capture_continuous(
                self.worker, format="jpeg", quality=100, use_video_port=True
            )
        ):
            if i % 2 == 1:
                continue  # The values set are only applied for the following picture
            self.compensate_shutter_speed(img)
            if i > 13:
                break
