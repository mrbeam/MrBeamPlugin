import argparse
import textwrap
from collections.abc import Mapping
from threading import Event
from multiprocessing import Pool
from octoprint_mrbeam.camera.definitions import (
    QD_KEYS,
    RESOLUTIONS,
    DIST_KEY,
    MTX_KEY,
    STOP_EVENT_ERR,
    ERR_NEED_CALIB,
    HUE_BAND_LB,
    HUE_BAND_UB,
    SUCCESS_WRITE_RETVAL,
    MIN_MARKER_PIX,
    MAX_MARKER_PIX,
    PIC_SETTINGS,
)
from octoprint_mrbeam.camera import corners, lens
import octoprint_mrbeam.camera as camera
from octoprint_mrbeam.util import dict_map, dict_merge
from octoprint_mrbeam.util.img import differed_imwrite
from octoprint_mrbeam.util.log import logme, debug_logger, logExceptions, logtime
from octoprint_mrbeam.mrb_logger import mrb_logger


import logging
import time
import os
import os.path as path
from os.path import dirname, basename, isfile, exists
import cv2
import numpy as np

logger = mrb_logger(__name__, lvl=logging.INFO)


class MbPicPrepError(Exception):
    """Something went wrong when undistorting and aligning the picture for the
    front-end."""

    pass


