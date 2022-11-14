#!/usr/bin/env python

import logging
import re


SPEED_NONE = 1500

HOMED_X = 500
HOMED_Y = 390


FLOAT_NUMBER = r"[0-9]+\.?[0-9]*"
FIND_X = r"X" + FLOAT_NUMBER
FIND_Y = r"Y" + FLOAT_NUMBER
FIND_SPEED = r"F" + FLOAT_NUMBER
FIND_INT = r"S" + FLOAT_NUMBER


def read(gcode, init_x=HOMED_X, init_y=HOMED_Y, init_intensity=-1):
    """Iterate through all of the relevent lines of gcode. Yields a tuple
    giving the nex position, speed and laser strength.

    :param gcode: Iterable object containing the gcode lines
    """
    line_counter = 0
    x = init_x
    y = init_y
    _x, _y = x, y
    speed = 0
    intensity = init_intensity
    # yield x, y, speed, intensity
    # regex compiled searches
    find_x = re.compile(FIND_X)
    find_y = re.compile(FIND_Y)
    find_speed = re.compile(FIND_SPEED)
    find_intensity = re.compile(FIND_INT)
    for line in gcode:
        line_counter += 1
        first_char = line[0]
        command = line[1:]
        if first_char == "G":
            # logging.debug("processing line : %s", line.strip('\n '))
            # Extract x and y coordinates
            found_x = _find_val(find_x, command)
            if found_x is not None:
                x = found_x
            found_y = _find_val(find_y, command)
            if found_y is not None:
                y = found_y
            second_char = command[0]
            if second_char == "0":
                # G0: Rapid Travel - maximum speed and turns off laser.
                # logging.debug("Yield x % 5s y % 5s speed % 3s intensity % 3s", x, y, SPEED_NONE, -1)
                yield x, y, SPEED_NONE, -1
            elif second_char == "1":
                # G1: Laser travel - use laser intensity and speed.
                # intensity = _find_val(find_intensity, command) or intensity
                found_int = _find_val(find_speed, command)
                if found_int is not None:
                    intensity = found_int
                # speed = _find_val(find_speed, command) or speed
                found_speed = _find_val(find_speed, command)
                if found_speed is not None:
                    speed = found_speed
                # logging.debug("Yield x % 5s y % 5s speed % 3s intensity % 3s", x, y, speed, intensity)
                yield x, y, speed, intensity
        elif first_char == "F":
            speed = _find_val(find_speed, command) or speed
        elif first_char == "M":
            # TODO
            pass


def read_file(path):
    """Same as ``read``, but takes a file path as input."""
    with open(path, "r") as gfile:
        for result in read(gfile.readlines()):
            yield result


def _find_val(pattern, search_string, type_=float):
    found = pattern.search(search_string)
    if found is None:
        return None
    else:
        span = found.span()
        slice_ = slice(span[0] + 1, span[1])
        return type_(search_string[slice_])
