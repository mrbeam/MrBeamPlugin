#!/usr/bin/env python3
from os.path import dirname, join, realpath

import pytest
import logging
import cv2
import numpy as np
from octoprint_mrbeam.camera.undistort import prepareImage
from octoprint_mrbeam.camera.lens import BoardDetectorDaemon
import octoprint_mrbeam.camera.lens as lens
import time


path = dirname(realpath(__file__))
CAM_DIR = join(path, "..", "rsc", "camera")


@pytest.mark.datafiles(
    join(CAM_DIR, "raw.jpg"),
    join(CAM_DIR, "lens_calib_bad.npz"),
)
def test_undist(datafiles):
    in_img = cv2.imread(str(datafiles / "raw.jpg"))
    cam_calib_path = str(datafiles / "lens_calib_bad.npz")
    __cam = np.load(cam_calib_path)
    res = prepareImage(
        in_img,
        str(datafiles / "out.jpg"),
        str(datafiles / "pic_settings.yaml"),
        cam_matrix=__cam["mtx"],
        cam_dist=__cam["dist"],
        undistorted=True,
        debug_out=True,
    )

    log_re = "\n\n".join([str(v) for v in res])

    # logging.warning(log_re)

    for i, _type in enumerate([dict, dict, list, type(None), dict, dict]):
        if not isinstance(res[i], _type):
            logging.error("%s should be of type %s" % (res[i], _type))
    assert res[5]["lens_corrected"]


BOARD_IMGS = tuple("tmp_raw_img_0%02i.jpg" % i for i in range(21, 31))


# TODO IRATXE: the following files do not exist!
BOARDS = pytest.mark.datafiles(
    join(CAM_DIR, "boards", "tmp_raw_img_021.jpg"),
    join(CAM_DIR, "boards", "tmp_raw_img_021.jpg.npz"),
    join(CAM_DIR, "boards", "tmp_raw_img_022.jpg"),
    join(CAM_DIR, "boards", "tmp_raw_img_022.jpg.npz"),
    join(CAM_DIR, "boards", "tmp_raw_img_023.jpg"),
    join(CAM_DIR, "boards", "tmp_raw_img_024.jpg"),
    join(CAM_DIR, "boards", "tmp_raw_img_025.jpg"),
    join(CAM_DIR, "boards", "tmp_raw_img_026.jpg"),
    join(CAM_DIR, "boards", "tmp_raw_img_027.jpg"),
    join(CAM_DIR, "boards", "tmp_raw_img_028.jpg"),
    join(CAM_DIR, "boards", "tmp_raw_img_029.jpg"),
    join(CAM_DIR, "boards", "tmp_raw_img_030.jpg"),
)


def inspectState(data):
    """Inspect the state each time it changes"""
    if isinstance(data, dict):
        # yaml dumps create a LOT of output
        # logging.debug('Calibration State Updated\n%s', yaml.dump(data))
        pass
    else:
        logging.error(
            "Data returned by state should be dict. Instead data : %s, %s",
            type(data),
            data,
        )
        assert isinstance(data, dict)


# todo iratxe: won't work, because boards don't exist
# @BOARDS
# def test_lens_calibration_abort(datafiles):
#     out_file = str(datafiles / "out.npz")
#
#     b = BoardDetectorDaemon(
#         out_file, runCalibrationAsap=True, stateChangeCallback=inspectState
#     )
#     # Board Detector doesn't start automatically
#     assert not b.is_alive()
#
#     try:
#         images = [str(datafiles / img) for img in BOARD_IMGS]
#         # add boards - Shouldn't start the board detector daemon
#         for path in images[:4]:
#             b.add(path)
#
#         b.state[images[0]]["state"] == lens.STATE_SUCCESS
#         b.state[images[3]]["state"] == lens.STATE_PENDING
#         b.state.lensCalibration["state"] == lens.STATE_PENDING
#
#         # Board Detector doesn't start when adding pictures to it
#         assert not b.is_alive()
#         # Start detecting the chessboard in pending pictures.
#         b.start()
#         assert b.is_alive()
#         len_state = len(b.state)
#         b.remove(images[3])
#         assert len_state == len(b.state) + 1
#         b.add(images[3])
#
#         # while b.detectedBoards < 3:
#         time.sleep(1)
#     except Exception as e:
#         logging.error(e)
#         b.stop()
#         b.join(1.0)
#         raise
#
#     b.stopAsap()
#
#     timeout_msg = "Termination of the calibration Daemon should have been faster"
#     # try:
#     b.join()
#     assert not b.is_alive(), timeout_msg
#     # except TimeoutError:
#     #     logging.error(timeout_msg)
#     #     raise
#     logging.info(
#         "Joined the lens calibratior stuff - ret %s, is_alive %s", ret, b.is_alive()
#     )


# todo iratxe: won't work, because boards don't exist
# @BOARDS
# @pytest.mark.skip("skipping full lens calibration")
# def test_lens_calibration(datafiles):
#     out_file = str(datafiles / "out.npz")
#
#     b = BoardDetectorDaemon(
#         out_file, runCalibrationAsap=True, stateChangeCallback=inspectState
#     )
#
#     try:
#         _images = [str(datafiles / img) for img in BOARD_IMGS]
#         for path in _images[:-1]:
#             b.add(path)
#         logging.debug(_images)
#
#         # Start detecting the chessboard in pending pictures.
#         b.start()
#
#         while not b.idle:
#             time.sleep(0.1)
#
#         if b.detectedBoards >= lens.MIN_BOARDS_DETECTED:
#             # Do not automatically run the calibration
#             assert b.state.lensCalibration["state"] == lens.STATE_PENDING
#             b.startCalibrationWhenIdle = True
#             while b.startCalibrationWhenIdle or not b.idle:
#                 time.sleep(0.1)
#
#             assert b.state.lensCalibration["state"] == lens.STATE_SUCCESS
#
#         # Hacky - when adding the chessboard, instantly check if the state is pending
#         b.add(_images[-1])
#         assert b.state.lensCalibration["state"] == lens.STATE_PENDING
#     except Exception as e:
#         logging.error(e)
#         b.stop()
#         b.join(1.0)
#         raise
#
#     b.stop()
#
#     try:
#         b.join(1.0)
#     except TimeoutError:
#         logging.error("Termination of the calibration Daemon should have been sooner")
#         raise
#
#     # # Start calibration
#     # b.startCalibrationWhenIdle = True
#     # b.scaleProcessors(4)
