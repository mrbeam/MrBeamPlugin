#!/usr/bin/env python

"""
Test the gcode creating functions
"""

import StringIO
import numpy as np

from PIL import Image
import logging
import pytest
from octoprint_mrbeam.gcodegenerator import img2gcode

# from os.path import dirname, basename, join, split, realpath


class TestG0Generation:
    def setup_method(self, method):

        self.fh = StringIO.StringIO()

        # with open("/tmp/test_img2gcode.gco", "w") as self.fh:
        self.ip = img2gcode.ImageProcessor(
            output_filehandle=self.fh,
            workingAreaWidth=500,
            workingAreaHeight=390,
            beam_diameter=0.1,
            backlash_x=0,
            overshoot_distance=1,
            intensity_black=999,
            intensity_white=111,
            intensity_black_user=77,
            intensity_white_user=11,
            speed_black=222,
            speed_white=1111,
            dithering=False,
            pierce_time=0,
            engraving_mode=img2gcode.ImageProcessor.ENGRAVING_MODE_PRECISE,
            extra_overshoot=True,
            eng_compressor=100,
            material=None,
        )
        # basics
        self.log = logging.getLogger()

    def teardown_method(self, method):
        self.fh.close()
        pass

    def test_get_gcode_g0(self):
        assert "G0S0" == self.ip._get_gcode_g0(x=None, y=None, comment=None)
        assert "G0X0.00Y0.00S0" == self.ip._get_gcode_g0(x=0, y=0, comment=None)
        assert "G0Y1.00S0; Linefeed" == self.ip._get_gcode_g0(
            x=None, y=1, comment="Linefeed"
        )
        assert "G0Y0.00S0; Y<min, Y set to 0, was -1" == self.ip._get_gcode_g0(
            x=None, y=-1, comment="Y<min"
        )
        assert "G0Y390.00S0; Y>max, Y set to 390, was 391" == self.ip._get_gcode_g0(
            x=None, y=391, comment="Y>max"
        )
        assert "G0X0.00S0; X<min, X set to 0, was -1" == self.ip._get_gcode_g0(
            x=-1, y=None, comment="X<min"
        )
        assert "G0X500.00S0; X>max, X set to 500, was 501" == self.ip._get_gcode_g0(
            x=501, y=None, comment="X>max"
        )
        with pytest.raises(ValueError) as exception:
            self.ip._get_gcode_g0(x=float("NaN"), y=None, comment=None)
        assert "Coordinate is NaN" in str(exception.value)
        with pytest.raises(ValueError) as exception:
            self.ip._get_gcode_g0(x=None, y=float("NaN"), comment=None)
        assert "Coordinate is NaN" in str(exception.value)

    def test_get_gcode_g1(self):
        assert "G1X0.00Y0.00" == self.ip._get_gcode_g1(
            x=0, y=0, s=None, f=None, comment=None
        )
        assert "G1Y1.00; Linefeed" == self.ip._get_gcode_g1(
            x=None, y=1, s=None, f=None, comment="Linefeed"
        )
        assert "G1Y0.00; Y<min, Y set to 0, was -1" == self.ip._get_gcode_g1(
            x=None, y=-1, s=None, f=None, comment="Y<min"
        )
        assert "G1Y390.00; Y>max, Y set to 390, was 391" == self.ip._get_gcode_g1(
            x=None, y=391, s=None, f=None, comment="Y>max"
        )
        assert "G1X0.00; X<min, X set to 0, was -1" == self.ip._get_gcode_g1(
            x=-1, y=None, s=None, f=None, comment="X<min"
        )
        assert "G1X500.00; X>max, X set to 500, was 501" == self.ip._get_gcode_g1(
            x=501, y=None, s=None, f=None, comment="X>max"
        )
        assert "G1X1.00S100; Intensity" == self.ip._get_gcode_g1(
            x=1, y=None, s=100, f=None, comment="Intensity"
        )
        assert "G1X1.00S0; Intensity<0, S set to 0, was -1" == self.ip._get_gcode_g1(
            x=1, y=None, s=-1, f=None, comment="Intensity<0"
        )
        assert (
            "G1X1.00S1300; Intensity>max, S set to 1300, was 99999"
            == self.ip._get_gcode_g1(
                x=1, y=None, s=99999, f=None, comment="Intensity>max"
            )
        )

        with pytest.raises(ValueError) as exception:
            self.ip._get_gcode_g1(x=None, y=None, s=None, f=None, comment=None)
        assert "GCode 'G1' at least requires one literal." in str(exception.value)

        with pytest.raises(ValueError) as exception:
            self.ip._get_gcode_g1(x=float("NaN"), y=None, comment=None)
        assert "Coordinate is NaN" in str(exception.value)

        with pytest.raises(ValueError) as exception:
            self.ip._get_gcode_g1(x=None, y=float("NaN"), comment=None)
        assert "Coordinate is NaN" in str(exception.value)

    def test_get_octogon_linefeed(self):
        direction_positive = True
        img_pos_mm = (0, 0)
        line_info = {
            "left": 0,
            "right": 10,
            "row": 0,
            "img_w": 10,
            "img_h": 3,
        }
        y = 0
        row = 0
        gc = self.ip._get_octogon_linefeed(
            direction_positive, img_pos_mm, line_info, y, row
        )
        assert gc == "foo", "octogon false"

    def test_generate_gcode(self):
        black10x3 = Image.new("L", (10, 3), (0))
        imgArray = [{"i": black10x3, "x": 0, "y": 0, "id": "black10x3"}]
        xMM = 495
        yMM = 2.3
        wMM = 1
        hMM = 0.3
        file_id = "generic black 10x3 px"
        self.ip.generate_gcode(imgArray, xMM, yMM, wMM, hMM, file_id)
        gc = self.fh.getvalue()
        print gc
        assert gc == "foo"

    def test_octo(self):
        direction_positive = not True
        img_pos_mm = (333, 111)
        line_info = {
            "left": None,
            "right": -1,
            "row": 0,
            "img_w": 0,
            "img_h": 3,
        }
        y = 0
        row = 0
        gc_ctx = {"x": 100, "y": 55}
        beam = 0.1

        if not direction_positive:
            _minmax = max
            side = "right"
            k = 1
        else:
            _minmax = min
            side = "left"
            k = -1

        _ov = 0  ###
        _bk = 10  ###
        extrema_x = _minmax(
            gc_ctx["x"],
            img_pos_mm[0] + beam * line_info[side] + k * (2 * _ov + _bk),
        )
        start = np.array([extrema_x, gc_ctx["y"]])  # None, None
        end = np.array([extrema_x, y])  # None, 0
        self.log.info("start: {}".format(start))
        self.log.info("end: {}".format(end))
        dy = end[1] - start[1]
        _vsp = _ov  # extra vertical_spacing in the overshoot
        _line1 = np.array([k, 0.0])
        _line2 = np.array([0.0, 1.0])
        _line3 = np.array([k, 1.0])
        _line4 = np.array([k, -1.0])
        # Extend the start and end point differently depending on
        # the line so there is no overlap between the overshoots
        self.log.info(
            "_ov={}, row={}, _vsp={}, dy={}, _line1={}".format(
                _ov, row, _vsp, dy, _line1
            )
        )
        # _ov=0, row=0, _vsp=0, dy=-55.0, _line1=[ 1.  0.]
        shift = _ov * (row % (_vsp / dy)) / 2 * _line1
        start = start + shift
        end = end + shift
        self.log.warning("start: {}, end: {}, shift:{}".format(start, end, shift))
        # base size of the octogon (dictates length of sides)
        _size = 2 * _ov
        overshoot_gco = "".join(
            map(
                lambda v: self.ip._get_gcode_g0(x=v[0], y=v[1], comment="octogon")
                + "\n",
                np.cumsum(
                    [
                        start + (_size + _vsp / 2) * _line4,
                        _size * _line1 / 2,
                        (_size + dy / 2) * _line3,
                        _vsp * _line2,
                        -(_size - dy / 2) * _line4,
                        -_size * _line1 / 2,
                    ],
                    axis=0,
                ),
            )
        )
        self.log.info(overshoot_gco)
