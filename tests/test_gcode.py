#!/usr/bin/env python

"""
Test the gcode creating functions
"""

from collections import Mapping
from itertools import cycle
import logging
import pytest
from octoprint.util import dict_merge
from octoprint_mrbeam.gcodegenerator import (
    img2gcode,
    img_separator,
    jobtimeestimation,
)
from os.path import dirname, basename, join, split, realpath


path = dirname(realpath(__file__))
GCODE_DIR = join(path, "rsc", "gcode")
IN_FILES = pytest.mark.datafiles(
    GCODE_DIR,
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
    else:
        # set default params if not given
        for i, op in enumerate(options):
            assert isinstance(op, Mapping)
            options[i] = dict_merge(DEFAULT_OPTIONS, options[i])
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
    # TODO test the time estimation of a pre-sliced gcode file
    paths = []
    options = []
    _test_raster_files(datafiles, paths, options)


@IN_FILES
@pytest.mark.skip("skipping")
def test_modes(datafiles):
    """
    Test whether the different modes produce an output.
    Does not analyse the result file.
    """
    # TODO
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
    # TODO
    paths = [str(datafiles / "simple.png"), str(datafiles / "islands2.png")]
    options = [
        {"x": -0.25, "y": -0.25},
        {"x": -1, "y": -1},
        {"x": W - 50, "y": H - 50},
        {"x": W - 1, "y": H - 1},
    ]
    for op in options:
        _test_raster_files(
            datafiles,
            paths,
            [
                op,
            ],
        )


@IN_FILES
@pytest.mark.skip("skipping")
def test_view_result(datafiles):
    # Create the DEFAULT_OUT_GCO file
    _test_raster_files(
        datafiles,
        [str(datafiles / "islands2.png")],
        [
            {"x": 100, "y": 100, "w": 30, "h": 30},
        ],
    )
    from tests.draw_gcode import draw_gcode_file

    draw_gcode_file(str(datafiles / DEFAULT_OUT_GCO), True, False)


@IN_FILES
def test_compare_results(datafiles):
    """
    Use the output of the gcode creator and
    compare it to the source image file.
    """
    import sys

    if sys.version_info < (3, 2, 0):
        logging.warning("Cannot run this test in Python2")
        exit("Cannot run this test in Python2")
    from tests.draw_gcode import draw_gcode_file
    import cairosvg

    paths = ([str(datafiles / "gradient.png")],)
    options = (
        [
            {"x": 100, "y": 100, "w": 30, "h": 30},
        ],
    )
    for p in paths:
        _test_raster_files(datafiles, [p], options)

        draw_gcode_file(
            str(datafiles / DEFAULT_OUT_GCO),
            True,
            False,
            out=str(datafiles / "out.svg"),
        )


############
## VECTOR ##
############
