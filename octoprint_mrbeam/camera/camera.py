#!/usr/bin/env python

from collections import deque
import logging
from threading import Thread, Lock, Event
import time

from exc import MrbCameraError

from octoprint.settings import settings
from .definitions import (
    DEFAULT_SHUTTER_SPEED,
    TARGET_AVG_ROI_BRIGHTNESS,
    BRIGHTNESS_TOLERANCE,
)
from octoprint_mrbeam.mrb_logger import mrb_logger
from octoprint_mrbeam.util import get_thread

# global camera
__camera__ = None
__camera_lock__ = Lock()


def camera(*args, **kwargs):
    """Make sure we only use one camera element at a time."""
    global __camera__
    if not isinstance(__camera__, Camera):
        __camera__ = DummyCamera(*args, **kwargs)
    return __camera__


class BaseCamera(object):
    """Base Camera class for the plugin."""

    # @contextmanager
    def __init__(self, worker, shutter_speed=0, *args, **kwargs):
        """
        :param worker: The pictures are recorded into this
        :type worker: str, "writable", filename or class with a write function (see PiCamera.capture input)
        """
        self._busy = Lock()  # When the camera is taking a picture
        # Thread that takes the picture asynchronously
        self._logger = mrb_logger(__name__, lvl=logging.INFO)
        self._async_capture_thread = None
        self.worker = worker
        self._shutter_speed = shutter_speed
        self._capture_args = (self.worker,)
        self._capture_kwargs = dict(format="jpeg")
        self.__closed = False

    def __enter__(self):
        global __camera_lock__
        if __camera_lock__.locked():
            raise MrbCameraError("Camera already in use in an other thread")
        __camera_lock__.acquire()
        self._logger.info("Starting the camera")

    def __exit__(self, exc_type, exc_value, traceback):
        global __camera_lock__
        self._logger.info("Stopping the camera")
        __camera_lock__.release()
        self.__closed = True

    def close(self):
        self.__closed = True

    def capture(self, output=None, *args, **kwargs):
        """Take a picture immediatly and return the picture object.

        Should acquire the ``self._busy`` lock during the capture
        """
        self._logger.error("capturing from BaseCamera")
        raise NotImplementedError

    def async_capture(self, **kwargs):
        """Starts or signals the camera to start taking a new picture. The new
        picture can be retrieved with MrbCamera.lastPic() Wait for the picture
        to be taken with MrbCamera.wait()

        :param kw:
        :type kw:
        :return:
        :rtype:
        """
        if self.__closed:
            raise MrbCameraError("The camera is closed.")
        _args = self._capture_args
        _kwargs = self._capture_kwargs
        _kwargs.update(kwargs)
        self._async_capture_thread = get_thread(daemon=True,)(
            self.capture
        )(*_args, **_kwargs)
        return self._async_capture_thread

    def wait(self, timeout=None):
        """Wait until the camera is available again to take a picture."""
        self._busy.acquire()
        self._busy.release()

    def lastPic(self):
        """Returns the last picture taken."""
        return self.worker.latest

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


from octoprint_mrbeam.camera.worker import MrbPicWorker


class DummyCamera(BaseCamera):
    def __init__(self, *args, **kwargs):
        from os.path import dirname, basename, join, split, realpath

        BaseCamera.__init__(self, *args, **kwargs)
        path = dirname(realpath(__file__))
        CAM_DIR = join(path, "rsc", "camera")
        try:
            self.def_pic = settings().get(
                ["mrbeam", "mock", "img_static"], defaults=settings().get(["webcam"])
            )
            self.def_folder = settings().get(["mrbeam", "mock", "img_folder"])
        except ValueError:
            sett = settings(init=True)
            self.def_pic = sett.get(
                ["mrbeam", "mock", "img_static"], defaults=sett.get(["webcam"])
            )
            self.def_folder = sett.get(["mrbeam", "mock", "img_folder"])
        self._input_files = deque([])
        if self.def_folder:
            for path in self.def_folder:
                self._input_files.append(path)
        elif self.def_pic:
            self._input_files.append(self.def_pic)
        else:
            raise MrbCameraError(
                "No picture paths have been defined for the dummy camera."
            )

    def capture(self, output=None, format="jpeg", *args, **kwargs):
        """Mocks the behaviour of picamera.PiCamera.capture, with the caviat
        that."""
        import numpy as np
        import cv2

        if self._busy.locked():
            raise MrbCameraError("Camera already busy taking a picture")
        self._busy.acquire()
        if self._shutter_speed and self._shutter_speed > 0:
            time.sleep(1 / _shutter_speed)
        else:
            time.sleep(0.3)
        if not output:
            output = self.worker
        _input = self._input_files[0]
        if isinstance(output, basestring):
            os.copy2(_input, output)
        elif "write" in dir(output):
            with open(_input, "rb") as f:
                output.write(f.read())
            if "flush" in dir(output):
                output.flush()
        else:
            raise MrbCameraError(
                "Nothing to write into - either output or the worker are no a path or writeable objects"
            )
        self._busy.release()
        self._input_files.rotate()
