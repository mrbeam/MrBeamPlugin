#!/usr/bin/env python3

from os.path import dirname, join, split
# from collections import NoneType

path = dirname(__file__)
print(path)
cam_dir = join(path, 'rsc', 'camera')

print(path)
import logging
import cv2
import numpy as np
from octoprint_mrbeam.camera.undistort import prepareImage

def test_undist():
    in_img = cv2.imread(join(cam_dir, 'raw.jpg'))
    cam_calib_path = join(cam_dir, 'lens_calib_bad.npz')
    __cam = np.load(cam_calib_path)
    res = prepareImage(
        in_img,
        join(cam_dir, 'out.jpg'),
        join(cam_dir, 'pic_settings.yaml'),
        cam_matrix=__cam['mtx'],
        cam_dist=__cam['dist'],
        undistorted=True,
    )

    log_re = '\n\n'.join([str(v) for v in res])

    logging.warning(log_re)

    for i, _type in enumerate([dict, dict, list, type(None), dict, dict]):
        if not isinstance(res[i], _type):
            logging.error("%s should be of type %s" % (res[i], _type))
    assert res[5]['lens_corrected']
