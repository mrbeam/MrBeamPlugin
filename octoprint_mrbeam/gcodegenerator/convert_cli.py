#!/usr/bin/env python
"""Command line interface for convert.py.

This program is free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation; either version 2 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program; if not, write to the Free Software
Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA
"""
from .converter import Converter
from .job_params import JobParams

import optparse
import os
import sys
import logging


if __name__ == "__main__":
    OptionParser = optparse.OptionParser(usage="usage: %prog [options] SVGfile")
    OptionParser.add_option(
        "-d",
        "--directory",
        action="store",
        type="string",
        dest="directory",
        default=None,
        help="Directory for gcode file",
    )
    OptionParser.add_option(
        "-f",
        "--filename",
        action="store",
        type="string",
        dest="file",
        default=None,
        help="File name",
    )
    OptionParser.add_option(
        "",
        "--dpi",
        action="store",
        type="float",
        dest="svgDPI",
        default="90",
        help="dpi of the SVG file. Use 90 for Inkscape and 72 for Illustrator",
    )
    OptionParser.add_option(
        "",
        "--biarc-max-split-depth",
        action="store",
        type="int",
        dest="biarc_max_split_depth",
        default="4",
        help="Defines maximum depth of splitting while approximating using biarcs.",
    )
    OptionParser.add_option(
        "",
        "--engrave",
        action="store_true",
        dest="engrave",
        default=False,
        help="Engrave Image/Design.",
    )
    OptionParser.add_option(
        "",
        "--no-header",
        type="string",
        help="omits Mr Beam start and end sequences",
        default="false",
        dest="noheaders",
    )

    options, args = OptionParser.parse_args(sys.argv[1:])
    option_dict = vars(options)
    svg_file = args[-1]

    if option_dict["file"] == None:
        without_path = os.path.basename(svg_file)
        option_dict["file"] = os.path.splitext(without_path)[0] + ".gcode"
        print("using default filename", option_dict["file"])
    if option_dict["directory"] == None:
        option_dict["directory"] = os.path.dirname(os.path.realpath(svg_file))
        print("using default folder", option_dict["directory"])

    debug_multicolor = [
        {
            "passes": "1",
            "feedrate": "1000",
            "pierce_time": "0",
            "color": "#000000",
            "intensity": "10",
            "job": 1,
        },
        {
            "passes": "1",
            "feedrate": "800",
            "pierce_time": "0",
            "color": "#ff0000",
            "intensity": "20",
            "job": 2,
        },
        {
            "passes": "1",
            "feedrate": "400",
            "pierce_time": "0",
            "color": "#0000ff",
            "intensity": "30",
            "job": 3,
        },
        {
            "passes": "1",
            "feedrate": "400",
            "pierce_time": "0",
            "color": "black",
            "intensity": "30",
            "job": 4,
        },
    ]

    params = dict()
    params["directory"] = option_dict["directory"]
    params["file"] = option_dict["file"]
    params["noheaders"] = "false"
    params["vector"] = debug_multicolor
    params["engrave"] = option_dict["engrave"]
    params["raster"] = {
        "intensity_white": JobParams.Default.INTENSITY_WHITE,
        "intensity_black": JobParams.Default.INTENSITY_BLACK,
        "speed_white": JobParams.Default.FEEDRATE_WHITE,
        "speed_black": JobParams.Default.FEEDRATE_BLACK,
        "contrast": JobParams.Default.CONTRAST,
        "sharpening": JobParams.Default.SHARPENING,
        "dithering": JobParams.Default.DITHERING,
        "beam_diameter": JobParams.Default.BEAM_DIAMETER,
        "pierce_time": JobParams.Default.PIERCE_TIME,
    }

    e = Converter(params, svg_file)
    ch = logging.StreamHandler()
    ch.setLevel(logging.DEBUG)
    formatter = logging.Formatter("%(asctime)s %(name)s %(levelname)s: %(message)s")
    ch.setFormatter(formatter)
    e._log.addHandler(ch)
    e.convert()
