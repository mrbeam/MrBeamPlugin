#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""img2gcode.py functions for digesting paths into a simple list structure.

Copyright (C) 2014 Teja Philipp, teja@mr-beam.org

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
import optparse
import logging
import math
import numpy as np
from PIL import Image
from PIL import ImageEnhance
import base64
import io
import os.path
import time
import sys
import re
from .img_separator import ImageSeparator
from .profiler import Profiler
from .job_params import JobParams

from octoprint_mrbeam.mrb_logger import mrb_logger

EXTRA_OVERSHOOT_EXTRA_DURATION = 0.45
EXTRA_OVERSHOOT_MIN_DIST = 1  # in mm


class ImageProcessor:

    ENGRAVING_MODE_FAST = "fast"
    ENGRAVING_MODE_PRECISE = "precise"
    ENGRAVING_MODE_BASIC = "basic"

    ENGRAVING_MODE_DEFAULT = ENGRAVING_MODE_PRECISE

    # Machine Profile Mock, TODO get proper machine profile
    FEEDRATE_MIN = 30
    FEEDRATE_MAX = 5000
    INTENSITY_MIN = 0
    INTENSITY_MAX = 1300

    def __init__(
        self,
        output_filehandle=None,
        workingAreaWidth=None,
        workingAreaHeight=None,
        contrast=JobParams.Default.CONTRAST,
        sharpening=JobParams.Default.SHARPENING,
        beam_diameter=JobParams.Default.BEAM_DIAMETER,
        backlash_x=0.0,
        intensity_black=JobParams.Default.INTENSITY_BLACK,
        intensity_white=JobParams.Default.INTENSITY_WHITE,
        intensity_black_user=None,
        intensity_white_user=None,
        speed_black=JobParams.Min.SPEED,
        speed_white=JobParams.Max.SPEED,
        dithering=JobParams.Default.DITHERING,
        engraving_mode=None,
        pierce_time=JobParams.Default.PIERCE_TIME,
        overshoot_distance=1,
        extra_overshoot=False,
        eng_compressor=JobParams.Default.ENG_COMPRESSOR,
        material=None,
        eng_passes=JobParams.Default.ENG_PASSES,
    ):

        self.log = mrb_logger("octoprint.plugins.mrbeam.img2gcode")
        self.profiler = Profiler("img2gcode")
        self.profiler.start("init")

        # if True base64 image data urls embedded into the GCODE will be broken into short lines. If False it's one long line
        self.MULTILINE_DATA_URLS = False

        self.debug = True  # general debug
        self.debugPreprocessing = False  # write each step image to /tmp
        # backlash compensation will be applied only on lines in negative axis direction
        self.backlash_compensation_x = 0.0
        try:
            self.backlash_compensation_x = float(backlash_x)
        except ValueError:
            self.log.warn(
                "Can't convert backlash_x into float. value is: '%s'", backlash_x
            )

        try:
            self.debug = _mrbeam_plugin_implementation._settings.get(
                ["dev", "debug_gcode"]
            )
            self.debugPreprocessing = _mrbeam_plugin_implementation._settings.get(
                ["dev", "debug_gcode"]
            )
        except (NameError, AttributeError):
            self.debug = True
            self.debugPreprocessing = True
            self.log.info(
                "Gcode debugging enabled (not running in Mr Beam Plugin environment"
            )
        else:
            self.log.info("Gcode debugging {} (read from config)".format(self.debug))
            pass

        if self.debug:
            self.log.setLevel(logging.DEBUG)

        self.output_filehandle = output_filehandle
        self.beam = (
            float(beam_diameter) if beam_diameter else JobParams.Default.BEAM_DIAMETER
        )
        self.pierce_time = (
            float(pierce_time) / 1000.0 if pierce_time else JobParams.Min.PIERCE_TIME
        )
        self.pierce_intensity = JobParams.Default.PIERCE_INTENSITY
        self.ignore_brighter_than = 254  # TODO parametrize
        self.ignore_darker_than = 1  # TODO parametrize
        self.intensity_black = (
            float(intensity_black) if intensity_black else JobParams.Min.INTENSITY
        )
        self.intensity_white = (
            float(intensity_white) if intensity_white else JobParams.Min.INTENSITY
        )
        self.intensity_black_user = intensity_black_user
        self.intensity_white_user = intensity_white_user
        self.feedrate_white = float(speed_white) if speed_white else JobParams.Max.SPEED
        self.feedrate_black = float(speed_black) if speed_black else self.FEEDRATE_MIN
        self.compressor = (
            eng_compressor  # This value might be None if there is no compressor
        )
        self.material = material
        self.contrastFactor = float(contrast) if contrast else 0.0
        self.sharpeningFactor = float(sharpening) if sharpening else 0.0
        self.dithering = dithering == True or dithering == "True"
        self.overshoot_distance = overshoot_distance
        self.extra_overshoot = extra_overshoot
        # engraving mode switches
        self.engraving_mode = engraving_mode or self.ENGRAVING_MODE_DEFAULT
        self.separation = self.engraving_mode == self.ENGRAVING_MODE_FAST
        self.line_by_line = self.engraving_mode == self.ENGRAVING_MODE_BASIC
        self.eng_passes = int(eng_passes) if eng_passes else JobParams.Min.ENG_PASSES

        # overshoot settings
        # given an acceleration of 700mm/s², these are the ways necessary to reach target speed of
        # 5000 mm/min: 5mm
        # 3000 mm/min: 2mm
        # 2000 mm/min: 1mm
        # 1000 mm/min: 0.5mm
        # self.overshoot_distance = 1 # 1mm comfortable compromise, TODO: calculate individually
        self.workingAreaWidth = workingAreaWidth
        self.workingAreaHeight = workingAreaHeight
        if self.pierce_time > JobParams.Min.PIERCE_TIME and self.overshoot_distance > 0:
            self.log.info("Disabling overshoot, pierce time is set.")
            self.overshoot_distance = 0

        # checks if intensity settings are inverted eg. anodized aluminum
        self.is_inverted = self.intensity_white > self.intensity_black
        # self.is_first_pixel = True

        self._lookup_intensity = {}
        self._lookup_feedrate = {}
        self._output_gcode = ""
        self.gc_ctx = GC_Context()
        self.profiler.stop("init")

    def get_settings_as_comment(self, x, y, w, h, file_id=""):
        # if file id has linebreaks, ensure every line has a ';' at the beginning.
        file_id_lines = ";".join(file_id.splitlines(1))
        comment = "; Image: {:.2f}x{:.2f} @ {:.2f},{:.2f}|{}\n".format(
            w, h, x, y, file_id_lines
        )  # important for gcode preview! DO NOT CHANGE!!!
        comment += "; self.beam = {:.2f}\n".format(self.beam)
        comment += "; pierce_time = {:.3f}s\n".format(self.pierce_time)
        comment += "; intensity_black = {:.0f}\n".format(self.intensity_black)
        comment += "; intensity_white = {:.0f}\n".format(self.intensity_white)
        comment += "; intensity_black_user = {}\n".format(self.intensity_black_user)
        comment += "; intensity_white_user = {}\n".format(self.intensity_white_user)
        comment += "; feedrate_white = {:.0f}\n".format(self.feedrate_white)
        comment += "; feedrate_black = {:.0f}\n".format(self.feedrate_black)
        comment += "; backlash_compensation_x = {:.3f}\n".format(
            self.backlash_compensation_x
        )

        comment += "; material = {}\n".format(self.material)
        comment += "; contrastFactor = {:.2f}\n".format(self.contrastFactor)
        comment += "; sharpeningFactor = {:.2f}\n".format(self.sharpeningFactor)
        comment += "; dithering = {}\n".format(self.dithering)
        comment += "; overshoot distance = {}\n".format(self.overshoot_distance)
        comment += "; separation = {}\n".format(self.separation)
        comment += "; eng_compressor = {}\n".format(self.compressor)
        return comment

    def img_prepare(self, img, w_mm, h_mm):
        """
        1. pixel reduction (w,h)
        2. remove transparency
        3. contrast
        4. greyscale
        5. sharpen
        (? .contrast / curves (material))
        6. dithering
        7. separation (optimizes duration)
        """
        self.debugPreprocessing = False
        orig_w, orig_h = img.size
        if w_mm < 0:
            w_mm = orig_w * self.beam

        if h_mm < 0:
            ratio = orig_w / float(orig_h)
            h_mm = w_mm / ratio

        dest_wpx = int(w_mm / self.beam)
        dest_hpx = int(h_mm / self.beam)

        # do not resize if its just one pixel
        if abs(dest_wpx - orig_w) <= 1:
            dest_wpx = orig_w
        if abs(dest_hpx - orig_h) <= 1:
            dest_hpx = orig_h

        # performance measurement
        self.profiler.start("scale")

        # 1. scale
        if dest_wpx != orig_w or dest_hpx != orig_h:
            self.log.info(
                "scaling {}x{} to {}x{}".format(orig_w, orig_h, dest_wpx, dest_hpx)
            )
            img = img.resize((dest_wpx, dest_hpx))
        else:
            self.log.info(
                "scaling - nothing to do, image remains {}x{}".format(orig_w, orig_h)
            )

        if self.debugPreprocessing:
            img.save("/tmp/img2gcode_1_resized.png")
        self.profiler.stop("scale")

        left, upper, right, lower = (0, 0, dest_wpx, dest_hpx)
        bbox = img.getbbox()
        #        self.log.info("#####")
        #        self.log.info(bbox)
        #        self.log.info((0, 0, dest_wpx, dest_hpx))

        # 1a. crop to bbox
        if True:
            self.profiler.start("crop")

            # TODO: this removes only transparent pixels, white pixels are still counted as content.
            bbox = img.getbbox()
            if bbox is None:
                self.log.debug(
                    "img_prepare() Empty bounding box, nothing to engrave. Returning"
                )
                return []

            left, upper, right, lower = bbox  # bbox is a tuple of four
            bb_w = right - left
            bb_h = lower - upper
            if bb_w != dest_wpx or bb_h != dest_hpx:
                img = img.crop(bbox)
                old_pixels = dest_wpx * dest_hpx
                bb_area = bb_w * bb_h
                ratio = bb_area / old_pixels
                self.log.debug(
                    "Cropped to bbox: Pixel reduction: %i -> %i (%f%%), bb_w: %s, bb_h: %s, left: %s, upper: %s, right: %s, lower: %s ",
                    old_pixels,
                    bb_area,
                    ratio,
                    bb_w,
                    bb_h,
                    left,
                    upper,
                    right,
                    lower,
                )
                if self.debugPreprocessing:
                    img.save("/tmp/img2gcode_1a_cropped.png")
                dest_wpx = bb_w
                dest_hpx = bb_h

            else:
                self.log.debug("Cropping skipped. Not necessary.")

            self.profiler.stop("crop").start("remove_transparency")

        # 2. remove transparency
        if (not self.is_inverted) and (img.mode == "RGBA"):
            whitebg = Image.new("RGBA", (dest_wpx, dest_hpx), "white")
            img = Image.alpha_composite(whitebg, img)

            if self.debugPreprocessing:
                img.save("/tmp/img2gcode_2_whitebg.png")

        self.profiler.stop("remove_transparency").start("contrast")

        # 3. contrast
        if self.contrastFactor > 1.0:
            contrast = ImageEnhance.Contrast(img)
            img = contrast.enhance(self.contrastFactor)  # 1.0 returns original
            if self.debugPreprocessing:
                img.save("/tmp/img2gcode_3_contrast.png")

        self.profiler.stop("contrast").start("greyscale")

        # 4. greyscale
        img = img.convert("L")
        if self.debugPreprocessing:
            img.save("/tmp/img2gcode_4_greyscale.png")

        # curves depending on material
        if self.material != "default":
            # TODO
            pass

        self.profiler.stop("greyscale").start("sharpness")

        # 5. sharpness (factor: 1 => unchanged , 25 => almost b/w)
        if self.sharpeningFactor > 1.0:
            sharpness = ImageEnhance.Sharpness(img)
            img = sharpness.enhance(self.sharpeningFactor)
            if self.debugPreprocessing:
                img.save("/tmp/img2gcode_5_sharpened.png")

        self.profiler.stop("sharpness").start("dithering")

        # 6. dithering
        if self.dithering == True:
            img = img.convert("1")
            if self.separation or not self.line_by_line:
                self.separation = False
                self.line_by_line = True
                self.log.warn(
                    "Dithering overwrites engraving mode (workaround for #455)"
                )  # TODO fix in frontend. separation does never make sense with dithering

            if self.debugPreprocessing:
                img.save("/tmp/img2gcode_6_dithered.png")

        self.profiler.stop("dithering")

        # 7. split image at white pixels
        separator = ImageSeparator()

        self.profiler.start("separation_contour")
        # 7.1. split by contour
        contour_parts = []
        if self.line_by_line:
            self.log.debug(
                "skipping contour separation, user selected line-by-line mode"
            )
            contour_parts = [{"i": img, "x": left, "y": upper, "id": "noid"}]
        else:
            self.log.debug("contour separation starting...")
            contour_parts = separator.separate_contours(
                img, x=left, y=upper, threshold=self.ignore_brighter_than + 1
            )
            self.log.debug("separated into {} contours".format(len(contour_parts)))

        parts = []
        if self.debugPreprocessing:
            for i, p in enumerate(contour_parts):
                img_data = p["i"]
                img_data.save(
                    "/tmp/img2gcode_7_contourpart_{:0>3}_@{},{}.png".format(
                        i, p["x"], p["y"]
                    )
                )

        self.profiler.stop("separation_contour").start("separation_lpf")

        if self.separation == True:
            for cp in contour_parts:

                # 7.2. split contour by left-pixels-first method
                img_data = cp["i"]
                off_x = cp["x"]
                off_y = cp["y"]

                tmp = separator.separate(cp, threshold=self.ignore_brighter_than + 1)
                if tmp is None:
                    parts.extend(contour_parts)
                else:
                    for p in tmp:
                        parts.append(
                            {
                                "i": p["i"],
                                "x": off_x + p["x"],
                                "y": off_y + p["y"],
                                "id": p["id"],
                            }
                        )

                self.log.debug("separated into {} parts".format(len(parts)))
        else:
            parts.extend(contour_parts)

        if self.debugPreprocessing:
            for i, p in enumerate(parts):
                img_data = p["i"]
                img_data.save(
                    "/tmp/img2gcode_7_part_{:0>3}_@{},{}.png".format(i, p["x"], p["y"])
                )

        self.profiler.stop("separation_lpf").finalize()
        return parts

    def generate_gcode(self, imgArray, xMM, yMM, wMM, hMM, file_id):
        """takes an array of objects containing the separated image and
        converts them to gcode.

        :param imgArray: array of imagedata containing dicts
        :param xMM: x position of the image in mm (origin: left bottom)
        :param yMM: y position of the image in mm (origin: left bottom)
        :param wMM: width of the image in mm
        :param hMM: height of the image in mm
        :param file_id: origin file id, stored in comment for debugging / analysis
        :type imgArray: [{i: imgdata, x: x_offset_px, y: y_offset_px }]
        :type x: int, float
        :type y: int, float
        :type w: int, float
        :type h: int, float
        :type file_id: string
        :returns: gcode
        :rtype: string
        """

        # write all parameters used for generating the gcode into the file
        self.profiler.start("settings_as_comment")
        settings_comment = self.get_settings_as_comment(xMM, yMM, wMM, hMM, "")
        self.log.info("img2gcode conversion started:\n%s" % settings_comment)
        self._append_gcode(self.get_settings_as_comment(xMM, yMM, wMM, hMM, file_id))
        self.profiler.stop("settings_as_comment").start("gc_before_img")
        xMM += self.beam / 2.0 * 0
        yMM -= self.beam

        # pre-condition: set mrbeam_compressor, set feedrate, enable laser with 0 intensity.
        if self.compressor is not None:
            self._append_gcode(
                "M100P{p} ; mrbeam_compressor:{p}".format(p=self.compressor)
            )  # set air_pressure
            self._append_gcode("G4P0.2   ; mrbeam_compressor spin up time")
        self._append_gcode("F{}".format(self.feedrate_white))  # set an initial feedrate
        self.gc_ctx.f = self.feedrate_white  # TODO hack. set with line above
        # self._append_gcode('M3S0') # enable laser
        self.gc_ctx.s = 0  # TODO hack. set with line above
        self.gc_ctx.laser_active = True  # TODO hack. set with line above

        direction_positive = True
        # self.is_first_pixel = True

        # sort imgArray
        self.profiler.stop("gc_before_img").start("sort_imgArray")
        imgArray = self._sortImgArray(imgArray)

        self.profiler.stop("sort_imgArray").start("write_img")
        # iterate through the image parts
        for p in range(0, int(self.eng_passes)):
            self._append_gcode(
                "; pass:%i/%s ; Engraving\n" % (p + 1, int(self.eng_passes))
            )
            for img_data in imgArray:
                # img_data = {'i': px_data, 'x': offset_px_x, 'y':offset_px_y, 'id': id_str}
                # note: offset_px_x and offset_px_y are offsets from top left of the unseparated original pixel image
                img = img_data["i"]
                size = img.size  # size of the img fraction in pixels
                height_px = size[1]

                # image part has its own pixel offset. Calc general absolute offset in MM
                x_off = (
                    img_data["x"] * self.beam + xMM
                )  # mm here, img_data['x'] is in pixels
                y_off = (
                    hMM - img_data["y"] * self.beam + yMM
                )  # mm here, but inverted for the y axis
                # self.log.info("yPx: {}, yMM: {}, hMM: {} => y_final: {}".format(img_data['y'], yMM, hMM, y_off))
                img_pos_mm = (x_off, y_off)  # lower left corner of partial image in mm

                self._append_gcode(
                    "; Begin part {} @ pixel ({},{}) with dimensions {}x{}".format(
                        img_data["id"], img_data["x"], img_data["y"], size[0], size[1]
                    )
                )

                # TODO improvement: find first non-white pixel from lower left
                x_start = x_off
                y_start = (
                    y_off - height_px * self.beam
                )  # lower left of the image, but with safety whitespace around the content
                gc = self._get_gcode_g0(
                    x=x_start,
                    y=y_start,
                    comment="; Move to start ({},{})".format(x_start, y_start),
                )
                self._append_gcode(gc)
                self._append_gcode("M3S0\nG4P0")  # initialize laser
                # iterate line by line
                pix = img.load()
                first_row = True
                for row in range(height_px - 1, -1, -1):
                    line_info = self.get_pixelinfo_of_line(pix, size, row)
                    y = img_pos_mm[1] - (self.beam * line_info["row"])

                    if direction_positive:
                        _minmax = min
                        side = "left"
                        k = -1
                    else:
                        _minmax = max
                        side = "right"
                        k = 1
                    if (
                        line_info["left"] != None
                        and y >= 0
                        and y <= self.workingAreaHeight
                    ):

                        if not first_row and self.extra_overshoot:
                            overshoot_gco = (
                                "; EXTRA_TIME "
                                + str(EXTRA_OVERSHOOT_EXTRA_DURATION)
                                + "s\n"
                            )
                            # Use the most extreme position of x from one line to an other
                            # assumes that self.gc_ctx.x was previously set
                            extrema_next_line = (
                                img_pos_mm[0]
                                + self.beam * line_info[side]
                                + k
                                * (
                                    2 * self.overshoot_distance
                                    + self.backlash_compensation_x
                                )
                            )
                            extrema_x = _minmax(self.gc_ctx.x, extrema_next_line)
                            # start and end are the positions the laserhead should be
                            # before and after the overshoot.
                            # Assumes that self.gc_ctx.y was previously set
                            start = np.array([extrema_x, self.gc_ctx.y])
                            end = np.array([extrema_x, y])
                            # /!\ direction_positive reverted at the end of loop
                            overshoot_gco += self.get_overshoot(
                                start,
                                end,
                                k,
                                self.overshoot_distance,
                                offset_counter=row,
                            )
                            self._append_gcode(overshoot_gco)

                        # prepare line start
                        self.write_gcode_for_line_start(
                            y,
                            img_pos_mm,
                            pix,
                            line_info,
                            direction_positive,
                            debug=self.debug,
                        )

                        # do line
                        self.write_gcode_for_trimmed_line(
                            img_pos_mm,
                            pix,
                            line_info,
                            direction_positive,
                            debug=self.debug,
                        )

                        # after line
                        self.write_gcode_for_line_end(
                            img_pos_mm, line_info, direction_positive, debug=self.debug
                        )

                        # flip direction after each line to go back and forth
                        direction_positive = not direction_positive
                        first_row = False
                    elif line_info["left"] != None:
                        # skip line vertical out of working area
                        self._append_gcode(
                            "; ignoring line y={}, out of working area.".format(y)
                        )

            self._append_gcode("; EndPart")
            self._append_gcode("M3S0")
            self._append_gcode("")
            self.gc_ctx.s = 0
            self.gc_ctx.laser_active = True

        self._append_gcode(";EndImage\nM5")  # important for gcode preview!
        # self._append_gcode(";EndImage\nM5\nM100P0 ; mrbeam_compressor:0") # important for gcode preview!
        self.profiler.stop("write_img")
        self.gc_ctx.laser_active = False
        return self._output_gcode

    def get_profiler(self):
        return self.profiler

    # helper methods for gcode generation
    def _sortImgArray(self, imgArray):
        # pragmatic O(n^2) sorting
        out = []
        # We want the laserhead begins bottom left (ltr reading direction). So put this as starting point.
        lastPos = (
            0,
            self.workingAreaHeight / self.beam,
        )  # untransformed px coordinates here: 0,0 is top left.
        while len(imgArray) > 0:
            dist = float("inf")
            closest = None
            for img in imgArray:
                (w, h) = img["i"].size
                start = (img["x"], img["y"] + h)
                dst = self._dist(start, lastPos)
                if dst < dist:
                    closest = img
                    dist = dst

            out.append(closest)
            imgArray.remove(closest)
            lastPos = (closest["x"] + closest["i"].size[0], closest["y"])

        return out

    def _dist(self, p0, p1):
        return math.sqrt((p0[0] - p1[0]) ** 2 + (p0[1] - p1[1]) ** 2)

    def _ignore_pixel_brightness(self, brightness):
        if self.is_inverted:  # inverted engraving, e.g. anodized aluminum
            return brightness < self.ignore_darker_than
        else:
            return brightness > self.ignore_brighter_than

    def get_pixelinfo_of_line(self, pixelArray, size, row_idx):
        w_px = size[0]  # width
        h_px = size[1]  # height
        first_idx = self.get_first_juicy_pixel(pixelArray, w_px, row_idx)
        if first_idx != None:
            last_idx = self.get_last_juicy_pixel(pixelArray, w_px, row_idx)
        else:
            last_idx = None
        y_idx = row_idx

        return {
            "left": first_idx,
            "right": last_idx,
            "row": y_idx,
            "img_w": w_px,
            "img_h": h_px,
        }

    def get_first_juicy_pixel(self, pixelArray, w_px, row):
        for i in range(w_px):
            if pixelArray[i, row] <= self.ignore_brighter_than:
                return i
        return None

    def get_last_juicy_pixel(self, pixelArray, w_px, row):
        for i in range(w_px - 1, -1, -1):
            if pixelArray[i, row] <= self.ignore_brighter_than:
                return i
        return None

    #######################################################################
    #
    # gcode generation methods
    #
    # all methods starting with write_gcode_*
    # 1. write their gcode directly with the self._append_gcode method
    # 2. write a \n at the end
    # 3. have a debug flag which adds comments to the gcode (before the final \n).
    #
    #######################################################################

    def write_gcode_for_line_start(
        self, y, img_pos_mm, pixelArray, line_info, direction_positive, debug=False
    ):
        """Writes GCode to ensure the precondition of a line gcode. This
        includes:

        - Move laserhead to correct starting position with G0
        - Do the overshoot move if necessary
        - Activate laser with 0 intensity
        """

        # Calculate line start coordinates (including overshoot distance)
        if direction_positive:
            x = img_pos_mm[0] + self.beam * line_info["left"] - self.overshoot_distance
        else:
            x = (
                img_pos_mm[0]
                + self.beam * line_info["right"]
                + self.overshoot_distance
                + self.backlash_compensation_x
            )

        # Move to line start coordinates
        comment = None
        if debug:
            arrow = (
                "->"
                if (direction_positive)
                else "<- [backlash_compensation_x: {:.3f}]".format(
                    self.backlash_compensation_x
                )
            )
            comment = "goto line start" + arrow

        gc = self._get_gcode_g0(x=x, y=y, comment=comment)
        self._append_gcode(gc)
        self.gc_ctx.s = 0
        self.gc_ctx.x = x
        self.gc_ctx.y = y

        # Calculate the overshoot move
        if self.overshoot_distance > 0:
            if direction_positive:
                x = x + self.overshoot_distance
            else:
                x = x - self.overshoot_distance

            comment = None
            if debug:
                comment = "overshoot move"
            gc = self._get_gcode_g0(x=x, comment=comment)
            self._append_gcode(gc)
            self.gc_ctx.s = 0
            self.gc_ctx.x = x

    def write_gcode_for_line_end(
        self, img_pos_mm, line_info, direction_positive, debug=False
    ):
        """Writes GCode to ensure the postcondition of a line gcode. This
        includes:

        - set laser intensity to 0
        """
        comment = ""
        if debug:
            arrow = "->" if direction_positive else "<-"
            comment = "; EOL: x=[{} {} {}], y={}".format(
                line_info["left"], arrow, line_info["right"], line_info["row"]
            )

        x = self.gc_ctx.x
        if self.overshoot_distance > 0:
            if direction_positive:
                x = x + self.overshoot_distance
            else:
                x = x - self.overshoot_distance

            comment = None
            if debug:
                comment = "overshoot move"
            gc = self._get_gcode_g0(x=x, comment=comment)
            self._append_gcode(gc)
            self.gc_ctx.s = 0
            self.gc_ctx.x = x
        else:
            self._append_gcode("M3S0" + comment)
            self.gc_ctx.s = 0
            self.gc_ctx.x = x

    def write_gcode_for_trimmed_line(
        self, img_pos_mm, pixelArray, line_info, direction_positive, debug=False
    ):
        """
        Writes GCode for one line of juicy pixels.
        Preconditions:
        - Laserhead is already moved to correct starting position with G0
        - Laser is active (still active or switched on with M3S0)
        """

        # iterate over juicy pixels
        if direction_positive:
            pixelrange = list(range(line_info["left"], line_info["right"] + 1))
        else:
            pixelrange = list(range(line_info["right"], line_info["left"] - 1, -1))

        row = line_info["row"]

        lastBrightness = self.ignore_brighter_than + 1
        for i in pixelrange:

            brightness = pixelArray[i, row]
            if brightness != lastBrightness:
                if i != pixelrange[0]:  # don't move after new line
                    xpos = img_pos_mm[0] + self.beam * (
                        i - 1 if direction_positive else i
                    )  # calculate position; backward lines need to be shifted by +1 beam diameter
                    xpos = (
                        xpos
                        if direction_positive
                        else xpos + self.backlash_compensation_x
                    )
                    pos = self.write_gcode_for_equal_pixels(
                        lastBrightness, xpos, debug=debug
                    )
            else:
                pass  # combine equal intensity values to one move

            lastBrightness = brightness

        if (
            not self._ignore_pixel_brightness(brightness)
            and self.get_intensity(brightness) > 0
        ):  # finish non-white line
            end_of_line = img_pos_mm[0] + pixelrange[-1] * self.beam
            end_of_line = (
                end_of_line
                if (direction_positive)
                else end_of_line + self.backlash_compensation_x
            )
            pos = self.write_gcode_for_equal_pixels(
                brightness, end_of_line, debug=debug
            )

    def write_gcode_for_equal_pixels(
        self, brightness, target_x, comment=None, debug=False
    ):
        """
        Writes gcode for a sequence of equal pixels.
        Chooses G1 or G0 depending on brightness, adds pierce-time gcode after G0 command
        Preconditions:
        - laser in position
        - laser activated
        """
        if debug:
            comment = "brightness: {}".format(brightness)

        # fast skipping whitespace
        if self._ignore_pixel_brightness(brightness):
            gcode = self._get_gcode_g0(x=target_x, comment=comment)
            self._append_gcode(gcode)
            self.gc_ctx.s = 0
            self.gc_ctx.x = target_x

            # pierce time after skipping whitespace
            if self.pierce_time > 0:
                gcode = self._get_gcode_g4(
                    intensity=self.pierce_intensity, time=self.pierce_time
                )
                self._append_gcode(gcode)
                self.gc_ctx.s = JobParams.Default.PIERCE_INTENSITY

        else:
            intensity = self.get_intensity(brightness)
            feedrate = self.get_feedrate(brightness)

            # if self.is_first_pixel:
            # 	gcode = self._get_gcode_g0(x=target_x, comment="first_px")
            # 	self._append_gcode(gcode)

            gcode = self._get_gcode_g1(
                x=target_x, s=intensity, f=feedrate, comment=comment
            )
            self._append_gcode(gcode)
            self.gc_ctx.s = intensity
            self.gc_ctx.f = feedrate
            self.gc_ctx.x = target_x

        # self.is_first_pixel = False
        return target_x, None

    # @staticmethod
    def get_overshoot(self, start, end, direction, size, offset_counter=None):
        """
        Create the gcode for a diamond / octogon overshoot, the returned gcode does not contain the start and end positions.
        This overshoot only goes from start and then "up" on the the y axis.
        end : Actually only uses the y value of the end
        size : base size of the octogon (dictates length of sides) - It's approximative
        offset_counter : Sets a different offset as it increments which spreads any remaining burn marks

        """
        # only need self for the g0 code
        # direction should be +- 1 and dictates whether to turn clockwise or anticlockwise

        # This is messy and to be overwritten with streamlined logic
        dy = float(end[1] - start[1])
        # changed measurement so the final size of the overshoot matches expected size.
        _size = float(max(EXTRA_OVERSHOOT_MIN_DIST, size)) / 4
        # extra vertical_spacing in the overshoot
        # necessary if dy < _size, it could otherwise still burn the material
        # This allows all edges to be at least _size long
        extra_vert = max(0, _size - dy)
        k = direction
        _line1 = np.array([k, 0.0])
        _line2 = np.array([0.0, 1.0])
        _line3 = np.array([k, 1.0])
        _line4 = np.array([k, -1.0])
        if isinstance(offset_counter, int):
            # Extend the start and end point differently depending on
            # the line so there is no overlap between the overshoots
            shift = _size * (offset_counter % max(dy, 1)) / 2 * _line1
            start = start + shift
            end = end + shift
        return "".join(
            map(
                lambda v: self._get_gcode_g0(x=v[0], y=v[1], comment="octogon") + "\n",
                np.cumsum(
                    [
                        start + (extra_vert / 2 + _size) * _line4,
                        _size * _line1,
                        (_size + dy / 4) * _line3,
                        (extra_vert + dy / 2) * _line2,
                        -(_size + dy / 4) * _line4,
                        -_size * _line1,
                    ],
                    axis=0,
                ),
            )
        )

    def _get_gcode_g0(self, x=None, y=None, comment=None):
        x, x_cmt = self._ensure_value_in_range(x, self.workingAreaWidth, 0, "X")
        y, y_cmt = self._ensure_value_in_range(y, self.workingAreaHeight, 0, "Y")
        x_gc = self._get_gcode_literal("X", x)
        y_gc = self._get_gcode_literal("Y", y)
        all_comments = self._join_gc_comments(comment, x_cmt, y_cmt)
        return "G0{}{}S0{}".format(x_gc, y_gc, all_comments)

    def _get_gcode_g1(self, x=None, y=None, s=None, f=None, comment=None):
        if x == None and y == None and s == None and f == None:
            raise ValueError("GCode 'G1' at least requires one literal.")
        x, x_cmt = self._ensure_value_in_range(x, self.workingAreaWidth, 0, "X")
        y, y_cmt = self._ensure_value_in_range(y, self.workingAreaHeight, 0, "Y")
        s, s_cmt = self._ensure_value_in_range(
            s, self.INTENSITY_MAX, self.INTENSITY_MIN, "S"
        )
        f, f_cmt = self._ensure_value_in_range(
            f, self.FEEDRATE_MAX, self.FEEDRATE_MIN, "F"
        )
        x_gc = self._get_gcode_literal("X", x)
        y_gc = self._get_gcode_literal("Y", y)
        s_gc = self._get_gcode_literal("S", s)
        f_gc = self._get_gcode_literal("F", f)

        all_comments = self._join_gc_comments(comment, x_cmt, y_cmt, s_cmt, f_cmt)
        return "G1{}{}{}{}{}".format(x_gc, y_gc, s_gc, f_gc, all_comments)

    def _ensure_value_in_range(self, value, maximum, minimum=0, prefix=""):
        """Returns a tuple :

        - number closest to value in range of minimum and maximum
        - comment if the input and output value don't match ; also logs it
        """
        if value == None:
            return None, ""
        elif isinstance(value, float) and math.isnan(value):
            # math.isnan() fails on non-float types
            raise ValueError("Coordinate is NaN")

        val = max(min(value, maximum), minimum)
        if val != value:
            message = "{} set to {}, was {}".format(prefix, val, value)
            self.log.debug(message)
            return (val, message)
        else:
            return value, ""

    def _join_gc_comments(self, *args):
        l = [_f for _f in args if _f]
        if len(l) > 0:
            return "; " + ", ".join(l)
        else:
            return ""

    def _get_gcode_g4(self, intensity=None, time=0):
        if time > 0:
            if intensity == None:
                intensity = self.pierce_intensity

            return "M3S{}\nG4P{}\n".format(str(intensity), str(time))  # Dwell for P ms
        else:
            return ""

    def _get_gcode_literal(self, lit, value):
        # TODO uncomment after fixing
        #        if isinstance(value, float) and math.isnan(value):
        #            raise ValueError("NaN Value in GCode Literal {}".format(lit))
        if value != None:
            if lit == "X" or lit == "Y":
                return lit + self.twodigits(value)
            if lit == "S" or lit == "F":
                return lit + str(value)
        else:
            return ""

    def dataUrl_to_gcode(self, dataUrl, w, h, x, y, file_id):
        gcode = ""
        img = self._dataurl_to_img(dataUrl)

        if img:
            imgArray = self.img_prepare(img, w, h)
            if self.MULTILINE_DATA_URLS:
                file_id = re.sub(
                    "(.{160})", "\\1\n", dataUrl, 0, re.DOTALL
                )  # newline after 160 chars for easy .gco handling in external viewers
            else:
                file_id = dataUrl
            gcode = self.generate_gcode(imgArray, x, y, w, h, file_id)
        return gcode

    def _dataurl_to_img(self, dataUrl):
        if dataUrl is None:
            self.log.info("ERROR: image is not base64 encoded")
            return None

        try:
            # get raw base64 data
            # remove "data:image/png;base64," and add a "\n" in front to get proper base64 encoding
            if dataUrl.startswith("data:"):
                commaidx = dataUrl.find(",")
                base64str = "\n" + dataUrl[commaidx:]

            image_string = io.BytesIO(base64.b64decode(base64str))
            return Image.open(image_string)
        except:
            self.log.exception(
                "Exception in _dataurl_to_img() dataUrl length: %s, dataUrl (shortened): %s",
                len(dataUrl),
                dataUrl[:100],
                analytics="_dataurl_to_img",
            )
            return None

    def imgurl_to_gcode(self, url, w, h, x, y, file_id):
        import urllib.request, urllib.parse, urllib.error, io

        file = io.StringIO(urllib.request.urlopen(url).read())
        img = Image.open(file)
        imgArray = self.img_prepare(img, w, h)
        gcode = self.generate_gcode(imgArray, x, y, w, h, file_id)
        return gcode

    # x,y are the lowerLeft of the image
    def img_to_gcode(self, path, w, h, x, y, file_id):
        img = Image.open(path)
        imgArray = self.img_prepare(img, w, h)
        gcode = self.generate_gcode(imgArray, x, y, w, h, file_id)
        return gcode

    def twodigits(self, fl):
        return "{0:.2f}".format(fl)

    def get_intensity(self, brightness):
        if not brightness in self._lookup_intensity:
            intensity = (1.0 - brightness / 255.0) * (
                self.intensity_black - self.intensity_white
            ) + self.intensity_white
            self._lookup_intensity[brightness] = int(intensity)
        return self._lookup_intensity[brightness]

    def get_feedrate(self, brightness):
        if not brightness in self._lookup_feedrate:
            feedrate = (
                brightness / 255.0 * (self.feedrate_white - self.feedrate_black)
                + self.feedrate_black
            )
            self._lookup_feedrate[brightness] = int(feedrate)
        return self._lookup_feedrate[brightness]

    def get_alpha_composition(self, pixel):
        brightness = pixel[0]  # 0..255
        opacity = pixel[1]  # 0..255
        composite = brightness * (opacity / 255.0) + 255 * (
            1 - opacity / 255.0
        )  # Cout = ColorA*AlphaA + White*(1-AlphaA)
        return composite

    def get_pierce_time_multiplier(self, col, row, pix, w, h, direction_positive):
        col_min = max(0, col - 1)
        col_max = min(col + 1, w - 1) + 1
        row_min = max(0, row - 1)
        row_max = min(row + 1, h - 1) + 1

        sum = 0
        pixels = 0
        for r in range(row_min, row_max):
            for c in range(col_min, col_max):
                if c != col or r != row:
                    pixels += 1
                    sum += pix[c, r]
        val = sum / 255.0 / pixels
        if val > 0.5:  # more than 50% of pixels around are white
            return val
        else:
            return 0

    def _append_gcode(self, gcode, add_new_line=True):
        if self.output_filehandle is not None:
            self.output_filehandle.write(gcode)
            if add_new_line:
                self.output_filehandle.write("\n")
        else:
            self._output_gcode += gcode
            if add_new_line:
                self._output_gcode += "\n"