# @logExceptions # useful if running in thread
@logtime()
def prepareImage(
    input_image,  #: Union[str, np.ndarray],
    path_to_output_image,  #: str,
    pic_settings=None,  #: Map or str
    cam_dist=None,  #: ? np.ndarray ?,
    cam_matrix=None,  #: ? np.ndarray ?,
    last_markers=None,  # {'NW': np.array(I, J), ... }
    size=RESOLUTIONS["1000x780"],
    quality=90,
    zoomed_out=False,
    debug_out=False,
    undistorted=False,
    saveRaw=False,
    blur=7,
    custom_pic_settings=None,
    stopEvent=None,
    min_pix_amount=MIN_MARKER_PIX,
    calibration_pic_size=None,  # (2048,1536), # picture size when the camera got calibrated
    threads=-1,
):
    # type: (Union[str, np.ndarray], basestring, np.ndarray, np.ndarray, Union[Mapping, basestring], Union[dict, None], tuple, int, bool, bool, bool, int, Union[None, Mapping], Union[None, Event], int) -> object
    """Loads image from path_to_input_image, does some preparations (undistort,
    warp) on it and saves it to path_to_output_img.

    :param input_image: The image to prepare. Either a filepath or a numpy array (as understood by cv2)
    :param path_to_output_image: filepath where to save the image to
    :param cam_dist: camera distance matrix (see cv2.camera_calibrate)
    :param cam_matrix: camera distortion matrix (see cv2.camera_calibrate)
    :param pic_settings: path to - or map as given by - pic_config.yaml
    :param last_markers: used to compensate if a (single) marker is covered or unrecognised
    :param size : (width,height) of output image size, default is (1000,780)
    :param quality: set quality of output image from 0 to 100, default is 90
    :param zoomed_out: zoom out on the final picture in order to account for object height
    :param debug_out: True if all in between pictures should be saved to output path directory
    :param blur: Amount of blur for the marker detection
    :param custom_pic_settings: Map : used to update certain keys of the pic settings file
    :param stopEvent: used to exit gracefully
    :param threads: number of threads to use for the marker detection. Set -1, 1, 2, 3 or 4. (recommended : 4, default: -1)
    """
    # debug_out = True
    if debug_out:
        logger.setLevel(logging.DEBUG)
        logger.info("DEBUG enabled")
    else:
        logger.setLevel(logging.WARNING)

    err = None
    savedPics = {"raw": False, "lens_corrected": False, "cropped": False}

    def save_debug_img(img, name):
        return camera.save_debug_img(
            img, name + ".jpg", folder=path.join(dirname(path_to_output_image), "debug")
        )

    if type(input_image) is str:
        # check image path
        logger.debug(
            "Starting to prepare Image. \ninput: <{}> - output: <{}>\ncam dist : <{}>\ncam matrix: <{}>\noutput_img_size:{} - quality:{} - debug_out:{}".format(
                input_image,
                path_to_output_image,
                cam_dist,
                cam_matrix,
                size,
                quality,
                debug_out,
            )
        )
        if not isfile(input_image):
            raise IOError(
                "Could not find a picture under path: <{}>".format(input_image)
            )
        # load image
        img = cv2.imread(input_image, cv2.IMREAD_COLOR)  # BGR
        if img is None:
            raise IOError(
                "Image file could not be loaded, path is {}".format(input_image)
            )
    elif type(input_image) is np.ndarray:
        logger.debug(
            "Starting to prepare Image. \ninput: <{} shape arr> - output: <{}>\ncam dist : <{}>\ncam matrix: <{}>\noutput_img_size:{} - quality:{} - debug_out:{}".format(
                input_image.shape,
                path_to_output_image,
                cam_dist,
                cam_matrix,
                size,
                quality,
                debug_out,
            )
        )
        img = input_image
    else:
        raise ValueError(
            "path_to_input_image-_in_camera_undistort_needs_to_be_a_path_(string)_or_a_numpy_array"
        )

    if stopEvent and stopEvent.isSet():
        return None, None, None, STOP_EVENT_ERR, {}, savedPics

    # search markers on undistorted pic
    dbg_markers = os.path.join(dirname(path_to_output_image), "debug", ".jpg")
    _mkdir(dirname(dbg_markers))
    outputPoints = _getColoredMarkerPositions(
        img,
        debug_out_path=dbg_markers,
        blur=blur,
        threads=threads,
        min_pix=min_pix_amount,
    )
    markers = {}
    # list of missed markers
    missed = []
    # TODO Python3 elegant filter : if len(list(filter(None.__ne__, markers.values()))) < 4: # elif # filter out None values
    for qd, val in outputPoints.items():
        if val is None:
            if last_markers is not None and qd in last_markers.keys():
                markers[qd] = list(last_markers[qd])
            missed.append(qd)
        else:
            markers[qd] = list(positem.item() for positem in val["pos"])
    if len(missed) > 1 and len(markers) == 4:
        err = "Missed marker %s" % missed
        logger.warning(err)
    elif len(markers) < 4:
        err = (
            "Missed marker(s) %s, no(t enough) history to guess missing marker position(s)"
            % missed
        )
        logger.warning(err)
        return None, markers, missed, err, outputPoints, savedPics
    if debug_out:
        save_debug_img(_debug_drawMarkers(img, markers), "drawmarkers")

    # Optimisation : Markers detected, we don't need the image in color anymore.
    img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    # workspaceCorners = corners.add_deltas(markers, pic_settings, False)
    # if workspaceCorners and debug_out: save_debug_img(_debug_drawCorners(img, workspaceCorners), "drawcorners_raw")

    do_undistortion = cam_dist is not None and cam_matrix is not None
    if do_undistortion:
        # Can be done simultaneously while the markers get detected on the raw picture
        # NOTE If in precision mode, there is no point in undistorting the image
        #      if we don't have enough markers (it doesn't get sent)
        # TODO do threaded while detecting the corners on raw img.
        img, dest_mtx = lens.undistort(img, cam_matrix, cam_dist)
        if debug_out or undistorted:
            savedPics["lens_corrected"] = save_debug_img(img, "undistorted")
        if debug_out:
            # undist_markers are not used to correct the picture, only for the debug purposes.
            undist_markers = lens.undist_dict(
                markers, cam_matrix, cam_dist, new_mtx=dest_mtx
            )
            logger.info("Saving undist drawmarkers")
            save_debug_img(
                _debug_drawMarkers(img, undist_markers), "drawmarkers_undist"
            )
    else:
        dest_mtx = None
    if stopEvent and stopEvent.isSet():
        return None, markers, missed, STOP_EVENT_ERR, outputPoints, savedPics

    # load pic_settings json
    if pic_settings is None:
        return None, markers, missed, ERR_NEED_CALIB, outputPoints, savedPics

    workspaceCorners = corners.add_deltas(
        markers, pic_settings, do_undistortion, cam_matrix, cam_dist, new_mtx=dest_mtx
    )

    if workspaceCorners is None:
        logger.error("Workspace Corners None??")

        return None, markers, missed, ERR_NEED_CALIB, outputPoints, savedPics
    logger.debug(
        "Workspace corners \nNW % 14s  NE % 14s\nSW % 14s  SE % 14s"
        % tuple(
            map(
                np.ndarray.tolist,
                list(map(workspaceCorners.__getitem__, ["NW", "NE", "SW", "SE"])),
            )
        )
    )
    if debug_out:
        save_debug_img(_debug_drawCorners(img, workspaceCorners), "drawcorners_undist")

    img = corners.warpImgByCorners(img, workspaceCorners, zoomed_out)
    if debug_out:
        save_debug_img(img, "warped")
    # get corners of working area
    if stopEvent and stopEvent.isSet():
        return None, markers, missed, STOP_EVENT_ERR, outputPoints, savedPics

    # Resize image to the final size
    retval = differed_imwrite(
        filename=path_to_output_image,
        img=cv2.resize(img, size),
        params=[int(cv2.IMWRITE_JPEG_QUALITY), quality],
    )
    savedPics["cropped"] = retval == SUCCESS_WRITE_RETVAL

    return workspaceCorners, markers, missed, err, outputPoints, savedPics


