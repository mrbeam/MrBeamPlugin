#!/usr/bin/env python

import re


SPEED_NONE = 1500

HOMED_X = 500
HOMED_Y = 390

FIND_X = r"X(\d+\.?\d+)"
FIND_Y = r"Y(\d+\.?\d+)"
FIND_SPEED = r"F(\d+\.?\d+)"
FIND_INT = r"S(\d+\.?\d+)"


def read(gcode, init_x=HOMED_X, init_y=HOMED_Y, init_intensity=-1):
    """
    Iterate through all of the relevent lines of gcode.
    Yields a tuple giving the nex position, speed and laser strength.
    :param gcode: Iterable object containing the gcode lines
    """
    line_counter = 0
    x = init_x
    y = init_y
    _x, _y = x, y
    speed = 0
    intensity = init_instensity
    yield x, y, speed, intensity
    # regex compiled searches
    find_x = re.compile(FIND_X)
    find_y = re.compile(FIND_Y)
    find_speed = re.compile(FIND_SPEED)
    find_intensity = re.compile(FIND_INT)
    for line in gcode:
        line_counter += 1
        first_char = line[0]
        if first_char == "G":
            command = line[1:]
            # Extract x and y coordinates
            for coord, pattern in [[x, find_x], [y, find_y]]:
                coord = _find_val(pattern, command) or coord
            second_char = command[0]
            if second_char == "0":
                # G0: Rapid Travel - maximum speed and turns off laser.
                yield x, y, SPEED_NONE, -1
            elif second_char == "1":
                # G1: Laser travel - use laser intensity and speed.
                intensity = _find_val(find_intensity, command, type_=int) or intensity
                speed = _find_val(find_speed, command, type_=int) or speed
                yield x, y, speed, intensity
        elif first_char == "F":
            speed = _find_val(find_speed, command, type_=int) or speed
        elif first_char == "M":
            # TODO
            pass


def read_file(path):
    """Same as ``read``, but takes a file path as input."""
    with open(gcode_file, "r") as gfile:
        for result in read(gfile.readlines()):
            yield result


def _find_val(pattern, search_string, type_=float):
    found = pattern.search(search_string)
    if found is None:
        return None
    else:
        return type_(slice(*command[found.span()]))
