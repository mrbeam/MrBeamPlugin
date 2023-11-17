/**
 * Created by andy on 03/03/2017.
 */
$(function () {
    function ReadyToLaserViewModel(params) {
        var self = this;
        window.mrbeam.viewModels["readyToLaserViewModel"] = self;

        self.ESTIMATED_DURATION_PLACEHOLDER = " ?";

        self.loginState = params[0];
        self.state = params[1];
        self.laserCutterProfiles = params[2];
        self.mrb_state = params[3];

        self.dialogElement = $(); // initialize not to undefined
        self.gcodeFile = undefined;

        self.jobTimeEstimationString = ko.observable(
            self.ESTIMATED_DURATION_PLACEHOLDER
        );
        self.jobTimeEstimationCalculated = ko.observable(false);

        self.debug = false;

        const Status = {
            READY_TO_LASER: "READY_TO_LASER",
            FAN_NOT_CONNECTED: "FAN_NOT_CONNECTED",
            FAN_NOT_ON_EXTERNAL_POWER: "FAN_NOT_ON_EXTERNAL_POWER",
            LID_OPEN: "LID_OPEN",
            COOLING: "COOLING",
            PAUSED: "PAUSED",
            UNKNOWN: "UNKNOWN",
            OK: "OK",
        };
        self.status = Status;

        self.ready_to_laser_state = ko
            .computed(function () {
                const isRTLMode = self.mrb_state.isRTLMode();
                const isPaused = self.mrb_state.isPaused();
                if (isRTLMode || isPaused) {
                    if (self.mrb_state.isAirfilterConnected() === false) {
                        return Status.FAN_NOT_CONNECTED;
                    } else if (
                        self.mrb_state.isAirfilterExternalPowered() === false
                    ) {
                        return Status.FAN_NOT_ON_EXTERNAL_POWER;
                    } else if (self.mrb_state.isInterlocksClosed() === false) {
                        return Status.LID_OPEN;
                    } else if (self.mrb_state.isCooling()) {
                        return Status.COOLING;
                    } else if (isRTLMode) {
                        return Status.READY_TO_LASER;
                    } else if (isPaused) {
                        return Status.PAUSED;
                    } else {
                        return Status.UNKNOWN;
                    }
                } else {
                    return Status.OK;
                }
            })
            .extend({ deferred: true }); // deferred to prevent multiple changes in a short time

        self.is_pause_mode = ko.computed(function () {
            const rtl_state = self.ready_to_laser_state();
            return rtl_state === Status.PAUSED || rtl_state === Status.COOLING;
        });
        self.show_dialog = ko
            .computed(function () {
                return self.ready_to_laser_state() !== Status.OK;
            })
            .extend({ rateLimit: 300 }); // rateLimit to prevent flickering

        //subscribe to show dialog to show or hide the modal
        self.show_dialog.subscribe(function (newValue) {
            self.setDialog();
        });

        self.lid_open = ko.computed(function () {
            return self.ready_to_laser_state() === Status.LID_OPEN;
        });
        self.fan_not_connected = ko.computed(function () {
            return self.ready_to_laser_state() === Status.FAN_NOT_CONNECTED;
        });
        self.fan_not_on_external_power = ko.computed(function () {
            return (
                self.ready_to_laser_state() === Status.FAN_NOT_ON_EXTERNAL_POWER
            );
        });
        self.cooling = ko.computed(function () {
            return self.ready_to_laser_state() === Status.COOLING;
        });
        self.ready_to_laser = ko.computed(function () {
            return self.ready_to_laser_state() === Status.READY_TO_LASER;
        });
        self.paused = ko.computed(function () {
            return self.ready_to_laser_state() === Status.PAUSED;
        });

        self.debug_log = function (triggerEvent) {
            if (self.debug) {
                console.log(
                    "ReadyToLaserViewModel.debug: (" +
                        triggerEvent +
                        ") is_rtl_mode: " +
                        self.ready_to_laser() +
                        ", ready_to_laser_state: " +
                        self.ready_to_laser_state() +
                        ", paused: " +
                        self.paused() +
                        ", is_pause_mode: " +
                        self.is_pause_mode() +
                        ", lid_open: " +
                        self.lid_open() +
                        ", is_cooling_mode: " +
                        self.cooling() +
                        ", is_fan_connected" +
                        self.fan_not_connected() +
                        ", fan_not_on_external_power" +
                        self.fan_not_on_external_power() +
                        ", $('#ready_to_laser_dialog').is(':visible'): " +
                        $("#ready_to_laser_dialog").is(":visible") +
                        ", $('#laser_job_done_dialog').is(':visible'): " +
                        $("#laser_job_done_dialog").is(":visible") +
                        ", mrb_state: " +
                        JSON.stringify(window.mrbeam.mrb_state)
                );
            }
        };

        self.onStartupComplete = function () {
            // I think this should already be done in on Startup()
            // But I do not want to change it  shortly before a rlease.
            self.dialogElement = $("#ready_to_laser_dialog");

            $("#laser_button").on("click", function () {
                self.resetJobTimeEstimation();
            });
            self.setDialog();

            if (MRBEAM_ENV_LOCAL === "DEV") {
                $(".dev_start_button").on("click", function () {
                    console.log("dev_start_button pressed...");
                    self._sendReadyToLaserRequest(true, true);
                });
            }
            self.onEventReadyToLaserStart = function (payload) {
                self._fromData(payload, "onEventReadyToLaserStart");
            };

            self.onEventReadyToLaserCanceled = function (payload) {
                self._fromData(payload, "onEventReadyToLaserCanceled");
            };

            self.onEventPrintStarted = function (payload) {
                self._fromData(payload, "onEventPrintStarted");
            };

            self.onEventPrintPaused = function (payload) {
                self._fromData(payload, "onEventPrintPaused");
            };

            self.onEventPrintResumed = function (payload) {
                self._fromData(payload, "onEventPrintResumed");
            };

            self.onEventPrintCancelled = function (payload) {
                self._setReadyToLaserCancel(false);
                self._fromData(payload, "onEventPrintCancelled");
            };

            self.fromCurrentData = function (data) {
                self._fromData(data);
            };

            self.onDataUpdaterPluginMessage = function (plugin, data) {
                if (plugin !== MRBEAM.PLUGIN_IDENTIFIER) {
                    return;
                }
                if (MRBEAM.STATE_KEY in data) {
                    self._fromData(data, "onDataUpdaterPluginMessage");
                }
            };
        }; // end onStartupComplete

        self.onEventJobTimeEstimated = function (payload) {
            self.formatJobTimeEstimation(
                payload["job_time_estimation_rounded"]
            );
            self._fromData(payload);
        };

        self.onEventMrbPluginVersion = function (payload) {
            self._fromData(payload);
        };

        /**
         * this is called from the outside once the slicing is done
         * @param gcodeFile
         */
        self.setGcodeFile = function (gcodeFile) {
            self.gcodeFile = gcodeFile;
        };

        self.resetJobTimeEstimation = function () {
            self.jobTimeEstimationString(self.ESTIMATED_DURATION_PLACEHOLDER);
            self.jobTimeEstimationCalculated(false);
        };

        self.formatJobTimeEstimation = function (seconds) {
            seconds = Number(seconds);
            if (seconds < 0) {
                self.resetJobTimeEstimation();
            } else {
                let hours = Math.floor(seconds / 3600);
                let minutes = Math.floor((seconds % 3600) / 60);
                let duration;

                if (hours === 0) {
                    if (minutes === 1) {
                        duration = "" + minutes + " " + gettext("minute");
                    } else {
                        duration = "" + minutes + " " + gettext("minutes");
                    }
                } else if (hours === 1) {
                    if (minutes < 10) {
                        minutes = "0" + minutes;
                    }
                    duration = hours + ":" + minutes + " " + gettext("hour");
                } else {
                    if (minutes < 10) {
                        minutes = "0" + minutes;
                    }
                    duration = hours + ":" + minutes + " " + gettext("hours");
                }

                self.jobTimeEstimationString("  ~ " + duration);
                self.jobTimeEstimationCalculated(true);
            }
        };

        // bound to both cancel buttons
        self.cancel_btn = function () {
            self._debugDaShit("cancel_btn() ");
            if (self.is_pause_mode()) {
                self.state.cancel();
            } else {
                self._setReadyToLaserCancel(true);
            }
        };

        self._fromData = function (payload, event) {
            // this is just for debugging
            if (event) {
                self.debug_log(event);
                setTimeout(function () {
                    self.debug_log(event);
                }, 1000);
            }

            if (
                !payload ||
                !(MRBEAM.STATE_KEY in payload) ||
                !payload[MRBEAM.STATE_KEY]
            ) {
                return;
            }
            let mrb_state = payload[MRBEAM.STATE_KEY];
            if (mrb_state) {
                self.updateSettingsAbout();
            }
        };

        self._setReadyToLaserCancel = function (notifyServer) {
            self._debugDaShit(
                "_setReadyToLaserCancel() notifyServer: ",
                notifyServer
            );
            self.dialogElement.modal("hide");
            if (notifyServer) {
                self._sendCancelReadyToLaserMode();
            }
            self.gcodeFile = undefined;
        };

        self.setDialog = function () {
            if (self.show_dialog()) {
                self.showDialog();
            } else if (!self.show_dialog()) {
                self.dialogElement.modal("hide");
            } else {
                self._debugDaShit("setDialog() nothing to do");
            }
        };

        self.showDialog = function (force) {
            self._debugDaShit("showDialog() " + (force ? "force!" : ""));

            var param = "show";
            if (self.is_pause_mode()) {
                // not dismissible in paused mode
                param = {
                    backdrop: "static",
                    keyboard: MRBEAM_ENV_LOCAL === "DEV",
                };
            }

            self._debugDaShit("showDialog() dialogIsInTransition <= true");
            self._debugDaShit("showDialog() show");
            self.dialogElement.modal(param);
        };

        self.refreshBindings = function () {
            ko.cleanNode(document.getElementById("ready_to_laser_dialog"));
            ko.applyBindings(
                self,
                document.getElementById("ready_to_laser_dialog")
            );
        };

        self._sendCancelReadyToLaserMode = function () {
            let data = { rtl_cancel: true };
            OctoPrint.simpleApiCommand(
                MRBEAM.PLUGIN_IDENTIFIER,
                SimpleApiCommands.READY_TO_LASER,
                data
            );
        };

        self._sendReadyToLaserRequest = function (ready, dev_start_button) {
            let data = { gcode: self.gcodeFile, ready: ready };
            if (dev_start_button) {
                data.dev_start_button = "start";
            }
            OctoPrint.simpleApiCommand(
                MRBEAM.PLUGIN_IDENTIFIER,
                SimpleApiCommands.READY_TO_LASER,
                data
            );
        };

        self.updateSettingsAbout = function () {
            $("#settings_mrbeam_about_support_mrb_state").html(
                JSON.stringify(window.mrbeam.mrb_state)
            );

            // it's ugly to have this here.
            var msg = [
                "MRBEAM_MODEL: " + MRBEAM_MODEL,
                "MRBEAM_HOSTNAME: " + MRBEAM_HOSTNAME,
                "MRBEAM_SERIAL: " + MRBEAM_SERIAL,
                "MRBEAM_LASER_HEAD_SERIAL: " + MRBEAM_LASER_HEAD_SERIAL,
                "MRBEAM_GRBL_VERSION: " + MRBEAM_GRBL_VERSION,
                "MRBEAM_ENV_SUPPORT_MODE: " + MRBEAM_ENV_SUPPORT_MODE,
                "BEAMOS_IMAGE: " + BEAMOS_IMAGE,
                "MRBEAM_LANGUAGE: " + MRBEAM_LANGUAGE,
                "BEAMOS_VERSION: " + MRBEAM_PLUGIN_VERSION,
                "MRBEAM_SW_TIER: " + MRBEAM_SW_TIER,
                "MRBEAM_ENV: " + MRBEAM_ENV,
                "read_to_laser_state: " + self.ready_to_laser_state(),
                "isAirfilterConnected: " +
                    self.mrb_state.isAirfilterConnected(),
                "isAirfilterExternalPowered: " +
                    self.mrb_state.isAirfilterExternalPowered(),
                "isInterlocksClosed: " + self.mrb_state.isInterlocksClosed(),
                "isCooling: " + self.mrb_state.isCooling(),
                "isRTLMode: " + self.mrb_state.isRTLMode(),
                "isPaused: " + self.mrb_state.isPaused(),
                "isLidFullyOpen: " + self.mrb_state.isLidFullyOpen(),
            ];
            $("#settings_mrbeam_debug_state").html(
                msg.join("\n") +
                    "\n" +
                    JSON.stringify(window.mrbeam.mrb_state, null, 2)
            );
        };

        self._debugDaShit = function (stuff) {
            if (self.debug) {
                if (typeof stuff === "object") {
                    console.log("_debugDaShit " + stuff.shift(), stuff);
                } else {
                    console.log("_debugDaShit " + stuff);
                }
            }
        };
    }

    OCTOPRINT_VIEWMODELS.push([
        ReadyToLaserViewModel,
        [
            "loginStateViewModel",
            "printerStateViewModel",
            "laserCutterProfilesViewModel",
            "mrbStateViewModel",
        ],
        ["#ready_to_laser_dialog"],
    ]);
});
