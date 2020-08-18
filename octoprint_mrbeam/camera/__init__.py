import io
from fractions import Fraction
import cv2, logging
import numpy as np
from numpy.linalg import norm
from threading import Event
from abc import ABCMeta, abstractmethod
import os
from octoprint_mrbeam.mrb_logger import mrb_logger
from octoprint_mrbeam.util.img import differed_imwrite
# Python 3 : use ABC instead of ABCMeta

SUCCESS_WRITE_RETVAL = 1

from octoprint_mrbeam.util.log import logtime, logme

try:
	import picamera
	PICAMERA_AVAILABLE = True
except ImportError as e:
	PICAMERA_AVAILABLE = False
	logging.getLogger(__name__).error(
		"Could not import module 'mrbcamera'. Disabling camera integration. (%s: %s)", e.__class__.__name__, e)


RESOLUTIONS = {
		'1000x780':  (1000, 780),
		'1920x1080': (1920, 1080),
		'2000x1440': (2000, 1440),
		'2048x1536': (2048, 1536),
		'2592x1944': (2592, 1944),
		'2592x1952': (2592, 1952),
}

N, W, S, E = 'N','W','S','E'
NW,NE,SW,SE = N+W, N+E, S+W, S+E
QD_KEYS = [NW,NE,SW,SE]

# Size of the corner search area
RATIO_W, RATIO_H = Fraction(1, 6), Fraction(1, 4)
# Padding distance from the edges of the image (The markers are never pressed against the border)
OFFSET_W, OFFSET_H = Fraction(0, 36), Fraction(0, 20)

LEGACY_STILL_RES = RESOLUTIONS['2048x1536'] # from octoprint_mrbeam __init___ : get_settings_defaults
DEFAULT_STILL_RES = RESOLUTIONS['2592x1944']  # Be careful : Resolutions accepted as increments of 32 horizontally and 16 vertically

# threshold; 2 consecutive pictures need to have a minimum difference
# before being undistorted and served
DIFF_TOLERANCE = 50

TARGET_AVG_ROI_BRIGHTNESS = 170
BRIGHTNESS_TOLERANCE = 40 # TODO Keep the brightness of the images tolerable

class Camera:
	__metaclass__ = ABCMeta

	@abstractmethod
	def __init__(self, stopEvent=None, *args, **kw):
		pass

	@abstractmethod
	def async_capture(self):
		pass

	pass

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
		assert(maxSize > 0)
		self._maxSize = maxSize
		self.times = []  # exposure time values
		self.busy = Event()
		self._logger = mrb_logger("mrbeam.camera.MrbPicWorker")
		if debug: self._logger.setLevel(logging.DEBUG)
		else: self._logger.setLevel(logging.WARNING)

	def currentBuf(self):
		return self.buffers[self.bufferIndex]

	def flush(self):
		# Is called when the camera is done writing the whole image into the buffer
		self.currentBuf().seek(0)
		self.latest = cv2.imdecode(np.fromstring(self.currentBuf().getvalue(), np.int8),
								   cv2.IMREAD_COLOR)
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
		if buf.startswith(b'\xff\xd8') and self.currentBuf().tell() > 0:
			# New frame; and the current buffer is not flushed.
			self.flush()
		# Add the buffer to the currently selected buffer
		self.busy.set()
		self.currentBuf().write(buf)

	def saveImg(self, path, n=1):
		"""Saves the last image or the n-th last buffer"""
		# Unused atm
		assert(0 < n <= self._maxSize)
		f = io.open(path, 'wb')
		ret = f.write(self.buffers[-n])
		f.close()
		return ret

def brightness_result(pic):
	"""
	Will measure which corner has an appropriate amount of brightness, and which
	corner seems to have a brightness correction.
	:param pic: picture to measure on
	:type pic: np.ndarray
	:return: a dict listiing the corners that need shutter speed adjustment,
	:return: a list that of the corners that are fine
	:rtype: Tuple(map, list)
	"""
	return {qd: brightness(roi) for roi, _, qd in getRois(pic)}

def getRois(img, ratioW=RATIO_W, ratioH=RATIO_H,  offsetW=OFFSET_W, offsetH=OFFSET_H): #(img: np.ndarray, ratioW: int=RATIO_W, ratioH: int=RATIO_H,):
	"""
	:param img: the input image from which to get the ROIs from
	:param ratioH: return this fraction of the height of the roi
	:param ratioW: return this fraction of the width  of the roi
	:yields: a slice of the image corresponding to an ROI, it's position and it's name (pole)
	:rtype numpy.ndarray, numpy.ndarray, str
	"""
	# Generator
	for pole in QD_KEYS:
		_sliceVert, _sliceHoriz = _roiSlice(img, pole, ratioW=ratioW, ratioH=ratioH, offsetW=offsetW, offsetH=offsetH)
		h, w = img.shape[:2]
		row, col = _sliceVert.start, _sliceHoriz.start
		# print("row: {}, col {}".format(row, col))
		yield img[_sliceVert, _sliceHoriz], np.array([row, col]), pole

