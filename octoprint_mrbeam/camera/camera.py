#!/usr/bin/env python

from collections import deque
from contextlib import contextmanager
from threading import Thread, Lock, Event

from exc import MrbCameraError

from octoprint.settings import settings

# global camera
__camera__ = None
__camera_lock__ = Lock()


def camera():
    """Make sure we only use one camera element at a time."""
    global __camera__
    if not isinstance(__camera__, Camera):
        __camera__ = DummyCamera()
    return __camera__


class BaseCamera(object):
    """Base Camera class for the plugin."""

    @contextmanager
    def __init__(self, worker, shutter_speed=None, *args, **kwargs):
        """
        :param worker: The pictures are recorded into this
        :type worker: str, "writable", filename or class with a write function (see PiCamera.capture input)
        """
        global __camera_lock__
        if __camera_lock__.locked():
            raise MrbCameraError("Camera already in use in an other thread")
        __camera_lock__.acquire()

        self._busy = Event()  # When the camera is taking a picture
        self._async_capture_thread = (
            None  # Thread that takes the picture asynchronously
        )
        self.worker = worker
        self.shutter_speed = shutter_speed
        self._capture_args = (self.worker,)
        self._capture_kwargs = dict(format="jpeg")

        try:
            yield self
        finally:
            __camera_lock__.release()

    def capture(self, output=None, *args, **kwargs):
        """Take a picture immediatly and return the picture object

        Should set the ``self._busy`` event during the capture
        """
        raise NotImplementedError

    def async_capture(self, **kwargs):
        """
        Starts or signals the camera to start taking a new picture.
        The new picture can be retrieved with MrbCamera.lastPic()
        Wait for the picture to be taken with MrbCamera.wait()
        :param kw:
        :type kw:
        :return:
        :rtype:
        """
        _args = self._capture_args
        _kwargs = self._capture_kwargs
        _kwargs.update(kwargs)
        t = Thread(target=self.capture, args=_args, kwargs=_kwargs)
        self._async_capture_thread = t
        t.start()
        return t

    def wait(self, timeout=None):
        """Wait until the camera is available again to take a picture"""
        return self._busy.wait(timeout=timeout)

    def lastPic(self):
        """Returns the last picture taken"""
        return self.worker.latest


class DummyCamera(BaseCamera):
    from octoprint_mrbeam.camera.worker import MrbPicWorker

    DEFAULT_PIC = settings().get(
        ["mrbeam", "mock", "img_static"], defaults=settings().get(["webcam"])
    )
    # DEFAULT_PIC = DEFAULT_PIC or settings().get(["webcam"])
    DEFAULT_FOLDER = settings().get(["mrbeam", "mock", "img_folder"])

    def __init__(self, *args, **kwargs):
        BaseCamera.__init__(self, *args, **kwargs)
        self._input_files = deque([])
        if DEFAULT_FOLDER:
            for path in DEFAULT_FOLDER:
                self._input_files.append(path)
        elif DEFAULT_PIC:
            self._input_files.append(path)
        else:
            raise MrbCameraError(
                "No picture paths have been defined for the dummy camera."
            )

    def capture(self, output=None, format="jpeg", *args, **kwargs):
        """Mocks the behaviour of picamera.PiCamera.capture, with the caviat that"""
        if self._busy.is_set():
            raise MrbCameraError("Camera already busy taking a picture")
        self._busy.set()
        if not output:
            output = self.worker
        _input = self.input_files[0]
        if isinstance(output, basestring):
            os.copy2(_input, output)
        elif "write" in dir(output):
            with open(_input, "rb") as f:
                output.write(f)
        else:
            raise MrbCameraError(
                "Nothing to write into - either output or the worker are no a path or writeable objects"
            )
        self._busy.clear()
        self._input_files.rotate()
