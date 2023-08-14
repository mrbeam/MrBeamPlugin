#!/usr/bin/env python3

from collections import Mapping
import yaml

from .definitions import (
    UNDIST_CALIB_MARKERS_KEY,
    UNDIST_CORNERS_KEY,
    FACT_RAW_CORNERS_KEY,
    CALIB_REFS,
    QD_KEYS,
    MAX_OBJ_HEIGHT,
    CAMERA_HEIGHT,
)
import logging
from os.path import isfile
import os
from octoprint_mrbeam.util import dict_map, makedirs
import numpy as np
from numpy.linalg import norm
import cv2
from octoprint_mrbeam.camera import lens
from octoprint_mrbeam.mrb_logger import mrb_logger

_logger = mrb_logger("octoprint.plugins.mrbeam.camera.corners")

# @logtime()
# DO NOT CHANGE - This is used by the camera plugin
def warpImgByCorners(image, corners, zoomed_out=False):
    """Warps the region delimited by the corners in order to straighten it.

    :param image: takes an opencv image
    :param corners: as qd-dict
    :param zoomed_out: whether to zoom out the pic to account for working height
    :return: image with corners warped
    """

    nw, ne, sw, se = [np.array(corners[qd]) for qd in QD_KEYS]

    # calculate maximum width and height for destination points
    width1 = norm(se - sw)
    width2 = norm(ne - nw)
    max_width = max(int(width1), int(width2))

    height1 = norm(ne - se)
    height2 = norm(nw - sw)
    max_height = max(int(height1), int(height2))

    if zoomed_out:
        factor = float(MAX_OBJ_HEIGHT) / CAMERA_HEIGHT / 2
        min_dst_x = factor * max_width
        max_dst_x = (1 + factor) * max_width
        min_dst_y = factor * max_height
        max_dst_y = (1 + factor) * max_height
        dst_size = (int((1 + 2 * factor) * max_width), int((1 + 2 * factor) * max_height))
    else:
        min_dst_x, max_dst_x = 0, max_width - 1
        min_dst_y, max_dst_y = 0, max_height - 1
        dst_size = (max_width, max_height)

    # source points for matrix calculation
    src = np.array((nw, ne, se, sw), dtype="float32")

    # destination points in the same order
    dst = np.array(
        [
            [min_dst_x, min_dst_y],  # nw
            [max_dst_x, min_dst_y],  # ne
            [max_dst_x, max_dst_y],  # sw
            [min_dst_x, max_dst_y],  # se
        ],
        dtype="float32",
    )

    # get the perspective transform matrix
    trans_matrix = cv2.getPerspectiveTransform(src, dst)

    # compute warped image
    warped_img = cv2.warpPerspective(image, trans_matrix, dst_size)
    return warped_img


def save_corner_calibration(
    path, new_corners, new_markers, hostname=None, plugin_version=None, from_factory=False
):
    """Save the settings onto a calibration file."""

    # transform dict
    for new_ in [new_corners, new_markers]:
        assert isinstance(new_, Mapping)
        assert all(qd in new_.keys() for qd in QD_KEYS)
    try:
        with open(path, "r") as f:
            # yaml.safe_load is None if file exists but empty
            pic_settings = yaml.safe_load(f) or {}
    except IOError:
        _logger.debug("Could not find the previous picture settings.")
        pic_settings = {}

    if from_factory:
        from .definitions import (
            FACT_RAW_CORNERS_KEY as __CORNERS_KEY,
            FACT_RAW_CALIB_MARKERS_KEY as __MARKERS_KEY,
        )
    else:
        from .definitions import (
            RAW_CORNERS_KEY as __CORNERS_KEY,
            RAW_CALIB_MARKERS_KEY as __MARKERS_KEY,
        )

    pic_settings[__CORNERS_KEY] = new_corners
    pic_settings[__MARKERS_KEY] = new_markers
    if hostname:
        pic_settings["hostname"] = hostname
    if plugin_version:
        pic_settings["version"] = plugin_version
    write_corner_calibration(pic_settings, path)


def write_corner_calibration(pic_settings, path):
    assert isinstance(pic_settings, Mapping), "pic_settings not mapping: {} {}".format(
        type(pic_settings), pic_settings
    )
    _logger.debug("Saving new corner calibration: {}".format(pic_settings))
    makedirs(path, parent=True, exist_ok=True)
    with open(path, "wb") as f:
        yaml.safe_dump(pic_settings, f, indent="  ", allow_unicode=True)
    _logger.info("New corner calibration has been saved")


