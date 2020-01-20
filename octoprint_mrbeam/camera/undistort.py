from multiprocessing import Pool
from fractions import Fraction
from numpy.linalg import norm

from octoprint_mrbeam.camera import RESOLUTIONS, QD_KEYS
import octoprint_mrbeam.camera as beamcam
from octoprint_mrbeam.util import dict_merge

CALIB_MARKERS_KEY = 'calibMarkers'
CORNERS_KEY = 'cornersFromImage'
M2C_VECTOR_KEY = 'marker2cornerVecs'
BLUR_FACTOR_THRESHOLD_KEY = 'blur_factor_threshold'
CALIBRATION_UPDATED_KEY = 'calibration_updated'
VERSION_KEY = 'version'
DIST_KEY = 'dist'
MTX_KEY = 'mtx'
RATIO_W_KEY = 'ratioW'
RATIO_H_KEY = 'ratioH'

STOP_EVENT_ERR = 'StopEvent was raised'

HUE_BAND_LB_KEY = 'hue_lower_bound'
HUE_BAND_LB = 125
HUE_BAND_UB = 185 # if value > 180 : loops back to 0

PIC_SETTINGS = {CALIB_MARKERS_KEY: None, CORNERS_KEY: None, M2C_VECTOR_KEY: None, CALIBRATION_UPDATED_KEY: False}

import logging
import time
import os
from os.path import dirname, basename, isfile, exists
import cv2
import numpy as np

PIXEL_THRESHOLD_MIN = 200


class MbPicPrepError(Exception):
    """Something went wrong when undistorting and aligning the picture for the front-end"""
    pass

