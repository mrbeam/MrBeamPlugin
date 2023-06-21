/*
 * View model for Mr Beam
 *
 * Author: Teja Philipp <teja@mr-beam.org>
 * License: AGPLv3
 */
/* global OctoPrint, OCTOPRINT_VIEWMODELS, INITIAL_CALIBRATION */

const MAX_BOARD_SCORE = 5;
const MIN_BOARDS_FOR_CALIBRATION = 9;

$(function () {
    function LensCalibrationViewModel(parameters) {
        let self = this;
        window.mrbeam.viewModels["lensCalibrationViewModel"] = self;
        self.calibration = parameters[0];
        self.analytics = parameters[1];
        self.camera = parameters[2];

        self.lensCalibrationActive = ko.observable(false);

        self.lensCalibrationNpzFileTs = ko.observable(null);
        self.rawPicSelection = ko.observableArray([]);

        self.cameraBusy = ko.computed(function () {
            return self
                .rawPicSelection()
                .some((elm) => elm.state === "camera_processing");
        });

        self.lensCalibrationNpzFileVerboseDate = ko.computed(function () {
            const ts = self.lensCalibrationNpzFileTs();
            if (ts !== null) {
                const d = new Date(ts);
                const verbose = d.toLocaleString("de-DE", {
                    timeZone: "Europe/Berlin",
                });
                return `Using .npz created at ${verbose}`;
            } else {
                return "No .npz file available";
            }
        });

        self.lensCalibrationComplete = ko.computed(function () {
            return "lensCalibration" in self.calibration.calibrationState()
                ? self.calibration.calibrationState().lensCalibration ===
                      "success"
                : false;
        });

        self.lensCalibrationBusy = ko.computed(function () {
            return "lensCalibration" in self.calibration.calibrationState()
                ? self.calibration.calibrationState().lensCalibration ===
                      "processing"
                : false;
        });

        self.boardsFound = ko.computed(function () {
            return self
                .rawPicSelection()
                .filter((elm) => elm.state === "success").length;
        });

        self.hasMinBoardsFound = ko.computed(function () {
            return self.boardsFound() >= MIN_BOARDS_FOR_CALIBRATION;
        });

        self.onStartupComplete = function () {
            if (window.mrbeam.isWatterottMode()) {
                self._refreshPics();
                $("#lenscal_tab_btn").click(function () {
                    self.startLensCalibration();
                });
            }
        };

        self.onSettingsHidden = function () {
            if (self.lensCalibrationActive()) {
                self.abortLensCalibration();
            }
        };

        self.onDataUpdaterPluginMessage = function (plugin, data) {
            if (plugin !== "mrbeam" || !data) return;

            if (!self.calibration.calibrationScreenShown()) {
                return;
            }

            if ("chessboardCalibrationState" in data) {
                let _d = data["chessboardCalibrationState"];

                self.calibration.calibrationState(_d);
                // { '/home/pi/.octoprint/uploads/cam/debug/tmp_raw_img_4.jpg': {
                //      state: "processing",
                //      tm_proc: 1590151819.735044,
                //      tm_added: 1590151819.674166,
                //      board_bbox: [[767.5795288085938, 128.93748474121094],
                //                   [1302.0089111328125, 578.4738159179688]], // [xmin, ymin], [xmax, ymax]
                //      board_center: [1039.291259765625, 355.92547607421875], // cx, cy
                //      found_pattern: null,
                //      index: 2,
                //      board_size: [5, 6]
                //    }, ...
                // }

                if ("lensCalibrationNpzFileTs" in _d) {
                    self.lensCalibrationNpzFileTs(
                        _d.lensCalibrationNpzFileTs > 0
                            ? _d.lensCalibrationNpzFileTs * 1000
                            : null
                    );
                }

                let heatmap_arr = [];
                let found_bboxes = [];
                let total_score = 0;
                for (const [path, value] of Object.entries(_d.pictures)) {
                    value.path = path;
                    value.url = path.replace(
                        "home/pi/.octoprint/uploads",
                        "downloads/files/local"
                    );
                    value.processing_duration =
                        value.tm_end !== null
                            ? (value.tm_end - value.tm_proc).toFixed(1) + " sec"
                            : "?";
                    heatmap_arr.push(value);
                    if (value.board_bbox) {
                        // TODO individual score should be attributed when all boxes are in the list
                        value.score = self._calcPicScore(
                            value.board_bbox,
                            found_bboxes
                        );
                        total_score += value.score;
                        found_bboxes.push(value.board_bbox);
                    }
                }
                self.updateHeatmap(_d.pictures);

                // TODO mv this into updateHeatmap
                for (let i = heatmap_arr.length; i < 9; i++) {
                    heatmap_arr.push({
                        index: -1,
                        path: null,
                        url: "",
                        state: "missing",
                    });
                }

                // required to refresh the heatmap
                $("#heatmap_container").html($("#heatmap_container").html());
                heatmap_arr.sort(function (l, r) {
                    if (l.index == r.index) return 0;
                    else if (l.index == -1) return 1;
                    else if (r.index == -1) return -1;
                    else return l.index < r.index ? -1 : 1;
                });

                self.rawPicSelection(heatmap_arr);
            }
        };

        self.startLensCalibration = function () {
            self.analytics.send_frontend_event("lens_calibration_start", {});
            self.lensCalibrationActive(true);
            self.calibration.simpleApiCommand(
                "calibration_lens_start",
                {},
                self._refreshPics,
                self._getRawPicError,
                "GET"
            );

            $("#settingsTabs").one("click", function () {
                self.abortLensCalibration();
            });
        };

        self.runLensCalibration = function () {
            self.calibration.simpleApiCommand(
                "camera_run_lens_calibration",
                {},
                function () {
                    new PNotify({
                        title: gettext("Calibration started"),
                        text: gettext(
                            "It shouldn't take long. Your device shows a green light when it is done."
                        ),
                        type: "info",
                        hide: true,
                    });
                },
                function () {
                    new PNotify({
                        title: gettext("Couldn't start the lens calibration."),
                        text: gettext(
                            "Is the machine on? Have you taken any pictures before starting the calibration?"
                        ),
                        type: "warning",
                        hide: false,
                    });
                },
                "POST"
            );
        };

        self.abortLensCalibration = function () {
            // TODO - Axel - Allow to kill the board detection.
            self.analytics.send_frontend_event("lens_calibration_abort", {});
            self.stopLensCalibration();
            self.resetView();
        };

        self.stopLensCalibration = function () {
            self.calibration.simpleApiCommand(
                "camera_stop_lens_calibration",
                {},
                function () {
                    self.resetLensCalibration();
                },
                function () {
                    // In case the users experience weird behaviour
                    new PNotify({
                        title: gettext("Couldn't stop the lens calibration."),
                        text: gettext(
                            "Please verify your connection to the device. Did you try canceling multiple times?"
                        ),
                        type: "warning",
                        hide: false,
                    });
                },
                "POST"
            );
        };

        self.resetLensCalibration = function () {
            self.lensCalibrationActive(false);
            self.resetHeatmap();
        };

        self.saveLensCalibrationData = function () {
            // TODO Gray out button when calibration state is STATE_PROCESSING
            self.analytics.send_frontend_event("lens_calibration_finish", {});
            self.runLensCalibration();
            self.resetView();
        };

        self.resetView = function () {
            self.calibration.resetUserView();
        };

        self.saveRawPic = function () {
            self.calibration.simpleApiCommand(
                "calibration_save_raw_pic",
                {},
                self._rawPicSuccess,
                self._saveRawPicError
            );
        };

        self.delRawPic = function () {
            $("#heatmap_board" + this.index).remove(); // remove heatmap
            self.calibration.simpleApiCommand(
                "calibration_del_pic",
                { name: this["path"] },
                self._refreshPics,
                self._delRawPicError,
                "POST"
            );
        };

        self.restoreFactory = function () {
            // message type not defined - not implemented for Calibration tool
            self.calibration.simpleApiCommand(
                "calibration_lens_restore_factory",
                {},
                function () {
                    new PNotify({
                        title: gettext("Reverted to factory settings."),
                        text: gettext(
                            "Your previous calibration has been deleted."
                        ),
                        type: "info",
                        hide: false,
                    });
                },
                function (response) {
                    new PNotify({
                        title: gettext("Failed to revert to factory settings."),
                        text: gettext(
                            "Information :\n" + response.responseText
                        ),
                        type: "warning",
                        hide: false,
                    });
                }
            );
        };

        self._refreshPics = function () {
            self.calibration.simpleApiCommand(
                "calibration_get_raw_pic",
                {},
                self._rawPicSuccess,
                self._getRawPicError,
                "GET"
            );
        };

        self._calcPicScore = function (bbox, found_bboxes) {
            if (!bbox) return 0;
            const [x1, y1] = bbox[0];
            const [x2, y2] = bbox[1];
            let max_overlap = 0;
            const area = (x2 - x1) * (y2 - y1);
            for (var i = 0; i < found_bboxes.length; i++) {
                var existing_bbox = found_bboxes[i];
                max_overlap = Math.max(
                    max_overlap,
                    self._getBboxIntersectingArea(bbox, existing_bbox)
                );
            }
            const score = (1 - max_overlap / area) * MAX_BOARD_SCORE;
            return score;
        };

        self._getBboxIntersectingArea = function (bb1, bb2) {
            // precondition: bb = [[xmin, ymin], [xmax, ymax]] with always _min < _max
            const [x11, y11] = bb1[0];
            const [x21, y21] = bb1[1];
            const [x12, y12] = bb2[0];
            const [x22, y22] = bb2[1];
            if (x21 < x12 || x11 > x22) return 0; // bboxes don't overlap on the x axis
            if (y21 < y12 || y11 > y22) return 0; // bboxes don't overlap on the y axis
            const dx = Math.min(x21, x22) - Math.max(x11, x12);
            const dy = Math.min(y21, y22) - Math.max(y11, y12);
            return dx * dy;
        };

        // HEATMAP
        self.resetHeatmap = function () {
            $("#segment_group rect").remove();
        };

        self.dehighlightHeatmap = function () {
            $("#segment_group rect").removeClass("highlight");
        };

        self.highlightHeatmap = function (data) {
            if (!data.path || data.state !== "success") return;
            let fileName = data.path.split("/").reverse()[0];
            let id = "heatmap_board" + fileName;
            // $("#"+id).addClass('highlight'); // no idea why this doesn't work anymore
            document.getElementById(id).classList.add("highlight");
        };

        self.updateHeatmap = function (picturesState) {
            let boxes = [];
            for (const [path, value] of Object.entries(picturesState)) {
                if (value.board_bbox) {
                    let fileName = path.split("/").reverse()[0];
                    const [x1, y1] = value.board_bbox[0];
                    const [x2, y2] = value.board_bbox[1];
                    boxes.push(
                        `<rect id="heatmap_board${fileName}" x="${x1}" y="${y1}" width="${
                            x2 - x1
                        }" height="${y2 - y1}" />`
                    );
                }
            }
            let heatmapGroup = $("#segment_group");
            heatmapGroup.empty();
            heatmapGroup.append(boxes);
        };

        // RAW PIC
        self._rawPicSuccess = function (response) {};
        self._saveRawPicError = function () {
            self._rawPicError(
                gettext("Failed to save the latest image."),
                gettext("Please check your connection to the device.")
            );
        };
        self._delRawPicError = function () {
            self._rawPicError(
                gettext("Failed to delete the latest image."),
                gettext("Please check your connection to the device.")
            );
        };
        self._getRawPicError = function () {
            self._rawPicError(
                gettext("Failed to refresh the list of images."),
                gettext("Please check your connection to the device.")
            );
        };

        self._rawPicError = function (err, msg) {
            // Shorthand - Only shows "I have no clue why" when no message was defined
            if (msg === undefined)
                msg = gettext("...and I have no clue why. Sorry.");
            new PNotify({
                title: err,
                text: msg,
                type: "warning",
                hide: true,
            });
        };

        // WATTEROTT ONLY
        self.lensCalibrationToggleQA = function () {
            $("#lensCalibrationPhases").toggleClass("qa_active");
        };
    }

    // view model class, parameters for constructor, container to bind to
    OCTOPRINT_VIEWMODELS.push([
        LensCalibrationViewModel,

        // e.g. loginStateViewModel, settingsViewModel, ...
        ["calibrationViewModel", "analyticsViewModel", "cameraViewModel"],

        // e.g. #settings_plugin_mrbeam, #tab_plugin_mrbeam, ...
        [
            "#lens_calibration_view",
            "#tab_lens_calibration",
            "#tab_lens_calibration_wrap",
        ],
    ]);
});
