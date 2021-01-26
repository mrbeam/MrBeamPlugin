#!/usr/bin/env python

"""
Draw the content of a gcode onto a canvas.
It can then be compared with the origin file.
"""

import logging
from test_gcode import W, H
from octoprint_mrbeam.gcodegenerator.read import HOMED_X, HOMED_Y
import time

LASER_WIDTH = 0.25

# SPEED
SPEED_NONE = 1500
SPEED_WHITE = 1200
SPEED_BLACK = 400
SPEED_CUT = 300

# INTENSITY
INT_NONE = -1
INT_WHITE = 0
INT_BLACK = 500
INT_CUT = 500

MAX_STRENGTH = float(INT_CUT) / SPEED_CUT

PASSES_CUT = 3

ANIMATION_SPEED = 1


def draw_gcode(gcode, graphical=False, sim_speed=False):
    """
    Draw the gcode result on a canvas.
    TODO get values of speed_black etc from gcode header
    """
    from octoprint_mrbeam.gcodegenerator.read import read as g_read

    return _draw_commands(g_read(gcode), graphical=graphical, sim_speed=sim_speed)


def draw_gcode_file(path, graphical=False, sim_speed=False):
    from octoprint_mrbeam.gcodegenerator.read import read_file as g_read

    # previous values
    return _draw_commands(g_read(path), graphical=graphical, sim_speed=sim_speed)


def _draw_commands(commands, graphical=False, sim_speed=False, out="out.svg"):
    """
    Draw the gcode commands on a canvas.
    """
    import turtle

    # previous values
    _x, _y = None, None
    # _speed = INT_NONE
    # if not graphical:
    #     turtle
    if not sim_speed or not graphical:
        turtle.speed(0)  # No animation speed
    turtle.pensize(LASER_WIDTH)
    turtle.hideturtle()
    turtle.penup()
    if graphical:
        turtle.getscreen().setworldcoordinates(0, 0, 500, 390)
    for x, y, speed, intensity in commands:
        if x == _x and y == _y:
            continue
        elif intensity == INT_NONE and x == HOMED_X and y == HOMED_Y:
            # Ignore homing position
            continue
        else:
            _x, _y = x, y
        # logging.debug("Moving to x % 5s y % 5s speed % 3s intensity % 3s", x, y, speed, intensity)
        assert speed > 0
        if sim_speed and graphical:
            turtle.speed(int(10 * speed / SPEED_NONE))
        if turtle.isdown() and intensity == INT_NONE:
            turtle.penup()
        elif intensity == INT_NONE:
            pass
        else:
            strength = intensity / speed
            color = tuple([turtle.colormode() * (1 - strength / MAX_STRENGTH)] * 3)
            turtle.pencolor(color)
            turtle.pendown()
        turtle.goto(x, y)
    if out:
        import canvasvg

        canvasvg.saveall(out, turtle.getscreen().getcanvas())
    if graphical:
        time.sleep(2)


def _draw_cut(gcode, canvas):
    """
    Draw the following part of the gcode as a cut.
    Stops iterarting over the gcode once it is no
    longer doing a cutting job.
    """
    pass


def _draw_engraving(gcode, canvas):
    """
    Draw the following part of the gcode as an engraving.
    Stops iterarting over the gcode once it is no
    longer doing a cutting job.
    """
    pass


def _show(canvas):
    """
    Refresh the canvas on the screen if you are
    debugging it that way
    """
    pass
