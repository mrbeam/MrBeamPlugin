from contextlib import contextmanager
from itertools import chain
import logging
import time
import threading
from threading import Thread, Event

from octoprint_mrbeam.mrb_logger import mrb_logger
from octoprint_mrbeam.camera.camera import BaseCamera, DummyCamera, __camera__
from exc import MrbCameraError, CameraValueException, CameraRuntimeException
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

# NOTICE: This is used by the camera plugin
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
        """Record pictures asynchronously in order to perform corrections
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
        # self._logger = mrb_logger("octoprint.plugins.mrbeam.util.camera.mrbcamera", lvl=logging.INFO)
        BaseCamera.__init__(self, worker, shutter_speed=shutter_speed)
        # PiCamera constructor does not take a worker or shutter_speed
        # https://picamera.readthedocs.io/en/release-1.13/api_camera.html#picamera.PiCamera
        global PICAMERA_AVAILABLE
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

        self.camera_error = False

        # self.exposure_mode = ''
        self.stopEvent = stopEvent or Event()  # creates an unset event if not given

        # TODO load the default settings

    def __enter__(self):
        BaseCamera.__enter__(self)
        global PICAMERA_AVAILABLE
        if PICAMERA_AVAILABLE:
            PiCamera.__enter__(self)
        # Cannot set shutter speed before opening the camera (picamera)
        if self._shutter_speed:
            self.shutter_speed = self._shutter_speed
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        global PICAMERA_AVAILABLE
        if PICAMERA_AVAILABLE:
            PiCamera.__exit__(self, exc_type, exc_value, traceback)
        BaseCamera.__exit__(self, exc_type, exc_value, traceback)

    def capture(self, output=None, format="jpeg", *args, **kwargs):
        global PICAMERA_AVAILABLE
        if output is None:
            output = self.worker

        if PICAMERA_AVAILABLE:
            self._busy.acquire()
        try:
            CameraClass.capture(self, output, format=format, *args, **kwargs)
        except AttributeError as e:
            self._logger.warning(
                "Caught Picamera internal error - self._camera is None"
            )
            self.camera_error = True
            raise exc.CameraException(e)
        except (
            CameraValueException,
            CameraRuntimeException,
        ) as e:
            self._logger.error(
                "Caught Picamera internal error - %s, deactivate PiCamera", e
            )
            self.camera_error = True
            raise exc.CameraException(e)
        except Exception as e:
            self._logger.error("Unknown camera error - %s, deactivate PiCamera", e)
            self.camera_error = True
            raise exc.CameraException(e)
        finally:
            if PICAMERA_AVAILABLE:
                self._busy.release()