def prepareImage(input_image,  #: Union[str, np.ndarray],
                 path_to_output_image,  #: str,
                 cam_dist,  #: ? np.ndarray ?,
                 cam_matrix,  #: ? np.ndarray ?,
                 pic_settings,  #: Map or str
                 last_markers=None, # {'NW': np.array(I, J), ... }
                 size=RESOLUTIONS['1000x780'],
                 quality=90,
                 save_undistorted=None,
                 debug_out=False,
                 blur=7,
                 custom_pic_settings=None,
                 stopEvent=None,
                 threads=-1):
    """
    Loads image from path_to_input_image, does some preparations (undistort, warp)
    on it and saves it to path_to_output_img.

    :param input_image: The image to prepare. Either a filepath or a numpy array (as understood by cv2)
    :param path_to_output_image: filepath where to save the image to
    :param cam_dist: camera distance matrix (see cv2.camera_calibrate)
    :param cam_matrix: camera distortion matrix (see cv2.camera_calibrate)
    :param pic_settings: path to - or map as given by - pic_config.yaml
    :param last_markers: used to compensate if a (single) marker is covered or unrecognised
    :param size : (width,height) of output image size, default is (1000,780)
    :param quality: set quality of output image from 0 to 100, default is 90
    :param save_undistorted: path to where the undistorted picture should be saved
    :param debug_out: True if all in between pictures should be saved to output path directory
    :param blur: Amount of blur for the marker detection
    :param custom_pic_settings: Map : used to update certain keys of the pic settings file
    :param stopEvent: used to exit gracefully
    :param threads: number of threads to use for the marker detection. Set -1, 1, 2, 3 or 4. (recommended : 4, default: -1)
    """
    logger = logging.getLogger('mrbeam.camera.undistort')
    if debug_out:
        logger.setLevel(logging.DEBUG)
        logger.info("DEBUG enabled")
    else:
        logger.setLevel(logging.WARNING)

    err = None

    # load pic_settings json
    if type(pic_settings) is str:
        pic_settings = _getPicSettings(pic_settings, custom_pic_settings)
        logger.debug('Loaded pic_settings: {}'.format(pic_settings))

    if not (M2C_VECTOR_KEY in pic_settings and _isValidQdDict(pic_settings[M2C_VECTOR_KEY])):
        pic_settings[M2C_VECTOR_KEY] = None
        err = 'No valid M2C_VECTORS found, please calibrate.'
        logger.error(err)
        return None, None, None, err

    if type(input_image) is str:
        # check image path
        logger.debug('Starting to prepare Image. \ninput: <{}> \noutput: <{}>\ncam dist : <{}>\ncam matrix: <{}>\nsize:{}\nquality:{}\nsave_undistorted:{}\ndebug_out:{}'.format(
                input_image, path_to_output_image, cam_dist, cam_matrix,
                size, quality, save_undistorted, debug_out))
        if not isfile(input_image):
            no_Image_error_String = 'Could not find a picture under path: <{}>'.format(input_image)
            logger.error(no_Image_error_String)
            return None, None, None, no_Image_error_String

        # load image
        img = cv2.imread(input_image, cv2.IMREAD_COLOR) #BGR
        if img is None:
            err = 'Could not load Image. Please check Camera and path_to_image.'
            logger.error(err)
            return None, None, None, err
    elif type(input_image) is np.ndarray:
        logger.debug('Starting to prepare Image. \ninput: <{}> \noutput: <{}>\ncam dist : <{}>\ncam matrix: <{}>\nsize:{}\nquality:{}\nsave_undistorted:{}\ndebug_out:{}'.format(
                "numpy ndarray", path_to_output_image, cam_dist, cam_matrix,
                size, quality, save_undistorted, debug_out))
        img = input_image
    else:
        raise ValueError("path_to_input_image in mb_pic needs to be a path (string) or a numpy array")
    # undistort image with cam_params
    img = _undistortImage(img, cam_dist, cam_matrix)

    if debug_out:
        save_debug_img(img, path_to_output_image, "undistorted")

    if stopEvent.isSet(): return None, None, None, STOP_EVENT_ERR

    # search markers on undistorted pic
    dbg_markers = os.path.join(dirname(path_to_output_image), "markers", basename(path_to_output_image))
    _mkdir(dirname(dbg_markers))
    outputPoints = _getColoredMarkerPositions(img,
                                              debug_out_path=dbg_markers,
                                              blur=blur,
                                              threads=threads)
    logger.debug('positions found: \n%s\n%s\n%s\n%s', *outputPoints.items())
    markers = {}
    # list of missed markers
    missed = []
    # TODO Python3 elegant filter : if len(list(filter(None.__ne__, markers.values()))) < 4: # elif # filter out None values
    for qd, val in outputPoints.items():
        if val is None:
            if last_markers is not None and qd in last_markers.keys():
                markers[qd] = last_markers[qd]
            missed.append(qd)
        else:
            markers[qd] = val['pos']

    # check if picture should be thrown away
    # if less then 3 markers are found
    # if len(missed) > 1 and len(markers) == 4:  # elif # filter out None values
    #     err = 'BAD_QUALITY:Too few markers (circles) recognized.'
    #     logger.debug(err)
    #     return None, markers, missed, err
    # elif len(missed) == 1 and len(markers) == 4:
    if len(missed) > 1 and len(markers) == 4:
        err = "Missed marker %s" % missed[0]
        logger.warning(err)
    elif len(markers) < 4:
        err = "Missed marker(s) %s, no(t enough) history to guess missing marker position(s)" % missed
        logger.warning(err)
        return None, markers, missed, err

    if stopEvent.isSet(): return None, markers, missed, STOP_EVENT_ERR

    if debug_out: save_debug_img(_debug_drawMarkers(img, markers), path_to_output_image, "drawmarkers")

    # get corners of working area
    workspaceCorners = {qd: markers[qd] + pic_settings[M2C_VECTOR_KEY][qd][::-1] for qd in QD_KEYS}
    logger.debug("Workspace corners \nNW % 14s  NE % 14s\nSW % 14s  SE % 14s"
                 % tuple(map(np.ndarray.tolist, map(workspaceCorners.__getitem__, ['NW', 'NE', 'SW', 'SE']))))
    if debug_out: save_debug_img(_debug_drawCorners(img, workspaceCorners), path_to_output_image, "drawcorners")

    # warp image
    warpedImg = _warpImgByCorners(img, workspaceCorners)
    if debug_out: save_debug_img(warpedImg, path_to_output_image, "colorwarp")

    if stopEvent.isSet(): return None, markers, missed, STOP_EVENT_ERR

    # resize and do NOT make greyscale, then save it
    # cv2.imwrite(filename=path_to_output_image,
    #             img=cv2.resize(warpedImg, size),
    #             params=[int(cv2.IMWRITE_JPEG_QUALITY), quality])
    # resize and MAKE greyscale, then save it
    cv2.imwrite(filename=path_to_output_image,
                img=cv2.cvtColor(cv2.resize(warpedImg, size), cv2.COLOR_BGR2GRAY),
                params=[int(cv2.IMWRITE_JPEG_QUALITY), quality])

    return workspaceCorners, markers, missed, err

