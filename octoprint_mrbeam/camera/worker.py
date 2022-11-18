from collections import deque
from definitions import SUCCESS_WRITE_RETVAL
import cv2
import io
import logging
from threading import Event

from octoprint_mrbeam.camera import brightness_result
from octoprint_mrbeam.mrb_logger import mrb_logger
import numpy as np


class MrbPicWorker(deque):
    """Circular raw I/O buffer designed for storing pictures.

    It could also do frame-by-frame work, but it could hurt recording speed (better
    to split the work on a different thread)
    See "Advanced Recipies" in the PiCamera tutorials:
    https://picamera.readthedocs.io/en/release-1.13/recipes2.html
    """

    def __init__(self, debug=False, maxlen=2, *args, **kwargs):
        deque.__init__(self, maxlen=maxlen, *args, **kwargs)
        assert maxlen > 0
        for _ in range(maxlen):
            self.append(io.BytesIO())
        self.latest = None
        self.avg_roi_brightness = {}
        self.busy = Event()
        self.count = 0
        self._logger = mrb_logger("mrbeam.camera.MrbPicWorker")

    def currentBuf(self):
        return self[0]

    def flush(self):
        # Is called when the camera is done writing the whole image into the buffer
        # PiCamera.capture calls this automatically when it done
        self.count += 1
        self.currentBuf().seek(0)
        self.latest = cv2.imdecode(
            np.fromstring(self.currentBuf().getvalue(), np.int8), cv2.IMREAD_COLOR
        )
        self.rotate()
        self.currentBuf().seek(0)
        self.currentBuf().truncate()
        self.avg_roi_brightness = brightness_result(self.latest)
        # TODO adjust camera shutter speed with these brightness measurements
        self.busy.clear()

    def write(self, buf):  # (self, buf: bytearray):
        """Write into the current buffer.

        Will automatically change buffer when a new JPEG image is
        detected.
        """
        if buf.startswith(b"\xff\xd8") and self.currentBuf().tell() > 0:
            # New frame; and the current buffer is not flushed.
            self.flush()
        # Add the buffer to the currently selected buffer
        self.busy.set()
        self.currentBuf().write(buf)

    def saveImg(self, path, n=1):
        """Saves the last image or the n-th buffer starting from the end."""
        # Unused atm
        assert 0 < n <= self.maxlen
        ret = None
        with io.open(path, "wb") as f:
            ret = f.write(self[-n])
        return ret
