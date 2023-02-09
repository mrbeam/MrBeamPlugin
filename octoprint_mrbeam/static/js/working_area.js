/* global snap, ko, $, Snap, API_BASEURL, _, CONFIG_WEBCAM_STREAM, ADDITIONAL_VIEWMODELS, mina, BEAMOS_DISPLAY_VERSION, WorkingAreaHelper, mrbeam, QuickShapeHelper, Promise, BEAMOS_VERSION */

MRBEAM_PX2MM_FACTOR_WITH_ZOOM = 1; // global available in this viewmodel and in snap plugins at the same time.
MRBEAM_WORKINGAREA_PAN_MM = [0, 0]; // global available in this viewmodel and in snap plugins at the same time.

// Render debugging utilities
MRBEAM_DEBUG_RENDERING = false; // setting to true enables lots of visual debug tools. Can be changed during runtime.

$(function () {
    function WorkingAreaViewModel(params) {
        var self = this;
        window.mrbeam.viewModels["workingAreaViewModel"] = self;

        self.SUPPORTED_IMAGE_TYPES = [
            "jpg",
            "jpeg",
            "png",
            "gif",
            "bmp",
            "pcx",
            "webp",
        ];

        self.parser = new gcParser();

        self.loginState = params[0];
        self.settings = params[1];
        self.state = params[2];
        self.files = params[3];
        self.profile = params[4];
        self.camera = params[5];
        self.readyToLaser = params[6];
        self.tour = params[7];
        self.analytics = params[8];

        self.log = [];
        self.gc_meta = {};

        self.command = ko.observable(undefined);
        self.id_counter = 1000;

        self.availableHeight = ko.observable(undefined);
        self.availableWidth = ko.observable(undefined);
        self.px2mm_factor = 1; // initial value
        self.workingAreaDPItoMM = 90 / 25.4;
        self.svgDPI = function () {
            return 90;
        }; // initial value, gets overwritten by settings in onAllBound()
        self.dxfScale = function () {
            return 1;
        }; // initial value, gets overwritten by settings in onAllBound()
        self.previewImgOpacity = ko.observable(1);
        self.previewImgOpacity.subscribe(function (newVal) {
            let col = newVal > 0.25 ? "#eeeeee" : "#999999";
            $("#coord_pattern_marker").attr("stroke", col);
            if (
                newVal !==
                self.settings.settings.plugins.mrbeam.cam.previewOpacity()
            ) {
                if (self.settings.savetimer !== undefined) {
                    clearTimeout(self.settings.savetimer);
                }
                self.settings.settings.plugins.mrbeam.cam.previewOpacity(
                    newVal
                );
                self.settings.savetimer = setTimeout(function () {
                    self.settings.saveData(undefined, function (newSettings) {
                        console.log(
                            "Saved previewOpacity",
                            newSettings.plugins.mrbeam.cam.previewOpacity
                        );
                        self.settings.savetimer = undefined;
                    });
                }, 2000);
            }
        });

        self.workingAreaWidthMM = ko.computed(function () {
            return self.profile.currentProfileData().volume.width();
        }, self);
        self.workingAreaHeightMM = ko.computed(function () {
            return self.profile.currentProfileData().volume.depth();
        }, self);

        // QuickShape limits
        self.rectangleMaxWidth = ko.computed(function () {
            return self.workingAreaWidthMM();
        }, self);
        self.rectangleMaxHeight = ko.computed(function () {
            return self.workingAreaHeightMM();
        }, self);
        self.lineMaxLength = ko.computed(function () {
            return self.workingAreaWidthMM();
        }, self);
        self.circleMaxRadius = ko.computed(function () {
            return self.workingAreaHeightMM();
        }, self);
        // TODO: The limit of the star radius should be calculated differently
        self.starMaxRadius = ko.computed(function () {
            return self.workingAreaHeightMM();
        }, self);
        // TODO: The limit of the heart width should be calculated differently
        self.heartMaxWidth = ko.computed(function () {
            return self.workingAreaWidthMM();
        }, self);
        // TODO: The limit of the heart height should be calculated differently
        self.heartMaxHeight = ko.computed(function () {
            return self.workingAreaHeightMM();
        }, self);

        self.imgTranslate = ko.computed(function () {
            // Used for the translate transformation of the picture on the work area
            return [-self.workingAreaWidthMM(), -self.workingAreaHeightMM()]
                .map((x) => x * self.camera.imgHeightScale())
                .join(" ");
        });
        self.zObjectImgTransform = ko.computed(function () {
            return (
                "scale(" +
                (1 + 2 * self.camera.imgHeightScale()) +
                ") translate(" +
                self.imgTranslate() +
                ")"
            );
        });
        self.flipYMatrix = ko.computed(function () {
            var h = self.workingAreaHeightMM();
            return Snap.matrix(1, 0, 0, -1, 0, h);
        }, self);

        // get overwritten by settings in onAllBound()
        self.gc_options = ko.computed(function () {
            return { enabled: false };
        });

        // QuickText fields
        self.fontMap = [
            "Allerta Stencil",
            "Amatic SC",
            "Comfortaa",
            "Fredericka the Great",
            "Kavivanar",
            "Lobster",
            "Merriweather",
            "Mr Bedfort",
            "Quattrocento",
            "Roboto",
        ];
        self.currentQuickTextFile = undefined;
        self.currentQuickTextAnalyticsData = undefined;
        self.currentQuickText = ko.observable(); // TODO check removal
        self.quickShapeNames = new Map([
            ["rect", gettext("Rectangle")],
            ["line", gettext("Line")],
            ["circle", gettext("Circle")],
            ["star", gettext("Star")],
            ["heart", gettext("Heart")],
        ]);
        self.currentQuickShapeFile = undefined;
        self.currentQuickShapeAnalyticsData = undefined;
        self.currentQuickShape = ko.observable();
        self.lastQuickTextFontIndex = 0;
        self.lastQuickTextStroke = false;
        self.lastQuickTextFill = true;
        self.lastQuickTextStrokeColor = "#e25303";
        self.lastQuickTextFillColor = "#000000";
        self.lastQuickTextCircle = 0;
        self.lastQuickTextClockwise = true;

        self.zoom = ko.observable(1.0);
        //		self.zoomPercX = ko.observable(0);
        //		self.zoomPercY = ko.observable(0);
        self.zoomOffX = ko.observable(0);
        self.zoomOffY = ko.observable(0);
        self.zoomViewBox = ko.computed(function () {
            var z = self.zoom();
            var w = self.workingAreaWidthMM() * z;
            var h = self.workingAreaHeightMM() * z;
            var x = self.zoomOffX();
            var y = self.zoomOffY();
            MRBEAM_WORKINGAREA_PAN_MM = [x, y];
            return [x, y, w, h].join(" ");
        });

        self.set_zoom_factor = function (delta, centerX, centerY) {
            var oldZ = self.zoom();
            var newZ = oldZ + delta;
            newZ = Math.min(Math.max(newZ, 0.25), 1);
            if (newZ !== self.zoom()) {
                if (newZ === 1) {
                    self.set_zoom_offX(0);
                    self.set_zoom_offY(0);
                } else {
                    var deltaWidth = self.workingAreaWidthMM() * delta;
                    var deltaHeight = self.workingAreaHeightMM() * delta;
                    var oldOffX = self.zoomOffX();
                    var oldOffY = self.zoomOffY();
                    self.set_zoom_offX(oldOffX - deltaWidth * centerX);
                    self.set_zoom_offY(oldOffY - deltaHeight * centerY);
                }
                self.zoom(newZ);
            }
        };
        self.set_zoom_offX = function (offset) {
            var max = (1 - self.zoom()) * self.workingAreaWidthMM();
            var min = 0;
            offset = Math.min(Math.max(offset, min), max);
            self.zoomOffX(offset);
        };
        self.set_zoom_offY = function (offset) {
            var max = (1 - self.zoom()) * self.workingAreaHeightMM();
            var min = 0;
            offset = Math.min(Math.max(offset, min), max);
            self.zoomOffY(offset);
        };
        self.zoom_factor_text = ko.computed(function () {
            if (self.zoom() !== 1) {
                return ((1 / self.zoom()) * 100).toFixed(0) + "%";
            } else {
                return "";
            }
        });

        self.hwRatio = ko.computed(function () {
            var w = self.workingAreaWidthMM();
            var h = self.workingAreaHeightMM();
            var ratio = h / w;
            return ratio;
        }, self);

        // TODO CLEM check comma expression for functionality!
        self.workingAreaDim = ko.computed(function () {
            var maxH = self.availableHeight();
            var maxW = self.availableWidth();
            var hwRatio = self.hwRatio();
            if ((hwRatio > 0, maxH > 0, maxW > 0)) {
                var w = 0;
                var h = 0;
                if (maxH / maxW > hwRatio) {
                    w = maxW;
                    h = maxW * hwRatio;
                } else {
                    w = maxH / hwRatio;
                    h = maxH;
                }
                var dim = [w, h];
                return dim;
            }
        });

        self.workingAreaWidthPx = ko.computed(function () {
            var dim = self.workingAreaDim();
            return dim ? dim[0] : 1;
        }, self);

        self.workingAreaHeightPx = ko.computed(function () {
            var dim = self.workingAreaDim();
            return dim ? dim[1] : 1;
        }, self);

        self.px2mm_factor = ko.computed(function () {
            return (
                (self.zoom() * self.workingAreaWidthMM()) /
                self.workingAreaWidthPx()
            );
        });

        // matrix scales svg units to display_pixels
        self.scaleMatrix = ko.computed(function () {
            var m = new Snap.Matrix();
            return m;
        });

        //		self.matrixMMflipY = ko.computed(function(){
        //			var m = new Snap.Matrix();
        //			var yShift = self.workingAreaHeightMM(); // 0,0 origin of the gcode is bottom left. (top left in the svg)
        //			m.scale(1, -1).translate(0, -yShift);
        //			return m;
        //		});

        self.scaleMatrixCrosshair = function () {
            var x = self.crosshairX !== undefined ? self.crosshairX() : 0;
            var y = self.crosshairY !== undefined ? self.crosshairY() : 0;
            var y = self.workingAreaHeightMM() - y;
            var m = "matrix(1, 0, 0, 1, " + x + ", " + y + ")";
            return m;
        };

        self.placedDesigns = ko.observableArray([]);
        self.working_area_empty = ko.computed(function () {
            return self.placedDesigns().length === 0;
        });

        self.spinnerShow = function () {
            $("body").addClass("activitySpinnerActive");
        };
        self.spinnerHide = function () {
            $("body").removeClass("activitySpinnerActive");
        };

        self.clear = function () {
            self.abortFreeTransforms();
            snap.selectAll("#userContent>*:not(defs)").remove();
            snap.selectAll("#placedGcodes>*").remove();
            snap.selectAll(
                "rect:not(#coordGrid):not(#highlightMarker):not(#translateHandle)"
            ).remove(); // TODO ? what for?
            self.placedDesigns([]);
        };

        self.getUsedColors = function (elem) {
            // TODO rewrite as snap plugin
            elem = !elem
                ? snap.select("#userContent")
                : typeof elem === "string"
                ? snap.select(elem)
                : elem;
            return self._getColorsOfSelector(".vector_outline", "stroke", elem);
        };

        self.hasEngraveOnlyComponents = function (elem) {
            elem = !elem
                ? snap.select("#userContent")
                : typeof elem === "string"
                ? snap.select(elem)
                : elem;
            return (
                elem.selectAll("image").length > 0 ||
                self.hasFilledVectors(elem) // TODO use is_filled()
            );
        };

        self._getColorsOfSelector = function (
            // TODO rewrite as snap plugin using is_stroked()
            selector,
            color_attr = "stroke",
            elem = null
        ) {
            let root = elem === null ? snap : elem;

            let colors = [];
            let items = root.selectAll(selector + "[" + color_attr + "]");
            for (var i = 0; i < items.length; i++) {
                let col = items[i].attr()[color_attr];
                const bb = items[i].getBBox();
                if (
                    bb.w > 0 &&
                    // TODO: the line path has zero height so this should be done in a different manner
                    // bb.h > 0 && // filters elements without dimension, e.g. <path> without d attrib.
                    col !== "undefined" &&
                    col !== "none" &&
                    col !== null &&
                    col !== ""
                ) {
                    colors.push(col);
                }
            }
            colors = _.uniq(colors); // unique
            return colors;
        };

        self.trigger_resize = function () {
            if (typeof snap !== "undefined" && snap !== null)
                self.abortFreeTransforms();
            var tabContentPadding = 18;
            self.availableHeight(
                document.documentElement.clientHeight -
                    $("#mrbeam-main-tabs").height() -
                    tabContentPadding
            ); // TODO remove magic number
            self.availableWidth($("#workingarea div.span8").innerWidth());
            //			console.log("availableHeight ", self.availableHeight());
            //			console.log("availableWidth ", self.availableWidth());
        };

        self.move_laser = function (data, evt) {
            self.abortFreeTransforms();
            const coord = self.getXYCoord(evt);
            self.move_laser_to_xy(coord.x, coord.y);
        };

        self.getXYCoord = function (evt) {
            var elemPos = evt.currentTarget.getBoundingClientRect();
            var x = self.px2mm(evt.clientX - elemPos.left);
            var y = self.px2mm(elemPos.bottom - evt.clientY);
            x = Math.min(x, self.workingAreaWidthMM());
            y = Math.min(y, self.workingAreaHeightMM());
            return { x: x, y: y };
        };

        self.move_laser_to_xy = function (x, y) {
            if (
                self.state.isOperational() &&
                !self.state.isPrinting() &&
                !self.state.isLocked()
            ) {
                $.ajax({
                    url: API_BASEURL + "plugin/mrbeam",
                    type: "POST",
                    dataType: "json",
                    contentType: "application/json; charset=UTF8",
                    data: JSON.stringify({
                        command: "position",
                        x: parseFloat(x.toFixed(2)),
                        y: parseFloat(y.toFixed(2)),
                    }),
                });
            } else {
                console.warn(
                    `Move Laser to ${x},${y} command while machine state not idle: ${self.state.stateString()}`
                );
            }
        };

        /**
         * All this logging is for debugging.
         * In version 0.7.11 (beta) some users complained that they were not able to home
         * @param source
         */
        self.performHomingCycle = function (source) {
            let stateString = self.state ? self.state.stateString() : null;
            OctoPrint.printer
                .home(["x", "y"])
                .done(function () {
                    console.log(
                        "Homing call OK (source: " +
                            source +
                            ", stateString: " +
                            stateString +
                            ")"
                    );
                })
                .fail(function (jqXHR, textStatus, errorThrown) {
                    setTimeout(function () {
                        let stateStringNew = self.state
                            ? self.state.stateString()
                            : null;
                        console.error(
                            "Homing call ERROR (source: " +
                                source +
                                ", stateString: " +
                                stateString +
                                ", stateStringNew: " +
                                stateStringNew +
                                "): " +
                                jqXHR.status +
                                " " +
                                errorThrown
                        );
                    }, 500);
                });
        };

        self.crosshairX = function () {
            var pos = self.state.currentPos();
            if (pos !== undefined) {
                return pos.x; //  - 15; // subtract width/2;
            } else {
                return -100;
            }
        };
        self.crosshairY = function () {
            var h =
                self.workingAreaDim !== undefined
                    ? self.workingAreaDim()[1]
                    : 0;
            var pos = self.state.currentPos();
            return pos !== undefined ? pos.y : -100; //  - 15) : -100; // subtract height/2;
        };

        self.px2mm = function (val) {
            return val * self.px2mm_factor();
        };

        self.mm2px = function (val) {
            return val / self.px2mm_factor();
        };

        self.mm2svgUnits = function (val) {
            return (val * self.svgDPI()) / 25.4;
        };

        self.startTour = function () {
            self.tour.startTour();
        };

        /**
         * Adds an entry to the list of placed designs.
         * Instead of pushing directly in the ko.observableArray, this method does some sanity checks
         *
         * @param {type} file
         * @returns {undefined}
         */
        self._listPlacedItem = function (file) {
            /**
             * file = {
             * id: <string> DOM id of the entry in the file list
             * previewId: <string> DOM id of the group in the svg. usually the id with -0 attached.
             * url: download url where it was fetched from (raspberry download url)
             * misfit: flag if it fits into the working area
             * type <string> used to select the correct template (model_svg, machinecode, model_img, split, ... )
             * components: knockout observableArray containing stroke colors (will be set here in this method)
             * components_engrave: knockout observable with boolean inside (will be set here in this method)
             * ...
             * }
             */

            // check if already in the working area svg
            const elem = snap.select("#" + file.previewId);
            if (!elem) {
                console.warn(
                    "No svg fragment placed for this previewId: " +
                        file.previewId
                );
            }
            // check if it is transformable
            if (
                !(
                    elem.data &&
                    typeof elem.data(
                        snap.mbtransform.BEFORE_TRANSFORM_CALLBACKS
                    ) === "object"
                )
            ) {
                console.warn(
                    "Svg fragment is not transformable: " + file.previewId
                );
            }

            if (elem) {
                file.components = ko.observableArray(self.getUsedColors(elem));
                file.components_engrave = ko.observable(
                    self.hasEngraveOnlyComponents(elem)
                );
                self.placedDesigns.push(file);
            }
        };

        /**
         *
         * @param {type} file (OctoPrint "file" object - example: {url: elem.url, origin: elem.origin, name: name, type: "split", refs:{download: elem.url}};)
         * @returns {Boolean}
         */
        self.isPlaced = function (file) {
            if (file === undefined) return false;

            var filePlaced = ko.utils.arrayFirst(
                this.placedDesigns(),
                function (d) {
                    return d.name === file.name;
                }
            );
            return filePlaced;
        };

        self.countPlacements = function (file) {
            // quicktexts can't get duplicated and don't have ["refs"]["download"]
            if (file["type"] === "quicktext" || file["type"] === "quickshape") {
                return 1;
            }
            var label = file["refs"]["download"];
            var p = snap.selectAll("g[mb\\:origin='" + label + "']");
            return p.length;
        };

        self.placeGcode = function (file) {
            var start_ts = Date.now();
            var previewId = self.getEntryId();

            // TODO think about if double placing a gcode file is a problem.
            //			if(snap.select('#'+previewId)){
            //				console.error("working_area placeGcode: file already placed.");
            //				return;
            //			} else {
            var g = snap.group();
            g.attr({
                id: previewId,
                "mb:id": self._normalize_mb_id(previewId),
            });
            snap.select("#placedGcodes").append(g);
            file.previewId = previewId;
            self._listPlacedItem(file);
            //			}

            self.loadGcode(file, function (gcode) {
                var duration_load = Date.now() - start_ts;
                start_ts = Date.now();
                var pathCallback = function (path) {
                    var points = [];
                    var intensity = -1;
                    for (var idx = 0; idx < path.length; idx++) {
                        var item = path[idx];
                        points.push([item.x, item.y]);
                        intensity = item.laser;
                    }
                    if (points.length > 0) {
                        self.draw_gcode(points, intensity, "#" + previewId);
                    }
                };
                var imgCallback = function (x, y, w, h, url) {
                    self.draw_gcode_img_placeholder(
                        x,
                        y,
                        w,
                        h,
                        url,
                        "#" + previewId
                    );
                };
                self.parser.parse(
                    gcode,
                    /(m0?3)|(m0?5)/i,
                    pathCallback,
                    imgCallback
                );

                // analytics
                var re = / beamOS:([0-9.]+) /;
                var match = re.exec(gcode.substring(0, 1000));
                var beamos_vers = match && match.length > 1 ? match[1] : null;
                var analyticsData = {
                    id: previewId,
                    file_type: "gco",
                    filename_hash: file.hash,
                    size: file.size,
                    duration_load: duration_load,
                    duration_processing: Date.now() - start_ts,
                    gco_generator_info: {
                        generator: beamos_vers ? "beamOS" : null,
                        version: beamos_vers ? beamos_vers : null,
                    },
                };
                self._analyticsPlaceGco(analyticsData);
            });
        };

        self.loadGcode = function (file, callback) {
            var url = file.refs.download;
            var date = file.date;
            $.ajax({
                url: url,
                data: { ctime: date },
                type: "GET",
                success: function (response, rstatus) {
                    if (rstatus === "success") {
                        if (typeof callback === "function") {
                            callback(response);
                        }
                    }
                },
                error: function () {
                    console.error(
                        "working_area.js placeGcode: unable to load ",
                        url
                    );
                },
            });
        };

        self.removeGcode = function (file) {
            var previewId = file.previewId;
            snap.selectAll("#" + previewId).remove();
            self.placedDesigns.remove(file);
        };

        self.placeUpload = function (data) {
            if (data.type === "machinecode") {
                self.placeGcode(data);
            } else if (data.type === "model") {
                var extension = data.name.split(".").pop().toLowerCase();
                if (extension === "svg") {
                    self.placeSVG(data);
                } else if (extension === "dxf") {
                    self.placeDXF(data);
                } else if (_.contains(self.SUPPORTED_IMAGE_TYPES, extension)) {
                    self.placeIMG(data);
                } else {
                    console.warn("Unable to place unidentified upload", data);
                }
            } else if (data.type === "recentjob") {
                self.placeSVG(data);
            } else {
                console.warn(
                    "Upload type is neither machinecode nor model",
                    data
                );
            }
        };

        /**
         * Call to place (add) a SVG file to working area
         * @param file
         * @param callback
         */
        self.placeSVG = function (file, callback) {
            var start_ts = Date.now();
            var url = self._getSVGserveUrl(file);
            self.spinnerShow();
            cb = function (fragment) {
                var duration_load = Date.now() - start_ts;
                start_ts = Date.now();
                if (WorkingAreaHelper.isBinaryData(fragment.node.textContent)) {
                    // workaround: only catching one loading error
                    self.file_not_readable();
                    return;
                }
                if (WorkingAreaHelper.isEmptyFile(fragment)) {
                    // empty svg files
                    self.empty_svg();
                    return;
                }
                var id = self.getEntryId();
                var previewId = self.generateUniqueId(id, file); // appends -# if multiple times the same design is placed.
                var origin = file["refs"]["download"];
                file.id = id; // list entry id
                file.previewId = previewId;
                file.url = url;
                file.misfit = false;

                // get scale matrix
                var generator_info = WorkingAreaHelper.getGeneratorInfo(
                    fragment
                );
                var doc_dimensions = self._getDocumentDimensionAttributes(
                    fragment
                );
                var unitScaleX = self._getDocumentScaleToMM(
                    doc_dimensions.units_x,
                    generator_info
                );
                var unitScaleY = self._getDocumentScaleToMM(
                    doc_dimensions.units_y,
                    generator_info
                );
                var mat = self.getDocumentViewBoxMatrix(
                    doc_dimensions,
                    doc_dimensions.viewbox
                );
                var scaleMatrixStr = new Snap.Matrix(
                    mat[0][0] * unitScaleX,
                    mat[0][1],
                    mat[1][0],
                    mat[1][1] * unitScaleY,
                    -mat[2][0] * unitScaleX,
                    -mat[2][1] * unitScaleY
                ).toTransformString();

                var analyticsData = {};
                analyticsData.file_type = "svg";
                analyticsData.svg_generator_info = generator_info;
                analyticsData.svg_generator_info.generator =
                    analyticsData.svg_generator_info.generator === "unknown"
                        ? null
                        : analyticsData.svg_generator_info.generator;
                analyticsData.svg_generator_info.version =
                    analyticsData.svg_generator_info.version === "unknown"
                        ? null
                        : analyticsData.svg_generator_info.version;
                analyticsData.duration_load = duration_load;
                analyticsData.duration_preprocessing = Date.now() - start_ts;
                var insertedId = self._prepareAndInsertSVG(
                    fragment,
                    previewId,
                    origin,
                    scaleMatrixStr,
                    {},
                    analyticsData,
                    file
                );
                self._listPlacedItem(file);
                if (typeof callback === "function") callback(insertedId);
            };
            try {
                // TODO Figure out why the loading exception is not caught.
                self.loadSVG(url, cb);
            } catch (e) {
                console.error(e);
                self.file_not_readable();
            }
        };

        /**
         * Call to place (add) a DXF file to working area
         * @param file
         * @param callback (otional)
         */
        self.placeDXF = function (file, callback) {
            var start_ts = Date.now();
            var url = self._getSVGserveUrl(file);
            self.spinnerShow();
            cb = function (fragment, timestamps) {
                var duration_load = timestamps.load_done
                    ? timestamps.load_done - start_ts
                    : null;
                var origin = file["refs"]["download"];

                var tx = 0;
                var ty = 0;
                var doc_dimensions = self._getDocumentDimensionAttributes(
                    fragment
                );
                var viewbox = doc_dimensions.viewbox.split(" ");
                var origin_left = parseFloat(viewbox[0]);
                var origin_top = parseFloat(viewbox[1]);
                if (!isNaN(origin_left) && origin_left < 0)
                    tx = -origin_left * self.dxfScale();
                if (!isNaN(origin_top) && origin_top < 0)
                    ty = -origin_top * self.dxfScale();
                // scale matrix
                var scaleMatrixStr = new Snap.Matrix(1, 0, 0, 1, tx, ty)
                    .scale(self.dxfScale())
                    .toTransformString();

                var id = self.getEntryId();
                var previewId = self.generateUniqueId(id, file); // appends -# if multiple times the same design is placed.

                file.id = id; // list entry id
                file.previewId = previewId;
                file.url = url;
                file.misfit = false;

                var analyticsData = {};
                analyticsData.file_type = "dxf";
                analyticsData.duration_load = duration_load;
                analyticsData.duration_preprocessing =
                    timestamps.parse_start && timestamps.parse_done
                        ? timestamps.parse_done - timestamps.parse_start
                        : null;
                var insertedId = self._prepareAndInsertSVG(
                    fragment,
                    previewId,
                    origin,
                    scaleMatrixStr,
                    {},
                    analyticsData,
                    file
                );
                self._listPlacedItem(file);
                if (typeof callback === "function") callback(insertedId);
            };
            try {
                // TODO this would be the much better way. Figure out why the loading exception is not caught.
                Snap.loadDXF(url, cb);
            } catch (e) {
                console.error(e);
                self.file_not_readable();
            }
        };

        /**
         * This should be the common handler for everything added to the working area that is converted to SVG
         * @param fragment svg snippet
         * @param id generated by placeSVG, placeDXF, placeImage, quick text, quick shape, ...
         * @param origin file url or uniq element source id
         * @param scaleMatrixStr (optional)
         * @param flags object with self-explaining keys (true per default): showTransformHandles, embedGCode, bakeTransforms
         * @returns {*}
         * @private
         */
        self._prepareAndInsertSVG = function (
            fragment,
            id,
            origin,
            scaleMatrixStr,
            flags,
            analyticsData,
            fileObj,
            start_ts
        ) {
            analyticsData = analyticsData || {};
            fileObj = fileObj || {};
            origin = origin || "";
            start_ts = start_ts || Date.now();

            self.spinnerShow();

            if (!analyticsData._skip) {
                // this is a flag used by quickShape
                analyticsData.id = fileObj ? fileObj.id : id;
                analyticsData.file_type =
                    analyticsData.file_type ||
                    (fileObj.display
                        ? fileObj.display.split(".").slice(-1)[0]
                        : origin.split(".").slice(-1)[0]);
                analyticsData.filename_hash =
                    fileObj.hash ||
                    origin
                        .split("/downloads/files/local/")
                        .slice(-1)[0]
                        .hashCode();
                analyticsData.size = fileObj.size;
                analyticsData.node_count = 0;
                analyticsData.node_types = {};
                analyticsData.path_char_lengths = [];
                analyticsData.text_font_families = [];
                analyticsData.removed_unsupported_elements = {};
                analyticsData.removed_unnecessary_elements = {};
                analyticsData.removed_import_references = {};
                analyticsData.ignored_elements = {};
                analyticsData.namespaces = [];

                let allNodes = fragment.selectAll("*");
                analyticsData.node_count = allNodes.length;
                for (let i = 0; i < allNodes.length; i++) {
                    if (!(allNodes[i].type in analyticsData.node_types)) {
                        analyticsData.node_types[allNodes[i].type] = 0;
                    }
                    analyticsData.node_types[allNodes[i].type]++;
                    if (allNodes[i].type === "path") {
                        analyticsData.path_char_lengths.push(
                            allNodes[i].attr("d").length
                        );
                    }
                    if (allNodes[i].type === "text") {
                        let fontFam = allNodes[i].node.style.fontFamily;
                        fontFam = fontFam
                            ? fontFam.replace(/"/g, "").replace(/'/g, "")
                            : null;
                        if (!fontFam || !Boolean(fontFam.trim())) {
                            fontFam = allNodes[i].node.getAttribute(
                                "font-family"
                            );
                        }
                        fontFam = fontFam
                            ? fontFam.replace(/"/g, "").replace(/'/g, "")
                            : null;
                        analyticsData.text_font_families.push(fontFam);
                    }
                }
            }

            try {
                // bug: bake() kills gradients because gradient coordinates are not transformed.
                var switches = $.extend(
                    {
                        showTransformHandles: true,
                        embedGCode: true,
                        bakeTransforms: true,
                    },
                    flags
                );
                fragment = self._removeUnsupportedSvgElements(
                    fragment,
                    analyticsData
                );

                // get original svg namespaces and store into working area root node
                let namespaces = self._getDocumentNamespaceAttributes(fragment);
                snap.attr(namespaces);
                _.merge(analyticsData.namespaces, namespaces); // analyticsData.namespaces is the destination object
                var newSvgAttrs = {};
                if (scaleMatrixStr) {
                    newSvgAttrs["transform"] = scaleMatrixStr;
                }

                // assign id directly after placement. otherwise it is not UI-removable in case of exceptions during placement.
                var newSvg = snap.group(fragment.selectAll("svg>*"));
                newSvg.attr({
                    id: id,
                    "mb:id": self._normalize_mb_id(id),
                    class: "userSVG",
                    "mb:origin": origin,
                });

                // remove hidden elements with "display:none" via a css class (svg fragment needs to be placed to use getComputedStyle())
                let allElems = newSvg.selectAll("*[class]");
                // console.log("found elements", allElems.length);
                for (var i = 0; i < allElems.length; i++) {
                    var el = allElems[i];
                    // also check visibility:hidden
                    if (window.getComputedStyle(el.node).display === "none") {
                        console.info(
                            "computed style display=none, removing element ",
                            el
                        );
                        el.remove();
                    }
                }

                newSvg.unref(true);

                // remove non-visible text elements (no text, TODO: just whitespace)
                const textElements = newSvg.selectAll("text");
                textElements.forEach((t) => {
                    const bb = t.getBBox();
                    if (bb.width === 0 || bb.height === 0) {
                        t.remove();
                    }
                });
                // handle texts
                var hasText = newSvg.selectAll("text,tspan");
                if (hasText && hasText.length > 0) {
                    self.svg_contains_text_warning(newSvg);
                }

                // remove style elements with online references
                var hasStyle = newSvg.selectAll("style");
                if (hasStyle && hasStyle.length > 0) {
                    for (var y = 0; y < hasStyle.length; y++) {
                        if (
                            hasStyle[y].node.innerHTML &&
                            hasStyle[y].node.innerHTML.search("@import ") >= 0
                        ) {
                            self.svg_contains_online_style_warning();
                            console.warn(
                                "Removing style element: web references not supported: ",
                                hasStyle[y].node.innerHTML
                            );
                            if (
                                !(
                                    hasStyle[y].type in
                                    analyticsData.removed_import_references
                                )
                            ) {
                                analyticsData.removed_import_references[
                                    hasStyle[y].type
                                ] = 0;
                            }
                            analyticsData.removed_import_references[
                                hasStyle[y].type
                            ]++;
                            hasStyle[y].node.remove();
                        }
                    }
                }

                newSvg.attr(newSvgAttrs);
                if (switches.bakeTransforms) {
                    window.mrbeam.bake_progress = 0;
                    var ignoredElements = newSvg.bake(
                        self._bake_progress_callback
                    ); // remove transforms
                    if (!analyticsData._skip) {
                        for (var i = 0; i < ignoredElements.length; i++) {
                            if (
                                !(
                                    ignoredElements[i] in
                                    analyticsData.ignored_elements
                                )
                            )
                                analyticsData.ignored_elements[
                                    ignoredElements[i]
                                ] = 0;
                            analyticsData.ignored_elements[
                                ignoredElements[i]
                            ]++;
                        }
                    }
                }
                newSvg
                    .selectAll("path")
                    .attr({ strokeWidth: "0.8", class: "vector_outline" });
                // replace all fancy color definitions (rgba(...), hsl(...), 'pink', ...) with hex values
                newSvg.selectAll("*[stroke]:not(#bbox)").forEach(function (el) {
                    var colStr = el.attr().stroke;
                    // handle stroke="" default value (#000000)
                    if (typeof colStr !== "undefined" && colStr !== "none") {
                        var colHex = WorkingAreaHelper.getHexColorStr(colStr);
                        el.attr("stroke", colHex);
                    }
                });
                newSvg.selectAll("*[fill]:not(#bbox)").forEach(function (el) {
                    var colStr = el.attr().fill;
                    // handle fill="" default value (#000000)
                    if (typeof colStr !== "undefined" && colStr !== "none") {
                        var colHex = WorkingAreaHelper.getHexColorStr(colStr);
                        el.attr("fill", colHex);
                    }
                });

                snap.select("#userContent").append(newSvg);
                // after placement ids have changed => select freshly placed fragment via id.
                self._addClickAndHoverHandlers(snap.select("#" + id), fileObj);

                return id;
            } catch (e) {
                analyticsData["error"] = e.stack;
                console.error(e);
                self.svg_place_general_error(e.stack);
            } finally {
                analyticsData.duration_processing = Date.now() - start_ts;
                self._analyticsPrepareAndInsertSVG(analyticsData);
                setTimeout(function () {
                    self.spinnerHide();
                }, 1);
            }
        };

        self._bake_progress_callback = function (percent, done, total) {
            window.mrbeam.bake_progress = percent;
            // console.log("_bake_progress_callback() "+percent.toFixed()+"% | " + done + " / " + total);
        };

        /**
         * Removes unsupported elements from fragment.
         * List of elements to remove is defined within this function in var unsupportedElems
         * @param fragment
         * @param analyticsData obj - this object gets modiyfied but not returned!!
         * @returns fragment
         * @private
         */
        self._removeUnsupportedSvgElements = function (
            fragment,
            analyticsData
        ) {
            // add more elements that need to be removed here
            var unsupportedElems = [
                "clipPath",
                "flowRoot",
                "switch",
                "#adobe_illustrator_pgf",
            ];

            for (var i = 0; i < unsupportedElems.length; i++) {
                var myElem = fragment.selectAll(unsupportedElems[i]);
                if (myElem.length !== 0) {
                    analyticsData.removed_unsupported_elements[
                        unsupportedElems[i]
                    ] = myElem.length;
                    console.warn(
                        "Warning: removed unsupported '" +
                            unsupportedElems[i] +
                            "' element in SVG"
                    );
                    self.svg_contains_unsupported_element_warning(
                        unsupportedElems[i]
                    );
                    myElem.remove();
                }
            }

            // remove other unnecessary or invisible ("display=none") elements
            let removeElements = fragment.selectAll(
                'title, metadata, script, [display=none], [style*="display:none"], inkscape\\:path-effect, sodipodi\\:namedview'
            );
            for (var i = 0; i < removeElements.length; i++) {
                if (
                    !(
                        removeElements[i] in
                        analyticsData.removed_unnecessary_elements
                    )
                )
                    analyticsData.removed_unnecessary_elements[
                        removeElements[i].type
                    ] = 0;
                analyticsData.removed_unnecessary_elements[
                    removeElements[i].type
                ]++;
                console.warn(
                    "Unsupported '" +
                        removeElements[i].type +
                        "' element in SVG is removed"
                );
            }
            removeElements.remove();
            return fragment;
        };

        self.loadSVG = function (url, callback) {
            Snap.ajax(url, function (req) {
                // add more filters for trouble character here.
                let svgStr = req.responseText.replace(/\u00A0/g, " "); // remove no-break-space ASCII:160, utf16:00a0
                let fragment = Snap.parse(svgStr);
                callback(fragment);
            });
        };

        self.removeSVG = function (file) {
            self.abortFreeTransforms();
            snap.selectAll("#" + file.previewId).remove();
            self.placedDesigns.remove(file);
        };
        self.fitSVG = function (file) {
            self.abortFreeTransforms();
            var svg = snap.select("#" + file.previewId);
            var fitMatrix = new Snap.Matrix();
            fitMatrix.scale(svg.data("fitMatrix").scale);
            fitMatrix.translate(
                svg.data("fitMatrix").dx,
                svg.data("fitMatrix").dy
            );
            fitMatrix.add(svg.transform().localMatrix);
            svg.transform(fitMatrix);
            self._mark_as_misfit(file, false, svg);
            self.svgTransformUpdate(svg);

            self.showTransformHandles(file.previewId, true);

            var mb_meta = self._set_mb_attributes(svg);
        };

        /**
         * Finds dimensions (wifth, height, etc..) of an SVG
         * @param fragment
         * @returns {{width: *, height: *, viewbox: *, units_x: *, units_y: *}}
         * @private
         */
        self._getDocumentDimensionAttributes = function (fragment) {
            if (fragment.select("svg") === null) {
                root_attrs = fragment.node.attributes;
            } else {
                var root_attrs = fragment.select("svg").node.attributes;
            }
            var doc_width = null;
            var doc_height = null;
            var doc_viewbox = null;
            var units_x = null;
            var units_y = null;

            // iterate svg tag attributes
            for (var i = 0; i < root_attrs.length; i++) {
                var attr = root_attrs[i];

                // get dimensions
                if (attr.name === "width") {
                    doc_width = attr.value;
                    units_x = doc_width.replace(/[\d.]+/, "");
                }
                if (attr.name === "height") {
                    doc_height = attr.value;
                    units_y = doc_height.replace(/[\d.]+/, "");
                }
                if (attr.name === "viewBox") doc_viewbox = attr.value;
            }
            return {
                width: doc_width,
                height: doc_height,
                viewbox: doc_viewbox,
                units_x: units_x,
                units_y: units_y,
            };
        };

        self._getDocumentScaleToMM = function (declaredUnit, generator) {
            if (declaredUnit === null || declaredUnit === "") {
                //				console.log("unit '" + declaredUnit + "' not found. Assuming 'px'");
                declaredUnit = "px";
            }
            if (declaredUnit === "px" || declaredUnit === "") {
                if (generator.generator === "inkscape") {
                    let isOldInkscapeVersion = NaN;
                    try {
                        isOldInkscapeVersion= window.compareVersions(
                            // 1.1.2 (1:1.1+202202050950+0a00cf5339) -> 1.1
                            generator.version.split('.').slice(0,2).join('.'),
                            "0.91"
                        ) <= 0;
                    } catch(e) {
                        let payload = {
                            error: e.message,
                        };
                        self._sendAnalytics("inkscape_version_comparison_error", payload);
                        console.log("inkscape_version_comparison_error: ", e);
                        // In case the comparison fails, we assume the version to be above 0.91
                        // This assumption (the scaling) does not have a major impact as it has
                        // been the case in the plugin up till 0.10.1-hotfix.2
                        isOldInkscapeVersion = true;
                    }

                    if (isOldInkscapeVersion) {
                        //						console.log("old inkscape, px @ 90dpi");
                        declaredUnit = "px_inkscape_old";
                    } else {
                        //						console.log("new inkscape, px @ 96dpi");
                        declaredUnit = "px_inkscape_new";
                    }
                } else if (generator.generator === "corel draw") {
                    //					console.log("corel draw, px @ 90dpi");
                } else if (generator.generator === "illustrator") {
                    //					console.log("illustrator, px @ 72dpi");
                    declaredUnit = "px_illustrator";
                } else if (generator.generator === "unknown") {
                    //					console.log('unable to detect generator, using settings->svgDPI:', self.svgDPI());
                    declaredUnit = "px_settings";
                    self.uuconv.px_settings = self.svgDPI() / 90; // scale to our internal 90
                }
            }
            var declaredUnitValue = self.uuconv[declaredUnit];
            var scale = declaredUnitValue / self.uuconv.mm;
            //			console.log("Units: " + declaredUnit, " => scale factor to mm: " + scale);
            return scale;
        };

        self._getDocumentNamespaceAttributes = function (file) {
            if (file.select("svg") === null) {
                root_attrs = file.node.attributes;
            } else {
                var root_attrs = file.select("svg").node.attributes;
            }
            var namespaces = {};

            // iterate svg tag attributes
            for (var i = 0; i < root_attrs.length; i++) {
                var attr = root_attrs[i];

                // copy namespaces into group
                if (attr.name.indexOf("xmlns") === 0) {
                    namespaces[attr.name] = attr.value;
                    // Illustrator uses namespaces that reference a entity defined as ENTITY outside of the xml of the svg.
                    // like this: xmlns:x="&ns_extend;"
                    // We replace it to xmlns:x="ENTITYREF_ns_extend"
                    if (attr.value.match(/^&.+;$/)) {
                        if (attr.name === "xmlns") {
                            namespaces[attr.name] =
                                "http://www.w3.org/2000/svg";
                        } else if (attr.name === "xmlns:xlink") {
                            // not sure if this is important
                            namespaces[attr.name] =
                                "http://www.w3.org/1999/xlink";
                        } else {
                            namespaces[attr.name] = attr.value
                                .replace(/&/g, "ENTITYREF_")
                                .replace(/;/g, "");
                        }
                    }
                }
            }
            return namespaces;
        };

        self.highlightDesign = function (data) {
            const svgEl = $("#" + data.previewId);
            svgEl.addClass("designHighlight");
            const fileEl = $("#" + data.id);
            fileEl.addClass("designHighlight");
        };
        self.removeHighlight = function (data) {
            const svgEl = $("#" + data.previewId);
            svgEl.removeClass("designHighlight");
            const fileEl = $("#" + data.id);
            fileEl.removeClass("designHighlight");
        };

        self.splitSVG = function (elem, event, method) {
            self.abortFreeTransforms();
            let srcElem = snap.select("#" + elem.previewId);

            let split_result;
            switch (method) {
                case "stroke-color":
                    split_result = srcElem.separate_by_stroke_colors();
                    break;
                case "non-intersecting": // TODO: provide cancel check and proper progress callback
                    split_result = srcElem.separate_by_non_intersecting_bbox(
                        null,
                        function (n) {
                            console.log(
                                "Separate non intersecting shapes: ",
                                n
                            );
                        }
                    );
                    break;
                case "horizontally":
                    split_result = srcElem.separate_horizontally();
                    break;
                case "vertically":
                case "divide":
                default:
                    split_result = srcElem.separate_vertically();
                    break;
            }

            if (split_result.parts.length > 1) {
                self.removeSVG(elem);
                for (let i = 0; i < split_result.parts.length; i++) {
                    const name = elem.name + "." + (i + 1);
                    let tp = Array.prototype.concat(elem.typePath, "split");
                    let file = {
                        url: elem.url,
                        origin: elem.origin,
                        name: name,
                        typePath: tp,
                        type: "split",
                        refs: { download: elem.url },
                    };
                    const id = self.getEntryId();
                    const previewId = self.generateUniqueId(id, file);
                    let fragment = split_result.parts[i];
                    fragment.clean_gc();
                    fragment.attr({ id: previewId, "mb:id": previewId });

                    file.id = id; // list entry id
                    file.previewId = previewId;
                    file.misfit = false;

                    let mb_meta = self._set_mb_attributes(fragment);
                    // remove class which was added by mouseover in the list.
                    self.removeHighlight(file);
                    self._prepareAndInsertSVG(
                        fragment,
                        previewId,
                        elem.origin,
                        "",
                        { showTransformHandles: false, embedGCode: false },
                        { _skip: true },
                        file
                    );
                    self._listPlacedItem(file);
                }
                if (split_result.overflow) {
                    new PNotify({
                        title: gettext("Limited split result."),
                        text: gettext(
                            `Splitting this design would result in too many parts. Here are ${split_result.length} parts. You can split the last one again if necessary.`
                        ),
                        type: "info",
                        hide: true,
                    });
                }
            } else {
                let failReason = "";
                switch (method) {
                    case "stroke-color":
                        failReason = gettext("No different line colors found.");
                        break;
                    case "non-intersecting":
                        failReason = gettext(
                            "No non-intersecting shapes found."
                        );
                        break;
                    case "divide":
                    case "horizontally":
                    case "vertically":
                        failReason = gettext("Looks like a single path.");
                }
                new PNotify({
                    title: gettext("Element not splittable with this method."),
                    text:
                        gettext("Can't split this design.") + " " + failReason,
                    type: "info",
                    hide: true,
                });
            }
        };

        self.duplicateSVG = function (src) {
            self.abortFreeTransforms();
            var srcElem = snap.select("#" + src.previewId);
            var clone_id =
                srcElem.attr("mb:clone_of") ||
                self._normalize_mb_id(src.previewId);
            var newSvg = srcElem.clone();
            newSvg.clean_gc();
            let prefix = clone_id.substr(0, clone_id.indexOf("_"));
            var id = self.getEntryId(prefix);
            var file = _.cloneDeep(src); // clone from src as quicktext has additional fields here.
            var previewId = self.generateUniqueId(id, file);
            file.id = id; // list entry id
            file.previewId = previewId;
            file.misfit = false;
            file.typePath = src.typePath;
            newSvg.attr({
                id: previewId,
                "mb:id": self._normalize_mb_id(previewId),
                "mb:clone_of": clone_id,
                class: srcElem.attr("class"),
            });

            // clone filter references
            if (newSvg.attr("class").includes("userIMG")) {
                let url = self._getIMGserveUrl(file);
                self._create_img_filter(previewId);
                newSvg.children()[0].attr({
                    filter: "url(#" + self._get_img_filter_id(previewId) + ")",
                    "data-serveurl": url,
                });
            }

            // clone <textPath> references
            if (newSvg.attr("class").includes("userText")) {
                const newCurvePathId = previewId + "_baselinepath";
                let curvePathId = srcElem.select("textPath").attr("href");
                let newCurvePath = snap.select(curvePathId).clone();
                newCurvePath.attr("id", newCurvePathId);
                newSvg.select("textPath").attr({
                    textpath: newCurvePath,
                    href: `#${newCurvePathId}`,
                });
            }

            // TODO use self._prepareAndInsertSVG()
            // self._prepareAndInsertSVG(fragment, previewId, origin, '', {showTransformHandles: false, embedGCode: false}, {_skip: true}, file);

            snap.select("#userContent").append(newSvg);
            self.placeSmart(newSvg);
            self.removeHighlight(newSvg);
            self.removeHighlight(file);
            self._addClickAndHoverHandlers(newSvg, file);
            self.check_sizes_and_placements();

            self._listPlacedItem(file);
        };

        self.placeSmart = function (elem) {
            // TODO: bug - should not place outside working area
            var spacer = 2;
            var label = elem.attr("mb:origin");
            var placed = snap.selectAll("g[mb\\:origin='" + label + "']");
            var maxY = -9999;
            var minX = self.workingAreaWidthMM();
            var lowestRow = [];
            var leftest = null;
            for (var i = 0; i < placed.length; i++) {
                var item = placed[i];
                if (item.id !== elem.id) {
                    var bbox = item.getBBox();
                    if (bbox.y === maxY) {
                        lowestRow.push(item);
                    } else if (bbox.y > maxY) {
                        lowestRow = [item];
                        maxY = bbox.y;
                    }
                    if (bbox.x < minX) {
                        minX = bbox.x;
                        leftest = item;
                    }
                }
            }
            var lowestRightest = null;
            var maxX = 0;
            for (var i = 0; i < lowestRow.length; i++) {
                var item = lowestRow[i];
                var bbox = item.getBBox();
                if (bbox.x2 > maxX) {
                    maxX = bbox.x2;
                    lowestRightest = item;
                }
            }
            var lowestBBox = lowestRightest.getBBox();
            var elemBBox = elem.getBBox();
            var newX = maxX + spacer;
            var newY = lowestBBox.y;

            if (newX + elemBBox.w > self.workingAreaWidthMM()) {
                newX = leftest.getBBox().x;
                newY = lowestBBox.y2 + spacer;
            }
            var dx = newX - elemBBox.x;
            var dy = newY - elemBBox.y;
            var elemCTM = elem.transform().localMatrix;
            elemCTM.e += dx;
            elemCTM.f += dy;
            elem.transform(elemCTM);
        };

        self._addClickAndHoverHandlers = function (fragment, fileObj) {
            // TODO check why called twice on add?
            //			console.log("clickhandlers, caller", self._addClickAndHoverHandlers.caller);
            // add hover handler to highlight design and list entry
            fragment.unmouseover();
            fragment.mouseover(function () {
                self.highlightDesign(fileObj);
            });
            fragment.unmouseout();
            fragment.mouseout(function () {
                self.removeHighlight(fileObj);
            });

            // adds onclick handler
            fragment.transformable(self._updateTransformationButtons); // onclickCallback
            fragment.mbtRegisterOnTransformCallback(self.svgTransformUpdate);
            fragment.mbtRegisterBeforeTransformCallback(function () {
                fragment.clean_gc();
            });
            fragment.mbtRegisterAfterTransformCallback(function () {
                var mb_meta = self._set_mb_attributes(fragment);
            });
            setTimeout(function () {
                fragment.mbtOnTransform();
            }, 200);
        };

        /**
         * toggle transformation handles
         * @param previewId or file
         */
        self.toggleTransformHandles = function (previewId) {
            if (typeof previewId === "object" && previewId.previewId) {
                previewId = previewId.previewId;
            }
            snap.mbtransform.toggleElement("#" + previewId);
            self._updateTransformationButtons();
        };

        self._updateTransformationButtons = function () {
            // TODO: call this on direct click on design
            $("#wa_filelist .entry").removeClass("mbtSelected");
            const items = snap.mbtransform.getSelection();
            for (var i = 0; i < items.length; i++) {
                const design = items[i];
                const file = self._getFileObjectForSvg(design);
                $("#" + file.id).addClass("mbtSelected");
            }
        };

        /**
         * Show or hide transformation handles
         * @param previewId or file
         * @param show true or false
         */
        self.showTransformHandles = function (previewId, show) {
            if (typeof previewId === "object" && previewId.previewId) {
                previewId = previewId.previewId;
            }
            if (show) {
                snap.mbtransform.activate("#" + previewId);
            } else {
                snap.mbtransform.deactivate();
            }
            self._updateTransformationButtons();
        };

        self.transformReset = function (previewId) {
            if (typeof previewId === "object" && previewId.previewId) {
                previewId = previewId.previewId;
            }
            self.abortFreeTransforms();
            const selector = `#${previewId}`;
            snap.mbtransform.reset_transform(selector);
            self.svgTransformUpdate(snap.select(selector));
        };

        self.svgTransformUpdate = function (svg) {
            const iM = svg.data(snap.mbtransform.INITIAL_MATRIX);
            const cM = svg.transform().localMatrix;
            const isTransformed =
                iM !== undefined &&
                (iM.a !== cM.a ||
                    iM.b !== cM.b ||
                    iM.c !== cM.c ||
                    iM.d !== cM.d ||
                    iM.e !== cM.e ||
                    iM.f !== cM.f);
            const transform = cM.split();
            const rot = ((transform.rotate + 180 + 720) % 360) - 180; // ensures -180° to 180°
            //			const shear = transform.shear; // not in use yet

            const globalScale = self.scaleMatrix().a;
            const bbox = svg.getBBox();
            const tx = bbox.x * globalScale;
            const ty = self.workingAreaHeightMM() - bbox.y2 * globalScale;
            const scalex = Math.abs(transform.scalex);
            const scaley = Math.abs(transform.scaley);
            const isMirrored = transform.scalex * transform.scaley < 0;
            //			const horizontal = bbox.width * globalScale;
            //			const vertical = bbox.height * globalScale;
            const horizontal = bbox.width * Math.sign(scalex) * globalScale;
            const vertical = bbox.height * Math.sign(scaley) * globalScale;

            const id = svg.attr("id");
            const label_id = id.substr(0, id.indexOf("-"));
            $("#" + label_id).toggleClass("isTransformed", isTransformed);
            $("#" + label_id).toggleClass("isMirrored", isMirrored);
            $("#" + label_id + " .translation").val(
                `${tx.toFixed(1)}, ${ty.toFixed(1)}`
            );
            $("#" + label_id + " .horizontal").val(
                `${horizontal.toFixed(1)} mm`
            );
            $("#" + label_id + " .vertical").val(`${vertical.toFixed(1)} mm`);
            $("#" + label_id + " .rotation").val(`${rot.toFixed(1)} °`);
            $("#" + label_id + " .horizontal_percent").val(
                `${(scalex * 100).toFixed(1)} %`
            );
            $("#" + label_id + " .vertical_percent").val(
                `${(scaley * 100).toFixed(1)} %`
            );
            self.check_sizes_and_placements();
        };

        self.svgManualTranslate = function (data, event) {
            if (
                event.keyCode === 13 ||
                event.type === "blur" ||
                event.keyCode === 38 ||
                event.keyCode === 40
            ) {
                const svg = snap.select("#" + data.previewId);
                const nt = WorkingAreaHelper.splitStringToTwoValues(
                    event.target.value
                );
                if (nt) {
                    const globalScale = self.scaleMatrix().a;
                    self.abortFreeTransforms();
                    let ntx = nt[0] / globalScale;
                    let nty =
                        (self.workingAreaHeightMM() - nt[1]) / globalScale;

                    snap.mbtransform.manualTransform(svg, { tx: ntx, ty: nty }); // absolute translation
                    self.check_sizes_and_placements();
                } else {
                    // reset to previous value
                    svg.mbtOnTransform();
                    svg.mbtAfterTransform();
                }
            }
        };
        self.svgManualRotate = function (data, event) {
            if (
                event.keyCode === 13 ||
                event.type === "blur" ||
                event.keyCode === 38 ||
                event.keyCode === 40
            ) {
                self.abortFreeTransforms();
                var svg = snap.select("#" + data.previewId);
                var newRotate = WorkingAreaHelper.parseFloatTolerant(
                    event.target.value
                );
                const oldRotation = svg.transform().localMatrix.split().rotate;
                snap.mbtransform.manualTransform(svg, {
                    angle: newRotate - oldRotation,
                }); // relative angle
                self.check_sizes_and_placements();
            }
        };
        self.svgManualMirror = function (data, event) {
            if (event.type === "click") {
                self.abortFreeTransforms();
                const svg = snap.select("#" + data.previewId);
                snap.mbtransform.manualTransform(svg, {
                    scalex: -1,
                    proportional: false,
                }); // relative Scale
                self.check_sizes_and_placements();
            }
        };
        self.svgManualWidth = function (data, event) {
            if (
                event.keyCode === 13 ||
                event.type === "blur" ||
                event.keyCode === 38 ||
                event.keyCode === 40
            ) {
                self.abortFreeTransforms();
                const svg = snap.select(`#${data.previewId}`);
                const isProp = $(`#${data.id} .file_list_entry`).hasClass(
                    "scale_proportional"
                );
                const isMirrored = $(`#${data.id}`).hasClass("isMirrored");
                const value = WorkingAreaHelper.parseFloatTolerant(
                    event.target.value
                );
                const lm = svg.transform().localMatrix;
                const currentSx = Math.sqrt(lm.a * lm.a + lm.b * lm.b); // rotation independent scalex factor
                const currentWidth = svg.getBBox().width;
                if (value !== 0) {
                    if (event.target.classList.contains("unit_mm")) {
                        snap.mbtransform.manualTransform(svg, {
                            width: value,
                            proportional: isProp,
                        }); // absolute width
                    } else if (
                        event.target.classList.contains("unit_percent")
                    ) {
                        const newWidth =
                            ((currentWidth / Math.abs(currentSx)) * value) /
                            100.0;
                        if (Math.abs(newWidth) < 0.1)
                            newWidth = Math.sign(newWidth) * 0.1; // avoid NaN for too small values
                        snap.mbtransform.manualTransform(svg, {
                            width: newWidth,
                            proportional: isProp,
                        }); // absolute width
                    }
                    self.check_sizes_and_placements();
                } else {
                    console.warn("Width can't be 0"); // TODO: reset transform?
                }
            }
            return false;
        };
        self.svgManualHeight = function (data, event) {
            if (
                event.keyCode === 13 ||
                event.type === "blur" ||
                event.keyCode === 38 ||
                event.keyCode === 40
            ) {
                self.abortFreeTransforms();
                const svg = snap.select("#" + data.previewId);
                const isProp = $(`#${data.id} .file_list_entry`).hasClass(
                    "scale_proportional"
                );
                const value = WorkingAreaHelper.parseFloatTolerant(
                    event.target.value
                );
                const lm = svg.transform().localMatrix;
                const currentSy = Math.sqrt(lm.c * lm.c + lm.d * lm.d); // rotation independent scaley factor
                const currentHeight = svg.getBBox().height;
                if (value !== 0) {
                    if (event.target.classList.contains("unit_mm")) {
                        snap.mbtransform.manualTransform(svg, {
                            height: value,
                            proportional: isProp,
                        }); // absolute height
                    } else if (
                        event.target.classList.contains("unit_percent")
                    ) {
                        const newHeight =
                            ((currentHeight / Math.abs(currentSy)) * value) /
                            100.0;
                        if (Math.abs(newHeight) < 0.1)
                            newHeight = Math.sign(newHeight) * 0.1; // avoid NaN for too small values
                        snap.mbtransform.manualTransform(svg, {
                            height: newHeight,
                            proportional: isProp,
                        }); // relative scale
                    }
                    self.check_sizes_and_placements();
                } else {
                    console.warn("Height can't be 0"); // TODO: reset transform?
                }
            }
        };

        self.svgManualUnitToggle = function (data, event) {
            $("#" + data.id).toggleClass("show_percent");
        };
        self.svgManualProportionalToggle = function (data, event) {
            event.preventDefault();
            $(`#${data.id} .file_list_entry`).toggleClass("scale_proportional");
            //            $(event.target).toggleClass("scale_proportional");
        };
        self.svgManualMultiply = function (data, event) {
            if (
                event.keyCode === 13 ||
                event.type === "blur" ||
                event.keyCode === 38 ||
                event.keyCode === 40
            ) {
                const colsRowsStr = event.target.value;
                const result = self._svgMultiplyUpdate(data, colsRowsStr);
                event.target.value = result;
            }
        };
        self._svgMultiplyUpdate = function (data, colsRowsStr) {
            self.abortFreeTransforms();
            var svg = snap.select("#" + data.previewId);
            let distX = 2;
            let distY = 2;
            let cols = 1;
            let rows = 1;
            let gridValueCount = 2;
            if (colsRowsStr !== undefined) {
                var gridValues = colsRowsStr.split(/[^0-9.]+/);
                gridValueCount = gridValues.length;
                cols = Math.round(parseFloat(gridValues[0])) || 1;
                rows = Math.round(parseFloat(gridValues[1])) || 1;
                distX = parseFloat(gridValues[2]) || 2;
                distY = parseFloat(gridValues[3]) || distX;
            }
            svg.grid(cols, rows, distX, distY);
            var mb_meta = self._set_mb_attributes(svg);
            svg.mbtOnTransform();
            self.check_sizes_and_placements();
            if (distX === 2 && distY === 2 && gridValueCount === 2) {
                return `${cols}×${rows}`;
            } else {
                if (distX === distY && gridValueCount === 3) {
                    return `${cols}×${rows} ${distX}`;
                } else {
                    return `${cols}×${rows} ${distX}⬌${distY}`;
                }
            }
        };
        self.imgManualAdjust = function (data, event) {
            if (
                event.type === "input" ||
                event.type === "blur" ||
                event.type === "keyUp"
            ) {
                event.target.dataset.value = event.target.value; // updates tooltips

                self.abortFreeTransforms();
                var newContrast = $("#" + data.id + " .contrast").val(); // 0..2, 1 means no adjustment
                var newBrightness = $("#" + data.id + " .brightness").val(); // -1..1, 0 means no adjustment
                var newGamma = $("#" + data.id + " .gamma").val(); // // 0.2..1.8, 1 means no adjustment
                var contrastVal = parseFloat(newContrast);
                var brCorrection = (1 - contrastVal) / 2; // 0.5..-0.5 // TODO investigate if we should take gamma into account as well
                var brightnessVal = parseFloat(newBrightness) + brCorrection;
                var gammaVal = parseFloat(newGamma);
                self.set_img_contrast(
                    data.previewId,
                    contrastVal,
                    brightnessVal,
                    gammaVal
                );
            }
        };

        self.imgManualSharpen = function (data, event) {
            if (
                event.type === "input" ||
                event.type === "blur" ||
                event.type === "keyUp"
            ) {
                event.target.dataset.value = event.target.value; // updates tooltips
                self.abortFreeTransforms();
                var newVal = $("#" + data.id + " .sharpen").val(); // 0..10, 0 means no adjustment
                var sharpenVal = parseFloat(newVal);
                self.set_img_sharpen(data.previewId, sharpenVal);
            }
        };

        self.imgManualCrop = function (data, event) {
            if (
                event.type === "input" ||
                event.type === "blur" ||
                event.type === "keyUp"
            ) {
                let t = parseFloat($("#" + data.id + " .crop_top").val());
                let l = parseFloat($("#" + data.id + " .crop_left").val());
                let r = parseFloat($("#" + data.id + " .crop_right").val());
                let b = parseFloat($("#" + data.id + " .crop_bottom").val());
                self.set_img_crop(data.previewId, t, l, r, b);
                if (l + r > 99)
                    $("#" + data.id + " .crop_right").val(100 - l - 1);
                if (t + b > 99)
                    $("#" + data.id + " .crop_bottom").val(100 - t - 1);
            }
        };

        self.outsideWorkingArea = function (svg) {
            var waBB = snap.select("#coordGrid").getBBox();
            var svgBB = svg.getBBox();

            var tooWide = svgBB.w > waBB.w;
            var tooHigh = svgBB.h > waBB.h;
            var scale = 1;
            if (tooWide || tooHigh) {
                scale = Math.min(waBB.w / svgBB.w, waBB.h / svgBB.h) - 0.0001; // scale minimal smaller to avoid rounding errors
            }

            var dx = 0;
            var dy = 0;
            var outside = false;
            if (svgBB.x < waBB.x) {
                // outside on the left
                dx = -svgBB.x + 0.01;
                outside = true;
            } else if (svgBB.x2 > waBB.x2) {
                // outside on the right
                dx = -svgBB.x2 + waBB.x2 - 0.01;
                outside = true;
            }
            if (svgBB.y < waBB.y) {
                dy = -svgBB.y + 0.01;
                outside = true;
            } else if (svgBB.y2 > waBB.y2) {
                dy = -svgBB.y2 + waBB.y2 - 0.01;
                outside = true;
            }

            return {
                oversized: tooWide || tooHigh,
                outside: outside,
                scale: scale,
                dx: dx,
                dy: dy,
            };
        };

        self.svg_contains_unsupported_element_warning = function (elemName) {
            elemName = elemName.replace("\\:", ":");
            var error =
                "<p>" +
                _.sprintf(
                    gettext(
                        "The SVG file contains unsupported elements: '%(elemName)s' These elements got removed."
                    ),
                    { elemName: elemName }
                ) +
                "</p>";
            new PNotify({
                title: _.sprintf(
                    gettext("Unsupported elements in SVG: '%(elemName)s'"),
                    { elemName: elemName }
                ),
                text: error,
                type: "warn",
                hide: false,
            });
        };

        self.svg_contains_text_warning = function (svg) {
            var error =
                "<p>" +
                _.sprintf(
                    gettext(
                        "The SVG file contains text elements.%(br)sIf you want to laser just their outlines,%(br)splease convert them to paths.%(br)sOtherwise they will be engraved with infill."
                    ),
                    { br: "<br/>" }
                ) +
                "</p>";
            new PNotify({
                title: gettext("Text elements found"),
                text: error,
                type: "warn",
                hide: false,
                buttons: {
                    sticker: false,
                },
            });
        };

        self.svg_contains_online_style_warning = function (svg) {
            var error =
                "<p>" +
                gettext(
                    "The SVG file contained style elements with online references. Since online references are not supported, we removed them. The image might look a bit different now."
                ) +
                "</p>";
            new PNotify({
                title: gettext("Style elements removed"),
                text: error,
                type: "warn",
                hide: false,
                buttons: {
                    sticker: false,
                },
            });
        };

        self.file_not_readable = function () {
            var error =
                "<p>" +
                _.sprintf(
                    gettext(
                        "The selected design file can not be handled. Please make sure it is a valid design file."
                    )
                ) +
                "</p>";
            new PNotify({
                title: gettext("File error."),
                text: error,
                type: "error",
                hide: false,
                buttons: {
                    sticker: false,
                },
            });
        };

        self.empty_svg = function () {
            var error =
                "<p>" +
                _.sprintf(
                    gettext(
                        "The selected design file does not have any content."
                    )
                ) +
                "</p>";
            new PNotify({
                title: gettext("Empty File."),
                text: error,
                type: "error",
                hide: false,
                buttons: {
                    sticker: false,
                },
            });
        };

        self.svg_place_general_error = function (stack) {
            var error =
                "<p>" +
                _.sprintf(
                    gettext(
                        "An unknown error occurred while processing this design file."
                    )
                ) +
                "</p>";
            error +=
                "<p>" +
                _.sprintf(
                    gettext(
                        "Please try reloading this browser window and try again. If this error remains, contact the Mr Beam Support Team. Make sure you provide the error message below together with the design file you're trying to process."
                    )
                ) +
                "</p>";
            error +=
                "<p><strong>" +
                _.sprintf(gettext("Error")) +
                ':</strong><br/><textarea spellcheck="false" style="width: 95%; background-color: inherit; font-size: 12px; line-height: normal; height: 70px; color: inherit; background-color: inherit;">' +
                stack +
                "</textarea></p>";
            new PNotify({
                title: gettext("Error"),
                text: error,
                type: "error",
                hide: false,
                buttons: {
                    sticker: false,
                },
            });
        };

        self.placeIMG = function (file, textMode) {
            var start_ts = Date.now();
            var url = self._getIMGserveUrl(file);
            self.spinnerShow();
            var img = new Image();
            textMode = textMode || false;
            img.onload = function () {
                var duration_load = Date.now() - start_ts;
                start_ts = Date.now();

                var wpx = this.width;
                var hpx = this.height;

                var dimMM = self.getUsefulDimensions(wpx, hpx);
                var wMM = dimMM[0];
                var hMM = dimMM[1];

                var y = self.workingAreaHeightMM() - hMM;
                var imgWrapper = snap.group();
                var newImg = imgWrapper.image(url, 0, y, wMM, hMM); //.attr({transform: 'matrix(1,0,0,-1,0,'+hMM+')'});
                var id = self.getEntryId();
                var previewId = self.generateUniqueId(id, file); // appends # if multiple times the same design is placed.
                self._create_img_filter(previewId);
                newImg.attr("data-serveurl", url);
                if (!window.mrbeam.browser.is_safari) {
                    // svg filters don't really work in safari: https://github.com/mrbeam/MrBeamPlugin/issues/586
                    newImg.attr(
                        "filter",
                        "url(#" + self._get_img_filter_id(previewId) + ")"
                    );
                }
                var imgWrapper = snap.group().attr({
                    id: previewId,
                    "mb:id": self._normalize_mb_id(previewId),
                    class: "userIMG",
                    "mb:origin": url,
                });
                if (textMode) {
                    imgWrapper.attr("style", "filter: url(#scan_text_mode)");
                }

                file.id = id;
                file.previewId = previewId;
                file.url = url;
                file.subtype = "bitmap";
                self._listPlacedItem(file);

                imgWrapper.append(newImg);
                // TODO use self._prepareAndInsertSVG()
                // self._prepareAndInsertSVG(fragment, previewId, origin, '', {showTransformHandles: false, embedGCode: false}, {_skip: true}, file);

                snap.select("#userContent").append(imgWrapper);
                self._addClickAndHoverHandlers(imgWrapper, file);

                // analytics
                let analyticsData = {
                    id: id,
                    pixel_width: wpx,
                    pixel_height: hpx,
                    size: file.size,
                    duration_load: duration_load,
                    duration_processing: Date.now() - start_ts,
                    file_type: file.display.split(".").slice(-1)[0],
                    filename_hash: file.hash,
                };
                self._analyticsPlaceImage(analyticsData);

                // remove Activity Spinner
                self.spinnerHide();
            };
            img.src = url;
        };

        self.placeImgUrl = function (url) {
            const name = "Data URL.png";
            let file = {
                date: Date.now(),
                display: "URL: " + name,
                name: name,
                origin: "url",
                path: "url",
                refs: { download: url, resource: url },
                size: url.length,
                type: "model",
                typePath: (2)[("model", "image")],
                weight: 1,
            };
            self.placeIMG(file, true);
        };

        self.removeIMG = function (file) {
            self._remove_img_filter(file.previewId);
            self.removeSVG(file);
        };

        self._create_img_filter = function (previewId) {
            var id = self._get_img_filter_id(previewId);
            var str =
                "<feComponentTransfer class='contrast_filter' in='colormatrix' result='contrast_result'>" +
                "<feFuncR type='gamma' amplitude='1' offset='0' exponent='1'/>" +
                "<feFuncG type='gamma' amplitude='1' offset='0' exponent='1'/>" +
                "<feFuncB type='gamma' amplitude='1' offset='0' exponent='1'/>" +
                "<feFuncA type='identity' />" +
                "</feComponentTransfer>" +
                "<feColorMatrix class='gray_scale_filter' type='saturate' values='0' in='contrast_result' result='gray_scale'/>" +
                "<feConvolveMatrix class='sharpening_filter' order='3 3' kernelMatrix='0 0 0 0 1 0 0 0 0' divisor='1' bias='0' targetX='1' targetY='1' edgeMode='duplicate' preserveAlpha='true' in='gray_scale' result='sharpened'/>";
            snap.filter(str).attr({
                id: id,
                filterUnits: "objectBoundingBox",
                x: "0%",
                y: "0%",
                width: "100%",
                height: "100%",
            });
            return id;
        };

        self._remove_img_filter = function (previewId) {
            var id = self._get_img_filter_id(previewId);
            var filter = snap.select("#" + id);
            if (filter !== null) filter.remove();
        };

        self._get_img_filter_id = function (previewId) {
            return "filter_" + previewId.replace("-", "__");
        };

        self.set_img_contrast = function (
            previewId,
            contrastValue,
            brightnessValue,
            gammaValue
        ) {
            if (
                isNaN(contrastValue) ||
                isNaN(brightnessValue) ||
                isNaN(gammaValue)
            ) {
                return;
            }
            var filter = snap.select("#" + self._get_img_filter_id(previewId));
            filter.select("feFuncR").attr({
                amplitude: contrastValue,
                offset: brightnessValue,
                exponent: gammaValue,
            });
            filter.select("feFuncG").attr({
                amplitude: contrastValue,
                offset: brightnessValue,
                exponent: gammaValue,
            });
            filter.select("feFuncB").attr({
                amplitude: contrastValue,
                offset: brightnessValue,
                exponent: gammaValue,
            });
        };

        self.set_img_sharpen = function (previewId, value) {
            if (isNaN(value)) {
                return;
            }
            // 3x3 matrix (1px radius) looks like this:
            // -i/9  -i/9  -i/9
            // -i/9 1+8i/9 -i/9
            // -i/9  -i/9  -i/9
            // i is the intensity factor: 0..40, 0 means identity projection.
            var n = -value / 9.0;
            var c = 1 + (8 * value) / 9.0;
            var matrix = [n, n, n, n, c, n, n, n, n].join(" ");
            var filter = snap.select("#" + self._get_img_filter_id(previewId));
            filter.select("feConvolveMatrix").attr({ kernelMatrix: matrix });
        };

        self.set_img_crop = function (previewId, top, left, right, bottom) {
            let filter = snap.select("#" + self._get_img_filter_id(previewId));
            let x = Math.min(left, 100 - right);
            let y = Math.min(top, 100 - bottom);
            let width = Math.max(100 - right - left, 0);
            let height = Math.max(100 - top - bottom, 0);
            filter.attr({
                x: left + "%",
                y: top + "%",
                width: width + "%",
                height: height + "%",
            });
        };

        self.moveSelectedDesign = function (ifX, ifY) {
            const selection = snap.mbtransform.getSelection();
            if (selection.length === 0) {
                console.info("No selection to move.");
                return;
            }
            var diff = 2;
            var globalScale = self.scaleMatrix().a;
            var nx = diff * ifX;
            var ny = diff * ifY;
            var ntx = nx / globalScale;
            var nty = ny / globalScale;

            snap.mbtransform.manualTransform(selection, {
                tx_rel: ntx,
                ty_rel: nty,
            });
        };

        self.removeSelectedDesign = function () {
            const selection = snap.mbtransform.getSelection();
            for (var s = 0; s < selection.length; s++) {
                var design = selection[s];
                const fileObj = self._getFileObjectForSvg(design);
                if (fileObj !== null) {
                    self.abortFreeTransforms();
                    self.removeSVG(fileObj);
                }
            }
        };

        self._getFileObjectForSvg = function (svg) {
            const previewId = svg.attr("mb:id");

            for (var i = 0; i < self.placedDesigns().length; i++) {
                var file = self.placedDesigns()[i];
                if (file.previewId === previewId) {
                    return file;
                }
            }
            console.log(
                "file object not in placedDesigns. previewId: " + previewId
            );
            return null;
        };

        self.getUsefulDimensions = function (wpx, hpx) {
            var maxWidthMM = wpx * 0.25; // TODO parametrize
            var maxHeightMM = hpx * 0.25; // TODO parametrize
            var aspectRatio = wpx / hpx;
            var destWidthMM = Math.min(
                self.workingAreaWidthMM() - 2,
                maxWidthMM
            );
            var destHeightMM = Math.min(
                self.workingAreaHeightMM() - 2,
                maxHeightMM
            );
            if (destWidthMM / aspectRatio > destHeightMM) {
                destWidthMM = destHeightMM * aspectRatio;
            } else {
                destHeightMM = destWidthMM / aspectRatio;
            }
            return [destWidthMM, destHeightMM];
        };

        // TODO not used? Check removal
        self.getDocumentDimensionsInPt = function (
            doc_width,
            doc_height,
            doc_viewbox
        ) {
            if (doc_width === null || doc_width === "100%") {
                // assume defaults if not set
                if (doc_viewbox !== null) {
                    var parts = doc_viewbox.split(" ");
                    if (parts.length === 4) {
                        doc_width = parts[2];
                    }
                }
                if (doc_width === "100%") {
                    doc_width = 744.09; // 210mm @ 90dpi
                }
                if (doc_width === null) {
                    doc_width = 744.09; // 210mm @ 90dpi
                }
            }
            if (doc_height === null || doc_height === "100%") {
                // assume defaults if not set
                if (doc_viewbox !== null) {
                    var parts = doc_viewbox.split(" ");
                    if (parts.length === 4) {
                        doc_height = parts[3];
                    }
                }
                if (doc_height === "100%") {
                    doc_height = 1052.3622047; // 297mm @ 90dpi
                }
                if (doc_height === null) {
                    doc_height = 1052.3622047; // 297mm @ 90dpi
                }
            }

            var widthPt = self.unittouu(doc_width);
            var heightPt = self.unittouu(doc_height);

            return [widthPt, heightPt];
        };

        self.getDocumentViewBoxMatrix = function (dim, vbox) {
            if (dim.width === null || dim.height === null) {
                return [
                    [1, 0, 0],
                    [0, 1, 0],
                    [0, 0, 1],
                ];
            }
            if (vbox !== null) {
                var width = parseFloat(dim.width);
                var height = parseFloat(dim.height);
                var parts = vbox.split(" ");
                if (parts.length === 4) {
                    var offsetVBoxX = parseFloat(parts[0]);
                    var offsetVBoxY = parseFloat(parts[1]);
                    var widthVBox = parseFloat(parts[2]);
                    var heightVBox = parseFloat(parts[3]);

                    var fx = width / widthVBox;
                    var fy = height / heightVBox;
                    const finalF = Math.min(fx, fy);
                    var dx = offsetVBoxX * fx;
                    var dy = offsetVBoxY * fy;
                    return [
                        [finalF, 0, 0],
                        [0, finalF, 0],
                        [dx, dy, 1],
                    ];
                }
            }
            return [
                [1, 0, 0],
                [0, 1, 0],
                [0, 0, 1],
            ];
        };

        //a dictionary of unit to user unit conversion factors
        self.uuconv = {
            px: 1, // Reference @ 90 dpi
            in: 90.0,
            pt: 1.25,
            px_inkscape_old: 1, // 90 dpi // < Inkscape v0.91
            px_inkscape_new: 0.9375, // 96 dpi
            px_illustrator: 1.25, // 72 dpi
            mm: 3.5433070866,
            cm: 35.433070866,
            m: 3543.3070866,
            km: 3543307.0866,
            pc: 15.0,
            yd: 3240,
            ft: 1080,
        };

        // Returns userunits given a string representation of units in another system'''
        self.unittouu = function (string) {
            var unit_re = new RegExp(
                "(" + Object.keys(self.uuconv).join("|") + ")$"
            );

            var unit_factor = 1;
            var u_match = string.match(unit_re);
            if (u_match !== null) {
                var unit = string.substring(u_match.index);
                string = string.substring(0, u_match.index);
                if (self.uuconv[unit]) unit_factor = self.uuconv[unit];
            }

            var p = parseFloat(string);
            if (p) return p * unit_factor;
            return 0;
        };

        self._getSVGserveUrl = function (file) {
            if (file && file["refs"] && file["refs"]["download"]) {
                var url = file.refs.download;
                if (!url.startsWith("data:")) {
                    // be sure to avoid caching.
                    url = url + "?" + Date.now();
                }
                return url;
            }
        };

        self._getIMGserveUrl = function (file) {
            return self._getSVGserveUrl(file);
        };

        self.templateFor = function (data) {
            if (data.type === "model" || data.type === "machinecode") {
                var extension = data.name.split(".").pop().toLowerCase();
                if (extension === "svg") {
                    return "wa_template_" + data.type + "_svg";
                } else if (extension === "dxf") {
                    return "wa_template_" + data.type + "_svg";
                } else if (_.contains(self.SUPPORTED_IMAGE_TYPES, extension)) {
                    return "wa_template_" + data.type + "_img";
                } else {
                    return "wa_template_" + data.type;
                }
            } else if (data.type === "recentjob" || data.type === "split") {
                return "wa_template_model_svg";
            } else if (data.type === "quicktext") {
                return "wa_template_quicktext";
            } else if (data.type === "quickshape") {
                return "wa_template_quickshape";
            } else {
                return "wa_template_dummy";
            }
        };

        self.getEntryId = function (prefix, length) {
            prefix = prefix || "wa";
            return prefix + "_" + WorkingAreaHelper.getHumanReadableId(length);
        };

        self.init = function () {
            // init snap.svg
            snap = Snap("#area_preview");
            self.px2mm_factor.subscribe(function (newVal) {
                if (!isNaN(newVal)) {
                    MRBEAM_PX2MM_FACTOR_WITH_ZOOM = newVal;
                    self.draw_coord_grid();
                }
            });
            self.workingAreaHeightMM.subscribe(function (newVal) {
                if (!isNaN(newVal)) self.draw_coord_grid();
            });
            self.workingAreaWidthMM.subscribe(function (newVal) {
                if (!isNaN(newVal)) self.draw_coord_grid();
            });

            $("#coordGrid").on("click", function (event) {
                self.abortFreeTransforms();
            });

            $("#coordGrid").on("dblclick", function (event) {
                self.move_laser({}, event);
            });
            snap.mbtransform_init();
            snap.debug_init();
        };

        self.draw_coord_grid = function () {
            if (snap === null) return;
            var grid = snap.select("#coordGrid");
            var w = self.workingAreaWidthMM();
            var h = self.workingAreaHeightMM();

            if (
                grid.attr("width") !== w ||
                grid.attr("height") !== h ||
                grid.attr("fill") === "none"
            ) {
                snap.selectAll("#coordPattern").remove();
                var max_lines = 20;

                var linedist =
                    Math.floor(
                        Math.max(
                            self.workingAreaWidthMM(),
                            self.workingAreaHeightMM()
                        ) /
                            (max_lines * 10)
                    ) * 10;
                var yPatternOffset = self.workingAreaHeightMM() % linedist;
                if (isNaN(yPatternOffset)) {
                    yPatternOffset = 0;
                }

                var marker = snap.path("M9,10h2M10,9v2").attr({
                    id: "coord_pattern_marker",
                    stroke: "#eeeeee",
                    fill: "none",
                    "stroke-width": "0.5",
                });
                //<path d="M8,10h4M10,8v4" stroke="#e25303" fill="none" stroke-width="0.5"></path>

                // dot pattern
                var p = marker.pattern(0, 0, linedist, linedist);
                p.attr({
                    id: "coordPattern",
                    x: linedist / 2,
                    y: linedist / 2 + yPatternOffset,
                });

                grid.attr({
                    width: w,
                    height: h,
                    fill: p,
                });
            }
        };

        self.generateUniqueId = function (idBase, file) {
            var suffix = "";
            if (file) {
                var suffix = self.countPlacements(file);
            } else {
                suffix = self.id_counter++;
            }

            var suffix = 0;
            var id = idBase + "-" + suffix;
            while (snap.select("#" + id) !== null) {
                suffix += 1;
                id = idBase + "-" + suffix;
            }
            return id;
        };

        self.abortFreeTransforms = function () {
            snap.mbtransform.deactivate();
            self._updateTransformationButtons();
        };

        /**
         *
         * @param {boolean} fillAreas: flag if rastering has to be done or not
         * @param {number} pxPerMM: resolution used for rastering text, images and filled paths
         * @returns {object}: {renderedSvg: result as string, jobTimeEstimationData: pathLengths & image summary, renderParams: params used for creation}
         */
        self.getCompositionSVG = async function (fillAreas, pxPerMM) {
            // stop ongoing operations
            self.abortFreeTransforms();

            self.spinnerShow();
            const renderStart = Date.now();
            console.log(`Frontend rendering startet ...`);

            // create svg to do the rendering within
            var wMM = self.workingAreaWidthMM();
            var hMM = self.workingAreaHeightMM();
            var wPT = wMM * self.workingAreaDPItoMM; // TODO ... switch to 96dpi ? Or even to mm?
            var hPT = hMM * self.workingAreaDPItoMM;
            var compSvg = self.getNewSvg("compSvg", wPT, hPT);
            compSvg.attr("viewBox", `0 0 ${wMM} ${hMM}`);
            var namespaces = self._getDocumentNamespaceAttributes(snap);
            compSvg.attr(namespaces);
            var attrs = {};
            var content = compSvg.g(attrs);

            // render paths and embed the resulting gcode
            snap.select("#userContent").embed_gc(
                self.flipYMatrix(),
                self.gc_options(),
                self.gc_meta
            );

            // copy all stuff placed by the user on the working area to the compSvg, cleanup afterwards and fill <defs> tag and fix references
            var userContent = snap.select("#userContent").clone();
            content.append(userContent);
            compSvg.selectAll(".deleteBeforeRendering").remove();
            const targetDefs = compSvg.select("svg>defs");

            // if text in document embed the fonts as dataUris, copy textPaths and fix id references
            if (userContent.selectAll(".userText").length > 0) {
                // embed textPaths
                const allTextPaths = snap.selectAll(
                    "defs>.quicktext_curve_path"
                );
                for (let i = 0; i < allTextPaths.length; i++) {
                    const tp = allTextPaths[i];
                    const original_id = tp.attr("id");
                    const clone = tp.clone();
                    const destTextPath = clone.appendTo(targetDefs);
                    destTextPath.attr({
                        id: original_id,
                        "mb:id": original_id,
                    });
                }

                const strokedText = userContent.selectAll(
                    '.userText text[stroke^="#"]'
                );
                strokedText.forEach((t) => {
                    const x = t.trace();
                });
            }

            // for bitmaps: embed filters
            // copy defs for filters (e.g. imgCropping, imgSharpening, etc...)
            var originalFilters = snap.selectAll("defs>filter");
            for (let i = 0; i < originalFilters.length; i++) {
                const original_id = originalFilters[i].attr("id");
                const clone = originalFilters[i].clone();
                const destFilter = clone.appendTo(targetDefs);
                destFilter.attr({ id: original_id, "mb:id": original_id });
            }

            // embed Images
            const allEmbeddedImages = await content.embedAllImages();
            let svgWithRenderedInfill = await self.rasterInfill(
                compSvg,
                fillAreas,
                pxPerMM
            );

            // console.log(`svgWithRenderedInfill ${svgWithRenderedInfill}}`);
            const svgStr = self._finalizeBackendSVG(
                svgWithRenderedInfill,
                namespaces
            );

            const length_summary = self.get_gc_length_summary(compSvg);
            // console.log(length_summary);
            $("#compSvg").remove();

            // hide spinner
            const renderEnd = Date.now();
            console.log(
                `Frontend rendering finished in ${
                    renderEnd - renderStart
                } millis`
            );
            self.spinnerHide();

            const params = {
                fillAreas: fillAreas,
                pxPerMM: pxPerMM,
                wMM: wMM,
                hMM: hMM,
                wPT: wPT,
                hPT: hPT,
                gcFlipMatrix: self.flipYMatrix(),
                gcOptions: self.gc_options(),
                gcMeta: self.gc_meta,
            };
            return {
                renderedSvg: svgStr,
                jobTimeEstimationData: length_summary,
                renderParams: params,
            };
        };

        self._finalizeBackendSVG = function (compSvg, namespaces) {
            // TODO check if viewbox, naespaces are already handled by getCompositionSVG()
            // set viewBox
            const wMM = self.workingAreaWidthMM();
            const hMM = self.workingAreaHeightMM();
            const viewBox = `0 0 ${wMM} ${hMM}`;
            compSvg.attr({ viewBox: viewBox });

            // ensure these namespaces are always present
            namespaces["xmlns"] = "http://www.w3.org/2000/svg";
            namespaces["xmlns:mb"] = "http://www.mr-beam.org/mbns";
            namespaces["xmlns:xlink"] = "http://www.w3.org/1999/xlink";
            compSvg.attr(namespaces);

            // add version and conversion info
            const gc_options_str = self
                .gc_options_as_string()
                .replace(/"/g, '"');
            compSvg.attr({
                "mb:beamOS_version": MRBEAM_PLUGIN_VERSION,
                "mb:gc_options": gc_options_str,
            });
            if (compSvg.children().length > 1) {
                // <defs> should be always present
                let svgStr = compSvg.outerSVG();

                // Firefox bug workaround.
                svgStr = WorkingAreaHelper.fix_svg_string(svgStr);
                return svgStr;
            } else {
                console.error(
                    "Conversion error! _finalizeBackendSVG was called without content. Should never happen."
                );
            }
        };

        self.get_gc_length_summary = function (svg) {
            let summary = { vectors: {}, no_info: 0, bitmaps: [] };

            const vectors = self.getStrokedVectors(svg);
            let lastEnd = null;
            vectors.forEach(function (e) {
                const color = Snap.getRGB(e.attr("stroke")).hex;
                const l = e.attr("mb:gc_length");
                if (l) {
                    if (!summary.vectors[color])
                        summary.vectors[color] = {
                            lengthInMM: 0,
                            positioningInMM: 0,
                        };
                    summary.vectors[color].lengthInMM += parseFloat(l);
                    if (lastEnd !== null) {
                        let start = [
                            parseFloat(e.attr("mb:start_x")),
                            parseFloat(e.attr("mb:start_y")),
                        ];
                        const posLength = euclideanDistance(start, lastEnd);
                        summary.vectors[color].positioningInMM += posLength;
                    }
                    lastEnd = [
                        parseFloat(e.attr("mb:end_x")),
                        parseFloat(e.attr("mb:end_y")),
                    ];
                } else {
                    summary.no_info += 1;
                }
            });

            const bitmaps = svg.selectAll("image.fillRendering");
            bitmaps.forEach(function (b) {
                const w = parseFloat(b.attr("mb:img_w"));
                const h = parseFloat(b.attr("mb:img_h"));
                const histogram = b
                    .attr("mb:histogram")
                    .split(",")
                    .map((v) => parseInt(v));
                const whitePixelRatio = parseFloat(
                    b.attr("mb:whitePixelRatio")
                );
                const innerWhitePixelRatio = parseFloat(
                    b.attr("mb:innerWhitePixelRatio")
                );
                const whitePixelsOutside = parseInt(
                    b.attr("mb:whitePixelsOutside")
                );
                const brightnessChanges = parseInt(
                    b.attr("mb:brightnessChanges")
                );
                const totalBrightnessChange = parseInt(
                    b.attr("mb:totalBrightnessChange")
                );
                if (w && h && histogram) {
                    summary.bitmaps.push({
                        w: w,
                        h: h,
                        histogram: histogram,
                        whitePixelRatio: whitePixelRatio,
                        innerWhitePixelRatio: innerWhitePixelRatio,
                        whitePixelsOutside: whitePixelsOutside,
                        brightnessChanges: brightnessChanges,
                        totalBrightnessChange: totalBrightnessChange,
                    });
                } else {
                    summary.no_info += 1;
                }
            });

            const items = vectors.length + bitmaps.length;
            if (items > 0) summary.no_info = summary.no_info / items;
            return summary;
        };

        self._normalize_mb_id = function (id) {
            return id ? id.replace(/\s/g, "_") : "";
        };

        self.gc_options_as_string = function () {
            var gc_options = self.gc_options();
            var res = [];
            for (var key in gc_options) {
                res.push(key + ":" + gc_options[key]);
            }
            res.push("userAgent:" + navigator.userAgent.replace(/"/g, '"'));
            return res.join(", ");
        };

        self._set_mb_attributes = function (snapSvg) {
            var mb_meta = {};
            snapSvg.selectAll("path").forEach(function (element) {
                var id = element.attr("id");

                // if there's no id, let's create one
                if (!id) {
                    id = self.generateUniqueId(self.getEntryId("wa", 6));
                    element.attr("id", id);
                }

                var my_meta = { node: element.node.nodeName || "" };
                var attrs = element.node.attributes;
                for (var i = 0; i < attrs.length; i++) {
                    if (
                        attrs[i].nodeName.startsWith("mb:") &&
                        attrs[i].nodeName !== "mb:gc"
                    ) {
                        my_meta[attrs[i].nodeName] = attrs[i].nodeValue;
                    }
                }
                var normalized_id = self._normalize_mb_id(id);
                if (
                    my_meta["mb:id"] &&
                    normalized_id !== my_meta["mb:id"] &&
                    !my_meta["mb:clone_of"]
                ) {
                    element.attr("mb:clone_of", my_meta["mb:id"]);
                    my_meta["mb:clone_of"] = my_meta["mb:id"];
                }

                element.attr("mb:id", normalized_id);

                my_meta["mb:id"] = normalized_id;
                mb_meta[id] = my_meta;
                self.gc_meta[id] = my_meta;
            });
            return mb_meta;
        };

        self.getPlacedSvgs = function () {
            var svgFiles = [];
            ko.utils.arrayForEach(self.placedDesigns(), function (design) {
                if (design.type === "model") {
                    var extension = design.name.split(".").pop().toLowerCase();
                    if (extension === "svg" || extension === "dxf") {
                        svgFiles.push(design);
                    }
                }
            });
            return svgFiles;
        };

        self.getPlacedImages = function () {
            return snap.selectAll("#userContent image");
        };

        self.hasTextItems = function () {
            if (
                snap.selectAll("#userContent tspan").length > 0 ||
                snap.selectAll("#userContent text").length > 0 ||
                snap.selectAll("userContent #text").length > 0
            ) {
                return true;
            } else {
                return false;
            }
        };

        self.getPlacedGcodes = ko.computed(function () {
            var gcodeFiles = [];
            ko.utils.arrayForEach(self.placedDesigns(), function (design) {
                if (design.type === "machinecode") {
                    const gcf = {
                        // filter properties. "components", "components_engrave" and "parent" cause circular dependencies during json generation
                        date: design.date,
                        display: design.display,
                        hash: design.hash,
                        links: design.links,
                        name: design.name,
                        notes: design.notes,
                        origin: design.origin,
                        //parent: {children: Array(126), parent: undefined}
                        path: design.path,
                        previewId: design.previewId,
                        refs: design.refs,
                        size: design.size,
                        type: design.type,
                        typePath: design.typePath,
                        weight: design.weight,
                    };
                    gcodeFiles.push(gcf);
                }
            });
            return gcodeFiles;
        }, self);

        self.hasFilledVectors = function (elem) {
            elem = !elem
                ? snap.selectAll("#userContent *")
                : typeof elem === "string"
                ? snap.select(elem)
                : elem.selectAll("*");
            for (var i = 0; i < elem.length; i++) {
                var e = elem[i];
                if (
                    [
                        "path",
                        "circle",
                        "ellipse",
                        "rect",
                        "line",
                        "polyline",
                        "polygon",
                        "text",
                        "tspan"
                    ].indexOf(e.type) >= 0
                ) {
                    var fill = e.attr("fill");
                    var op = e.attr("fill-opacity");
                    if (fill !== "none" && op > 0) {
                        return true;
                    }
                }
            }
            return false;
        };
        self.hasStrokedVectors = function () {
            var el = snap.selectAll("#userContent *");
            for (var i = 0; i < el.length; i++) {
                var e = el[i];
                if (
                    [
                        "path",
                        "circle",
                        "ellipse",
                        "rect",
                        "line",
                        "polyline",
                        "polygon",
                        "path",
                    ].indexOf(e.type) >= 0
                ) {
                    var stroke = e.attr("stroke");
                    var sw = e.attr("stroke-width");
                    if (stroke !== "none" && parseFloat(sw) > 0) {
                        return true;
                    }
                }
            }
            return false;
        };

        self.getStrokedVectors = function (paper) {
            let elements = paper.selectAll(".vector_outline");
            let out = [];
            for (var i = 0; i < elements.length; i++) {
                var e = elements[i];
                // TODO use is_stroked() from render_fills
                var stroke = e.attr("stroke");
                var sw = e.attr("stroke-width");
                if (stroke !== "none" && parseFloat(sw) > 0) {
                    out.push(e);
                }
            }
            return elements;
        };

        self.draw_gcode = function (points, intensity, target) {
            var stroke_color = intensity === 0 ? "#BBBBBB" : "#FF0000";
            var d = "M" + points.join(" ");
            var p = snap.path(d).attr({
                fill: "none",
                stroke: stroke_color,
                strokeWidth: 0.5,
                "vector-effect": "non-scaling-stroke",
            });
            snap.select(target).append(p);
        };

        self.draw_gcode_img_placeholder = function (x, y, w, h, url, target) {
            if (url !== "" && w > 0 && h > 0) {
                var p = snap.image(url, x, y, w, h).attr({
                    transform: "matrix(1,0,0,-1,0," + String(h + y * 2) + ")",
                    filter: "url(#gcimage_preview)",
                });
            } else {
                console.info(
                    "Loaded GCode contains image but preview can't be shown ",
                    x,
                    y,
                    w,
                    h,
                    url
                );
            }

            snap.select(target).append(p);
        };

        self.clear_gcode = function () {
            snap.select("#gCodePreview").clear();
        };

        self.onStartup = function () {
            self.state.workingArea = self;
            self.files.workingArea = self;
            $(window).resize(function () {
                self.trigger_resize();
            });
            self.trigger_resize(); // initialize
            self.init();
            // init tinyColorPicker if not done yet
            $("#qs_colorPicker_stroke").tinycolorpicker();
            $("#qs_colorPicker_stroke").bind(
                "change",
                self._qs_currentQuickShapeUpdate
            );
            $("#qs_colorPicker_fill").tinycolorpicker();
            $("#qs_colorPicker_fill").bind(
                "change",
                self._qs_currentQuickShapeUpdate
            );
            $("#qt_colorPicker_stroke").tinycolorpicker();
            $("#qt_colorPicker_stroke").bind(
                "change",
                throttle((event) => self._qt_currentQuickTextUpdate(event), 200)
            );
            $("#qt_colorPicker_fill").tinycolorpicker();
            $("#qt_colorPicker_fill").bind(
                "change",
                throttle((event) => self._qt_currentQuickTextUpdate(event), 200)
            );
        };

        self.onAllBound = function (allViewModels) {
            self.svgDPI = self.settings.settings.plugins.mrbeam.svgDPI; // we assign ko function
            self.dxfScale = self.settings.settings.plugins.mrbeam.dxfScale;
            self.previewImgOpacity(
                self.settings.settings.plugins.mrbeam.cam.previewOpacity()
            );

            self.gc_options = ko.computed(function () {
                return {
                    beamOS: BEAMOS_DISPLAY_VERSION,
                    gc_nextgen: mrbeam.path.version,
                    enabled: self.settings.settings.plugins.mrbeam.gcode_nextgen.enabled(),
                    precision: self.settings.settings.plugins.mrbeam.gcode_nextgen.precision(),
                    optimize_travel: self.settings.settings.plugins.mrbeam.gcode_nextgen.optimize_travel(),
                    small_paths_first: self.settings.settings.plugins.mrbeam.gcode_nextgen.small_paths_first(),
                    clip_working_area: self.settings.settings.plugins.mrbeam.gcode_nextgen.clip_working_area(),
                    clipRect: [
                        0,
                        0,
                        self.workingAreaWidthMM(),
                        self.workingAreaHeightMM(),
                    ],
                };
            });
            $("#quick_shape_dialog").on("hidden", function () {
                self._qs_removeInvalid();
                self._qs_dialogClose();
            });
            $("#quick_text_dialog").on("hidden", function () {
                self._qt_dialogClose();
            });

            // opens preview pane on the left if hovered over one of the pink markers on the working area
            $("#camera_markers circle").mouseenter(function (e) {
                // If found is undefined, we do not show the markers
                found = self.camera.markersFound[
                    $(e.target).attr("id").replace("marker", "")
                ]();
                if (
                    !$("#wa_view_settings_body").hasClass("in") &&
                    found !== undefined &&
                    !found
                ) {
                    $("#wa_view_settings_body").collapse("toggle");
                }
            });

            self.initCrossHairDragging();
        };

        self.onTabChange = function (current, prev) {
            // Since Settings is not a BS dialog anymore,
            // we need to trigger 'show' and 'hidden' events "manually"
            // for OctoPrint to trigger onSettingsShown() and onSettingsHidden()
            if (current === "#settings") {
                if (self.settings && self.settings.settingsDialog) {
                    self.settings.settingsDialog.trigger("show");
                }
            } else if (prev === "#settings") {
                if (self.settings && self.settings.settingsDialog) {
                    self.settings.settingsDialog.trigger("hide");
                }
            }
        };

        self.onAfterTabChange = function (current, prev) {
            if (current === "#workingarea") {
                self.trigger_resize();
            }
            if (prev === "#settings") {
                // Since Settings is not a BS dialog anymore,
                // we need to trigger 'show' and 'hidden' events "manually"
                // for OctoPrint to trigger onSettingsShown() and onSettingsHidden()
                if (self.settings && self.settings.settingsDialog) {
                    self.settings.settingsDialog.trigger("hidden");
                }
            }
        };

        self.onBeforeTabChange = function (current, prev) {
            self.abortFreeTransforms(); // otherwise transformation is reported when design is not displayed. => has 0 size afterwards.
        };

        self.check_sizes_and_placements = function () {
            ko.utils.arrayForEach(self.placedDesigns(), function (design) {
                if (
                    design.type === "model" ||
                    design.type === "quicktext" ||
                    design.type === "quickshape" ||
                    design.type === "recentjob"
                ) {
                    var svg = snap.select("#" + design.previewId);
                    var misfitting = self.outsideWorkingArea(svg);
                    self._mark_as_misfit(design, misfitting, svg);
                }
            });
        };

        /**
         * Takes one design (element from placedDesigns) and marks it as misfit or un-marks it
         * @param design design element to mark or unmark (element from placedDesigns)
         * @param fitMatrix (from self.outsideWorkingArea()) or null or flash-ish if mark should be removed
         * @param svg (optional)  snap.select('#' + design.previewId);
         */
        self._mark_as_misfit = function (design, fitMatrix, svg) {
            if (!svg) {
                svg = snap.select("#" + design.previewId);
            }
            if (fitMatrix && (fitMatrix.oversized || fitMatrix.outside)) {
                design.misfit = true;
                $("#" + design.id).addClass("misfit");
                svg.addClass("misfit");
                svg.selectAll("*").forEach(function (e) {
                    e.addClass("misfit");
                });
                svg.data("fitMatrix", fitMatrix);
            } else {
                design.misfit = false;
                $("#" + design.id).removeClass("misfit");
                svg.removeClass("misfit");
                svg.selectAll("*").forEach(function (e) {
                    e.removeClass("misfit");
                });
                svg.data("fitMatrix", null);
            }
        };

        // raster the infill and inject it as an image into the svg
        self.rasterInfill = async function (
            svg, // is compSvg reference
            fillAreas,
            pxPerMM
        ) {
            // split SVG and get an array of clusters
            let clusters = svg.splitRasterClusters(fillAreas);

            // only render clusters overlapping the working area
            const waBB = snap.select("#coordGrid").getBBox();
            clusters = clusters.filter(function (c, idx) {
                const intersects = Snap.path.isBBoxIntersect(c.bbox, waBB);
                if (!intersects)
                    console.info(
                        `Cluster ${idx} is outside workingArea. Skipping`
                    );
                return intersects;
            });

            // get used fonts in text tags
            const whitelist = svg.getUsedFonts();
            // get font declarations for quickText fonts
            const fontDecl = WorkingAreaHelper.getFontDeclarations(whitelist);
            clusters = clusters.map((c) => {

                c.elements.forEach((element) => {
                    if(element.is_stroked() && element.is_filled()){
                        let elementStyle = element.attr("style");
                        let strokeStylingArray = elementStyle?.match(/stroke[^;]*;/g);
                        let strokeAttr = element.attr("stroke");
                        element.stroke = {
                            strokeStyling: strokeStylingArray,
                            strokeAttr: strokeAttr
                        }
                        let elementStyleWithoutStrokeStyling = elementStyle?.replace(new RegExp(strokeStylingArray.join('|'), 'g'), '');
                        element.attr("style", elementStyleWithoutStrokeStyling);
                        element.attr("stroke", "none");
                    }
                });

                c.svgDataUrl = svg.toWorkingAreaDataURL(
                    self.workingAreaWidthMM(),
                    self.workingAreaHeightMM(),
                    fontDecl,
                    svg.select("style")?.node?.innerHTML, // include SVG styling
                    `.toRaster.rasterCluster${c.idx}`
                );
                return c;
            });

            if (MRBEAM_DEBUG_RENDERING) {
                debugBase64(
                    clusters.map((c) => {
                        return c.svgDataUrl;
                    }),
                    `Step 1: Raster Cluster SVGs`
                );
            }
            if (fillAreas) {
                let pngs = await Promise.all(
                    clusters.map((c) =>
                        url2png(c.svgDataUrl, pxPerMM, c.bbox).then(function (
                            rasterResult
                        ) {
                            const fillImage = svg.image(
                                rasterResult.dataUrl,
                                c.bbox.x,
                                c.bbox.y,
                                c.bbox.w,
                                c.bbox.h
                            );

                            // total path length of engraving line by line
                            const gcLength =
                                c.bbox.w * c.bbox.h * pxPerMM + c.bbox.h; // contains enlargement of bbox due to webfont loading bug.
                            fillImage.attr({
                                id: `fillRendering${c.idx}`,
                                "mb:img_w": c.bbox.w, // for Job Time Estimation 2.0
                                "mb:img_h": c.bbox.h,
                                "mb:histogram": rasterResult.analysis.histogram,
                                "mb:whitePixelRatio":
                                    rasterResult.analysis.whitePixelRatio,
                                "mb:innerWhitePixelRatio":
                                    rasterResult.analysis.innerWhitePixelRatio,
                                "mb:whitePixelsOutside":
                                    rasterResult.analysis
                                        .whitePixelsAtTheOutside,
                                "mb:brightnessChanges":
                                    rasterResult.analysis.brightnessChanges,
                                "mb:totalBrightnessChange":
                                    rasterResult.analysis.totalBrightnessChange,
                                "mb:gc_length": gcLength,
                                class: "fillRendering",
                            });

                            c.elements.forEach((element) => {
                                if("stroke" in element){
                                    let elementStyle = element.attr("style");
                                    element.attr("style", elementStyle + element.stroke.strokeStyling);
                                    element.attr("stroke", element.stroke.strokeAttr);
                                } else {
                                    element.remove()
                                }
                            });

                            return rasterResult;
                        })
                    )
                );

                if (MRBEAM_DEBUG_RENDERING) {
                    debugBase64(
                        pngs.map((r) => r.dataUrl),
                        `Step 2: PNG of cluster`
                    );
                }

                svg.selectAll(".deleteAfterRendering").remove();

                if (MRBEAM_DEBUG_RENDERING) {
                    debugBase64(
                        svg.toDataURL(),
                        "Step 3: SVG with fill rendering"
                    );
                }
                return svg;
            } else {
                return Promise.resolve(svg);
            }
        };

        self.onBeforeBinding = function () {
            self.files.workingArea = self;
        };

        self.getNewSvg = function (id, w, h) {
            var svg = Snap(w, h);
            svg.attr("id", id);
            svg.attr("xmlns", "http://www.w3.org/2000/svg");
            svg.attr("xmlns:mb", "http://www.mr-beam.org/mbns");
            svg.attr("xmlns:xlink", "http://www.w3.org/1999/xlink");
            svg.selectAll("desc").remove();
            return svg;
        };

        self._enableWorkingAreaOverModal = function () {
            $("#area_preview").addClass("overModalBG");
        };
        self._disableWorkingAreaOverModal = function () {
            setTimeout(function () {
                $("#area_preview").removeClass("overModalBG");
            }, 300);
        };

        // ***********************************************************
        //  QUICKSHAPE start
        // ***********************************************************

        self.newQuickShape = function () {
            self.abortFreeTransforms();
            var file = self._qs_placeQuickShape();
            self.editQuickShape(file);
        };

        /**
         * Equivalent to self.placeSVG for QuickShape
         * @returns file object
         */
        self._qs_placeQuickShape = function () {
            var w = self.workingAreaWidthMM() / 5;
            var h = w * 0.5;
            var x = (self.workingAreaWidthMM() - w) / 2;
            var y = (self.workingAreaHeightMM() - h) / 3;
            var r = 0;

            var id = self.getEntryId("qs");
            var origin = id;
            var ts = Date.now();
            var file = {
                date: ts,
                name: "",
                id: id,
                previewId: null,
                url: null,
                misfit: false,
                origin: "local",
                path: null,
                type: "quickshape",
                typePath: ["quickshape"],
                qs_params: {
                    type: "#rect",
                    stroke: true,
                    color: "#e25303",
                    fill: false,
                    fill_color: "#000000",
                    rect_w: w,
                    rect_h: h,
                    rect_radius: r,
                    line_length: w,
                    circle_radius: w,
                    star_radius: w / 2,
                    star_corners: 5,
                    star_sharpness: 0.5522,
                    heart_w: w,
                    heart_h: 0.8 * w,
                    heart_lr: 0,
                },
                invalid: false,
            };
            var previewId = self.generateUniqueId(id, file); // appends -# if multiple times the same design is placed.
            file.previewId = previewId;

            var d = QuickShapeHelper.getRect(w, h, r);
            var shapeSvg =
                '<svg><g><path d="' +
                d +
                '" stroke-width="1" stroke="' +
                file.qs_params.color +
                '" fill="#ffffff" fill-opacity="0" /></g></svg>';
            var fragment = Snap.parse(shapeSvg);

            var scaleMatrixStr = new Snap.Matrix(1, 0, 0, 1, x, y).toString();
            self._prepareAndInsertSVG(
                fragment,
                previewId,
                origin,
                "",
                { showTransformHandles: false, embedGCode: false },
                { _skip: true },
                file
            );
            self._listPlacedItem(file);
            //			self._addClickAndHoverHandlers(fragment, file);
            $("#" + previewId).attr("transform", scaleMatrixStr);

            return file;
        };

        /**
         * Opens QuickShape window to edit an existing QuickShape object
         * @param file Object representing the QuickShape to edit
         */
        self.editQuickShape = function (file) {
            var params = file.qs_params;
            self.showTransformHandles(file.previewId, false);
            self.currentQuickShapeFile = null;
            $("#quick_shape_dialog").modal({ keyboard: true });
            $("#quick_shape_dialog").one(
                "hide",
                self._qs_currentQuickShapeShowTransformHandlesIfNotEmpty
            );
            // firing those change events is necessary to work around a bug in chrome|knockout|js.
            // Otherwise entering numbers directly does not fire the change event if the number
            // is accidentially equal to the field content it had before .val(..).
            $("#quick_shape_rect_w").val(params.rect_w).change();
            $("#quick_shape_rect_h").val(params.rect_h).change();
            $("#quick_shape_rect_radius").val(params.rect_radius).change();
            $("#quick_shape_line_length").val(params.line_length).change();
            $("#quick_shape_circle_radius").val(params.circle_radius).change();
            $("#quick_shape_star_radius").val(params.star_radius).change();
            $("#quick_shape_star_corners").val(params.star_corners).change();
            $("#quick_shape_star_sharpness")
                .val(params.star_sharpness)
                .change();
            $("#quick_shape_heart_w").val(params.heart_w).change();
            $("#quick_shape_heart_h").val(params.heart_h).change();
            $("#quick_shape_heart_lr").val(params.heart_lr).change();
            $("#quick_shape_stroke").prop("checked", params.stroke);
            $("#qs_colorPicker_stroke")
                .data("plugin_tinycolorpicker")
                .setColor(params.color);
            //			$('#quick_shape_color').val(params.color).change();
            $("#quick_shape_fill").prop("checked", params.fill);
            $("#qs_colorPicker_fill")
                .data("plugin_tinycolorpicker")
                .setColor(params.fill_color);
            //			$('#quick_shape_fill_brightness').val(params.fill_brightness).change();
            self.currentQuickShapeFile = file;

            $("#shape_tab_link_" + params.type.substr(1)).tab("show");
            $("#quick_shape_dialog div.tab-pane.active input:first").focus();
            self._qs_currentQuickShapeUpdate();
        };

        /**
         * shows transformation handles on QS if it exists.
         * @private
         */
        self._qs_currentQuickShapeShowTransformHandlesIfNotEmpty = function () {
            if (
                self.currentQuickShapeFile &&
                self.currentQuickShapeFile.previewId
            ) {
                self.showTransformHandles(
                    self.currentQuickShapeFile.previewId,
                    true
                );
            }
        };

        self.switchQuickShape = function (newShapeType) {
            if (self.currentQuickShapeFile) {
                self.currentQuickShapeFile.qs_params.type = newShapeType;
            }
            self._qs_currentQuickShapeUpdate();
        };

        /**
         * updates the actual SVG object, the file list object and more
         * Needs to be called after all changes to a QuickShape object
         *
         * Updates will be done for the QS object self.currentQuickShapeFile is pointing to
         */
        self._qs_currentQuickShapeUpdate = function () {
            if (self.currentQuickShapeFile) {
                //				var type = $('#shape_tabs li.active a').attr('href');
                var type = self.currentQuickShapeFile.qs_params.type;
                let name = self.quickShapeNames.get(type.substr(1));
                self.currentQuickShapeFile.name = name;
                self.currentQuickShape(self.currentQuickShapeFile.name);
                var qs_params = {
                    type: type,
                    color: $("#quick_shape_color").val(),
                    rect_w: WorkingAreaHelper.limitValue(parseFloat($("#quick_shape_rect_w").val()), self.rectangleMaxWidth()),
                    rect_h: WorkingAreaHelper.limitValue(parseFloat($("#quick_shape_rect_h").val()), self.rectangleMaxHeight()),
                    rect_radius: parseFloat(
                        $("#quick_shape_rect_radius").val()
                    ),
                    line_length: WorkingAreaHelper.limitValue(parseFloat(
                        $("#quick_shape_line_length").val()
                    ), self.lineMaxLength()),
                    circle_radius: WorkingAreaHelper.limitValue(parseFloat(
                        $("#quick_shape_circle_radius").val()
                    ), self.circleMaxRadius()),
                    star_radius: WorkingAreaHelper.limitValue(parseFloat(
                        $("#quick_shape_star_radius").val()
                    ), self.starMaxRadius()),
                    star_corners: parseInt(
                        $("#quick_shape_star_corners").val(),
                        10
                    ),
                    star_sharpness: parseFloat(
                        $("#quick_shape_star_sharpness").val()
                    ),
                    heart_w: WorkingAreaHelper.limitValue(parseFloat($("#quick_shape_heart_w").val()), self.heartMaxWidth()),
                    heart_h: WorkingAreaHelper.limitValue(parseFloat($("#quick_shape_heart_h").val()), self.heartMaxHeight()),
                    heart_lr: parseFloat($("#quick_shape_heart_lr").val()),
                    stroke: $("#quick_shape_stroke").prop("checked"),
                    fill_color: $("#quick_shape_fill_brightness").val(),
                    fill: $("#quick_shape_fill").prop("checked"),
                };

                self.currentQuickShapeFile.components.removeAll();
                if (qs_params.stroke) {
                    self.currentQuickShapeFile.components.push(qs_params.color);
                }
                self.currentQuickShapeFile.components_engrave(qs_params.fill);

                // update svg object
                var g = snap.select("#" + self.currentQuickShapeFile.previewId);
                setTimeout(function () {
                    g.mbtOnTransform();
                }, 200);
                var shape = g.select("path");
                var d;
                switch (qs_params.type) {
                    case "#line":
                        d = QuickShapeHelper.getLine(qs_params.line_length);
                        break;
                    case "#circle":
                        d = QuickShapeHelper.getCircle(qs_params.circle_radius);
                        break;
                    case "#star":
                        d = QuickShapeHelper.getStar(
                            qs_params.star_radius,
                            qs_params.star_corners,
                            qs_params.star_sharpness
                        );
                        break;
                    case "#heart":
                        d = QuickShapeHelper.getHeart(
                            qs_params.heart_w,
                            qs_params.heart_h,
                            qs_params.heart_lr
                        );
                        break;
                    default:
                        // #rect
                        d = QuickShapeHelper.getRect(
                            qs_params.rect_w,
                            qs_params.rect_h,
                            qs_params.rect_radius
                        );
                        break;
                }
                let stroke = qs_params.stroke ? qs_params.color : "none";
                let fill = "#ffffff";
                let fill_op = 0;
                if (qs_params.fill) {
                    fill = qs_params.fill_color;
                    fill_op = 1;
                }
                shape.attr({
                    d: d,
                    stroke: stroke,
                    fill: fill,
                    "fill-opacity": fill_op,
                });
                self.currentQuickShapeFile.qs_params = qs_params;
                if (
                    d === "" ||
                    (qs_params.stroke === false && qs_params.fill === false)
                ) {
                    self.currentQuickShapeFile.invalid = true;
                } else {
                    self.currentQuickShapeFile.invalid = false;
                }

                // update fileslist
                $("#" + self.currentQuickShapeFile.id + " .title").text(name);
                // update clones if present
                let colsRowsStr = $(
                    "#" + self.currentQuickShapeFile.id + " input.multiply"
                ).val();
                self._svgMultiplyUpdate(
                    self.currentQuickShapeFile,
                    colsRowsStr
                );

                // analytics
                let analyticsData = {
                    id: self.currentQuickShapeFile.id,
                    file_type: "quickShape",
                    type: type.substr(1),
                    stroke: qs_params.stroke,
                    stroke_color: qs_params.color,
                    fill: qs_params.fill,
                    fill_color: qs_params.fill_color,
                    name: name,
                };
                for (let myKey in qs_params) {
                    if (myKey.startsWith(analyticsData.type)) {
                        analyticsData[myKey] = qs_params[myKey];
                    }
                }

                // actual analytics are written when the dialog is closed
                self.currentQuickShapeAnalyticsData = analyticsData;
            }
        };

        self._qs_removeInvalid = function () {
            if (self.currentQuickShapeFile) {
                var remove = self.currentQuickShapeFile.invalid;
                if (remove) {
                    console.info(
                        "Removed invalid QuickShape:",
                        self.currentQuickShapeFile
                    );
                    self.removeSVG(self.currentQuickShapeFile);
                    self.currentQuickShapeFile = null;
                }
            }
        };
        self._qs_dialogClose = function () {
            self._qs_removeInvalid();
            self._analyticsQuickShapeUpdate(
                self.currentQuickShapeAnalyticsData
            );
        };

        // ***********************************************************
        //  QUICKSHAPE end
        // ***********************************************************

        // ***********************************************************
        //  QUICKTEXT start
        // ***********************************************************

        /**
         * Opens QuickText window and places a new quickText Object
         * to the working_area and file list.
         */
        self.newQuickText = function () {
            var file = self._qt_placeQuicktext();
            self.editQuickText(file);
        };

        /**
         * Opens QuickText window to edit an existing QuickText object
         * @param file Object representing the QuickText to edit
         */
        self.editQuickText = function (file) {
            self.currentQuickTextFile = file;
            const strokeColor =
                self.currentQuickTextFile.strokeColor || "#e25303";
            const fillColor = self.currentQuickTextFile.fillColor || "#000000";
            self._qt_currentQuickTextUpdate();
            $("#quick_text_dialog").one(
                "hide",
                self._qt_currentQuickTextRemoveIfEmpty
            );
            $("#quick_text_dialog").one(
                "hide",
                self._qt_currentQuickTextShowTransformHandlesIfNotEmpty
            );
            // TODO check if necessary
            $("#quick_text_dialog").one("shown", function () {
                $("#quick_text_dialog_text_input").focus();
            });
            $("#quick_text_dialog").modal({ keyboard: true });
            self.showTransformHandles(
                self.currentQuickTextFile.previewId,
                false
            );
            $("#quick_text_stroke").prop(
                "checked",
                self.currentQuickTextFile.stroke
            );
            $("#qt_colorPicker_stroke")
                .data("plugin_tinycolorpicker")
                .setColor(strokeColor);
            $("#quick_text_fill").prop(
                "checked",
                self.currentQuickTextFile.fill
            );
            $("#qt_colorPicker_fill")
                .data("plugin_tinycolorpicker")
                .setColor(fillColor);

            // round text radio buttons & slider
            $("#qt_round_text_section div.btn").removeClass("active");
            const cw = self.currentQuickTextFile.clockwise;
            const straight = self.currentQuickTextFile.circle === 0;
            let btn = "#quick_text_straight";
            if (!straight) btn = cw ? "#quick_text_cw" : "#quick_text_ccw";
            $(btn).addClass("active");
            $("#qt_round_text_section").toggleClass("straight", straight);
            self._qt_setCirclePath(cw, self.currentQuickTextFile.circle);
            $("#quick_text_dialog_text_input").focus();
        };

        /**
         * callback/subscription to changes of the text field
         */
        self.currentQuickText.subscribe(function (nuText) {
            if (self.currentQuickTextFile) {
                self.currentQuickTextFile.name = nuText;
            }
            self._qt_currentQuickTextUpdate();
        });

        let quickTextRadioInput = $('input[type=radio][name=stroke_or_fill]');
        quickTextRadioInput.on("change", function () {
            if(self.currentQuickTextFile){
                if (this.value === "stroke") {
                        self.currentQuickTextFile.stroke = self.lastQuickTextStroke = true;
                        self.currentQuickTextFile.fill = self.lastQuickTextFill = false;
                }
                if (this.value === "fill"){
                        self.currentQuickTextFile.fill = self.lastQuickTextFill = true;
                        self.currentQuickTextFile.stroke = self.lastQuickTextStroke = false;
                }
            }
            self._qt_currentQuickTextUpdate();
        });

        /**
         * callback/subscription for the circle slider
         */
        $("#quick_text_dialog_circle").on("input change", function (e) {
            if (self.currentQuickTextFile) {
                self.currentQuickTextFile.circle = parseFloat(
                    e.currentTarget.value
                );
                self.lastQuickTextCircle = self.currentQuickTextFile.circle;
                self._qt_currentQuickTextUpdate();
            }
        });
        /**
         * callback/subscription for the circle direction toggler
         */
        $("#quick_text_straight").on("click", function (event) {
            $("#qt_round_text_section div.btn").removeClass("active");
            $("#quick_text_straight").addClass("active");
            $("#qt_round_text_section").addClass("straight");
            self._qt_setCirclePath(true, 0);
        });
        $("#quick_text_cw").on("click", function (event) {
            $("#qt_round_text_section div.btn").removeClass("active");
            $("#quick_text_cw").addClass("active");
            $("#qt_round_text_section").removeClass("straight");
            self._qt_setCirclePath(true, 30);
        });
        $("#quick_text_ccw").on("click", function (event) {
            $("#qt_round_text_section div.btn").removeClass("active");
            $("#quick_text_ccw").addClass("active");
            $("#qt_round_text_section").removeClass("straight");
            self._qt_setCirclePath(false, 30);
        });

        /**
         * callback for the next font button
         */
        self.currentQuickTextFontNext = function () {
            if (self.currentQuickTextFile) {
                self.currentQuickTextFile.fontIndex++;
                if (
                    self.currentQuickTextFile.fontIndex >= self.fontMap.length
                ) {
                    self.currentQuickTextFile.fontIndex = 0;
                }
                self.lastQuickTextFontIndex =
                    self.currentQuickTextFile.fontIndex;
                self._qt_currentQuickTextUpdate();
            }
        };

        /**
         * callback for the previous font button
         */
        self.currentQuickTextFontPrev = function () {
            if (self.currentQuickTextFile) {
                self.currentQuickTextFile.fontIndex--;
                if (self.currentQuickTextFile.fontIndex < 0) {
                    self.currentQuickTextFile.fontIndex =
                        self.fontMap.length - 1;
                }
                self.lastQuickTextFontIndex =
                    self.currentQuickTextFile.fontIndex;
                self._qt_currentQuickTextUpdate();
            }
        };

        /**
         * updates the actual SVG object and the file list object and more
         * Needs to be called after all changes to a QuickText object
         *
         * Updates will be done for the QT object self.currentQuickTextFile is pointing to
         */
        self._qt_currentQuickTextUpdate = function () {
            if (self.currentQuickTextFile) {
                self.currentQuickText(self.currentQuickTextFile.name);
                let quickTextInputField = $("#quick_text_dialog_text_input");
                const displayText =
                    self.currentQuickTextFile.name !== ""
                        ? self.currentQuickTextFile.name
                        : quickTextInputField.attr(
                              "placeholder"
                          );

                // get all parameters
                const font = self.fontMap[self.currentQuickTextFile.fontIndex];
                const isStraightText = $("#quick_text_straight").hasClass(
                    "active"
                );
                const counterclockwise = $("#quick_text_ccw").hasClass(
                    "active"
                );

                const isFilled = self.currentQuickTextFile.fill;
                const fillColor = (self.currentQuickTextFile.fillColor = $(
                    "#quick_text_fill_brightness"
                ).val());
                const ity = rgb_from_hex(fillColor).x;
                const fill = isFilled ? fillColor : "none";
                const previewFill = isFilled ? fillColor : "#ffffff";
                const isStroked = self.currentQuickTextFile.stroke;
                const strokeColor = (self.currentQuickTextFile.strokeColor = $(
                    "#quick_text_stroke_color"
                ).val());
                const stroke = isStroked ? strokeColor : "none";
                const fakeStroke = `${strokeColor} 0px 0px 1px,${strokeColor} 0px 0px 1px,${strokeColor} 0px 0px 1px`;
                const shadowIty = ity > 200 ? (ity - 200) / 100 : 0;
                const shadow = isStroked
                    ? fakeStroke
                    : `rgba(226, 85, 3, ${shadowIty}) 0px 0px 16px`;
                const ligatures = isStraightText ? "initial" : "none";
                const g = snap.select(
                    "#" + self.currentQuickTextFile.previewId
                );

                const textAttrs = {
                    "font-family": font,
                    fill: fill,
                    stroke: stroke,
                };

                // update straight text DOM node
                const straightText = g.select(".straightText");
                straightText.attr(textAttrs);

                // update curved text DOM nodes
                const curvedText = g.select(".curvedText");
                curvedText.attr(textAttrs);
                const textPathEl = curvedText.select("textPath");
                const textPathAttr = textPathEl.attr();
                const path = snap.select(textPathAttr.href);
                const textLength = self._qt_currentQuicktextGetTextLength(
                    displayText,
                    font
                );
                const d = self._qt_currentQuicktextGetCirclePath(
                    self.currentQuickTextFile.circle,
                    textLength,
                    counterclockwise
                );
                path.attr({ d: d });

                // update text content and click handle bbox
                let bb;
                const textPathNode = textPathEl.node;
                if (isStraightText) {
                    textPathNode.textContent = "";
                    straightText.node.textContent = displayText;
                    bb = straightText.getBBox();
                } else {
                    textPathNode.textContent = displayText;
                    straightText.node.textContent = "";
                    bb = curvedText.getBBox();
                }

                // update text stroke
                let qtOutlineGroup = g.select(".qtOutlineGroup");
                if (isStroked) {
                    // create text stroke path if option is enabled and ignore if already added
                    if (!qtOutlineGroup.select("path")) {
                        qtOutlineGroup.path().attr({
                            class: "qtOutline vector_outline",
                        });
                    }
                    // add selected attributes to stroke path
                    g.select("path").attr({
                        stroke: strokeColor,
                        fill: "#ffffff",
                        "fill-opacity": 0,
                    });
                } else {
                    qtOutlineGroup.select("path")?.remove();
                }

                // update text rect (rect is for selection only)
                g.select("rect").attr({
                    x: bb.x,
                    y: bb.y,
                    width: bb.width,
                    height: bb.height,
                    // When quicktext fill is enabled/disabled, the fill-opacity controls the inclusion/exclusion of the filling
                    "fill-opacity": isFilled ? 1 : 0
                });

                // update font of input field
                quickTextInputField.css({
                    "text-shadow": shadow,
                    color: previewFill,
                    "font-family": font,
                    "font-variant-ligatures": ligatures,
                });
                // update input placeholder color if stroked
                let StrokedQuickTextPlaceholderClass = 'mrb-quicktext-stroked-placeholder';
                if(isStroked){
                    quickTextInputField.addClass(StrokedQuickTextPlaceholderClass);
                }
                // update input placeholder color if not stroked
                if(!isStroked && quickTextInputField.hasClass(StrokedQuickTextPlaceholderClass)){
                    quickTextInputField.removeClass(StrokedQuickTextPlaceholderClass);
                }

                $("#quick_text_dialog_font_name").text(font);
                //                $("#quick_text_fill_brightness").val(fillColor);
                //                $("#quick_text_stroke_color").val(strokeColor);

                // update fileslist title
                $("#" + self.currentQuickTextFile.id + " .title").text(
                    displayText
                );
                // update engrave component color
                $(`#${self.currentQuickTextFile.id} .engrave_component`).css({
                    display: isFilled ? "inherit" : "none",
                });
                // update stroke component color
                $(`#${self.currentQuickTextFile.id} .stroke_color`).css({
                    "background-color": strokeColor,
                    display: isStroked ? "inherit" : "none",
                });
                // update fileslist dimensions by triggering transform
                setTimeout(function () {
                    g.mbtOnTransform();
                }, 200);
                // update clones
                let multiply_str = $(
                    "#" + self.currentQuickTextFile.id + " input.multiply"
                ).val();
                self._svgMultiplyUpdate(
                    self.currentQuickTextFile,
                    multiply_str
                );

                // usage analytics
                self.currentQuickTextAnalyticsData = {
                    id: self.currentQuickTextFile.id,
                    file_type: "quickText",
                    text_length: self.currentQuickTextFile.name.length,
                    brightness: ity,
                    fill: self.currentQuickTextFile.fill,
                    fill_color: self.currentQuickTextFile.fillColor,
                    stroke: self.currentQuickTextFile.stroke,
                    stroke_color: self.currentQuickTextFile.strokeColor,
                    font: font,
                    font_index: self.currentQuickTextFile.fontIndex,
                    is_straight: isStraightText,
                    curved_ccw: counterclockwise,
                };
            }
        };

        self._qt_setCirclePath = function (cw, amount) {
            self.currentQuickTextFile.circle = amount;
            self.currentQuickTextFile.clockwise = cw;
            self.lastQuickTextCircle = self.currentQuickTextFile.circle;
            self.lastQuickTextClockwise = self.currentQuickTextFile.clockwise;
            $("#quick_text_dialog_circle").val(
                self.currentQuickTextFile.circle
            );
            self._qt_currentQuickTextUpdate();
        };

        /**
         * generates <path_data> for the path to align the QT on.
         *
         * @param {float} circlePercent percentage of text bending (0: straight line, 100: text aligned on full circle).
         * @param {float} textLength length of the text to bend in mm (more precise: working area coord units).
         * @param {boolean} counterclockwise direction of the circle path (clockwise: text on the outside, countercw: text on the inside)
         */
        self._qt_currentQuicktextGetCirclePath = function (
            circlePercent,
            textLength,
            counterclockwise
        ) {
            const d = QuickShapeHelper.getTextPath(
                0,
                0,
                circlePercent,
                textLength,
                counterclockwise
            );
            return d;
        };

        /**
         * generates <path_data> for the path to align the QT on.
         *
         * @param {string} text for which the length is estimated.
         * @param {string} fontname of the font in use.
         */
        self._qt_currentQuicktextGetTextLength = function (text, fontname) {
            // Lengths estimated by this String "1234567890qwertzuiopü+asdfghjklöä#<yxcvbnm,.-"
            // total length was measured and divided through those 45 characters to get avg. char width.
            // Estimation is the text length multiplied with the avg char width.
            // Estimation is ok. Too short is not critical, too long would not allow to close a full circle
            const font_width_mapping = {
                "Allerta Stencil": 499 / 45.0,
                "Amatic SC": 283 / 45.0,
                Comfortaa: 492 / 45.0,
                "Fredericka the Great": 421 / 45.0,
                Kavivanar: 425 / 45.0,
                Lobster: 388 / 45.0,
                Merriweather: 504 / 45.0,
                "Mr Bedfort": 375 / 45.0,
                Quattrocento: 445 / 45.0,
                Roboto: 442 / 45.0,
            };
            const textLength = Math.max(text.length, 5);
            const avgCharWidth = font_width_mapping[fontname] || 12; // Fallback
            return textLength * avgCharWidth;
        };

        /**
         * removes an QT object with an empty text from stage
         */
        self._qt_currentQuickTextRemoveIfEmpty = function () {
            if (
                self.currentQuickTextFile &&
                self.currentQuickTextFile.name === ""
            ) {
                self.removeSVG(self.currentQuickTextFile);
            }
        };

        /**
         * shows transformation handles on QT if it exists.
         * @private
         */
        self._qt_currentQuickTextShowTransformHandlesIfNotEmpty = function () {
            if (
                self.currentQuickTextFile &&
                self.currentQuickTextFile.previewId &&
                self.currentQuickTextFile.name !== ""
            ) {
                self.showTransformHandles(
                    self.currentQuickTextFile.previewId,
                    true
                );
            }
        };

        /**
         * Equivalent to self.placeSVG for QuickText
         * @returns file object
         */
        self._qt_placeQuicktext = function () {
            var start_ts = Date.now();
            var placeholderText = $("#quick_text_dialog_text_input").attr(
                "placeholder"
            );

            var file = {
                date: Date.now(),
                name: "",
                id: null,
                previewId: null,
                url: null,
                misfit: false,
                origin: "local",
                path: null,
                type: "quicktext",
                typePath: ["quicktext"],
                fontIndex: self.lastQuickTextFontIndex,
                stroke: self.lastQuickTextStroke,
                fill: self.lastQuickTextFill,
                strokeColor: self.lastQuickTextStrokeColor,
                fillColor: self.lastQuickTextFillColor,
                circle: self.lastQuickTextCircle,
                clockwise: self.lastQuickTextClockwise,
            };

            file.id = self.getEntryId("qt");
            file.previewId = self.generateUniqueId(file.id, file); // appends -# if multiple times the same design is placed.

            var uc = snap.select("#userContent");
            var x = self.workingAreaWidthMM() / 2;
            var y = self.workingAreaHeightMM() / 3;
            var size = self.workingAreaHeightMM() / 20;

            // TODO use self._prepareAndInsertSVG(...)
            // self._prepareAndInsertSVG(fragment, previewId, origin, '', {showTransformHandles: false, embedGCode: false}, {_skip: true}, file);
            // replaces all code below.

            // TODO: Bug: SW-1445
            // path for curved text
            const path = snap
                .path()
                .attr({
                    id: file.previewId + "_baselinepath",
                    d: `M0,0m${
                        -self.workingAreaWidthMM() / 2
                    },0h${self.workingAreaWidthMM()}`,
                    class: "quicktext_curve_path",
                    style: "stroke:#00aaff; stroke-width:2; fill:none",
                })
                .toDefs();

            const style = [
                `white-space: pre`,
                `font-size: ${size}px`,
                `text-anchor: middle`,
                `vector-effect: non-scaling-stroke`,
                `stroke-width: 2px`,
                `stroke-linejoin: round`,
                `stroke-linecap: round`,
            ].join("; ");
            const curvedText = uc.text(0, 0, placeholderText);
            curvedText.attr({
                style: style + "font-variant-ligatures: none;",
                textpath: path,
            });
            curvedText.node.classList.add("curvedText");
            curvedText.textPath.attr({ startOffset: "50%", style: style });

            const straightText = uc.text(0, 0, placeholderText);
            straightText.attr({
                style: style,
                class: "straightText",
            });

            const textStroke = uc.g().attr({
                class: "qtOutlineGroup",
            });

            var box = uc.rect(); // will be placed and sized by self._qt_currentQuickTextUpdateText()
            box.attr({
                opacity: "0",
                // opacity: "0.3",
                // fill: "yellow"
                class: "deleteBeforeRendering",
            });

            var group = uc.group(straightText, curvedText, textStroke, box);
            group.attr({
                id: file.previewId,
                "mb:id": self._normalize_mb_id(file.previewId),
                class: "userText",
                transform: `translate(${x},${y})`,
                "mb:origin": `beamos://quicktext`,
            });

            self._addClickAndHoverHandlers(group, file);

            self._listPlacedItem(file);

            // var dur = ((Date.now() - start_ts) /1000);
            // console.log("_qt_placeQuicktext() DONE "+ dur + "s");
            // // self._analyticsPlaceDesign('quickText', dur, file.previewId);
            // self._analyticsQuickTextUpdate()

            return file;
        };

        self._qt_dialogClose = function () {
            // render outline once the dialog is closed
            const id = self.currentQuickTextFile.previewId;
            const qtElem = snap.select("#" + id);
            if (qtElem) qtElem.setQuicktextOutline(0.0, 0); // TODO Margin Bug

            if (self.currentQuickTextAnalyticsData.text_length !== 0) {
                self._analyticsQuickTextUpdate(
                    self.currentQuickTextAnalyticsData
                );
            }
        };

        // ***********************************************************
        //  QUICKTEXT end
        // ***********************************************************

        // ***********************************************************
        //  move laserhead by crosshair dragging
        // ***********************************************************
        self.initCrossHairDragging = function () {
            const crosshairHandle = snap.select("#crosshair");
            window.mrbeam.draggableCrosshair = { debug: false };

            // TODO get from https://github.com/mrbeam/MrBeamPlugin/blob/2682b7a2e97373478e6516a98c8ba766d26ff317/octoprint_mrbeam/static/js/lasercutterprofiles.js#L276
            // once this branch feature/SW-244... is merged.
            const fx = self.profile.currentProfileData().axes.x.speed();
            const fy = self.profile.currentProfileData().axes.y.speed();
            const maxSpeed = Math.min(fx, fy);

            crosshairHandle.mousedown(function (event) {
                self.abortFreeTransforms();
                window.mrbeam.draggableCrosshair.origin = self.state.currentPos();
                window.mrbeam.draggableCrosshair.destination =
                    window.mrbeam.draggableCrosshair.origin;

                const boundaries = [
                    0,
                    0,
                    self.workingAreaWidthMM(),
                    self.workingAreaHeightMM(),
                ];

                // create a dummy crosshair attached to the pointer to visualize what this function does
                const dummy = crosshairHandle.clone();
                dummy.attr("id", "crosshairDummy");
                snap.append(dummy);

                // move our absolutely positioned ball under the pointer
                const handleBBox = crosshairHandle.getBBox();
                const initialPos = self._get_pointer_event_position_MM(
                    event,
                    snap.node
                );
                const handleOffset = {
                    x: initialPos.x - handleBBox.cx,
                    y: initialPos.y - handleBBox.cy,
                };
                setCrosshairPosMM(initialPos);

                /* This adds the click-offset to the position,
                 * asserts that the result it in the boundaries of the working area,
                 * moves the dummy crosshair
                 * and inverts the y axis for a mm coordinate in our gcode coords system.
                 *
                 * @param {object} pos from the event
                 * @returns {object} corrected position {x: float, y: float}
                 */
                function setCrosshairPosMM(pos) {
                    pos.x -= handleOffset.x;
                    pos.y -= handleOffset.y;
                    pos = self._assert_coords_in_boundaries(pos, boundaries);
                    dummy.transform(Snap.matrix(1, 0, 0, 1, pos.x, pos.y));
                    return { x: pos.x, y: boundaries[3] - pos.y };
                }

                function onMouseMove(event) {
                    if (event.which !== 1) {
                        // Mouse button released outside target workingArea or outside browser window
                        stopCrossHairDragging(event);
                        console.log("onMouseMove stopped", event.which);
                    } else {
                        const pos = self._get_pointer_event_position_MM(
                            event,
                            snap.node
                        );
                        const dest = setCrosshairPosMM(pos);
                        window.mrbeam.draggableCrosshair.destination = dest;
                    }
                }

                /*
                 * moves the laserhead towards the destination.
                 * maximum step 30mm
                 */
                function updateCrossHairDragging() {
                    let origin = window.mrbeam.draggableCrosshair.origin;
                    let dest = window.mrbeam.draggableCrosshair.destination;

                    if (dest === null) {
                        // drag finished or cancelled
                        clearInterval(
                            window.mrbeam.draggableCrosshair.interval
                        );
                    } else {
                        if (self._distance(origin, dest) < 0.01) {
                            // otherwise setInterval triggers constant gcode sending
                            return;
                        }
                        const intermediatePos = self._getPointOfLineMM(
                            origin,
                            dest,
                            30
                        );

                        self.move_laser_to_xy(
                            intermediatePos.x,
                            intermediatePos.y
                        );

                        // draw position of the last gcode command sent
                        if (window.mrbeam.draggableCrosshair.debug) {
                            const estimatedMoveDurationMS =
                                (intermediatePos.dist / (maxSpeed / 60)) * 1000; // milliseconds
                            console.log(
                                "estimatedMove",
                                estimatedMoveDurationMS
                            );
                            let debugC = snap.circle({
                                cx: intermediatePos.x,
                                cy: boundaries[3] - intermediatePos.y,
                                r: 2,
                                fill: "#ffff00",
                            });
                            setTimeout(function () {
                                debugC.remove();
                            }, estimatedMoveDurationMS);
                        }

                        // reflect current movement for the calculation of the next step towards destination
                        window.mrbeam.draggableCrosshair.origin = intermediatePos;
                    }
                }

                function stopCrossHairDragging(event) {
                    clearInterval(window.mrbeam.draggableCrosshair.interval);
                    window.mrbeam.draggableCrosshair.destination = null;

                    self._sendAnalytics("workingarea_crosshair_dragging", {})

                    const pos = self._get_pointer_event_position_MM(
                        event,
                        snap.node
                    );
                    const finalPos = setCrosshairPosMM(pos);
                    self.move_laser_to_xy(finalPos.x, finalPos.y);
                    console.info("Stop:", finalPos.x, finalPos.y);

                    document.removeEventListener("mousemove", onMouseMove);
                    document.removeEventListener(
                        "mouseup",
                        stopCrossHairDragging
                    );
                    setTimeout(function () {
                        dummy.remove();
                    }, 3000);
                }

                // start frequent gcode sending & update
                window.mrbeam.draggableCrosshair.interval = setInterval(
                    updateCrossHairDragging,
                    300
                );

                // add listeners
                document.addEventListener("mousemove", onMouseMove);
                document.addEventListener("mouseup", stopCrossHairDragging);
            });
        };

        self._distance = function (p1, p2) {
            return Math.sqrt(
                (p2.x - p1.x) * (p2.x - p1.x) + (p2.y - p1.y) * (p2.y - p1.y)
            );
        };

        self._getPointOfLineMM = function (p1, p2, mm) {
            const totalDist = self._distance(p1, p2);
            const percent = Math.min(1, mm / totalDist);
            const p = self._getPointOfLinePercent(p1, p2, percent);
            p.dist = totalDist * percent;
            return p;
        };

        self._getPointOfLinePercent = function (p1, p2, percent) {
            const x = p1.x + percent * (p2.x - p1.x);
            const y = p1.y + percent * (p2.y - p1.y);
            return { x: x, y: y };
        };

        // general modification keys
        self.wa_key_down = function (target, ev) {
            console.log("Keydown", target, ev);
            // ctrlKey for PC, metaKey for Mac command key
            if (ev.originalEvent.ctrlKey || ev.originalEvent.metaKey) {
                target.classList.add("ctrl");
            }
        };
        self.wa_key_up = function (target, ev) {
            // ctrlKey for PC, metaKey for Mac command key
            if (ev.originalEvent.ctrlKey || ev.originalEvent.metaKey) {
                target.classList.remove("ctrl");
            }
        };

        // on working_area: only works if shift key is down
        self.wheel_zoom_wa = function (target, ev) {
            if (ev.originalEvent.shiftKey) {
                self.wheel_zoom_monitor(target, ev);
            }
        };

        // on working_area: opposite direction than on monitor
        self.mouse_drag_wa = function (target, ev) {
            if (ev.originalEvent.shiftKey) {
                var pos = self._get_pointer_event_position_MM(
                    ev.originalEvent,
                    ev.currentTarget
                );
                var newOffX = self.zoomOffX() - pos.dx;
                var newOffY = self.zoomOffY() - pos.dy;
                self.set_zoom_offX(newOffX);
                self.set_zoom_offY(newOffY);
            }
        };

        self.wheel_zoom_monitor = function (target, ev) {
            var wheel = ev.originalEvent.deltaY;
            var targetBBox = ev.currentTarget.getBoundingClientRect();
            var xPerc =
                (ev.originalEvent.clientX - targetBBox.left) / targetBBox.width;
            var yPerc =
                (ev.originalEvent.clientY - targetBBox.top) / targetBBox.height;
            var deltaZoom = Math.sign(wheel) / 100;
            self.set_zoom_factor(deltaZoom, xPerc, yPerc);
        };

        self.mouse_drag_monitor = function (target, ev) {
            if (ev.originalEvent.buttons === 1) {
                var pos = self._get_pointer_event_position_MM(
                    ev.originalEvent,
                    ev.currentTarget
                );
                var newOffX = self.zoomOffX() + pos.dx;
                var newOffY = self.zoomOffY() + pos.dy;
                self.set_zoom_offX(newOffX);
                self.set_zoom_offY(newOffY);
            }
        };

        self._get_pointer_event_position_MM = function (event, target) {
            var percPos = self._get_pointer_event_position_Percent(
                event,
                target
            );
            var x =
                percPos.x * self.workingAreaWidthMM() * self.zoom() +
                self.zoomOffX();
            var y =
                percPos.y * self.workingAreaHeightMM() * self.zoom() +
                self.zoomOffY();
            var dx = percPos.dx * self.workingAreaWidthMM() * self.zoom();
            var dy = percPos.dy * self.workingAreaHeightMM() * self.zoom();
            return { x: x, y: y, dx: dx, dy: dy };
        };

        self._get_pointer_event_position_Percent = function (event, target) {
            var targetBBox = target.getBoundingClientRect();
            var xPerc = (event.clientX - targetBBox.left) / targetBBox.width;
            var yPerc = (event.clientY - targetBBox.top) / targetBBox.height;
            var dxPerc = event.movementX / targetBBox.width;
            var dyPerc = event.movementY / targetBBox.height;
            return { x: xPerc, y: yPerc, dx: dxPerc, dy: dyPerc };
        };

        self._assert_coords_in_boundaries = function (p, boundaries) {
            p.x = Math.max(boundaries[0], Math.min(boundaries[2], p.x));
            p.y = Math.max(boundaries[1], Math.min(boundaries[3], p.y));
            return p;
        };

        /**
         * Analytics Stuff
         */

        self._analyticsPrepareAndInsertSVG = function (analyticsData) {
            if (analyticsData._skip) {
                return;
            }
            analyticsData.file_type = analyticsData.file_type || null;
            self._sendAnalytics("workingarea_place_svg_generic", analyticsData);
            console.log("workingarea_place_svg_generic: ", analyticsData);
        };

        self._analyticsPlaceImage = function (analyticsData) {
            if (analyticsData._skip) {
                return;
            }
            analyticsData.file_type = analyticsData.file_type || null;
            self._sendAnalytics("workingarea_place_image", analyticsData);
            console.log("workingarea_place_image: ", analyticsData);
        };

        self._analyticsQuickShapeUpdate = function (analyticsData) {
            if (analyticsData) {
                self._sendAnalytics(
                    "workingarea_place_quickshape_update",
                    analyticsData
                );
                console.log(
                    "workingarea_place_quickshape_update: ",
                    analyticsData
                );
            }
        };

        self._analyticsQuickTextUpdate = function (analyticsData) {
            if (analyticsData) {
                self._sendAnalytics(
                    "workingarea_place_quicktext_update",
                    analyticsData
                );
                console.log(
                    "workingarea_place_quicktext_update: ",
                    analyticsData
                );
            }
        };

        self._analyticsPlaceGco = function (analyticsData) {
            if (analyticsData) {
                self._sendAnalytics("workingarea_place_gcode", analyticsData);
                console.log("workingarea_place_gcode: ", analyticsData);
            }
        };

        self._sendAnalytics = function (event, payload) {
            self.analytics.send_fontend_event(event, payload);
        };
    }

    // view model class, parameters for constructor, container to bind to
    ADDITIONAL_VIEWMODELS.push([
        WorkingAreaViewModel,
        [
            "loginStateViewModel",
            "settingsViewModel",
            "printerStateViewModel",
            "gcodeFilesViewModel",
            "laserCutterProfilesViewModel",
            "cameraViewModel",
            "readyToLaserViewModel",
            "tourViewModel",
            "analyticsViewModel",
        ],
        [
            document.getElementById("area_preview"),
            document.getElementById("homing_overlay"),
            document.getElementById("working_area_files"),
            document.getElementById("quick_text_dialog"),
            document.getElementById("quick_shape_dialog"),
            document.getElementById("wa_view_settings"),
            document.getElementById("mrb_object_height"),
            document.getElementById("zoomFactor"),
        ],
    ]);
});
