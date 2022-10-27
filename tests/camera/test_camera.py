#!/usr/bin/env python
import pytest
import time
from os.path import dirname, join, realpath

from mock.mock import MagicMock, patch
from octoprint_mrbeam.camera import exc

from octoprint_mrbeam.camera.exc import MrbCameraError
from octoprint_mrbeam.camera.mrbcamera import MrbCamera
from octoprint_mrbeam.camera.worker import MrbPicWorker
from tests.testutils.fetch_resource import fetch

path = dirname(realpath(__file__))
CAM_DIR = join(path, "..", "rsc", "camera")

RESOURCES = [join(CAM_DIR, "raw.jpg")]
fetch(RESOURCES)


@pytest.mark.datafiles(
    join(CAM_DIR, "raw.jpg"),
)
def test_normal_use(datafiles):
    sett.set(
        ["mrbeam", "mock", "img_static"],
        str(datafiles / "raw.jpg"),
        force=True,
    )
    worker = MrbPicWorker()
    with MrbCamera(worker, shutter_speed=500) as cam:
        cam.capture()
        cam.async_capture()
        cam.wait()
        assert worker.count == 2
        assert cam.lastPic() is not None


def test_open_multiple_cams():
    worker = MrbPicWorker()
    try:
        with MrbCamera(worker) as cam1:
            with MrbCamera(worker) as cam2:
                raise Exception("Should not be able to open 2 cameras at the same time")
    except MrbCameraError as e:
        return


def test_concurrent_captures():
    with patch(
        "octoprint_mrbeam.camera.camera.settings",
        return_value=MagicMock(),
    ):
        worker = MrbPicWorker()
        with MrbCamera(worker, shutter_speed=0.5) as cam1:
            cam1.async_capture()
            time.sleep(0.2)
            try:
                cam1.capture()
            except exc.CameraException:
                return
            raise Exception("Should not be able to take 2 pictures at the same time")
