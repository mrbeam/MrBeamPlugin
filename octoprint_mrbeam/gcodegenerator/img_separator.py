# coding=utf-8
#!/usr/bin/env python

"""
img_separator.py
bitmap separation for speed optimized raster processing

Copyright (C) 2018 Mr Beam Lasers GmbH
Author: Teja Philipp, teja@mr-beam.org

"""
import optparse
import logging
from PIL import Image
import cv2
import numpy as np
import os.path
import glob

from octoprint_mrbeam.mrb_logger import mrb_logger
from octoprint_mrbeam.util.img import differed_imwrite

(cvMajor, cvMinor) = cv2.__version__.split(".")[:2]
isCV2 = cvMajor == "2"
isCV31 = cvMajor == "3" and cvMinor == "1"
isCV34 = cvMajor == "3" and cvMinor == "4"


class ImageSeparator:

    MAX_OUTER_CONTOURS = 30

    def __init__(self):
        self.log = mrb_logger("octoprint.plugins.mrbeam.img_separator")
        self.img_debug_folder = "/tmp/separate_contours"

        files = glob.glob(self.img_debug_folder + "/*")
        for f in files:
            os.remove(f)

        self.debug = True
        try:
            self.debug = _mrbeam_plugin_implementation._settings.get(
                ["dev", "debug_gcode"]
            )
        except (NameError, AttributeError):
            self.debug = True
            self.log.info(
                "Gcode debugging enabled (not running in Mr Beam Plugin environment"
            )
        else:
            self.log.info("Gcode debugging {} (read from config)".format(self.debug))
            pass

        if self.debug:
            self.log.setLevel(logging.DEBUG)

    # 1. separation method called "left pixels first"
    def separate(self, img_data, threshold=255, callback=None):
        """
        Separates img (a Pillow Image object) according to some magic into a list of img objects.
        Afterwards all parts merged togehter are equal to the input image.
        Supports so far only Grayscale images (mode 'L')
        Arguments:
        img -- a Pillow Image object

        Keyword arguments:
        threshold -- all pixels brighter than this threshold are used for separation
        callback -- instead of waiting for the list to return, a callback(img, iteration) can be used to save memory
        """

        img = img_data["i"]
        (width, height) = img.size

        x_limit = [0] * height  # [0, 0, 0, .... ]
        iteration = 0
        pixel_count = 0
        parts = []
        while True:
            (x_limit, separation) = self._separate_partial(
                img, start_list=x_limit, threshold=threshold
            )
            if separation == None:
                return parts

            pixel_count += separation.size[0] * separation.size[0]
            if pixel_count > 60000000000:
                # 60000000000 is a pretty random value. i found that it tends to crash (due to memory) if higher.
                # But it depends on the image. Some images can got till 1.3 times that value without problems....
                self.log.warn(
                    "Skipping separate() too many pixel in mem. iterations: %s, total pixel_count: %s",
                    iteration,
                    pixel_count,
                    analytics=True,
                )
                return None

            id_str = ":".join([img_data["id"], str(iteration)])
            result = {"i": separation, "x": 0, "y": 0, "id": id_str}
            if callback != None:
                callback(result, iteration)
            else:
                parts.append(result)

            all_done = all(l >= width for l in x_limit)
            if all_done:
                return parts
            iteration += 1

    def _separate_partial(self, img, start_list, threshold=255):

        (width, height) = img.size
        pxArray = img.load()

        # iterate line by line
        tmp = None
        for row in range(0, height):
            x = self._find_first_gap_in_row(
                pxArray, width, height, start_list[row], row, threshold=threshold
            )
            if x <= width:
                if tmp == None:  # new separated image
                    tmp = Image.new("L", (width, height), "white")
                box = (start_list[row], row, x, row + 1)
                region = img.crop(box)
                tmp.paste(region, box)

            start_list[row] = x
        return (start_list, tmp)

    def _find_first_gap_in_row(self, pxArray, w, h, x, y, threshold=255):
        skip = True  # assume white pixel at the beginning

        for i in range(x, w):
            px = pxArray[i, y]

            brightness = px
            if brightness < threshold:  # "rising edge" -> colored pixel
                skip = False

            if skip == False:
                if brightness >= threshold:  # "falling edge" -> white pixel again
                    return i

        return w

    # 2. contour based separation method
    def separate_contours(self, img, x=0, y=0, threshold=255, callback=None):
        """
        Arguments:
        img -- a Pillow Image object
        """
        w, h = img.size
        monochrome_original = np.array(
            img, dtype=np.uint8
        )  # should be grayscale already
        id_str = "c0"
        data = {"i": monochrome_original, "x": int(x), "y": int(y), "id": id_str}
        self._dbg_image(monochrome_original, data["id"] + "_0_monochrome.png")

        to_process = [data]
        parts = []
        level = 0
        # now split global_mask recursive
        while len(to_process) > 0:
            next_item = to_process.pop(0)
            off_x = next_item["x"]
            off_y = next_item["y"]
            tmp = self._split_by_outer_contour(next_item, level, monochrome_original)
            if len(tmp) == 1:
                parts.append(tmp[0])
            else:
                for i in tmp:
                    i["x"] += off_x
                    i["y"] += off_y
                    part_h, part_w = i["i"].shape
                    if (
                        part_w > 100 or part_h > 100
                    ):  # 1cm ... 5cm depending on the resolution (TODO -> dynamic)
                        to_process.append(i)
                    else:
                        parts.append(i)
            level += 1

        # create PIL image type from cv2 type
        pil_images = []
        number = 0
        for i in parts:
            separation = Image.fromarray(np.uint8(i["i"]))
            i["i"] = separation
            # TODO move callback and transformation into own function and place it directly in the recursion
            # collect results
            if callback != None:
                callback(i, number)
                pil_images.append(i)
            else:
                pil_images.append(i)
            number += 1

        if self.debug:
            self._dbg_is_separation_ok(
                parts,
                monochrome_original,
                "9_diff_contours.png",
                "Contour separation buggy. See ",
            )

        return pil_images

    def _split_by_outer_contour(self, mask_data, level, monochrome_original):
        """
        :param mask_data: {'i': cv_np_array, 'x': x_offset, 'y': y_offset, 'id':id_str}
        :param level: depth of the recursion
        :param monochrome_original:
        """
        # This should be improved.
        # If there are too many too little contours found and engraved separately, the way in between these contours
        # becomes more overhead than we save compared to the naive line-by-line algorithm.
        # What we do so far is that we fall back to the naive algorithm if there are more than x contours found.
        # Possible improvements:
        # - small objects in close proximity should be combined.
        # - We could get bbox of any contour and check, if others are contained. But with a big banana shaped object, this might just cover everything else.
        # - Teja: sort contours by starting pos closest end pos

        img = mask_data["i"]
        h, w = img.shape
        original_offset_x = mask_data["x"]
        original_offset_y = mask_data["y"]
        self.log.debug("Input {}: w*h: {}*{})".format(level, w, h))
        self._dbg_image(img, mask_data["id"] + "_0_input_.png")

        input_mask = self._prepare_img_for_contour_separation(img)
        self._dbg_image(input_mask, mask_data["id"] + "_1_input_mask.png")
        _, contours, hierarchy = self._get_contours(input_mask)

        parts = []  # array of mask_data dicts

        amount = len(contours)
        self.log.info("Found {} contours.".format(amount))
        if self.debug:
            for i in range(amount):
                nextContourIdx, prevContourIdx, firstChildIdx, parentIdx = hierarchy[0][
                    i
                ]
                cnt_x, cnt_y, cnt_w, cnt_h = cv2.boundingRect(contours[i])
                self.log.debug(
                    "Contour {}#{}: w*h: {}*{} @ x,y: {},{} (parent: {}, child: {})".format(
                        mask_data["id"],
                        i,
                        cnt_w,
                        cnt_h,
                        cnt_x,
                        cnt_y,
                        parentIdx,
                        firstChildIdx,
                    )
                )

        if amount == 1:
            self.log.info("No contour separation possible. Returning full image.")
            return [mask_data]

        if amount > self.MAX_OUTER_CONTOURS:
            self.log.info(
                "Found %s contours which seems too many (max: %s). Returning full image.",
                amount,
                self.MAX_OUTER_CONTOURS,
            )
            return [mask_data]

        import gc

        nonWhiteParts = 0
        for i in range(amount):
            id_str = mask_data["id"] + "." + str(i)  # use input mask id as prefix
            nextContourIdx, prevContourIdx, firstChildIdx, parentIdx = hierarchy[0][i]

            # create partial mask
            mask = cv2.bitwise_not(np.zeros((h, w), np.uint8))
            cv2.drawContours(mask, contours, i, (0), -1)
            self._dbg_image(mask, id_str + "_2_contourmask.png")

            # crop input picture to mask size
            mask_h, mask_w = mask.shape
            cropped_original = monochrome_original[0:mask_h, 0:mask_w]

            # apply mask to original image
            separation_cv = cv2.bitwise_or(cropped_original, mask)

            # and crop again to bbox of contour
            cnt_x, cnt_y, cnt_w, cnt_h = cv2.boundingRect(contours[i])
            cropped = separation_cv[cnt_y : cnt_y + cnt_h, cnt_x : cnt_x + cnt_w]

            if self._is_only_whitespace(cropped):
                self.log.debug(
                    "Contour {}#{} (w*h: {}*{} @ {},{}) is only white space. Skipping...".format(
                        mask_data["id"], i, cnt_w, cnt_h, cnt_x, cnt_y
                    )
                )

            else:
                data = {"i": cropped, "x": cnt_x, "y": cnt_y, "id": id_str}
                parts.append(data)
                nonWhiteParts += 1
                self._dbg_image(cropped, id_str + "_3_sliced_.png")

            # a try to prevent the system from overflowing memory wise
            del mask
            del cropped
            del cropped_original
            del separation_cv
            gc.collect()

        self.log.info("Contour separation emitted {} parts.".format(nonWhiteParts))
        return parts

    def _prepare_img_for_contour_separation(self, monochrome, threshold=255):
        maxValue = 255
        th, filtered = cv2.threshold(
            monochrome, threshold - 1, maxValue, cv2.THRESH_BINARY
        )

        # if(pixel_at_0,0 is white):
        filtered = cv2.bitwise_not(
            filtered
        )  # invert. find_contours looks for bright objects on dark background.
        return filtered

    def _get_contours(self, img, method=cv2.RETR_EXTERNAL):
        self.log.info("OpenCV Version:" + cv2.__version__)
        # RETR_EXTERNAL, RETR_LIST, RETR_TREE, RETR_CCOMP
        # see https://docs.opencv.org/ref/master/d9/d8b/tutorial_py_contours_hierarchy.html
        # TODO: switch to RETR_LIST and handle hierarchy recursively
        if isCV2:
            self.log.info(
                "OpenCV "
                + cv2.__version__
                + " : filtering top level contours with img size cropped by one px on each side"
            )
            contours, hierarchy = cv2.findContours(
                img.copy(), method, cv2.CHAIN_APPROX_SIMPLE
            )

        else:
            self.log.info(
                "OpenCV "
                + cv2.__version__
                + " : filtering top level contours with img size cropped by one px on each side"
            )
            _, contours, hierarchy = cv2.findContours(
                img, method, cv2.CHAIN_APPROX_SIMPLE
            )
        return (img, contours, hierarchy)

    def _is_only_whitespace(self, img):
        # check if 'white space':
        inverted = cv2.bitwise_not(img)
        return cv2.countNonZero(inverted) == 0

    def _dbg_image(self, img, filename):
        try:
            if not os.path.exists(self.img_debug_folder):
                os.makedirs(self.img_debug_folder)
        except OSError:
            self.log.error("Error: Creating directory. " + self.img_debug_folder)
        if self.debug:
            path = self.img_debug_folder + "/" + filename
            if type(img) is np.ndarray:
                differed_imwrite(path, img)
            elif type(img) is Image.Image:
                img.save(path)
            return path

    def _dbg_is_separation_ok(self, parts, original, path_if_error, msg_if_error):
        if type(original) is np.ndarray:
            original = Image.fromarray(np.uint8(original))
        w, h = original.size
        debug_assembly = Image.new("L", (w, h), "white")

        for i in parts:
            self._dbg_image(i["i"], i["id"] + "_8_output.png")
            debug_assembly.paste(i["i"], (i["x"], i["y"]))
        self._dbg_image(debug_assembly, "9_control.png")
        from PIL import ImageChops

        control = ImageChops.difference(original, debug_assembly)
        color_extrema = control.getextrema()
        if color_extrema != (0, 0):
            path = self._dbg_image(control, path_if_error)
            self.log.error(msg_if_error + path)
            return False
        else:
            return True


if __name__ == "__main__":
    import sys

    opts = optparse.OptionParser(usage="usage: %prog [options] <imagefile>")
    opts.add_option(
        "-t",
        "--threshold",
        type="int",
        default="255",
        help="intensity for white (skipped) pixels, default 255",
        dest="threshold",
    )

    (options, args) = opts.parse_args()
    path = args[0]
    filename, _ = os.path.splitext(path)
    output_name = filename + "_"

    sepp = ImageSeparator()
    sepp.log.setLevel(logging.DEBUG)
    lh = logging.StreamHandler(sys.stdout)
    sepp.log.addHandler(lh)

    img = Image.open(path)
    # remove transparency
    if img.mode == "RGBA":
        whitebg = Image.new("RGBA", img.size, "white")
        img = Image.alpha_composite(whitebg, img)
        print("removed alpha channel.")
        if True:
            img.save("/tmp/img2gcode_2_whitebg.png")
    img = img.convert("L")

    def write_to_file_callback(part, iteration):
        print(part)
        if part != None:
            part["i"].save(output_name + "{:0>3}".format(iteration) + ".png", "PNG")

    # sepp.separate(img, callback=write_to_file_callback)
    sepp.separate_contours(img, callback=write_to_file_callback)