def _getColoredMarkerPositions(img, debug_out_path=None, blur=5, threads=-1):
    """Allows a multi-processing implementation of the marker detection algo. Up to 4 processes needed."""
    outputPoints = {}
    # check all 4 corners
    CORES = 4 # recommended to use 4 processes for the 4 different threads
    if threads > 0:
        # takes around ~ 10MB RAM / thread
        p = Pool(threads)
        results = {}
        brightness = None
        for roi, pos, qd in beamcam.getRois(img):
            brightness = np.average(roi)
            # print("brightness of corner {} : {}".format(qd, brightness))
            outputPoints[qd] = {'brightness': brightness} # Todo Ignore -> Tested in the MrbImgWorker
            results[qd] = (p.apply_async(_getColoredMarkerPosition,
                                         args=(roi,),
                                         kwds=dict(debug_out_path=debug_out_path,
                                                   blur=blur,
                                                   quadrant=qd)), pos)
        while not all(r.ready() for r, pos in results.values()):
            time.sleep(.1)
        p.close()
        for qd, (r, pos) in results.items():
            outputPoints[qd] = r.get()
            if outputPoints[qd] is not None:
                outputPoints[qd]['pos'] += pos
        p.join()

    else:
        for roi, pos, qd in beamcam.getRois(img):
            brightness = np.average(roi)
            # print("brightness of corner {} : {}".format(qd, brightness))
            outputPoints[qd] = {'brightness': brightness}
            outputPoints[qd] = _getColoredMarkerPosition(roi,
                                                         debug_out_path=debug_out_path,
                                                         blur=blur,
                                                         quadrant=qd)
            if outputPoints[qd] is not None:
                outputPoints[qd]['pos'] += pos
    return outputPoints