class GC_Context:
    """Helper class to track last gcode values."""

    def __init__(self):
        self.x = None
        self.y = None
        self.f = None
        self.s = None
        self.laser_active = False


# debug string
# base64img = "data:image/png;base64,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ZaxZsyagn/noo49w2WWXhbllFEs4jZda7d271+/zkiThwgsvxD//+U9UVVXhnnvuYfCIUYmJibjuuuuwevVqLF++HFdeeWW72+a31z+o42EGQq3uvvtuvPzyy17fy8rKwvjx4zFp0iRMmDCB96GOY42Njfj888+xYMECLFy40KfGNmbMmJgpxlNkMIAQAGDr1q0YNGgQTp8+jV69emHSpEmYNGkSRo0aBZvNZnXzKMJkWcZ3332HBQsWYMGCBfj+++8hyzL+8Y9/8N411IoBhCDLMh588EHk5+dj0qRJqKystLpJFGUOHjyIhQsXYtWqVXj55Zd5u10CwABCREQGsYhORESGMIAQEZEhDCBERGQIAwgRERnCAEJERIYwgBARkSEMIEREZAgDCBERGcIAQkREhjCAEBGRIQwgRERkCAMIEREZwgBCRESGMIAQEZEhDCBERGQIAwgRERnCAEJERIYwgBARkSEMIEREZAgDCBERGcIAQkREhjCAEBGRIQwgRERkCAMIEREZwgBCRESGMIAQEZEhDCBERGQIAwgRERnCAEJERIYwgBARkSEMIEREZAgDCBERGcIAQkREhjCAEBGRIQwgRERkCAMIEREZwgBCRESGMIAQEZEhDCBERGQIAwgRERnCAEJERIYwgBARkSEMIEREZAgDCBERGcIAQkREhjCAEBGRIQwgRERkCAMIEREZwgBCRESGMIAQEZEhDCBERGQIAwgRERnCAEJERIYwgBARkSEMIEREZAgDCBERGcIAQkREhjCAEBGRIQwgRERkCAMIEREZwgBCRESGMIAQEZEhDCBERGQIAwgRERnCAEJERIYwgBARkSEMIEREZAgDCBERGcIAQkREhjCAEBGRIQwgRERkCAMIEREZwgBCRESGMIAQEZEhDCBERGQIAwgRERnCAEJERIYwgBARkSEMIEREZAgDCBERGcIAQkREhjCAEBGRIQwgRERkCAMIEREZwgBCRESGMIAQEZEhDCBERGQIAwgRERnCAEJERIYwgBARkSEMIEREZMj/B/S4NfenjNciAAAAAElFTkSuQmCC="