# @logtime()
# @logme(False, True)
def _getColoredMarkerPositions(
    img, debug_out_path=None, blur=5, threads=-1, min_pix=MIN_MARKER_PIX
):
    """Allows a multi-processing implementation of the marker detection algo.

    Up to 4 processes needed.
    """
    outputPoints = {}
    # check all 4 corners
    if threads > 0:
        # takes around ~ 10MB RAM / thread
        p = Pool(threads)
        results = {}
        brightness = None
        for roi, pos, qd in camera.getRois(img):
            results[qd] = (
                p.apply_async(
                    _getColoredMarkerPosition,
                    args=(roi,),
                    kwds=dict(
                        debug_out_path=debug_out_path,
                        blur=blur,
                        quadrant=qd,
                        min_pix=min_pix,
                    ),
                ),
                pos,
            )
        while not all(r.ready() for r, pos in results.values()):
            time.sleep(0.1)
        p.close()
        for qd, (r, pos) in results.items():
            outputPoints[qd] = r.get()
            if outputPoints[qd] is not None:
                outputPoints[qd]["pos"] += pos
        p.join()
    else:
        for roi, pos, qd in camera.getRois(img):
            outputPoints[qd] = _getColoredMarkerPosition(
                roi,
                debug_out_path=debug_out_path,
                blur=blur,
                quadrant=qd,
                min_pix=min_pix,
            )
            if outputPoints[qd] is not None:
                outputPoints[qd]["pos"] += pos
    return outputPoints


@logExceptions
# @logme(False, True)
# @logtime()
def _getColoredMarkerPosition(
    roi,
    debug_out_path=None,
    blur=5,
    quadrant=None,
    d_min=8,
    d_max=30,
    visual_debug=False,
    min_pix=MIN_MARKER_PIX,
):
    """Tries to find a single pink marker inside the image (or the Region of
    Interest). It then outputs the information about found marker (for now,
    just its center position).

    :param roi:
    :type roi:
    :param debug_out_path:
    :type debug_out_path:
    :param blur:
    :type blur:
    :param quadrant: The corner region of the image ('NW', 'NE', 'SW', 'SE')
    :type quadrant: basestring
    :param d_min: minimal diameter of the *inner* (distorted) marker edge
    :type d_min: int
    :param d_max: maximal diameter of the *outer* (distorted) marker edge
    :type d_max: int
    :return:
    :rtype:
    """
    # Smooth out picture
    roiBlur = cv2.GaussianBlur(roi, (blur, blur), 0)
    # Use the opposite color of Magenta (Green) to contrast the markers the most
    transformToGreen = np.array([[0.0, 1.0, 0.0]])
    greenBlur = cv2.transform(roiBlur, transformToGreen)
    # if visual_debug: debugShow(greenBlur, "green")
    # Threshold the green channel
    ret, threshOtsuMask = cv2.threshold(
        greenBlur, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU
    )
    blocksize = 11
    gaussianMask = cv2.adaptiveThreshold(
        greenBlur,
        255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY_INV,
        blocksize,
        2,
    )
    roiBlurThresh = cv2.bitwise_and(
        roiBlur, roiBlur, mask=cv2.bitwise_or(threshOtsuMask, gaussianMask)
    )
    if debug_out_path:
        debug_quad_path = debug_out_path.replace(".jpg", "{}.jpg".format(quadrant))
    else:
        debug_quad_path = None
    for spot, center, start, stop, count in _get_white_spots(
        cv2.bitwise_or(threshOtsuMask, gaussianMask), min_pix=min_pix
    ):
        spot.dtype = np.uint8
        if visual_debug:
            cv2.imshow(
                "{} : spot".format(quadrant),
                cv2.imdecode(np.fromiter(spot, dtype=np.uint8), cv2.IMREAD_GRAYSCALE),
            )
            cv2.waitKey(0)
        if isMarkerMask(spot[start[1] : stop[1], start[0] : stop[0]]):
            hsv_roi = cv2.cvtColor(roiBlurThresh, cv2.COLOR_BGR2HSV)
            avg_hsv = np.average(
                [hsv_roi[pos] for pos in zip(*np.nonzero(spot))], axis=0
            )
            if HUE_BAND_LB <= avg_hsv[0] <= 180 or 0 <= avg_hsv[0] <= HUE_BAND_UB:
                x, y = np.round(center).astype("int")  # y, x
                debug_roi = cv2.drawMarker(
                    cv2.bitwise_or(threshOtsuMask, gaussianMask),
                    (x, y),
                    (0, 0, 255),
                    cv2.MARKER_CROSS,
                    line_type=4,
                )
                if debug_quad_path:
                    differed_imwrite(
                        debug_quad_path,
                        debug_roi,
                        params=[cv2.IMWRITE_JPEG_QUALITY, 100],
                    )
                return dict(pos=center, avg_hsv=avg_hsv, pix_size=count)
    # No marker found
    if debug_quad_path:
        differed_imwrite(debug_quad_path, roiBlurThresh)
    return None


