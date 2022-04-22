import logging
import re
import shutil
import os
import time
import machine_settings

from biarc import biarc
from point import Point
import numpy

import simplestyle
import simpletransform
import cubicsuperpath

from profiler import Profiler
from job_params import JobParams
from img2gcode import ImageProcessor
from svg_util import get_path_d, _add_ns, unittouu

from octoprint_mrbeam.mrb_logger import mrb_logger

from lxml import etree


class Converter:

    PLACEHOLDER_LASER_ON = ";_laseron_"
    PLACEHOLDER_LASER_OFF = ";_laseroff_"

    defaults = {
        "directory": None,
        "file": None,
        "svgDPI": 90,
        "noheaders": "false",
        "engrave": False,
        "raster": {
            "intensity_white": JobParams.Default.INTENSITY_WHITE,
            "intensity_black": JobParams.Default.INTENSITY_BLACK,
            "speed_white": JobParams.Default.FEEDRATE_WHITE,
            "speed_black": JobParams.Default.FEEDRATE_BLACK,
            "contrast": JobParams.Default.CONTRAST,
            "sharpening": JobParams.Default.SHARPENING,
            "dithering": JobParams.Default.DITHERING,
            "beam_diameter": JobParams.Default.BEAM_DIAMETER,
            "pierce_time": JobParams.Default.PIERCE_TIME,
            "eng_compressor": JobParams.Default.ENG_COMPRESSOR,
        },
        "vector": [],
        "material": None,
        "design_files": [],
        "advanced_settings": False,
    }

    _tempfile = "/tmp/_converter_output.tmp"

    def __init__(
        self,
        params,
        model_path,
        workingAreaWidth=None,
        workingAreaHeight=None,
        min_required_disk_space=0,
    ):
        self._log = mrb_logger("octoprint.plugins.mrbeam.converter")
        self.workingAreaWidth = workingAreaWidth
        self.workingAreaHeight = workingAreaHeight
        self.optimize_path_order = True
        self.optimize_max_paths = 500

        # debugging
        self.transform_matrix = {}
        self.transform_matrix_reverse = {}
        self.orientation_points = {}

        self.colorParams = {}
        self.colorOrder = []
        self.gc_options = None
        self.options = self.defaults
        self.setoptions(params)
        self.svg_file = model_path
        self.document = None
        self._min_required_disk_space = min_required_disk_space
        self._log.info("Converter Initialized: %s", self.options)
        # todo need material,bounding_box_area here
        self._add_conversion_details_analytics()

    def setoptions(self, opts):
        # set default values if option is missing
        # self._log.info("opts: %s" % opts)
        for key in self.options.keys():
            if key in opts:
                self.options[key] = opts[key]
                if key == "vector":
                    for paramSet in opts["vector"]:
                        self.colorOrder.append(paramSet["color"])
                        self.colorParams[paramSet["color"]] = paramSet
            else:
                self._log.info("Using default %s = %s" % (key, str(self.options[key])))

    @staticmethod
    def _calculate_mpr_value(intensity, speed, passes=JobParams.Default.PASSES):
        if intensity and speed and passes:
            mpr = round(float(intensity) / float(speed) * int(passes), 2)
        else:
            mpr = None

        return mpr

    def _add_conversion_details_analytics(self):
        if "material" in self.options:
            _mrbeam_plugin_implementation.analytics_handler.add_material_details(
                self.options["material"]
            )

        if (
            "engrave" in self.options
            and self.options["engrave"]
            and "raster" in self.options
        ):
            eng_settings = self.options["raster"]
            additional_data = {
                "svgDPI": self.options["svgDPI"],
                "mpr_black": self._calculate_mpr_value(
                    eng_settings.get("intensity_black"), eng_settings.get("speed_black")
                ),
                "mpr_white": self._calculate_mpr_value(
                    eng_settings.get("intensity_white"), eng_settings.get("speed_white")
                ),
            }
            eng_settings.update(additional_data)
            _mrbeam_plugin_implementation.analytics_handler.add_engraving_parameters(
                eng_settings
            )

        if "vector" in self.options and self.options["vector"]:
            for cut_settings in self.options["vector"]:
                additional_data = {
                    "svgDPI": self.options["svgDPI"],
                    "mpr": self._calculate_mpr_value(
                        cut_settings.get("intensity"),
                        cut_settings.get("feedrate"),
                        cut_settings.get("passes"),
                    ),
                }
                cut_settings.update(additional_data)
                _mrbeam_plugin_implementation.analytics_handler.add_cutting_parameters(
                    cut_settings
                )

        if "design_files" in self.options and self.options["design_files"]:
            for design_file in self.options["design_files"]:
                _mrbeam_plugin_implementation.analytics_handler.add_design_file_details(
                    design_file
                )

    def init_output_file(self):
        # remove old file if exists.
        try:
            os.remove(self._tempfile)
        except OSError:
            pass
        # create new file and return file handle.

    def check_free_space(self):
        disk = os.statvfs("/")
        # calculation of disk usage
        totalBytes = disk.f_bsize * disk.f_blocks  # disk size in bytes
        totalUsedSpace = disk.f_bsize * (disk.f_blocks - disk.f_bfree)  # used bytes
        totalAvailSpace = float(disk.f_bsize * disk.f_bfree)  #
        totalAvailSpaceNonRoot = float(disk.f_bsize * disk.f_bavail)
        self._log.info(
            "Disk space: total: "
            + self._get_human_readable_bytes(totalBytes)
            + ", used: "
            + self._get_human_readable_bytes(totalUsedSpace)
            + ", available: "
            + self._get_human_readable_bytes(totalAvailSpace)
            + ", available for non-super user: "
            + self._get_human_readable_bytes(totalAvailSpaceNonRoot)
            + ", min required: "
            + self._get_human_readable_bytes(self._min_required_disk_space)
        )
        if (
            self._min_required_disk_space > 0
            and totalAvailSpaceNonRoot < self._min_required_disk_space
        ):
            msg = (
                "Only "
                + self._get_human_readable_bytes(totalAvailSpaceNonRoot)
                + " disk space available. Min required: "
                + self._get_human_readable_bytes(self._min_required_disk_space)
            )
            raise OutOfSpaceException(msg)

    def _get_human_readable_bytes(self, amount):
        str = "%d Bytes" % amount
        if amount > 1024 and amount <= 1024 * 1024:  # kB
            str += " (%.2f kB)" % (amount / 1024)
        if amount > 1024 * 1024 and amount <= 1024 * 1024 * 1024:  # MB
            str += " (%.2f MB)" % (amount / 1024 / 1024)
        if amount > 1024 * 1024 * 1024:  # GB
            str += " (%.2f GB)" % (amount / 1024 / 1024 / 1024)
        return str

    def convert(
        self,
        is_job_cancelled,
        on_progress=None,
        on_progress_args=None,
        on_progress_kwargs=None,
    ):
        profiler = Profiler("convert")
        profiler.start("s1_start")
        self.init_output_file()
        self.check_free_space()  # has to be after init_output_file (which removes old temp files occasionally)

        profiler.stop("s1_start").start("s2_parse")
        self.parse()
        is_job_cancelled()  # check after parsing svg xml.
        profiler.stop("s2_parse").start("s3_matrix")

        options = self.options
        options["doc_root"] = self.document.getroot()

        # Get all Gcodetools data from the scene.
        self.calculate_conversion_matrix()
        profiler.stop("s3_matrix").start("s4_paths")
        self.collect_paths()
        profiler.stop("s4_paths").start("preparing_progress")

        def report_progress(
            on_progress, on_progress_args, on_progress_kwargs, done, total
        ):
            is_job_cancelled()  # frequent checks between each path / image
            # self._log.info("#### calling is_job_cancelled @ %i / %i" % (done, total))
            if total == 0:
                total = 1

            progress = done / float(total)
            if on_progress is not None:
                if on_progress_args is None:
                    on_progress_args = ()
                if on_progress_kwargs is None:
                    on_progress_kwargs = dict()

                on_progress_kwargs["_progress"] = progress
                on_progress(*on_progress_args, **on_progress_kwargs)

        self._log.info("processing %i layers" % len(self.layers))
        # sum up
        itemAmount = 1
        for layer in self.layers:
            if layer in self.paths:
                itemAmount += len(self.paths[layer])
            if layer in self.images:
                itemAmount += len(self.images[layer])

        processedItemCount = 0
        report_progress(
            on_progress,
            on_progress_args,
            on_progress_kwargs,
            processedItemCount,
            itemAmount,
        )
        profiler.stop("preparing_progress").start("write_gco_header")

        with open(self._tempfile, "a") as fh:
            # write comments to gcode
            gc_options_str = "; gc_nexgen gc_options: {}\n".format(self.gc_options)
            fh.write(gc_options_str)
            fh.write(
                "; created:{}\n".format(
                    time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime())
                )
            )
            gc_color_str = "; laser params: {}\n".format(self.colorParams)
            fh.write(gc_color_str)

            fh.write(self._get_gcode_header())

            # images
            profiler.stop("write_gco_header").start("s5_images")
            self._log.info("Raster conversion: %s" % self.options["engrave"])
            for layer in self.layers:
                if layer in self.images and self.options["engrave"]:
                    for imgNode in self.images[layer]:
                        file_id = imgNode.get("data-serveurl", "")
                        x = imgNode.get("x")
                        y = imgNode.get("y")
                        if x is None:
                            x = "0"
                        if y is None:
                            y = "0"

                        # pt units
                        x = float(x)
                        y = float(y)
                        w = float(imgNode.get("width"))
                        h = float(imgNode.get("height"))

                        _upperLeft = [x, y]
                        _lowerRight = [x + w, y + h]

                        # apply svg transforms
                        _mat = self._get_transforms(imgNode)
                        simpletransform.applyTransformToPoint(_mat, _upperLeft)
                        simpletransform.applyTransformToPoint(_mat, _lowerRight)

                        ### original style with orientation points :( ... TODO
                        # mm conversion
                        upperLeft = self._transform(_upperLeft, layer, False)
                        lowerRight = self._transform(_lowerRight, layer, False)

                        w = abs(lowerRight[0] - upperLeft[0])
                        h = abs(lowerRight[1] - upperLeft[1])

                        # contrast = 1.0, sharpening = 1.0, beam_diameter = 0.25,
                        # intensity_black = 1000, intensity_white = 0, speed_black = 30, speed_white = 500,
                        # dithering = True, pierce_time = 500, separation = True, material = "default"
                        rasterParams = self.options["raster"]
                        ip = ImageProcessor(
                            output_filehandle=fh,
                            workingAreaWidth=self.workingAreaWidth,
                            workingAreaHeight=self.workingAreaHeight,
                            beam_diameter=rasterParams["beam_diameter"],
                            backlash_x=_mrbeam_plugin_implementation._settings.get(
                                ["machine", "backlash_compensation_x"]
                            ),
                            overshoot_distance=1,
                            intensity_black=rasterParams["intensity_black"],
                            intensity_white=rasterParams["intensity_white"],
                            intensity_black_user=rasterParams["intensity_black_user"],
                            intensity_white_user=rasterParams["intensity_white_user"],
                            speed_black=rasterParams["speed_black"],
                            speed_white=rasterParams["speed_white"],
                            dithering=rasterParams["dithering"],
                            pierce_time=rasterParams["pierce_time"],
                            engraving_mode=rasterParams["engraving_mode"],
                            extra_overshoot=rasterParams["extra_overshoot"],
                            eng_compressor=rasterParams["eng_compressor"],
                            material=self.options["material"],
                            eng_passes=rasterParams["eng_passes"],
                        )
                        # material = rasterParams['material'] if 'material' in rasterParams else None)
                        data = imgNode.get("href")
                        if data is None:
                            data = imgNode.get(_add_ns("href", "xlink"))

                        if data.startswith("data:"):
                            ip.dataUrl_to_gcode(
                                data, w, h, upperLeft[0], lowerRight[1], file_id
                            )
                        elif data.startswith("http://"):
                            ip.imgurl_to_gcode(
                                data, w, h, upperLeft[0], lowerRight[1], file_id
                            )
                        else:
                            self._log.error("Unable to parse img data", data)

                        profiler.nest_data(ip.get_profiler())

                        processedItemCount += 1
                        report_progress(
                            on_progress,
                            on_progress_args,
                            on_progress_kwargs,
                            processedItemCount,
                            itemAmount,
                        )
                    else:
                        self._log.info(
                            "postponing non-image layer %s" % (layer.get("id"))
                        )

            profiler.stop("s5_images").start("s6_vectors")

            # paths
            self._log.info("Vector conversion: %s paths" % len(self.paths))

            for layer in self.layers:
                if layer in self.paths:
                    paths_by_color = dict()
                    for path in self.paths[layer]:
                        self._log.info(
                            "path %s, %s, stroke: %s, fill: %s, mb:gc: %s"
                            % (
                                layer.get("id", None),
                                path.get("id", None),
                                path.get("stroke", None),
                                path.get("class", None),
                                path.get(_add_ns("gc", "mb"), "")[:100],
                            )
                        )

                        strokeInfo = self._get_stroke(path)
                        if strokeInfo["visible"] == False:
                            continue

                        stroke = strokeInfo["color"]
                        if "d" not in path.keys():
                            self._log.error(
                                "Warning: One or more paths don't have 'd' parameter"
                            )
                            continue
                        if stroke not in paths_by_color.keys() and stroke != "default":
                            paths_by_color[stroke] = []
                        d = path.get("d")
                        if d != "":
                            paths_by_color[stroke].append(path)  # += path
                            processedItemCount += 1
                            report_progress(
                                on_progress,
                                on_progress_args,
                                on_progress_kwargs,
                                processedItemCount,
                                itemAmount,
                            )

                    layerId = layer.get("id", "?")
                    pathId = path.get("id", "?")

                    # path_sorting: set initial laser pos, assuming pleasant left to right, bottom to top processing order
                    current_x = 0
                    current_y = 0

                    # for each color generate GCode
                    for colorKey in self.colorOrder:
                        if colorKey == "none":
                            continue

                        settings = self.colorParams.get(
                            colorKey,
                            {
                                "intensity": -1,
                                "feedrate": -1,
                                "passes": 0,
                                "pierce_time": 0,
                                "cut_compressor": 100,
                            },
                        )
                        if (
                            settings["feedrate"] == None
                            or settings["feedrate"] == -1
                            or settings["intensity"] == None
                            or settings["intensity"] <= 0
                        ):
                            self._log.info(
                                "convert() skipping color %s, no valid settings %s."
                                % (colorKey, settings)
                            )
                            continue

                        if not colorKey in paths_by_color:
                            self._log.info(
                                "convert() skipping color %s, no paths with this color (clipped? path in <defs>?. "
                                % (colorKey)
                            )
                            continue

                        # gcode_before_job
                        fh.write(
                            machine_settings.gcode_before_job(
                                color=colorKey,
                                compressor=settings.get("cut_compressor", "100"),
                            )
                        )

                        self._log.info(
                            "convert() path sorting active: %s, path size %i below maximum %i."
                            % (
                                self.optimize_path_order,
                                len(paths_by_color[colorKey]),
                                self.optimize_max_paths,
                            )
                        )
                        # if this O(n^2) algorithm blows performance, limit inner loop to just search within the first 100 items.
                        while len(paths_by_color[colorKey]) > 0:
                            path_sorting = self.optimize_path_order and (
                                len(paths_by_color[colorKey]) < self.optimize_max_paths
                            )
                            # pick closest starting point to (current_x, current_y)
                            closestPath = None
                            if path_sorting:
                                dist = float("inf")
                                for p in paths_by_color[colorKey]:
                                    start_x = p.get(_add_ns("start_x", "mb"), None)
                                    start_y = p.get(_add_ns("start_y", "mb"), None)

                                    if start_x != None and start_y != None:
                                        d = pow(float(start_x) - current_x, 2) + pow(
                                            float(start_y) - current_y, 2
                                        )
                                        if d < dist:
                                            dist = d
                                            closestPath = p

                            path = None
                            if closestPath != None:
                                path = closestPath
                            else:
                                path = paths_by_color[colorKey][0]

                            # process next / closest path...
                            curveGCode = ""
                            mbgc = path.get(_add_ns("gc", "mb"), None)
                            if mbgc != None:
                                curveGCode = self._use_embedded_gcode(mbgc)
                            else:
                                d = path.get("d")
                                csp = cubicsuperpath.parsePath(d)
                                csp = self._apply_transforms(path, csp)
                                curve = self._parse_curve(csp, layer)
                                curveGCode = self._generate_gcode(curve)

                            fh.write(
                                "; Layer:"
                                + layerId
                                + ", outline of:"
                                + pathId
                                + ", stroke:"
                                + colorKey
                                + ", "
                                + str(settings)
                                + "\n"
                            )
                            ity = settings["intensity"]
                            pt = settings["pierce_time"]
                            fr = int(settings["feedrate"])
                            passes = int(settings["passes"])
                            for p in range(0, passes):
                                if passes > JobParams.Min.PASSES and settings.get(
                                    "progressive", False
                                ):
                                    f = round(fr * (1 - 0.5 * p / (passes - 1)))
                                else:
                                    f = fr
                                fh.write("; pass:%i/%s\n" % (p + 1, settings["passes"]))
                                # TODO tbd DreamCut different for each pass?
                                gc = self._replace_params_gcode(
                                    curveGCode, colorKey, f, ity, pt
                                )
                                fh.write(gc)

                            # set current position after processing the path
                            end_x = path.get(_add_ns("end_x", "mb"), None)
                            end_y = path.get(_add_ns("end_y", "mb"), None)
                            if end_x != None and end_y != None:
                                current_x = float(end_x)
                                current_y = float(end_y)

                            # finally removed processed path
                            paths_by_color[colorKey].remove(path)

                        # TODO check if _after_job should be one(two?) levels less indented
                        # gcode_after_job
                        fh.write(machine_settings.gcode_after_job(color=colorKey))
            fh.write(self._get_gcode_footer())

        profiler.stop("s6_vectors").start("s7_export")
        self.export_gcode()
        profiler.stop("s7_export")
        summary = profiler.finalize().getShortSummary()
        self._log.info("conversion finished. Timing: %s", summary)

    def collect_paths(self):
        self._log.info("collect_paths")
        self.paths = {}
        self.images = {}
        self.layers = [self.document.getroot()]

        self.gc_options = self.document.getroot().get(_add_ns("gc_options", "mb"))
        self._log.info("gc_nexgen gc_options data in svg: %s", self.gc_options)

        def recursive_search(g, layer):
            items = g.getchildren()
            items.reverse()
            if len(items) > 0:
                self._log.debug("recursive search: %i - %s" % (len(items), g.get("id")))

            for i in items:
                # TODO layer support
                if (
                    i.tag == _add_ns("g", "svg")
                    and i.get(_add_ns("groupmode", "inkscape")) == "layer"
                ):
                    styles = simplestyle.parseStyle(i.get("style", ""))
                    if "display" not in styles or styles["display"] != "none":
                        self.layers += [i]
                        recursive_search(i, i)
                    else:
                        self._log.info("Skipping hidden layer: '%s'" % i.get("id", "?"))

                else:
                    # path
                    if i.tag == _add_ns("path", "svg"):
                        d = get_path_d(i)
                        if not d == None:
                            self._handle_node(i, layer)
                        else:
                            self._log.debug("Skipping path with empty d attribute.")

                    # rect, line, polygon, polyline, circle, ellipse
                    elif (
                        i.tag == _add_ns("rect", "svg")
                        or i.tag == "rect"
                        or i.tag == _add_ns("line", "svg")
                        or i.tag == "line"
                        or i.tag == _add_ns("polygon", "svg")
                        or i.tag == "polygon"
                        or i.tag == _add_ns("polyline", "svg")
                        or i.tag == "polyline"
                        or i.tag == _add_ns("ellipse", "svg")
                        or i.tag == "ellipse"
                        or i.tag == _add_ns("circle", "svg")
                        or i.tag == "circle"
                    ):

                        # TODO not necessary if path has embedded gcode
                        i.set("d", get_path_d(i))
                        self._handle_node(i, layer)

                    # image
                    elif i.tag == _add_ns("image", "svg"):
                        x = i.get("x")
                        y = i.get("y")
                        if x == None:
                            x = "0"
                        if y == None:
                            y = "0"

                        self._log.info(
                            "added image "
                            + i.get("width")
                            + "x"
                            + i.get("height")
                            + "@"
                            + x
                            + ","
                            + y
                        )
                        self._handle_image(i, layer)

                    # group
                    elif i.tag == _add_ns("g", "svg"):
                        recursive_search(i, layer)

                    elif (
                        i.tag == _add_ns("defs", "svg")
                        or i.tag == "defs"
                        or i.tag == _add_ns("desc", "svg")
                        or i.tag == "desc"
                    ):
                        self._log.info("ignoring tag: %s" % (i.tag))

                    else:
                        self._log.warn(
                            "ignoring not supported tag: %s \n%s"
                            % (i.tag, etree.tostring(i))
                        )

        recursive_search(self.document.getroot(), self.document.getroot())
        self._log.info("self.layers: %i" % len(self.layers))
        self._log.info("self.paths: %i" % len(self.paths))

    def parse(self, file=None):
        try:
            stream = open(self.svg_file, "r")
            p = etree.XMLParser(huge_tree=True, recover=True)
            self.document = etree.parse(stream, parser=p)
            stream.close()
            self._log.info("parsed %s" % self.svg_file)
        except Exception as e:
            self._log.error("unable to parse %s: %s" % (self.svg_file, e.message))

    def _handle_image(self, imgNode, layer):
        self.images[layer] = (
            self.images[layer] + [imgNode] if layer in self.images else [imgNode]
        )

    def _handle_node(self, node, layer):
        stroke = self._get_stroke(node)
        fill = self._get_fill(node)

        has_classes = (
            node.get("class", None) is not None
        )  # TODO parse styles instead of assuming that the style applies visibility
        visible = (
            has_classes
            or stroke["visible"]
            or fill["visible"]
            or (stroke["color"] == "unset" and fill["color"] == "unset")
        )
        processColor = self._process_color(stroke["color"])
        if visible and processColor:
            simpletransform.fuseTransform(node)
            self.paths[layer] = (
                self.paths[layer] + [node] if layer in self.paths else [node]
            )

    def _get_stroke(self, node):
        stroke = {}
        stroke["width"] = 1
        stroke["width_unit"] = "px"
        stroke["color"] = "unset"
        stroke["opacity"] = 1
        stroke["visible"] = True

        # "stroke", "stroke-width", "stroke-opacity", "opacity"
        styles = simplestyle.parseStyle(node.get("style"))
        color = node.get("stroke", None)
        if color is None:
            if "stroke" in styles:
                color = styles["stroke"]

        if color != None and color != "none" and color != "":
            stroke["color"] = color

        width = node.get("stroke-width", "")
        if width is "":
            if "stroke-width" in styles:
                width = styles["stroke-width"]
        if width != "none" and width != "":
            try:
                strokeWidth = float(re.sub(r"[^\d.]+", "", width))
                stroke["width"] = strokeWidth
                # todo: unit
            except ValueError:
                pass

        stroke_opacity = node.get("stroke-opacity", 1)
        if stroke_opacity is 1:
            if "stroke-opacity" in styles:
                try:
                    stroke_opacity = float(styles["stroke-opacity"])
                except ValueError:
                    pass

        opacity = node.get("opacity", 1)
        if opacity is 1:
            if "opacity" in styles:
                try:
                    opacity = float(styles["opacity"])
                except ValueError:
                    pass

        stroke["opacity"] = min(opacity, stroke_opacity)
        stroke["visible"] = (
            stroke["color"] is not None
            and stroke["opacity"] > 0
            and stroke["width"] > 0
        )
        return stroke

    def _get_fill(self, node):
        fill = {}
        fill["color"] = "unset"
        fill["opacity"] = 1
        fill["visible"] = True

        # "fill", "fill-opacity", "opacity"
        styles = simplestyle.parseStyle(node.get("style"))
        color = node.get("fill", None)
        if color is None:
            if "fill" in styles:
                color = styles["fill"]
        if color != None and color != "none" and color != "":
            fill["color"] = color

        fill_opacity = node.get("fill-opacity", 1)
        if fill_opacity is 1:
            if "fill-opacity" in styles:
                try:
                    fill_opacity = float(styles["fill-opacity"])
                except ValueError:
                    pass

        opacity = node.get("opacity", 1)
        if opacity is 1:
            if "opacity" in styles:
                try:
                    opacity = float(styles["opacity"])
                except ValueError:
                    pass

        fill["opacity"] = min(opacity, fill_opacity)
        fill["visible"] = fill["color"] is not None and fill["opacity"] > 0
        return fill

    def _process_color(self, color):
        if color in self.colorParams.keys():
            return True
        else:
            self._log.debug("Skipping color: %s " % color)
            return False

    def _check_dir(self):
        if self.options["directory"][-1] not in ["/", "\\"]:
            if "\\" in self.options["directory"]:
                self.options["directory"] += "\\"
            else:
                self.options["directory"] += "/"
        self._log.info("Checking directory: '%s'" % self.options["directory"])
        if os.path.isdir(self.options["directory"]):
            pass
        else:
            self._log.error(
                "Directory does not exist! Please specify existing directory at Preferences tab!"
            )
            return False

    def _apply_transforms(self, g, csp):
        trans = self._get_transforms(g)
        if trans != [[1, 0, 0], [0, 1, 0]]:  # todo can trans be [] anyways?
            self._log.warn("still transforms in the SVG %s" % trans)
            simpletransform.applyTransformToPath(trans, csp)
        return csp

    def _get_transforms(self, g):
        root = self.document.getroot()
        trans = [[1, 0, 0], [0, 1, 0]]
        while g != root:
            if "transform" in g.keys():
                t = g.get("transform")
                t = simpletransform.parseTransform(t)
                trans = simpletransform.composeTransform(t, trans) if trans != [] else t
                self._log.debug("Found transform: " % trans)
            g = g.getparent()
        return trans

    def _parse_curve(self, p, layer, w=None, f=None):
        c = []
        if len(p) == 0:
            return []
        p = self._transform_csp(p, layer)

        ### Sort to reduce Rapid distance
        k = range(1, len(p))
        keys = [0]
        while len(k) > 0:
            end = p[keys[-1]][-1][1]
            dist = None
            for i in range(len(k)):
                start = p[k[i]][0][1]
                dist = max(
                    (-((end[0] - start[0]) ** 2 + (end[1] - start[1]) ** 2), i), dist
                )
            keys += [k[dist[1]]]
            del k[dist[1]]

        # keys = range(1,len(p)) # debug unsorted.
        for k in keys:
            subpath = p[k]
            c += [[[subpath[0][1][0], subpath[0][1][1]], "move", 0, 0]]
            for i in range(1, len(subpath)):
                sp1 = [[subpath[i - 1][j][0], subpath[i - 1][j][1]] for j in range(3)]
                sp2 = [[subpath[i][j][0], subpath[i][j][1]] for j in range(3)]
                c += (
                    biarc(sp1, sp2, 0, 0)
                    if w == None
                    else biarc(sp1, sp2, -f(w[k][i - 1]), -f(w[k][i]))
                )
            c += [[[subpath[-1][1][0], subpath[-1][1][1]], "end", 0, 0]]

        # self._log.debug("Curve: " + str(c))
        return c

    def _transform_csp(self, csp_, layer, reverse=False):
        self._log.debug("_transform_csp %s , %s, %s" % (csp_, layer, reverse))
        csp = [
            [
                [csp_[i][j][0][:], csp_[i][j][1][:], csp_[i][j][2][:]]
                for j in range(len(csp_[i]))
            ]
            for i in range(len(csp_))
        ]
        for i in xrange(len(csp)):
            for j in xrange(len(csp[i])):
                for k in xrange(len(csp[i][j])):
                    csp[i][j][k] = self._transform(csp[i][j][k], layer, reverse)
        return csp

    def _transform(self, source_point, layer, reverse=False):
        self._log.debug("_transform %s,%s,%s " % (source_point, layer, reverse))
        if layer == None:
            layer = self.document.getroot()
        if layer not in self.transform_matrix:
            for i in range(self.layers.index(layer), -1, -1):
                if self.layers[i] in self.orientation_points:
                    break  # i will remain after the loop

            if self.layers[i] not in self.orientation_points:
                self._log.error("No orientation points for '%s' layer!" % layer)
            elif self.layers[i] in self.transform_matrix:
                self.transform_matrix[layer] = self.transform_matrix[self.layers[i]]
            else:
                orientation_layer = self.layers[i]
                points = self.orientation_points[orientation_layer][0]
                if len(points) == 2:
                    points += [
                        [
                            [
                                (points[1][0][1] - points[0][0][1]) + points[0][0][0],
                                -(points[1][0][0] - points[0][0][0]) + points[0][0][1],
                            ],
                            [
                                -(points[1][1][1] - points[0][1][1]) + points[0][1][0],
                                points[1][1][0] - points[0][1][0] + points[0][1][1],
                            ],
                        ]
                    ]
                if len(points) == 3:
                    self._log.debug(
                        "Layer '%s' Orientation points: "
                        % orientation_layer.get(_add_ns("label", "inkscape"))
                    )
                    for point in points:
                        self._log.debug(point)

                    matrix = numpy.array(
                        [
                            [points[0][0][0], points[0][0][1], 1, 0, 0, 0, 0, 0, 0],
                            [0, 0, 0, points[0][0][0], points[0][0][1], 1, 0, 0, 0],
                            [0, 0, 0, 0, 0, 0, points[0][0][0], points[0][0][1], 1],
                            [points[1][0][0], points[1][0][1], 1, 0, 0, 0, 0, 0, 0],
                            [0, 0, 0, points[1][0][0], points[1][0][1], 1, 0, 0, 0],
                            [0, 0, 0, 0, 0, 0, points[1][0][0], points[1][0][1], 1],
                            [points[2][0][0], points[2][0][1], 1, 0, 0, 0, 0, 0, 0],
                            [0, 0, 0, points[2][0][0], points[2][0][1], 1, 0, 0, 0],
                            [0, 0, 0, 0, 0, 0, points[2][0][0], points[2][0][1], 1],
                        ]
                    )

                    if numpy.linalg.det(matrix) != 0:
                        m = numpy.linalg.solve(
                            matrix,
                            numpy.array(
                                [
                                    [points[0][1][0]],
                                    [points[0][1][1]],
                                    [1],
                                    [points[1][1][0]],
                                    [points[1][1][1]],
                                    [1],
                                    [points[2][1][0]],
                                    [points[2][1][1]],
                                    [1],
                                ]
                            ),
                        ).tolist()
                        self.transform_matrix[layer] = [
                            [m[j * 3 + i][0] for i in range(3)] for j in range(3)
                        ]

                    else:
                        self._log.error(
                            "Orientation points are wrong! (if there are two orientation points they sould not be the same. If there are three orientation points they should not be in a straight line.)"
                        )
                else:
                    self._log.error(
                        "Orientation points are wrong! (if there are two orientation points they sould not be the same. If there are three orientation points they should not be in a straight line.)"
                    )

            self.transform_matrix_reverse[layer] = numpy.linalg.inv(
                self.transform_matrix[layer]
            ).tolist()

        x, y = source_point[0], source_point[1]
        if not reverse:
            t = self.transform_matrix[layer]
        else:
            t = self.transform_matrix_reverse[layer]
        return [
            t[0][0] * x + t[0][1] * y + t[0][2],
            t[1][0] * x + t[1][1] * y + t[1][2],
        ]

    ################################################################################
    ###
    ###		Generate Gcode
    ###		Generates Gcode on given curve.
    ###
    ###		Curve definition [start point, type = {'arc','line','move','end'}, arc center, arc angle, end point, [zstart, zend]]
    ###
    ################################################################################
    def _generate_gcode(self, curve):
        self._log.warn("_generate_gcode() - deprecated")

        def c(c):
            # returns gcode for coordinates/parameters
            c = [
                c[i] if i < len(c) else None for i in range(6)
            ]  # fills missing coordinates/parameters with none
            if c[5] == 0:
                c[5] = None
            s = [" X", " Y", " Z", " I", " J", " K"]
            r = ""
            for i in range(6):
                if c[i] != None:
                    r += s[i] + (
                        "%.4f" % (round(c[i], 4))
                    )  # truncating leads to invalid GCODE ID33
            return r

        if len(curve) == 0:
            return ""

        self._log.debug("Curve: " + str(curve))
        g = ""

        lg = "G00"
        for i in range(1, len(curve)):
            # 	Creating Gcode for curve between s=curve[i-1] and si=curve[i] start at s[0] end at s[4]=si[0]
            s = curve[i - 1]
            si = curve[i]
            if s[1] == "move":
                g += "G0" + c(si[0]) + "\n" + self.PLACEHOLDER_LASER_ON + "\n"
                lg = "G00"
            elif s[1] == "end":
                g += self.PLACEHOLDER_LASER_OFF + "\n"
                lg = "G00"
            elif s[1] == "line":
                if lg == "G00":
                    g += self.PLACEHOLDER_LASER_ON + "\n"
                g += "G01 " + c(si[0]) + "\n"
                lg = "G01"
            elif s[1] == "arc":
                r = [(s[2][0] - s[0][0]), (s[2][1] - s[0][1])]
                if lg == "G00":
                    g += self.PLACEHOLDER_LASER_ON + "\n"
                if (r[0] ** 2 + r[1] ** 2) > 0.1:
                    r1, r2 = (Point(s[0]) - Point(s[2])), (Point(si[0]) - Point(s[2]))
                    if abs(r1.mag() - r2.mag()) < 0.001:
                        g += (
                            ("G02" if s[3] < 0 else "G03")
                            + c(
                                si[0] + [None, (s[2][0] - s[0][0]), (s[2][1] - s[0][1])]
                            )
                            + "\n"
                        )
                    else:
                        r = (r1.mag() + r2.mag()) / 2
                        g += (
                            ("G02" if s[3] < 0 else "G03")
                            + c(si[0])
                            + " R%f" % (r)
                            + "\n"
                        )
                    lg = "G02"
                else:
                    g += "G01" + c(si[0]) + "\n"
                    lg = "G01"
        if si[1] == "end":
            g += self.PLACEHOLDER_LASER_OFF + "\n"
        return g

    def _use_embedded_gcode(self, gcode):
        self._log.debug("_use_embedded_gcode() %s", gcode[:100])
        return gcode.replace(" ", "\n")

    def _replace_params_gcode(self, gcode, color, feedrate, intensity, pierce_time):
        self._log.debug("_replace_params_gcode() %i %s", len(gcode), gcode[:100])
        feedrateCode = "F%s;%s\n" % (feedrate, color)
        intensityCode = (
            machine_settings.gcode_before_path_color(color, intensity) + "\n"
        )
        piercetimeCode = ""
        pt = int(pierce_time)
        if pt > 0:
            piercetimeCode = "G4P%.3f\n" % (round(pt / 1000.0, 4))
        gcode = (
            gcode.replace(
                self.PLACEHOLDER_LASER_ON, feedrateCode + intensityCode + piercetimeCode
            )
            + "\n"
        )
        gcode = (
            gcode.replace(
                self.PLACEHOLDER_LASER_OFF, machine_settings.gcode_after_path()
            )
            + "\n"
        )
        return gcode

    def export_gcode(self):
        self._check_dir()

        destination = self.options["directory"] + self.options["file"]
        shutil.move(self._tempfile, destination)
        self._log.info("wrote file: %s" % destination)

    def _get_gcode_header(self):

        if self.options["noheaders"]:
            return machine_settings.cooling_fan_speedup_gcode
        else:
            return (
                machine_settings.gcode_header
                + "G21\n\n"
                + cooling_fan_speedup_gcode
                + "\n"
            )

    def _get_gcode_footer(self):
        if self.options["noheaders"]:
            gcode = []
            gcode.append("; end of job")
            gcode.append("M05")
            if _mrbeam_plugin_implementation.compressor_handler.has_compressor():
                gcode.append("M100P0 ; mrbeam_compressor off")
            return "\n".join(gcode)
        else:
            return machine_settings.gcode_footer

    def calculate_conversion_matrix(self, layer=None):
        self._log.info("Calculating transformation matrix for layer: %s" % layer)
        if layer == None:
            layer = self.document.getroot()
        if layer in self.orientation_points:
            self._log.error("Layer already has a transformation matrix points!")

        # translate == ['0', '-917.7043']
        if layer.get("transform") != None:
            self._log.warn("FOUND TRANSFORM: %s " % layer.get("transform"))
            translate = (
                layer.get("transform")
                .replace("translate(", "")
                .replace(")", "")
                .split(",")
            )
        else:
            translate = [0, 0]

        # doc height in pixels (38 mm == 134.64566px)
        h = self._get_document_height()
        doc_height = unittouu(h)
        viewBoxM = self._get_document_viewbox_matrix()
        viewBoxScale = viewBoxM[1][1]  # TODO use both coordinates.

        self._log.info(
            "Document height: %s   viewBoxTransform: %s" % (str(doc_height), viewBoxM)
        )

        points = [[100.0, 0.0, 0.0], [0.0, 0.0, 0.0], [0.0, 100.0, 0.0]]
        orientation_scale = (
            self.options["svgDPI"] / 25.4
        ) / viewBoxScale  # 3.5433070660 @ 90dpi
        points = points[:2]

        self._log.info("using orientation scale %s, i=%s" % (orientation_scale, points))
        opoints = []
        for i in points:
            # X == Correct!
            # si == x,y coordinate in px
            # si have correct coordinates
            # if layer have any tranform it will be in translate so lets add that
            si = [
                i[0] * orientation_scale,
                (i[1] * orientation_scale) + float(translate[1]),
            ]

            # TODO avoid conversion to cubicsuperpath, calculate p0 and p1 directly
            # point[0] = self._apply_transforms(node,cubicsuperpath.parsePath(node.get("d")))[0][0][1]
            d = (
                "m %s,%s 2.9375,-6.343750000001 0.8125,1.90625 6.843748640396,-6.84374864039 0,0 0.6875,0.6875 -6.84375,6.84375 1.90625,0.812500000001 z z"
                % (si[0], -si[1] + doc_height / viewBoxScale)
            )
            csp = cubicsuperpath.parsePath(d)
            # self._log.info('### CSP %s' % csp)
            ### CSP [[[[0.0, 1413.42519685], [0.0, 1413.42519685], [0.0, 1413.42519685]], [[2.9375, 1407.081446849999], [2.9375, 1407.081446849999], [2.9375, 1407.081446849999]], [[3.75, 1408.987696849999], [3.75, 1408.987696849999], [3.75, 1408.987696849999]], [[10.593748640396, 1402.143948209609], [10.593748640396, 1402.143948209609], [10.593748640396, 1402.143948209609]], [[10.593748640396, 1402.143948209609], [10.593748640396, 1402.143948209609], [10.593748640396, 1402.143948209609]], [[11.281248640396, 1402.831448209609], [11.281248640396, 1402.831448209609], [11.281248640396, 1402.831448209609]], [[4.437498640396001, 1409.675198209609], [4.437498640396001, 1409.675198209609], [4.437498640396001, 1409.675198209609]], [[6.343748640396001, 1410.48769820961], [6.343748640396001, 1410.48769820961], [6.343748640396001, 1410.48769820961]], [[0.0, 1413.42519685], [0.0, 1413.42519685], [0.0, 1413.42519685]], [[0.0, 1413.42519685], [0.0, 1413.42519685], [0.0, 1413.42519685]]]]

            p0 = csp[0][0][1]
            p1 = [i[0], i[1], i[2]]
            point = [p0, p1]
            opoints += [point]

        if opoints != None:
            self.orientation_points[layer] = (
                self.orientation_points[layer] + [opoints[:]]
                if layer in self.orientation_points
                else [opoints[:]]
            )
            self._log.info(
                "Generated orientation points in '%s' layer: %s"
                % (layer.get(_add_ns("label", "inkscape")), opoints)
            )
        else:
            self._log.error(
                "Warning! Found bad orientation points in '%s' layer. Resulting Gcode could be corrupt!"
            ) % layer.get(_add_ns("label", "inkscape"))

    def _get_document_width(self):
        width = self.document.getroot().get("width")
        if width == None:
            vbox = self.document.getroot().get("viewBox")
            if vbox != None:
                self._log.info(
                    "width property not set in root node, fetching from viewBox attribute"
                )
                parts = vbox.split(" ")
                if len(parts) == 4:
                    width = parts[2]

        if width == "100%":
            width = 744.09  # 210mm @ 90dpi
            self._log.info("Overriding width from 100 percents to %s" % width)

        if width == None:
            width = 744.09  # 210mm @ 90dpi
            self._log.info("width not set. Assuming width is %s" % width)
        return str(width)

    def _get_document_height(self):
        height = self.document.getroot().get("height")
        if height == None:
            self._log.info(
                "height property not set in root node, fetching from viewBox attribute"
            )
            vbox = self.document.getroot().get("viewBox")
            if vbox != None:
                parts = vbox.split(" ")
                if len(parts) == 4:
                    height = parts[3]

        if height == "100%":
            height = 1052.3622047  # 297mm @ 90dpi
            self._log.info("Overriding height from 100 percents to %s" % height)

        if height == None:
            height = 1052.3622047  # 297mm @ 90dpi
            self._log.info("Height not set. Assuming height is %s" % height)
        return str(height)

    def _get_document_viewbox_matrix(self):
        vbox = self.document.getroot().get("viewBox")
        if vbox != None:
            self._log.info("Found viewbox attribute %s" % vbox)
            widthPx = unittouu(self._get_document_width())
            heightPx = unittouu(self._get_document_height())
            parts = vbox.split(" ")
            if len(parts) == 4:
                offsetVBoxX = float(parts[0])
                offsetVBoxY = float(parts[1])
                widthVBox = float(parts[2]) - float(parts[0])
                heightVBox = float(parts[3]) - float(parts[1])

                fx = widthPx / widthVBox
                fy = heightPx / heightVBox
                dx = offsetVBoxX * fx
                dy = offsetVBoxY * fy
                m = [[fx, 0, 0], [0, fy, 0], [dx, dy, 1]]
                return m

        return [[1, 0, 0], [0, 1, 0], [0, 0, 1]]


class OutOfSpaceException(Exception):
    pass