def _roiSlice(img, pole, ratioW=RATIO_W, ratioH=RATIO_H,  offsetW=OFFSET_W, offsetH=OFFSET_H): #(img: np.ndarray, pole: [str, None], ratioW: int=RATIO_W, ratioH: int=RATIO_H, ):
	"""
	Returns a slice of the img that can be used directly as:
	:param img: the input image from which to get the ROIs from
	:type img: numpy.ndarray
	:param pole: The corner region of the image ('NW', 'NE', 'SW', 'SE')
	:type pole: basestring
	:param ratioW: return this fraction of the width  of the roi
	:type ratioW: Union[float, Fraction]
	:param ratioH: return this fraction of the height of the roi
	:type ratioH: Union[float, Fraction]
	:param offsetW: distance from the border of the picture (width-wise)
	:type offsetW: Union[float, Fraction]
	:param offsetH: distance from the border of the picture (height-wise)
	:type offsetH: Union[float, Fraction]
	:return: A slice of a corner region of the input image
	:rtype: tuple[slice]
	"""
	assert(0 < ratioH < 1 and 0 < ratioW < 1)
	h, w = img.shape[:2]
	h2, w2 =  int(h * ratioH), int(w * ratioW)
	oh, ow = int(offsetH * h), int(offsetW * w)
	borders = {
			N: slice(oh, h2 + oh),
			S: slice(h - h2 - oh, h - oh),
			W: slice(ow, w2 + ow),
			E: slice(w - w2 - ow, w - ow),
	}
	_vert, _horiz = pole # assumes the poles are written NW = 'NW' etc...
	return borders[_vert], borders[_horiz]

def brightness(img):
	"""
	Determines of the image brightness is - within a tolerance margin - close
	to a target brightness.
	:param img: Input image
	:type img: numpy.ndarray
	:returns: brightness of the image
	:rtype int
	"""
	if len(img.shape) == 3:
		# Colored RGB or BGR (*Do Not* use HSV images with this function)
		# create brightness with euclidean norm

		pix2pix_brightness = norm(img, axis=2) / np.sqrt(3)
		percentile = np.percentile(pix2pix_brightness, q=80)
		# quantile = np.quantile(pix2pix_brightness, q=0.8) # numpy.__version__ > 1.15.0
		return np.average(pix2pix_brightness[pix2pix_brightness > percentile])
	else:
		# Grayscale
		return np.average(img)

def get_same_size(imageA, imageB, upscale=True):
	"""
	Resizes the smallest to fit the larger image, or the other way around if upscale is False.
	:param imageA:
	:type imageA: np.ndarray
	:param imageB:
	:type imageB: np.ndarray
	:return: The resized versions of imageA and imageB
	:rtype: Tuple(np.ndarray, np.ndarray)
	"""
	if (upscale and imageA.shape[0] > imageB.shape[0]) or \
			(not upscale and imageB.shape[0] > imageA.shape[0]):
		return cv2.resize(imageA, imageB.shape[:2][::-1]), imageB
	elif (upscale and imageB.shape[0] > imageA.shape[0]) or \
			(not upscale and imageA.shape[0] > imageB.shape[0]):
		return imageA, cv2.resize(imageB, imageA.shape[:2][::-1])
	else:
		return imageA, imageB

# @logtime()
def gaussBlurDiff(imageA, imageB, thresh=DIFF_TOLERANCE, blur=7, resize = 1):
	"""
	Compares the two images by blurring them. If the strongest difference measured
	is higher than the threshold, then they are considered to be different and
	the function returns True.
	"""
	assert(blur % 2 == 1)
	if len(imageA.shape) == 3:
		# if img is colored, only keep 1 color channel for comparison
		A, B = (img[:,:,0] for img in (imageA, imageB))
	else:
		A, B = imageA, imageB
	# Resize the images if need be
	if resize != 1:
		A, B = [cv2.resize(img, tuple(int(s * resize) for s in img.shape[:2])) for img in [A,B]]
	images = list(get_same_size(*(A,B), upscale=False))
	images = [cv2.GaussianBlur(img, (blur, blur), 2 * blur) for img in images]
	images = np.asarray(images, dtype=np.int16) # No int overflow
	diff = np.max(np.abs(np.diff(images, axis=0)))
	return np.max(np.abs(np.diff(images, axis=0))) > thresh

#@logtime()
# @logme(True)
def save_debug_img(img, path, folder=None):
	"""Saves the image in a folder along the given path"""
	if not folder:
		folder = os.path.dirname(path)
	else:
		path = os.path.join(folder, path)
	if folder and not os.path.exists(folder):
		os.makedirs(folder)
	return differed_imwrite(path, img)
