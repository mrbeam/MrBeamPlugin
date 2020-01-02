import math
from fractions import Fraction
import cv2, logging
import numpy as np
from numpy.linalg import norm
from itertools import chain
try:
    import octoprint_mrbeam.util.mrbcamera
    from mrbcamera import MrbCamera
    PICAMERA_AVAILABLE = True
except Exception as e:
    from dummycamera import DummyCamera as MrbCamera
    PICAMERA_AVAILABLE = False
    logging.getLogger("octoprint.plugins.mrbeam.iobeam.lidhandler").warn(
            "Could not import module 'picamera'. Disabling camera integration. (%s: %s)", e.__class__.__name__, e)


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

BRIGHTNESS_TOLERANCE = 80
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
        self.good_corner_bright = []
        assert(maxSize > 0)
        self._maxSize = maxSize
        self.times = []  # exposure time values
        self.detectedBrightness = []

    def write(self, buf): # (self, buf: bytearray):
        if buf.startswith(b'\xff\xd8'):
            # New frame; set the current processor going and grab
            # a spare one
            nparr = np.frombuffer(buf, np.int8)
            img_np = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            self.images.append(img_np)
            if len(self.images) > self._maxSize:
                del self.images[0]
                del self.good_corner_bright[0]
                del self.detectedBrightness[0]
            rois = {}
            goodRois = []
            for roi, _, pole in getRois(img_np):
                bright = goodBrightness(roi)
                rois.update({pole: bright})
                if bright == 0:
                    goodRois.append(pole)
            self.good_corner_bright.append(goodRois)
            self.detectedBrightness.append(rois)
            # TODO auto-adjust camera shutter_speed from here
            # print("images stored : ", len(self.images))

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
        cv2.imwrite(path, self.images[-n])


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
    h2, w2 =  h // ratioH, w // ratioW
    borders = {
            N: slice(offsetH, h2 + offsetH),
            S: slice(h - h2 - offsetH, h - offsetH),
            W: slice(offsetW, w2 + offsetW),
            E: slice(w - w2 - offsetW, w - offsetW),
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
    err = (imageA.astype("int16") - imageB.astype("int16")) ** 2
    err[err < tolerance] = 0
    return np.count_nonzero(err)
