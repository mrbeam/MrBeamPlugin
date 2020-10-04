#!/usr/bin/env python

"""
Test the gcode creating functions
"""

from octoprint_mrbeam.gcodegenerator import (
    img2gcode,
    img_separator,
    jobtimeestimation,
)


def test_trivial_img2gcode():
    """Test a trivial input image to create gcode output."""
    pass


def test_gcode_stress_test():
    """
    Test a bunch of different images,
    mostly to test how long the conversions take
    """

    pass


def test_memory_stress():
    """
    Test whether the memory management is sufficient.
    Only pertinent with very large engravings.
    """
    pass


def test_time_estimation():
    """
    Compare the real engraving / laser job time to the
    predicted duration
    """
    # TODO
    pass


def test_engraving_modes():
    """
    Test whether the different modes produce an output.
    Does not analyse the result file.
    """
    pass
