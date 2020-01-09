import io
import math
from fractions import Fraction
import cv2, logging
import numpy as np
from numpy.linalg import norm
from itertools import chain
# try:
from octoprint_mrbeam.util.camera.mrbcamera import MrbCamera, BRIGHTNESS_TOLERANCE
PICAMERA_AVAILABLE = True
# except Exception as e:
#     from dummycamera import DummyCamera as MrbCamera
#     PICAMERA_AVAILABLE = False
#     logging.getLogger("octoprint.plugins.mrbeam.util.camera").error(
#             "Could not import module 'mrbcamera'. Disabling camera integration. (%s: %s)", e.__class__.__name__, e)


RESOLUTIONS = {
        '1000x780':  (1000, 780),
        '1920x1080': (1920, 1080),
        '2592x1952': (2592, 1952),
        '2592x1944': (2592, 1944),
        '2000x1440': (2000, 1440)
}
DEFAULT_STILL_RES = RESOLUTIONS['2592x1944']  # Be careful : Resolutions accepted as increments of 32 horizontally and 16 vertically


N, W, S, E = 'N','W','S','E'
NW,NE,SW,SE = N+W, N+E, S+W, S+E
QD_KEYS = [NW,NE,SW,SE]

# Size of the corner search area
RATIO_W, RATIO_H = Fraction(1, 8), Fraction(1, 4)
# Padding distance from the edges of the image (The markers are never pressed against the border)
OFFSET_W, OFFSET_H = Fraction(1, 32), Fraction(1, 10)

DIFF_TOLERANCE = 400

MrbCamera = MrbCamera # Makes it importable

def goodBrightness(img, targetAvg=128, tolerance=BRIGHTNESS_TOLERANCE):
    """
    Returns 0 if the brightness is inside the tolerance margins,
    Returns the offset brightness if outside
    """
    if len(img.shape) == 3:
        # create brightness with euclidean norm
        brightness = np.average(norm(img, axis=0))
    else:
        # Grayscale
        brightness = np.average(img)

    if abs(brightness - targetAvg) < tolerance:
        return 0
    else:
        return brightness - targetAvg


class MrbPicWorker(object):
    def __init__(self, maxSize=3):
        self.images = []
        self.firstImg = True
        self.buffers = [io.BytesIO() for _ in range(maxSize)]
        self.bufferIndex = 0
        self.latest = None
        self.good_corner_bright = []
        assert(maxSize > 0)
        self._maxSize = maxSize
        self.times = []  # exposure time values
        self.detectedBrightness = []
        self._logger = logging.getLogger("octoprint.plugins.mrbeam.util.camera.MrbPicWorker")

    def write(self, buf): # (self, buf: bytearray):
        # try:
        if buf.startswith(b'\xff\xd8') and not self.firstImg:
            # New frame; set the current processor going and grab
            # a spare one
            self.currentBuf().seek(0)
            self.latest = cv2.imdecode(np.fromstring(self.currentBuf().getvalue(), np.int8),
                                       cv2.IMREAD_COLOR)
            self.bufferIndex = (self.bufferIndex + 1) % self._maxSize
            self.currentBuf().seek(0)
            self.currentBuf().truncate()
            # TODO start thread alongside for the light processing ?
            if len(self.good_corner_bright) > self._maxSize:
                del self.good_corner_bright[0]
                del self.detectedBrightness[0]
            rois = {}
            goodRois = []
            for roi, _, pole in getRois(self.latest):
                bright = goodBrightness(roi)
                rois.update({pole: bright})
                if bright == 0:
                    goodRois.append(pole)
            self.good_corner_bright.append(goodRois)
            self.detectedBrightness.append(rois)
            # TODO auto-adjust camera shutter_speed from here
            # print("images stored : ", len(self.images))

        # except Exception as e:
        #     self._logger.error("%s, %s", e.__class__.__name__, e)
        # Add the buffer to the currently selected buffer

        self.currentBuf().write(buf)
        self.firstImg = False

    def currentBuf(self):
        return self.buffers[self.bufferIndex]

    def flush(self):
        return

    def allCornersCovered(self):
        # TODO good_corners_bright changed
        return all(qd in chain(self.good_corner_bright) for qd in QD_KEYS)

    def bestImg(self, targetAvg=128):
        bestIndex = -1
        bestDist = -1
        for i, img in enumerate(self.images):
            if bestDist == -1 or abs(np.average(img) - targetAvg) < bestDist:
                bestDist = abs(np.average(img) - targetAvg)
                bestIndex = i
        return bestIndex, self.images[bestIndex]

    def merge(self, names=None):  # Iterator=None):
        """Use the Mertens picture merging algo to create an HDR-like picture"""
        # When told to flush (this indicates end of recording), shut
        # down in an orderly fashion.
        print("images fused : ", len(self.images))
        for i, img in enumerate(self.images):
            if names:
                cv2.imwrite(next(names), img)
            else:
                cv2.imwrite("really%i.jpg" % i, img)
        merge_mertens = cv2.createMergeMertens()
        return merge_mertens.process(self.images) * 255  # , times=times

    def saveImg(self, path, n=1):
        """Saves the last image or the n-th last image"""
        cv2.imwrite(path, self.latest)


def getRois(img, ratioW=RATIO_W, ratioH=RATIO_H,  offsetW=OFFSET_W, offsetH=OFFSET_H): #(img: np.ndarray, ratioW: int=RATIO_W, ratioH: int=RATIO_H,):
    # Generator
    for pole in QD_KEYS:
        _sliceVert, _sliceHoriz = _roiSlice(img, pole, ratioW, ratioH, offsetW, offsetH)
        h, w = img.shape[:2]
        row, col = _sliceVert.start, _sliceHoriz.start
        # print("row: {}, col {}".format(row, col))
        yield img[_sliceVert, _sliceHoriz], np.array([row, col]), pole

def _roiSlice(img, pole, ratioW=RATIO_W, ratioH=RATIO_H,  offsetW=OFFSET_W, offsetH=OFFSET_H): #(img: np.ndarray, pole: [str, None], ratioW: int=RATIO_W, ratioH: int=RATIO_H, ):
    # returns a slice of the img that can be used directly as:
    # _slice = _roiSlice(img, pole)
    # roi = img[_slice]
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

def mse(imageA, imageB):
    # the 'Mean Squared Error' between the two images is the
    # sum of the squared difference between the two images;
    # NOTE: the two images must have the same dimension
    err = np.sum((imageA.astype("float") - imageB.astype("float")) ** 2)
    err /= float(imageA.shape[0] * imageA.shape[1])

    # return the MSE, the lower the error, the more "similar"
    # the two images are
    return err

def diff(imageA, imageB, tolerance=DIFF_TOLERANCE):
    """The number of pixels that have a higher square difference than the threshold"""
    # NOTE: the two images must have the same dimension
    if imageA.shape[0] > imageB.shape[0]:
        imageA = cv2.resize(imageA, imageB.shape[:2][::-1])
    if imageB.shape[0] > imageA.shape[0]:
        imageB = cv2.resize(imageB, imageA.shape[:2][::-1])
    err = (imageA.astype("int16") - imageB.astype("int16")) ** 2
    err[err < tolerance] = 0
    return np.count_nonzero(err)