def isMarkerMask(mask, d_min=10, d_max=60, visual_debug=False):
    """Tests the mask to know if it could plausably be a marker.

    :param mask: The mask to compare
    :type mask: Union[Iterable, numpy.ndarray]
    :return: True if it is a marker (circle-ish), False if not
    :rtype: generator[bool]
    """
    path = os.path.join(os.path.dirname(__file__), "../files/camera/marker_mask.bmp")
    marker_mask_tester = cv2.imread(path, cv2.IMREAD_GRAYSCALE)
    if marker_mask_tester is None:
        raise OSError("File not found : %s" % path)
    h1, w1 = marker_mask_tester.shape[:2]
    h2, w2 = mask.shape[:2]
    if h2 > h1 or w2 > w1:
        return False
    # todo resize mask to correct size
    # crop / resize mask to same size as marker_mask_tester

    # Center the mask on a canvas the size of the test mask
    marker = np.zeros(marker_mask_tester.shape[:2], dtype=np.uint8)
    offH, offW = (h1 - h2) // 2, (w1 - w2) // 2
    marker[offH : h2 + offH, offW : w2 + offW] = mask
    if visual_debug:
        cv2.imshow("My marker", marker * 255)
    # Tests if the mask is completely inside the marker_mask_tester,
    # i.e. it didn't change after applying the mask
    return np.all(marker == cv2.bitwise_and(marker_mask_tester, marker))


def _get_white_spots(mask, min_pix=MIN_MARKER_PIX, max_pix=MAX_MARKER_PIX):
    """Iterates over the white connected spots on the picture (aka white
    blobs)"""
    # Label each separate zones on the mask (The black background + the white blobs)
    lenLabels, labels = cv2.connectedComponents(mask)
    unique_labels, counts_elements = np.unique(labels, return_counts=True)
    # The filter also filters out the black background
    _filter = lambda args: max_pix > args[0] > min_pix
    filtered_elm = list(filter(_filter, list(zip(counts_elements, unique_labels))))
    for count, label in sorted(filtered_elm, reverse=True):
        bool_connected_spot = labels == label
        # get the geometrical center of that blob
        non_zeros = np.transpose(np.nonzero(bool_connected_spot))
        start, stop = np.min(non_zeros, axis=0), np.max(non_zeros, axis=0)
        center = (start + stop) // 2
        yield bool_connected_spot, center[::-1], start[::-1], stop[::-1], count


def _debug_drawMarkers(raw_img, markers):
    """Draw the markers onto an image."""
    img = raw_img.copy()
    if len(img.shape) == 2:
        img = cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)
    for qd, pos in markers.items():
        if pos is None:
            continue
        (mw, mh) = list(map(int, pos))
        cv2.circle(img, (mw, mh), 15, (255, 255, 255), 4)
        cv2.putText(
            img,
            "M - " + qd,
            (mw + 15, mh - 5),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.5,
            (0, 150, 0),
            2,
            cv2.LINE_AA,
        )
    return img


def _debug_drawCorners(raw_img, corners):
    """Draw the corners onto an image."""
    img = raw_img.copy()
    for qd in corners:
        (cx, cy) = list(map(int, corners[qd]))
        cv2.circle(img, (cx, cy), 15, (150, 0, 0), 4)
        cv2.putText(
            img,
            "C - " + qd,
            (cx + 15, cy - 5),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.5,
            (0, 150, 0),
            2,
            cv2.LINE_AA,
        )
    return img


def _mkdir(folder):
    if not exists(folder):
        os.makedirs(folder)