def _getColoredMarkerPosition(roi, debug_out_path=None, blur=5, quadrant=None, rmin=8, rmax=30):
    logger = logging.getLogger('mrbeam.camera.undistort')
    # TODO Use mask to eliminate false positives
    # Smooth out picture
    roiBlur = cv2.GaussianBlur(roi, (blur, blur), 0)
    # Use the opposite color of Magenta (Green) to contrast the markers the most
    transformToGreen = np.array([[.0, 1.0, .0]])
    greenBlur = cv2.transform(roiBlur, transformToGreen)
    # debugShow(greenBlur, "green")
    # Threshold the green channel
    ret, threshOtsuMask = cv2.threshold(greenBlur, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
    blocksize = 11
    gaussianMask = cv2.adaptiveThreshold(greenBlur, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY_INV, blocksize, 2)
    roiBlurThresh         =  cv2.bitwise_and( roiBlur, roiBlur, mask=cv2.bitwise_or(threshOtsuMask, gaussianMask))
    # debugShow(roiBlurThresh, "otsu")
    hsv_roiBlurThresh     =  cv2.cvtColor(    roiBlurThresh,     cv2.COLOR_BGR2HSV)
    # Use a sliding hue mask with a local maxima detector to find the magenta markers
    hsv_roiBlurThreshBand, hsvMask = _get_hue_mask(hsv_roiBlurThresh, bandsize=23, pixTrigAmount = PIXEL_THRESHOLD_MIN)
    if hsv_roiBlurThreshBand is None:
        cv2.imwrite(debug_out_path.replace('.jpg', '{}.jpg'.format(quadrant)), roiBlurThresh)
        return None
    # Label each separate zones on the mask (The black background + the white blobs)
    lenLabels, labels = cv2.connectedComponents(hsvMask)
    # logger.debug("Nb of labels : %d", lenLabels)

    unique_labels, counts_elements = np.unique(labels, return_counts=True)
    # logger.debug("Nb of each labels : %s", counts_elements)
    # Sort out the most common (background black) label by setting it's freq to 0
    black_label_index = np.argmax(counts_elements)
    counts_elements[black_label_index] = 0
    # Get the second most common label (The biggest white blob)
    most_present_label = unique_labels[np.argmax(counts_elements)]
    # get the geometrical center of that blob
    non_zeros = np.transpose(np.nonzero(labels == most_present_label))
    center = (np.max(non_zeros, axis=0) + np.min(non_zeros, axis=0)) / 2
    # TODO extra precision : apply marker_mask to find more precise location to the marker

    # ensure at least some circles were found
    if debug_out_path is not None:
        debug_quad_path = debug_out_path.replace('.jpg', '{}.jpg'.format(quadrant))
        logger.debug("Writing debug image at %s", debug_out_path)
        if center is None:
            cv2.imwrite(debug_quad_path, hsvMask)
            # debugShow(roiBlurOtsuBand, "shape")
        else:
            y, x = np.round(center).astype("int") # y, x
            debug_roi = cv2.drawMarker(cv2.cvtColor(hsvMask, cv2.COLOR_GRAY2BGR), (x, y), (0, 0, 255), cv2.MARKER_CROSS)
            cv2.imwrite(debug_quad_path, debug_roi)
            # debugShow(debug_roi, "shape")
    if center is None: return None  # hue_lower=hue_lower, pixels=affected, )
    else:              return dict(pos=center, )  # pixels=affected, hue_lower=hue_lower)

def _undistortImage(img, dist, mtx):
    """Apply the camera calibration matrices to distort the picture back straight"""
    h, w = img.shape[:2]
    newcameramtx, roi = cv2.getOptimalNewCameraMatrix(mtx, dist, (w, h), 1, (w, h))

    # undistort image
    mapx, mapy = cv2.initUndistortRectifyMap(mtx, dist, None, newcameramtx, (w, h), 5)
    return cv2.remap(img, mapx, mapy, cv2.INTER_LINEAR)

def _get_hue_mask(hsv_roi, bandsize=11, pixTrigAmount=500, pixTooMany=3000): #(hsv_roi: np.ndarray, bandsize=11, pixTrigAmount=500, pixTooMany=3000):
    """
    Returns hue mask with dynamic hue range. Tries to find the right amount of pixels in a given hue window
    not enough pixels have been found (less than PIXEL_THRESHOLD_UPPER)
    Uses a local maxima finder (maximisePixCount) to get the optimal mask as given by
    a generator (concatGen and _slidingHueMask)
    :param ms: markersettings
    :param qd: quadrant
    :param hsv_roi: the roi in hsv format
    :return: huemask,affected,hue_lower
    """
    # debugShow(hsv_roi, "_get_hue_mask")
    def maximisePixCount(maskGenerator):
        # TODO look for clusters of pixels
        trigger = False
        ret = None
        _mask = None
        _prev_mask = None
        pix_amount = -1
        for maskedImg, mask in maskGenerator:

            # debugShow(maskedImg, "maskedImg")
            coloredPix = np.count_nonzero(mask) # # counts for each value of h s and v
            if not trigger and coloredPix > pixTrigAmount:
                # print("##########triggered : ", coloredPix)
                trigger = True
                pix_amount = coloredPix
                ret, _mask = maskedImg, mask
            elif trigger and (pix_amount == -1 or coloredPix > pix_amount):
                # print("trigger : {}, better pixies amount : {} < {}".format(trigger, pix_amount, coloredPix))
                pix_amount = coloredPix
                ret, _mask = maskedImg, mask
            elif trigger and pix_amount > coloredPix:
                # Merge with previous masks to maximise the quality of the circle
                if _prev_mask is None:
                    # _mask cannot be None
                    return ret, cv2.bitwise_or(_mask, mask)
                else:
                    # the previous img
                    return ret, reduce(cv2.bitwise_or, (_prev_mask, _mask, mask))
            _prev_mask = _mask
        return ret, _mask

    # TODO see itertools.chain
    def concatGen(generators):
        if len(generators) == 0:
            return
        else:
            for elm in generators[0]:
                yield elm
            for elm in concatGen(generators[1:]):
                yield elm

    return maximisePixCount(concatGen([_slidingHueMask(hsv_roi, bandsize+2, sBound=(60, 255), vBound=(60, 255), dS=4, dV=4),
                                       # High light situaton : Markers always have a high value and broad variety of saturation
                                       _slidingHueMask(hsv_roi, bandsize+5, sBound=(40, 255), vBound=(180, 255), dS=15, dV=15, ascending=False),
                                       # Cold to neutral and dim light doesn't make the markers pop out as well :
                                       # Both value and saturation are bad, but Hue is usually pretty high
                                       #
                                       _slidingHueMask(hsv_roi, bandsize+5, hBound=(145, 190), sBound=(50, 200), vBound=(60, 220), dS=17, dV=17),
                                       ]))

def _slidingHueMask(hsv_roi, bandSize, hBound=None, sBound=(0, 255), vBound=(0, 255), dS=5, dV=4, ascending=True, refine=-1):
    #(hsv_roi: np.ndarray, bandSize: int, sBound=(0, 255), vBound=(0, 255), dS=5, dV=4, ascending= True, refine=-1):
    """
    Generates masks of the input image by thresholding the image hue inside a certain range.
    That range is then slided around inside HUE_BAND_LB and HUE_BAND_UP. (wraps around when reaching
    the maximum hue of 180 in order to be circular)
    Slides with increments of bandSize / 2
    if refine:
        after sliding, takes the best performing band, and perform a local maxima search with the dichotomic search
    """
    if ascending:
        if hBound is not None: h1, h2 = hBound
        else: h1, h2 = HUE_BAND_LB, HUE_BAND_UB
        s1, s2 = sBound
        v1, v2 = vBound
    else:
        if hBound is not None: h2, h1 = hBound
        else: h2, h1 = HUE_BAND_LB, HUE_BAND_UB
        s1, s2 = sBound[::-1]
        v1, v2 = vBound[::-1]
    bands = np.linspace(h1, h2, int(abs(h2-h1) / bandSize * 2) + 1)
    # bands.append(h2)
    # subdivide Saturation and Hue in same number of bands (S growing, H decreasing)
    sBand = np.linspace(s1, s2, len(bands)).astype(int)
    # dS = 5 # expand Saturation filter window by this size
    vBand = np.linspace(v2, v1, len(bands)).astype(int)
    # dV = 4 # expand Value filter window by this size
    for i, band in enumerate(bands[:-2]):
        if ascending:
            lb = np.array([bands[i]   % 180,     sBand[i]  -dS,           vBand[i+2]-dV], np.uint8)
            ub = np.array([bands[i+2] % 180, min(sBand[i+2]+dS, 255), min(vBand[i]  +dV, 255)], np.uint8)
        else:
            ub = np.array([bands[i]   % 180, min(sBand[i]  +dS, 255), min(vBand[i+2]+dV, 255)], np.uint8)
            lb = np.array([bands[i+2] % 180,     sBand[i+2]-dS,           vBand[i]  -dV], np.uint8)
        if     (ascending and bands[i] <= 180 and bands[i+2] >  180) or \
                (not ascending and bands[i]  > 180 and bands[i+2] <= 180) :
            _ub = np.array([180, ub[1], ub[2]], np.uint8)
            _lb = np.array([0  , lb[1], lb[2]], np.uint8)
            # print("_lb {} _ub {}".format(_lb, _ub))
            lmask = cv2.inRange(hsv_roi, lb, _ub)
            rmask = cv2.inRange(hsv_roi, _lb, ub)
            mask = cv2.bitwise_or(lmask, rmask)
        else:
            mask = cv2.inRange(hsv_roi, lb, ub)
        # print("lb {} ub {}".format(lb, ub))
        # print("mask pix number ", np.count_nonzero(mask))
        out = 255 * np.ones(hsv_roi.shape)
        out = cv2.bitwise_and(hsv_roi, hsv_roi, mask=mask)
        yield out, mask

def _warpImgByCorners(image, corners):
    """
    Warps the region delimited by the corners in order to straighten it.
    :param image: takes an opencv image
    :param corners: as qd-dict
    :return: image with corners warped
    """

    def f(qd):
        return np.array(corners[qd])

    nw, ne, sw, se = map(f, QD_KEYS)

    # calculate maximum width and height for destination points
    width1 = norm(se - sw)
    width2 = norm(ne - nw)
    maxWidth = max(int(width1), int(width2))

    height1 = norm(ne - se)
    height2 = norm(nw - sw)
    maxHeight = max(int(height1), int(height2))

    # source points for matrix calculation
    src = np.array((nw[::-1], ne[::-1], se[::-1], sw[::-1]), dtype="float32")

    # destination points in the same order
    dst = np.array([
            [0, 0],  # nw
            [maxWidth - 1, 0],  # ne
            [maxWidth - 1, maxHeight - 1],  # sw
            [0, maxHeight - 1]], dtype="float32")  # se

    # get the perspective transform matrix
    transMatrix = cv2.getPerspectiveTransform(src, dst)

    # compute warped image
    warpedImg = cv2.warpPerspective(image, transMatrix, (maxWidth, maxHeight))
    return warpedImg

def _debug_drawMarkers(raw_img, markers):
    """Draw the markers onto an image"""
    img = raw_img.copy()

    for qd, pos in markers.items():
        if pos is None:
            continue
        (mh, mw) = map(int, pos)
        cv2.circle(img, (mw, mh), 15, (0, 150, 0), 4)
        cv2.putText(img, 'M - '+qd, (mw + 15, mh - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 150, 0), 2, cv2.LINE_AA)
    return img

def _debug_drawCorners(raw_img, corners):
    """Draw the corners onto an image"""
    img = raw_img.copy()
    for qd in corners:
        (cy, cx) = map(int, corners[qd])
        cv2.circle(img, (cx, cy), 15, (150, 0, 0), 4)
        cv2.putText(img, 'C - '+qd, (cx + 15, cy - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 150, 0), 2, cv2.LINE_AA)
    return img

def save_debug_img(img, normal_img_path, folderName):
    """Saves the image in a folder along the given path"""
    dbg_path = os.path.join(dirname(normal_img_path), folderName, basename(normal_img_path))
    _mkdir(dirname(dbg_path))
    cv2.imwrite(dbg_path, img)

def _mkdir(folder):
    if not exists(dirname(folder)):
        os.mkdir(dirname(folder))

def _getCamParams(path_to_params_file):
    """
    :param path_to_params_file: Give Path to cam_params file as .npz
    :returns cam_params as dict
    """
    if not isfile(path_to_params_file) or os.stat(path_to_params_file).st_size == 0:
        logging.error("Please provide a valid: PATH_TO/camera_params.npz or similiar")
        raise MbPicPrepError("Please provide a valid: PATH_TO/camera_params.npz or similiar")
    else:
        try:
            valDict = np.load(path_to_params_file)
        except Exception as e:
            raise MbPicPrepError('Exception while loading cam_params: {}'.format(e))

        if not all(param in valDict for param in [DIST_KEY, MTX_KEY]):
            raise MbPicPrepError('CamParams missing in File, please do a new Camera Calibration. (Chessboard)')

    return valDict

def _getPicSettings(path_to_settings_file, custom_pic_settings=None):
    """
    :param path_to_settings_file: Give Path to pic_settings yaml
    :param path_to_last_markers_json: needed for overwriting file if updated
    :return: pic_settings as dict
    """
    if not isfile(path_to_settings_file) or os.stat(path_to_settings_file).st_size == 0:
        print("No pic_settings file found, created new one.")
        pic_settings = PIC_SETTINGS
        if custom_pic_settings is not None:
            pic_settings = dict_merge(pic_settings, custom_pic_settings)
        settings_changed = True
    else:
        import yaml
        try:
            with open(path_to_settings_file) as yaml_file:
                pic_settings = yaml.safe_load(yaml_file)
            if M2C_VECTOR_KEY in pic_settings and pic_settings[M2C_VECTOR_KEY] is not None:
                for qd in QD_KEYS:
                    pic_settings[M2C_VECTOR_KEY][qd] = np.array(pic_settings[M2C_VECTOR_KEY][qd])
            settings_changed = False
        except:
            print("Exception while loading '%s' > pic_settings file not readable, created new one. ", yaml_file)
            pic_settings = PIC_SETTINGS
            settings_changed = True

        # if not MARKER_SETTINGS_KEY in pic_settings or not all(param in pic_settings[MARKER_SETTINGS_KEY] for param in PIC_SETTINGS[MARKER_SETTINGS_KEY].keys()):
        #     logging.info('Bad picture settings file, loaded default marker settings')
        #     pic_settings[MARKER_SETTINGS_KEY] = PIC_SETTINGS[MARKER_SETTINGS_KEY]
        #     settings_changed = True

    return pic_settings

def _isValidQdDict(qdDict):
    """
    :param: qd-Dict to test for valid Keys
    :returns True or False
    """
    if type(qdDict) is not dict:
        result = False
    else:
        result = all(qd in qdDict and len(qdDict[qd]) == 2 for qd in QD_KEYS)
    return result
