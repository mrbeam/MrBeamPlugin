from contextlib import contextmanager
from itertools import chain
import logging
import time
import threading
from threading import Thread, Event

from octoprint_mrbeam.mrb_logger import mrb_logger
from octoprint_mrbeam.camera.camera import BaseCamera, DummyCamera, __camera__
from exc import MrbCameraError
from . import exc


try:
    import picamera
    from picamera import PiCamera

    PICAMERA_AVAILABLE = True
except (ImportError, OSError) as e:
    PICAMERA_AVAILABLE = False
    logging.getLogger("octoprint.plugins.mrbeam.util.camera").error(
        "Could not import module 'mrbcamera'. Disabling camera integration. (%s: %s)",
        e.__class__.__name__,
        e,
    )


def mrbCamera(*args, **kwargs):
    global __camera__
    if not isinstance(__camera__, MrbCamera):
        if isinstance(__camera__, BaseCamera):
            raise MrbCameraError(
                "Could not create a specialised mrbCamera because an other camera is running."
            )
        __camera__ = MrbCamera(*args, **kwargs)
    elif __camera__.closed:
        __camera__ = MrbCamera(*args, **kwargs)
    return __camera__


CameraClass = PiCamera if PICAMERA_AVAILABLE else DummyCamera


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
        self._logger = mrb_logger("octoprint.plugins.mrbeam.util.camera.mrbcamera")
        BaseCamera.__init__(self, worker, shutter_speed=shutter_speed)
        # PiCamera constructor does not take a worker or shutter_speed
        # https://picamera.readthedocs.io/en/release-1.13/api_camera.html#picamera.PiCamera

        if PICAMERA_AVAILABLE:
            PiCamera.__init__(self, *args, **kwargs)
            self.sensor_mode = 2
            self.vflip = True
            self.hflip = True
            self.iso = 150
            self.awb_mode = "auto"
            self.meter_mode = "matrix"
            self.start_preview()
        else:
            DummyCamera.__init__(self, worker, *args, **kwargs)

        # self.exposure_mode = ''
        self.stopEvent = stopEvent or Event()  # creates an unset event if not given

        # TODO load the default settings

    def __enter__(self):
        BaseCamera.__enter__(self)
        if PICAMERA_AVAILABLE:
            PiCamera.__enter__(self)
        # Cannot set shutter speed before opening the camera (picamera)
        self.shutter_speed = self._shutter_speed
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        if PICAMERA_AVAILABLE:
            PiCamera.__exit__(self, exc_type, exc_value, traceback)
        BaseCamera.__exit__(self, exc_type, exc_value, traceback)

    def capture(self, output=None, format="jpeg", *args, **kwargs):
        if output is None:
            output = self.worker
        if PICAMERA_AVAILABLE:
            if self._busy.locked():
                raise MrbCameraError("Camera already busy taking a picture")
            self._busy.acquire()
        try:
            CameraClass.capture(self, output, format=format, *args, **kwargs)
        finally:
            if PICAMERA_AVAILABLE:
                self._busy.release()