def _getCamParams(path_to_params_file):
    """
    :param path_to_params_file: Give Path to cam_params file as .npz
    :returns cam_params as dict
    """
    if not isfile(path_to_params_file) or os.stat(path_to_params_file).st_size == 0:
        logging.warning("Camera lens calibration file not found.")
        return None
    else:
        try:
            valDict = np.load(path_to_params_file)
        except Exception as e:
            raise MbPicPrepError("Exception_while_loading_cam_params-_{}".format(e))

        if not all(param in valDict for param in [DIST_KEY, MTX_KEY]):
            raise MbPicPrepError(
                "CamParams_missing_in_File-_please_do_a_new_Camera_Calibration_(Chessboard)"
            )
    return valDict


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Detect the markers in the pictures provided or from the camera",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=textwrap.dedent(
            """\
	Examples
	=============================================================
	Find the markers in the .jpg pictures contained in my_picture_folder and
	save the undistorted pictures in my_picture_folder/undistort/
	  python undistort.py my_picture_folder/*.jpg
	Undistort picture.jpg and store the result in path/to/undistort/picture.jpg
	  ls path/to/picture.jpg | entr python undistort.py /path/to/picture.jpg
	"""
        ),
    )
    # parser.add_argument('outfolder', nargs='?',# type=argparse.FileType('w'),
    #                     default='markers_out')
    parser.add_argument("images", metavar="IMG", nargs="+", default=["auto"])
    parser.add_argument(
        "-p",
        "--parameters",
        metavar="PARAM.npz",
        required=False,
        default=None,
        help="The file storing the camera lens correction",
    )
    parser.add_argument(
        "-c",
        "--config",
        metavar="PIC_CONFIG.yaml",
        required=False,
        default=None,  # "/home/pi/.octoprint/cam/pic_settings.yaml",
        help="?",
    )
    parser.add_argument(
        "-q",
        "--quality",
        metavar="Q",
        type=int,
        required=False,
        default=65,
        help="jpg compression quality, default is 65 (percent)",
    )
    parser.add_argument(
        "-l", "--lastmarkers", metavar="MARKERS.json", required=False, help=""
    )
    # Dummy camera for debugging the camera.__init__ and camera.dummy
    # parser.add_argument('-d', '--dummy', required=False, action='store_true', default=not(PICAMERA_AVAILABLE),
    #                     help="Use a dummy camera that emulates taking the provided pictures")
    parser.add_argument(
        "-j",
        metavar="THREADS",
        type=int,
        required=False,
        default=4,
        help="Number of worker threads",
    )
    parser.add_argument(
        "-o",
        "--out-folder",
        metavar="OUTFOLDER",
        required=False,
        help="Save the undistorted pictures in this folder",
    )
    parser.add_argument(
        "-s",
        "--save-markers",
        metavar="OUT.npz",
        required=False,
        help="Save the found markers in OUT.npz for later comparison",
    )
    parser.add_argument(
        "-D",
        "--debug",
        required=False,
        action="store_true",
        default=False,
        help="Save intermediary debug images in the output folder",
    )

    args = parser.parse_args()
    print(format(args.config))
    # imgFiles = list(map(lambda x: x.strip('\n'), args.inimg))
    # print(imgFiles)
    if args.out_folder:
        out_folder = args.out_folder
    else:
        out_folder = os.path.join(os.path.dirname(args.images[0]), "undistort")
    print("Saving detected markers to folder %s" % out_folder)

    cam_param_path = args.parameters
    if cam_param_path:
        cam_params = _getCamParams(args.parameters)
        dist = cam_params[DIST_KEY]
        mtx = cam_params[MTX_KEY]
    else:
        dist = None
        mtx = None

    # outpath = img + ".out.jpg"
    if not os.path.exists(args.out_folder):
        os.mkdir(args.out_folder)

    # load pic_settings json
    # pic_settings = _getPicSettings(args.last)
    markers = None
    for img_path in args.images:
        img = cv2.imread(img_path)

        workspaceCorners, markers, missed, err, _, _ = prepareImage(
            img,
            path.join(out_folder, path.basename(img_path)),
            pic_settings=args.config,
            cam_dist=dist,
            cam_matrix=mtx,
            last_markers=None,
            size=(2000, 1560),
            quality=args.quality,
            zoomed_out=False,
            debug_out=args.debug,
            blur=7,
            stopEvent=None,
            threads=-1,
        )

        if len(missed) > 0:
            print(
                "Missed markers : % 15s for picture %s" % (", ".join(missed), img_path)
            )
        # TODO save in npz file
