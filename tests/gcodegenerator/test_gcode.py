#!/usr/bin/env python

"""
Test the gcode creating functions
"""

from itertools import cycle
import pytest
from octoprint_mrbeam.gcodegenerator import img2gcode
from os.path import dirname, join, realpath


path = dirname(realpath(__file__))
GCODE_DIR = join(path, "..", "rsc", "gcode")  # this directory doesn't exist!
IN_FILES = pytest.mark.datafiles(
    GCODE_DIR,
    # join(GCODE_DIR, "*.gco"),
    # join(GCODE_DIR, "*.jpg"),
    # join(GCODE_DIR, "*.png"),
    # join(GCODE_DIR, "*.svg"),
)

W, H = 500, 390

STRESS_COUNT = 3

# TODO frozen_dict
DEFAULT_OPTIONS = {"w": 100, "h": 100, "x": 10, "y": 10, "file_id": "SomeDummyText"}
DEFAULT_OUT_GCO = "out.gco"

############
## RASTER ##
############


def _test_raster_files(datafiles, paths, options, repeat=0, keep_out_file_name=False):
    """
    Run the files from given path through the image processor with
    the given options. If options is not the same list length as paths,
    it will cycle around.
    :param paths: list of file paths
    :param options: list of kwargs (Mapping) forwarded to ImageProcessor.img_to_gcode
    :param repeat: repeat an additional N times (runs Once if repeat==0)
    """
    default_out = str(datafiles / DEFAULT_OUT_GCO)
    if not options:
        options = [
            DEFAULT_OPTIONS,
        ]
    options = cycle(options)
    for _ in range(repeat + 1):
        for p in paths:
            # in convert image path to datauri?
            if keep_out_file_name:
                out = p + ".gco"
            else:
                out = default_out
            with open(out, "w") as f:
                ip = img2gcode.ImageProcessor(f, W, H)
                ip.img_to_gcode(p, **next(options))


@IN_FILES
@pytest.mark.skip("skipping")
def test_all(datafiles):
    """
    Test images over and over for detecting cpu stress,
    mostly to test how long the conversions take
    """
    paths = [path for path in datafiles.listdir() if str(path).endswith(".png")]
    options = []
    _test_raster_files(datafiles, paths, options, STRESS_COUNT)


@pytest.mark.skip("skipping")
@IN_FILES
def test_trivial_img2gcode(datafiles):
    """Test a trivial input image to create gcode output."""
    paths = [
        str(datafiles / "black_pix.png"),
        str(datafiles / "white_pix.png"),
    ]
    options = []
    _test_raster_files(datafiles, paths, options)
    pass


@pytest.mark.skip("skipping stress test")
@IN_FILES
def test_gcode_stress_test(datafiles):
    """
    Test images over and over for detecting cpu stress,
    mostly to test how long the conversions take
    """
    paths = [
        str(datafiles / "simple.png"),
        str(datafiles / "gradient.png"),
    ]
    options = []
    _test_raster_files(datafiles, paths, options, STRESS_COUNT)


@pytest.mark.skip("skipping")
@IN_FILES
def test_islands(datafiles):
    """
    Test the separation of islands.
    Only pertinent with very large engravings with
    multiple islands
    """
    paths = [
        str(datafiles / "islands1.png"),
        str(datafiles / "islands2.png"),
    ]
    options = []
    _test_raster_files(datafiles, paths, options)


@pytest.mark.skip("skipping stress test")
@IN_FILES
def test_memory_stress(datafiles):
    """
    Test whether the memory management is sufficient.
    Only pertinent with very large engravings with
    multiple islands
    """
    paths = [
        str(datafiles / "islands_large.png"),
    ]
    options = []
    _test_raster_files(datafiles, paths, options)


@IN_FILES
@pytest.mark.skip("skipping")
def test_time_estimation(datafiles):
    """
    Compare the real engraving / laser job time to the
    predicted duration
    """
    paths = []
    options = []
    _test_raster_files(datafiles, paths, options)
    # TODO test the time estimation of a pre-sliced gcode file


@IN_FILES
@pytest.mark.skip("skipping")
def test_modes(datafiles):
    """
    Test whether the different modes produce an output.
    Does not analyse the result file.
    """
    paths = [
        str(datafiles / "simple.png"),
        str(datafiles / "gradient.png"),
    ]
    options = []
    _test_raster_files(datafiles, paths, options)


@IN_FILES
@pytest.mark.skip("skipping")
def test_work_area_clip(datafiles):
    """
    Test whether the ouptut gcode of clipping images
    gets properly cropped.
    """
    # TODO How to input .mrb files?
    paths = []
    options = []
    _test_raster_files(datafiles, paths, options)


@IN_FILES
@pytest.mark.skip("skipping")
def test_result(datafiles):
    # Create the DEFAULT_OUT_GCO file
    _test_raster_files(
        datafiles,
        [str(datafiles / "simple.png")],
        [
            {"x": 100, "y": 100, "w": 100, "h": 100},
        ],
    )
    from ..testutils.draw_gcode import draw_gcode_file

    draw_gcode_file(str(datafiles / DEFAULT_OUT_GCO), True, False)


############
## VECTOR ##
############