def get_corner_calibration(pic_settings):
    """Returns the corner calibration written to pic_settings If given a dict,
    assumes this is already the pic_setings."""
    if isinstance(pic_settings, Mapping):
        return pic_settings
    elif not isfile(pic_settings) or os.stat(pic_settings).st_size == 0:
        return None
    try:
        with open(pic_settings) as yaml_file:
            return yaml.safe_load(yaml_file)
    except yaml.YAMLError:
        _logger.info(
            "Exception while loading '%s' > pic_settings file not readable",
            pic_settings,
        )
        return None


def get_deltas_and_refs(
    settings,
    undistorted=False,
    mtx=None,
    dist=None,
	new_mtx=None,
    from_factory=False,
):
    """Returns the relative positions (delta) of the markers and corners
    according to the calibration (in px) By default, returns delta for the raw
    pictures.

    If `undistorted==True` and matrix and dist are given, will return the undistorted coordinates
    calculated from the raw settings.
    Otherwise, try to find the undistorted values written in the calibration file (Legacy mode).
    :param path_to_settings_file: either settings dict or path to pic_settings yaml
    :param undistorted: Get the delta for the undistorted version of the picture.
    :param mtx: lens distortion matrix
    :param dist: from the lens calibration
    :param path_to_last_markers_json: needed for overwriting file if updated
    :return: pic_settings as dict
    """
    pic_settings = get_corner_calibration(settings)
    if pic_settings is None:
        return None, None, None

    # Values taken from the calibration file. Used as a reference to warp the image correctly.
    # Legacy devices only have the values for the lensCorrected position.
    calibration_references = dict_map(
        lambda key: pic_settings.get(key, None), CALIB_REFS
    )
    for k in calibration_references.keys():
        calibration_references[k]["result"] = None

    priority_list = ["user", "factory"] if not from_factory else ["factory"]
    for types, ref in calibration_references.items():
        # Find the correct reference position for both the markers and the corners
        if undistorted:
            for k in priority_list:
                # Prioritize converting positions from the raw values we have saved.
                # (It is calibration-agnostic)
                if ref[k]["raw"] is not None and mtx is not None and dist is not None:
                    # Distort reference points
                    ref["result"] = lens.undist_dict(ref[k]["raw"], mtx, dist)
                    break  # no need to go further in the priority list
                elif ref[k]["undistorted"]:
                    ref["result"] = dict_map(np.array, ref[k]["undistorted"])
                    break  # no need to go further in the priority list
        else:
            for k in priority_list:
                # Prioritize converting positions from the raw values we have saved.
                # (It is calibration-agnostic)
                if ref[k]["raw"] is not None:
                    ref["result"] = dict_map(np.array, ref[k]["raw"])
                    break  # no need to go further in the priority list
                elif ref[k]["undistorted"] is not None:
                    # TODO reverse distort references
                    # Could not find how to undistort,
                    # will ask to redo calibration.
                    ref["result"] = None
    ref_markers, ref_corners = (
        calibration_references[k]["result"] for k in ["markers", "corners"]
    )
    if any(r is None for r in (ref_markers, ref_corners)):
        # Not enough refenrences to continue,
        # cannot apply warp perspective
        return None, None, None
    delta = {qd: ref_corners[qd] - ref_markers[qd] for qd in QD_KEYS}
    return delta, ref_markers, ref_corners


def get_deltas(*args, **kwargs):
    """Wrapper for get_deltas_and_refs that only returns the deltas."""
    deltas, _, _ = get_deltas_and_refs(*args, **kwargs)
    return deltas


def add_deltas(markers, pic_settings, undistorted, *args, **kwargs):
    # NOTE: There is _bad_ duplication w/ regards to get_deltas_and_refs which
    # already applies the correct delta for plain pictures.
    # See ``OctoPrint-Camera.corners.add_deltas``
    # _logger.warning(markers)
    from_factory = kwargs.pop("from_factory", False)
    deltas = get_deltas(
        pic_settings, undistorted, *args, from_factory=from_factory, **kwargs
    )
    if deltas is None:
        return None
    # try getting raw deltas first
    if undistorted:
        deltas = get_deltas(pic_settings, undistorted, *args, **kwargs)
        # Use the lens corrected deltas. not as good
        _markers = lens.undist_dict(markers, *args, **kwargs)
        return {qd: _markers[qd] + deltas[qd] for qd in QD_KEYS}
    else:
        return dict({qd: markers[qd] + deltas[qd] for qd in QD_KEYS})
