/*
 * View model for Mr Beam
 *
 * Author: Teja Philipp <teja@mr-beam.org>
 * License: AGPLv3
 */
/* global OctoPrint, OCTOPRINT_VIEWMODELS, INITIAL_CALIBRATION */

const CUSTOMER_CAMERA_VIEWS = {
    settings: "#camera_settings_view",
    lens: "#lens_calibration_view",
    corner: "#corner_calibration_view",
};

$(function () {
    function CameraSettingsViewModel(parameters) {
        let self = this;
        window.mrbeam.viewModels["cameraSettingsViewModel"] = self;
        self.camera = parameters[0];
        self.state = parameters[1]; // isOperational
        self.readyToLaser = parameters[2]; // lid_fully_open & debug tab with mrb state
        self.settingsViewModel = parameters[3];
        self.workingArea = parameters[4];
        self.loginState = parameters[5];
        self.settingsActive = ko.observable(false);
        self.cameraSettingsActive = ko.observable(false);

        self.isLocked = ko.observable(false);
        self.imageReloadTimer = undefined

        // Lens calibration status needed in this viewModel.
        // TODO make it a part of the mrb state (when we have a state wrapper)
        self.lensDaemonAlive = ko.observable(false);
        /**
         * lazy-loading manually implemented.
         * Only returns an URL if the image element is visible.
         */
        self.statusRawImageUrl = ko.computed(function () {
            return self.settingsActive() && self.cameraSettingsActive()
                ? self.camera.availablePicUrl()["raw"]
                : null;
        });

        // ---------------- CAMERA STATUS ----------------
        // If either of the other two requirements are not met (lid open, operational),
        // we say that the markers were not found (if they were, of course)
        self.fourMarkersFound = ko.computed(function () {
            return (
                self.readyToLaser.lid_fully_open() &&
                self.statusOnlyOperational() &&
                self.camera.markerState() === 4
            );
        });

        // If Mr Beam is not locked, printing or paused, we tell to the user it's operational.
        // state.isOperational wouldn't work, because all of the others are substates of it.
        self.statusOnlyOperational = ko.computed(function () {
            return (
                !self.isLocked() &&
                !self.state.isPrinting() &&
                !self.state.isPaused()
            );
        });

        self.cameraStatusOk = ko.computed(function () {
            return (
                self.readyToLaser.lid_fully_open() &&
                self.statusOnlyOperational() &&
                self.fourMarkersFound() &&
                !self.camera.needsCornerCalibration()
            ); // This already includes the other two, but just to see it more clear
        });

        self.lidMessage = ko.computed(function () {
            return self.readyToLaser.lid_fully_open()
                ? gettext("The lid is open")
                : gettext(
                      "The lid is closed: Please open the lid to start the camera"
                  );
        });

        self.onlyOperationalMessage = ko.computed(function () {
            if (self.isLocked()) {
                return gettext(
                    "Mr Beam is not homed: Please go to the working area and do a Homing Cycle"
                );
            } else if (self.state.isPrinting() || self.state.isPaused()) {
                return gettext(
                    "Mr Beam is currently performing a laser job. The camera does not work during a laser job"
                );
            } else if (self.state.isOperational()) {
                return gettext("Mr Beam is in state Operational");
            } else {
                return gettext(
                    "Mr Beam is not in state Operational: The camera does not work during a laser job"
                );
            }
        });

        self.markersMessage = ko.computed(function () {
            let notFound = [];
            for (const [marker, found] of Object.entries(
                self.camera.markersFound
            )) {
                if (!found()) {
                    notFound.push(self.camera.MARKER_DESCRIPTIONS[marker]);
                }
            }
            let notFoundStr = notFound.join(", ");

            if (!self.fourMarkersFound() && notFound.length === 0) {
                return gettext("No markers found since camera did not launch");
            } else if (self.fourMarkersFound()) {
                return gettext("All 4 pink corner markers are recognized");
            } else {
                return (
                    gettext(
                        "Not all pink corner markers are recognized. Missing markers: "
                    ) + notFoundStr
                );
            }
        });

        self.markerDetectionMode = function () {
            // retrieve the detection mode from the back end
            remember = self.settings.plugins.mrbeam.cam.remember_markers_across_sessions();
            if (remember === undefined) return "reliable";
            else return remember ? "reliable" : "accurate";
        };

        self.setMarkerDetectionMode = function (val, event) {
            // Default is "Reliable". If the user changed it, set "Accurate".
            if (event !== undefined)
                self.setMarkerDetectionMode(event.target.value);
            else if (val === undefined) {
                self.setMarkerDetectionModeBtn(self.markerDetectionMode());
            } else {
                // self.settings.plugins.mrbeam.cam.remember_markers_across_sessions(true);
                let _data = {
                    cam: {
                        remember_markers_across_sessions: val === "reliable",
                    },
                };
                $("#camera_settings_marker_detection button").prop(
                    "disabled",
                    true
                );
                OctoPrint.settings
                    .savePluginSettings("mrbeam", _data)
                    .done(
                        // "remember_markers_across_sessions",
                        function (data, status, xhr) {
                            console.log(
                                "simpleApiCall response for saving remember_markers_across_sessions: ",
                                data,
                                status,
                                xhr
                            );
                            self.setMarkerDetectionModeBtn(val === "reliable");
                        }
                    )
                    .fail(function () {
                        console.error(
                            "Unable to save remember_markers_across_sessions: ",
                            data,
                            status,
                            xhr
                        );
                        new PNotify({
                            title: gettext(
                                "Error while selecting the marker detection mode"
                            ),
                            text: _.sprintf(
                                gettext(
                                    "Unable to select the marker detection mode at the moment."
                                )
                            ),
                            type: "error",
                            hide: true,
                        });
                        self.setMarkerDetectionModeBtn(val !== "reliable");
                    });
            }
        };

        self.setMarkerDetectionModeBtn = function (mode) {
            // Sets the buttons to the correct mode and enables them
            // mode : "accurate" or "reliable" or true (reliable) or false(accurate)
            if (typeof mode === "boolean")
                mode = mode ? "reliable" : "accurate";
            $('#camera_settings_marker_detection button[value="' + mode + '"]')
                .addClass("active")
                .prop("disabled", false)
                .siblings()
                .removeClass("active")
                .prop("disabled", false);
        };

        self.onAllBound = function () {
            self.setMarkerDetectionMode();
            new MutationObserver(
                self._testCameraSettingsActive
            ).observe(
                document.getElementById("settings_plugin_mrbeam_camera"),
                { attributes: true }
            );
        };

        self.onStartupComplete = function () {
            $("#settings_plugin_mrbeam_camera_link").click(function () {
                self.changeUserView("settings");
            });
            self.checkCalibStatus = ko.computed(function () {
                // Get the state of the chessboard detection thread
                // Can only allow to start the lens calibration if
                // it is dead
                if (
                    !window.mrbeam.isWatterottMode() &&
                    self.loginState.loggedIn()
                ) {
                    OctoPrint.simpleApiCommand(
                        "mrbeam",
                        "calibration_get_lens_calib_alive",
                        {}
                    )
                        .done(function (response) {
                            self.lensDaemonAlive(response.alive);
                        })
                        .fail(function (response) {
                            new PNotify({
                                title: gettext(
                                    "Failed to update the Lens Calibration Status."
                                ),
                                text: gettext(
                                    "There is nothing to worry about, but here is some extra information :\n" +
                                        response.responseText
                                ),
                                type: "warning",
                                hide: true,
                            });
                        });
                }
            });
            self.cameraSettingsActive.subscribe(self.cameraSettingsActiveChanged)
        };

        self.onBeforeBinding = function () {
            self.settings = self.settingsViewModel.settings;
        };

        self.onSettingsShown = function () {
            self.settingsActive(true);
            self._testCameraSettingsActive();
            self._updateIsLocked();
        };

        self.onSettingsHidden = function () {
            self.settingsActive(false);
            self._testCameraSettingsActive();
        };

        // It's necessary to read state.isLocked and update the value manually because this is injected after the
        // binding is done (from the MotherVM)
        self._updateIsLocked = function () {
            if (self.state.isLocked()) {
                self.isLocked(true);
            } else {
                self.isLocked(false);
            }
        };

        self.onDataUpdaterPluginMessage = function (plugin, data) {
            if ("event" in data) {
                // calibration daemon state should be synchronised
                // even when not showing the settings screen
                // TODO AXEL : This doesn't seem to work ...
                console.log(data);
                if (
                    data["event"] == "lensCalibStart" ||
                    data["event"] == "lensCalibAlive"
                ) {
                    self.lensDaemonAlive(true);
                } else if (data["event"] == "lensCalibExit") {
                    self.lensDaemonAlive(false);
                }
            }
        };
        self._testCameraSettingsActive = function () {
            let isActive =
                self.settingsActive() &&
                $("#settings_plugin_mrbeam_camera").hasClass("active");
            self.cameraSettingsActive(isActive);
        };

        // self.larger = function(){
        // 	var val = Math.min(self.calSvgScale() + 1, 10);
        // 	self.calSvgScale(val);
        // }
        // self.smaller = function(){
        // 	var val = Math.max(self.calSvgScale() - 1, 1);
        // 	self.calSvgScale(val);
        // }
        // self.move = function(dx, dy){
        // 	self.calSvgDx(self.calSvgDx()+dx);
        // 	self.calSvgDy(self.calSvgDy()+dy);
        // }
        // self.resetMove = function(){
        // 	self.calSvgDx(0);
        // 	self.calSvgDy(0);
        // }

        self.changeUserView = function (toView) {
            Object.entries(CUSTOMER_CAMERA_VIEWS).forEach(
                ([view_name, view_id]) => {
                    if (view_name === toView) {
                        $(view_id).show();
                    } else {
                        $(view_id).hide();
                    }
                }
            );
        };

        self.cameraSettingsActiveChanged = function(newvalue){
            if (newvalue){
                OctoPrint.simpleApiCommand("mrbeam", "take_undistorted_picture", {})
                self.imageReloadTimer = setInterval(function () {
                    OctoPrint.simpleApiCommand("mrbeam", "take_undistorted_picture", {})
                }, 3000);
            }else{
                if (self.imageReloadTimer){clearInterval(self.imageReloadTimer)}
            }
        }
    }

    // view model class, parameters for constructor, container to bind to
    OCTOPRINT_VIEWMODELS.push([
        CameraSettingsViewModel,

        // e.g. loginStateViewModel, settingsViewModel, ...
        [
            "cameraViewModel",
            "printerStateViewModel",
            "readyToLaserViewModel",
            "settingsViewModel",
            "workingAreaViewModel",
            "loginStateViewModel",
        ],

        // e.g. #settings_plugin_mrbeam, #tab_plugin_mrbeam, ...
        ["#camera_settings_view"],
    ]);
});
