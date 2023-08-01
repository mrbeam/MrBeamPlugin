const MARKERS = ["NW", "NE", "SE", "SW"];

$(function () {
    function CameraViewModel(parameters) {
        var self = this;
        window.mrbeam.viewModels["cameraViewModel"] = self;

        self.settings = parameters[0];
        self.state = parameters[1];
        self.loginState = parameters[2];

        self.TAB_NAME_WORKING_AREA = "#workingarea";
        self.FALLBACK_IMAGE_URL =
            "/plugin/mrbeam/static/img/beam-cam-static.jpg";
        self.MARKER_DESCRIPTIONS = {
            NW: gettext("Top left"),
            SW: gettext("Bottom left"),
            NE: gettext("Top right"),
            SE: gettext("Bottom right"),
        };

        self.needsCornerCalibration = ko.observable(false);
        self.needsRawCornerCalibration = ko.observable(false);

        self.rawUrl = "/downloads/files/local/cam/debug/raw.jpg"; // TODO get from settings
        self.undistortedUrl =
            "/downloads/files/local/cam/debug/undistorted.jpg"; // TODO get from settings
        self.croppedUrl = "/downloads/files/local/cam/beam-cam.jpg";
        self.timestampedCroppedImgUrl = ko.observable("");
        self.webCamImageElem = undefined;
        self.isCamCalibrated = false;
        self.firstImageLoaded = false;
        self.countImagesLoaded = ko.observable(0);
        self.imagesInSession = ko.observable(0);

        self.markersFound = {
            NW: ko.observable(),
            SW: ko.observable(),
            SE: ko.observable(),
            NE: ko.observable(),
        };
        self.maxWorkingHeight = 38; // in mm
        self.defaultMargin = self.maxWorkingHeight / 582;
        self.objectZ = ko.observable(0); // in mm
        self.cornerMargin = ko.observable(self.defaultMargin / 2);
        self.imgHeightScale = ko.computed(function () {
            return (
                self.cornerMargin() *
                (1 - self.objectZ() / self.maxWorkingHeight)
            );
        });

        self.availablePic = ko.observable({
            raw: false,
            lens_corrected: false,
            cropped: false,
        });
        self._availablePicUrl = ko.observable({
            default: STATIC_URL,
            raw: null,
            lens_corrected: null,
            cropped: null,
        });
        self.availablePicUrl = ko.computed(function () {
            var ret = self._availablePicUrl();
            var before = _.clone(ret); // shallow copy
            for (let _t of [
                ["cropped", self.croppedUrl],
                ["lens_corrected", self.undistortedUrl],
                ["raw", self.rawUrl],
            ]) {
                if (self.availablePic()[_t[0]])
                    ret[_t[0]] =
                        _t[0] === "cropped"
                            ? self.timestampedCroppedImgUrl()
                            : self.getTimestampedImageUrl(_t[1]);
            }
            self._availablePicUrl(ret);
            var selectedTab = $("#camera-calibration-tabs .active a").attr(
                "id"
            );
            if (selectedTab === "lenscal_tab_btn") return before;
            else return ret;
        });

        // event listener callbacks //

        self.onAllBound = function () {
            self.cameraActive = ko.computed(function () {
                // Needs the motherViewModel to set the interlocks
                // Output not used yet -
                // Function updates self.imageInSession (Which is used)
                let ret =
                    self.firstRealimageLoaded() &&
                    self.state.isOperational() &&
                    !self.state.isPrinting() &&
                    !self.state.isLocked() &&
                    !self.state.interlocksClosed();
                if (!ret) {
                    self.imagesInSession(0);
                }
                return ret;
            });
            self.webCamImageElem = $("#beamcam_image_svg");
            self.cameraMarkerElem = $("#camera_markers");
            // self.webCamImageElem.removeAttr('onerror');
            self.croppedUrl =
                self.settings.settings.plugins.mrbeam.cam.frontendUrl();

            if (window.mrbeam.browser.is_safari) {
                // svg filters don't really work in safari: https://github.com/mrbeam/MrBeamPlugin/issues/586
                self.webCamImageElem.attr("filter", "");
            }

            // loading_overlay disappears only if this is set to true
            // not working in Safari
            self.webCamImageElem.load(function () {
                self.firstImageLoaded = true;
                self.countImagesLoaded(self.countImagesLoaded() + 1);
            });

            // trigger initial loading of the image
            self.loadImage(self.croppedUrl);
        };

        // Image resolution notification //
        self.imgResolution = ko.observable("Low");
        self.imgResolutionNoticeDisplay = ko.computed(function () {
            if (self.imgResolution() === "Low") return "inherit";
            else return "none";
        });

        self.markerState = ko.computed(function () {
            // Returns the number of markers found
            if (
                MARKERS.reduce(
                    (prev, key) =>
                        prev || self.markersFound[key]() === undefined,
                    false
                )
            )
                return undefined;
            return MARKERS.reduce(
                (prev_val, key) => prev_val + self.markersFound[key](),
                0
            );
        });

        self.showMarkerWarning = ko.computed(function () {
            if (self.markerState() === undefined) return false;
            else if (self.markerState() < 4) return true;
            else return false;
        });

        self.firstRealimageLoaded = ko.computed(function () {
            return self.countImagesLoaded() >= 2;
        });

        self.markerMissedClass = ko.computed(function () {
            var ret = "";
            MARKERS.forEach(function (m) {
                if (
                    self.markersFound[m]() !== undefined &&
                    !self.markersFound[m]()
                )
                    ret = ret + " marker" + m;
            });
            if (self.cameraMarkerElem !== undefined) {
                if (self.imagesInSession() == 0) {
                    ret = ret + " gray";
                    // Somehow the filter in css doesn't work
                    self.cameraMarkerElem.attr({
                        style: "filter: url(#grayscale_filter)",
                    });
                } else self.cameraMarkerElem.attr({ style: "" });
            }
            return ret;
        });

        self.onDataUpdaterPluginMessage = function (plugin, data) {
            if (plugin !== "mrbeam" || !data) return;
            if ("need_camera_calibration" in data) {
                self._needCalibration(data["need_camera_calibration"]);
            }
            if ("need_raw_camera_calibration" in data) {
                self.needsRawCornerCalibration(
                    data["need_raw_camera_calibration"]
                );
            }

            if ("beam_cam_new_image" in data) {
                const mf = data["beam_cam_new_image"]["markers_found"];
                MARKERS.forEach(function (m) {
                    self.markersFound[m](mf.includes(m));
                });

                if (data["beam_cam_new_image"]["error"] === undefined) {
                    self._needCalibration(false);
                } else if (
                    data["beam_cam_new_image"]["error"] ===
                    "Camera_calibration_is_needed"
                ) {
                    self._needCalibration(true);
                }
                if ("workspace_corner_ratio" in data["beam_cam_new_image"]) {
                    // workspace_corner_ratio should be a float
                    // describing the fraction of the img where
                    // the z=0 view starts.
                    self.cornerMargin(
                        data["beam_cam_new_image"]["workspace_corner_ratio"]
                    );
                } else {
                    self.cornerMargin(0);
                }
                self.loadImage(self.croppedUrl);
            }
        };

        self._needCalibration = function (val) {
            if ((val === undefined || val) && !self.needsCornerCalibration()) {
                new PNotify({
                    title: gettext("Corner Calibration needed"),
                    text: gettext(
                        "Please calibrate the camera under Settings -> Camera -> Corner Calibration."
                    ),
                    type: "warning",
                    tag: "calibration_needed",
                    hide: false,
                });
            }
            if (val !== undefined) self.needsCornerCalibration(val);
            else self.needsCornerCalibration(true);
        };

        self.loadImage = function (url) {
            var myImageUrl = self.getTimestampedImageUrl(url);
            var img = $("<img>");
            img.load(function () {
                self.timestampedCroppedImgUrl(myImageUrl);
                if (window.mrbeam.browser.is_safari) {
                    // load() event seems not to fire in Safari.
                    // So as a quick hack, let's set firstImageLoaded to true already here
                    self.firstImageLoaded = true;
                    self.countImagesLoaded(self.countImagesLoaded() + 1);
                }
                if (this.width > 1500 && this.height > 1000)
                    self.imgResolution("High");
                else self.imgResolution("Low");

                // respond to backend to tell we have loaded the picture
                if (INITIAL_CALIBRATION) {
                    $.ajax({
                        type: "GET",
                        url: "/plugin/mrbeam/on_camera_picture_transfer",
                    });
                } else if (self.loginState.loggedIn()) {
                    OctoPrint.simpleApiCommand(
                        "mrbeam",
                        "on_camera_picture_transfer",
                        {}
                    );
                } else {
                    console.warn(
                        "User not logged in, cannot confirm picture download."
                    );
                }
                self.imagesInSession(self.imagesInSession() + 1);
            });
            if (!self.firstImageLoaded) {
                img.error(function () {
                    self.timestampedCroppedImgUrl(self.FALLBACK_IMAGE_URL);
                });
            }
            img.attr({ src: myImageUrl });
        };

        self.getTimestampedImageUrl = function (url) {
            let result;
            if (url) {
                result = url;
            } else if (self.croppedUrl) {
                result = self.croppedUrl;
            }
            if (result) {
                if (result.match(/(\?|&)ts=/))
                    result = result.replace(
                        /(\?|&)ts=[0-9]+/,
                        "$1ts=" + new Date().getTime()
                    );
                else {
                    result += result.lastIndexOf("?") > -1 ? "&ts=" : "?ts=";
                    result += new Date().getTime();
                }
            }
            return result;
        };

        self.send_camera_image_to_analytics = function () {
            if (self.loginState.loggedIn()) {
                OctoPrint.simpleApiCommand(
                    "mrbeam",
                    "send_camera_image_to_analytics",
                    {}
                );
            } else {
                console.warn(
                    "User not logged in, cannot send image to analytics."
                );
            }
        };
    }

    // view model class, parameters for constructor, container to bind to
    ADDITIONAL_VIEWMODELS.push([
        CameraViewModel,
        ["settingsViewModel", "printerStateViewModel", "loginStateViewModel"],
        [], // nothing to bind.
    ]);
});
