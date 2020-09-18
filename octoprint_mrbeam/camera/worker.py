from definitions import SUCCESS_WRITE_RETVAL
import cv2
import io
import logging
from threading import Event

from octoprint_mrbeam.camera import brightness_result
from octoprint_mrbeam.mrb_logger import mrb_logger
import numpy as np


class MrbPicWorker(object):
    """
	The class that take care of buffering the pictures taken from the camera.
	It can also do frame-by-frame work, but it could hurt recording speed (better
	to split the work on a different thread)
	See "Advanced Recipies" in the PiCamera tutorials:
	https://picamera.readthedocs.io/en/release-1.13/recipes2.html
	"""

    def __init__(self, maxSize=3, debug=False):
        self.images = []
        self.firstImg = True
        self.buffers = [io.BytesIO() for _ in range(maxSize)]
        self.bufferIndex = 0
        self.latest = None
        self.avg_roi_brightness = {}
        assert maxSize > 0
        self._maxSize = maxSize
        self.times = []  # exposure time values
        self.busy = Event()
        self._logger = mrb_logger("mrbeam.camera.MrbPicWorker")
        if debug:
            self._logger.setLevel(logging.DEBUG)
        else:
            self._logger.setLevel(logging.WARNING)

    def currentBuf(self):
        return self.buffers[self.bufferIndex]

    def flush(self):
        # Is called when the camera is done writing the whole image into the buffer
        self.currentBuf().seek(0)
        self.latest = cv2.imdecode(
            np.fromstring(self.currentBuf().getvalue(), np.int8), cv2.IMREAD_COLOR
        )
        self.bufferIndex = (self.bufferIndex + 1) % self._maxSize
        self.currentBuf().seek(0)
        self.currentBuf().truncate()
        self.avg_roi_brightness = brightness_result(self.latest)
        # TODO adjust camera shutter speed with these brightness measurements
        self.busy.clear()

    def write(self, buf):  # (self, buf: bytearray):
        """
		Write into the current buffer.
		Will automatically change buffer when a new JPEG image is detected.
		"""
        if buf.startswith(b"\xff\xd8") and self.currentBuf().tell() > 0:
            # New frame; and the current buffer is not flushed.
            self.flush()
        # Add the buffer to the currently selected buffer
        self.busy.set()
        self.currentBuf().write(buf)

    def saveImg(self, path, n=1):
        """Saves the last image or the n-th last buffer"""
        # Unused atm
        assert 0 < n <= self._maxSize
        f = io.open(path, "wb")
        ret = f.write(self.buffers[-n])
        f.close()
        return ret
