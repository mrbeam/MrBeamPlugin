import os
from os import path
import logging

logger = logging.getLogger("tests.camera")
logger.setLevel(logging.DEBUG)

from octoprint_mrbeam.camera import undistort
from octoprint_mrbeam.printing.profile import LaserCutterProfileManager
import cv2

CAM_FOLDER = path.join(path.dirname(path.abspath(__file__)), "cam")

path_to_cam_params = path.join(CAM_FOLDER, "lens_correction_2048x1536.npz")
path_to_pic_settings = path.join(CAM_FOLDER, "pic_settings.yaml")
path_to_last_markers = path.join(CAM_FOLDER, "last_markers.json")

mrb_volume = LaserCutterProfileManager.default['volume']
out_pic_size = int(mrb_volume['width']), int(mrb_volume['depth'])
logging.debug("out pic size : %s", out_pic_size)

# load cam_params from file
cam_params = undistort._getCamParams(path_to_cam_params)
logging.debug('Loaded cam_params: {}'.format(cam_params))

# load pic_settings json
pic_settings = undistort._getPicSettings(path_to_pic_settings)
logging.debug('Loaded pic_settings: {}'.format(pic_settings))
for file in os.listdir(path.join(CAM_FOLDER, "undistorted_images")):
    print("############# %s ############ " % file)
    if file.endswith(".jpg"):
        input_image = cv2.imread(path.join(CAM_FOLDER, "undistorted_images", file))
        path_to_output_image = path.join(CAM_FOLDER, "prepared_images", path.basename(file))
        undistort.prepareImage(input_image,  #: Union[str, np.ndarray],
                               path_to_output_image,  #: str,
                               cam_dist=cam_params[undistort.DIST_KEY],
                               cam_matrix=cam_params[undistort.MTX_KEY],
                               pic_settings=pic_settings,
                               last_markers=None,
                               size=out_pic_size,
                               quality=65,
                               debug_out=True,  # self.save_debug_images,
                               stopEvent=None,
                               threads=-1)
