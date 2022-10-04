#!/usr/bin/env python

"""Test the gcode creating functions."""

import io
import numpy as np

import logging
import pytest
from octoprint.util import dict_merge
from octoprint_mrbeam.gcodegenerator import img2gcode

# from os.path import dirname, basename, join, split, realpath


class TestG0Generation:
    def setup_method(self, method):
        """
        Setup to allow each function to have a generic image processor.
        """
        self.fh = io.StringIO()

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

    def test_overshoot(self):
        for size in [0, 0.0, 1.123456, 30]:
            for dy in [0, 0.001, 0.5, 3, 50]:
                # for dx in [0, .001, .5, 3, 50]:
                dx = 0  # change when the overshoot can change with a higher dx
                self.ip.backlash_x = size
                start = np.array([2, 2])
                end = start + np.array([dx, dy])
                gc = self.ip.get_overshoot(start, end, 1, size, offset_counter=0)
                self.log.debug("{} - size {} -> {}\n{}".format(start, size, end, gc))
                assert "nan" not in gc.lower()
                # assert gc == "foo"

    def test_generate_gcode(self):
        from PIL import Image

        black10x3 = Image.new("L", (10, 3), (0))
        imgArray = [{"i": black10x3, "x": 0, "y": 0, "id": "black10x3"}]
        xMM = 495
        yMM = 2.3
        wMM = 1
        hMM = 0.3
        file_id = "generic black 10x3 px"
        self.ip.generate_gcode(imgArray, xMM, yMM, wMM, hMM, file_id)
        gc = self.fh.getvalue()
        self.log.debug("\n" + gc)
        # assert gc == "foo"