if __name__ == "__main__":
    opts = optparse.OptionParser(usage="usage: %prog [options] <imagefile>")
    opts.add_option(
        "-x",
        "--x-position",
        type="float",
        default="0",
        help="x position of the image (corner top left) on the working area",
        dest="x",
    )
    opts.add_option(
        "-y",
        "--y-position",
        type="float",
        default="0",
        help="y position of the image (corner top left) on the working area",
        dest="y",
    )
    opts.add_option(
        "-w",
        "--width",
        type="float",
        default=-1,
        help="width of the image in mm. If omitted one pixel equals the beam diameter.",
        dest="width",
    )
    opts.add_option(
        "",
        "--height",
        type="float",
        default=-1,
        help="height of the image in mm. If omitted aspect ratio will be preserved.",
        dest="height",
    )
    opts.add_option(
        "",
        "--workingAreaWidth",
        type="float",
        default=500,
        help="max width in mm. (Default 500)",
        dest="waWidth",
    )
    opts.add_option(
        "",
        "--workingAreaHeight",
        type="float",
        default=390,
        help="max height in mm. (Default 390)",
        dest="waHeight",
    )
    opts.add_option(
        "",
        "--beam-diameter",
        type="float",
        help="laser beam diameter, default 0.25mm",
        default=0.25,
        dest="beam_diameter",
    )
    opts.add_option(
        "",
        "--backlash_x",
        type="float",
        help="precision compensation x axis, default 0.00mm",
        default=0.00,
        dest="backlash_x",
    )
    opts.add_option(
        "-s",
        "--speed",
        type="float",
        help="engraving speed, default 1000mm/min",
        default=1000,
        dest="feedrate",
    )
    opts.add_option(
        "",
        "--img-intensity-white",
        type="int",
        default="0",
        help="intensity for white pixels, default 0",
        dest="intensity_white",
    )
    opts.add_option(
        "",
        "--img-intensity-black",
        type="int",
        default="1000",
        help="intensity for black pixels, default 1000",
        dest="intensity_black",
    )
    opts.add_option(
        "",
        "--img-speed-white",
        type="int",
        default="500",
        help="speed for white pixels, default 500",
        dest="speed_white",
    )
    opts.add_option(
        "",
        "--img-speed-black",
        type="int",
        default="30",
        help="speed for black pixels, default 30",
        dest="speed_black",
    )
    opts.add_option(
        "-t",
        "--pierce-time",
        type="float",
        default="0",
        help="time to rest after laser is switched on in milliseconds",
        dest="pierce_time",
    )
    opts.add_option(
        "-c",
        "--contrast",
        type="float",
        help="contrast adjustment: 0.0 => gray, 1.0 => unchanged, >1.0 => intensified",
        default=1.0,
        dest="contrast",
    )
    opts.add_option(
        "",
        "--sharpening",
        type="float",
        help="image sharpening: 0.0 => blurred, 1.0 => unchanged, >1.0 => sharpened",
        default=1.0,
        dest="sharpening",
    )
    opts.add_option(
        "",
        "--dithering",
        type="string",
        help="convert image to black and white pixels",
        default="false",
        dest="dithering",
    )
    opts.add_option(
        "",
        "--mode",
        type="string",
        help="engraving mode: {}, {}, {}".format(
            ImageProcessor.ENGRAVING_MODE_FAST,
            ImageProcessor.ENGRAVING_MODE_BASIC,
            ImageProcessor.ENGRAVING_MODE_DEFAULT,
        ),
        default=ImageProcessor.ENGRAVING_MODE_DEFAULT,
        dest="engraving_mode",
    )
    opts.add_option(
        "",
        "--no-headers",
        action="store_true",
        default=False,
        help="omits Mr Beam start and end sequences",
        dest="noheaders",
    )

    (options, args) = opts.parse_args()
    path = args[0]
    if len(args) == 2:
        gcodefile = args[1]
    else:
        filename, _ = os.path.splitext(path)
        gcodefile = filename + ".gco"

    image = Image.open(path)
    buffer = io.StringIO()
    image.save(buffer, format="PNG")
    img_str = base64.b64encode(buffer.getvalue())
    datauri = "data:image/png;base64," + img_str
    orig_w, orig_h = image.size
    if options.width < 0:
        options.width = orig_w * options.beam_diameter

    if options.height < 0:
        ratio = orig_w / float(orig_h)
        options.height = options.width / ratio

    with open(gcodefile, "w") as fh:
        header = ""
        footer = ""
        if not options.noheaders:
            # TODO get headers from machine_settings.py
            header = """
$H
G92X507Y390Z0
G90
M8
G21

"""
            footer = """
M5
G0X0Y0
M9
M2
"""

        fh.write(header)

        boolDither = options.dithering == "true"
        ip = ImageProcessor(
            output_filehandle=fh,
            workingAreaWidth=options.waWidth,
            workingAreaHeight=options.waHeight,
            contrast=options.contrast,
            sharpening=options.sharpening,
            beam_diameter=options.beam_diameter,  # use 1.0 for easy debugging.
            backlash_x=options.backlash_x,
            # beam_diameter = options.beam_diameter,
            intensity_black=options.intensity_black,
            intensity_white=options.intensity_white,
            intensity_black_user=options.speed_black,
            intensity_white_user=options.speed_white,
            speed_black=options.speed_black,
            speed_white=options.speed_white,
            dithering=boolDither,
            engraving_mode=options.engraving_mode,
            pierce_time=options.pierce_time,
            material=None,
        )

        lh = logging.StreamHandler(sys.stdout)
        lh.setLevel(logging.DEBUG)
        ip.log.addHandler(lh)
        ip.profiler.log.addHandler(lh)

        path = args[0]
        print(options)
        ip.img_to_gcode(
            path, options.width, options.height, options.x, options.y, datauri
        )
        # ip.dataUrl_to_gcode(base64img, options.width, options.height, options.x, options.y)

        fh.write(footer)

    print("gcode written to " + gcodefile)
