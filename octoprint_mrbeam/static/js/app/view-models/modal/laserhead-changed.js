$(function () {
    function LaserheadChangedViewModel(params) {
        let self = this;
        window.mrbeam.viewModels["LaserheadChangedViewModel"] = self;

        self.settings = params[0];
        self.loginState = params[1];
        self.laserheadModelId = ko.observable();
        self.laserheadModelSupported = ko.observable();
        self.step = ko.observable(1);

        self.laserheadChangedShowPreviousButton = ko.computed(function () {
            return self.step() > 1;
        });

        self.maxSteps = ko.computed(function () {
            if (self.laserheadModelId() === mrbeam.laserheadModel.X) {
                return 3;
            } else {
                return 1;
            }
        });

        self.lastStep = ko.computed(function () {
            return self.step() >= self.maxSteps();
        });

        self.laserheadChangedShowStepForLaserhead = function (step, laserhead) {
            return (
                self.laserheadModelId() === laserhead && self.step() === step
            );
        };

        self.showStepForLaserheadS = function (step) {
            return ko.computed(function () {
                return self.laserheadChangedShowStepForLaserhead(
                    step,
                    mrbeam.laserheadModel.S
                );
            }, self);
        };

        self.showStepForLaserheadX = function (step) {
            return ko.computed(function () {
                return self.laserheadChangedShowStepForLaserhead(
                    step,
                    mrbeam.laserheadModel.X
                );
            }, self);
        };

        self.onUserLoggedIn = function () {
            if (self.loginState.currentUser?.()?.active) {
                if (self.settings.settings.plugins.mrbeam.laserheadChanged()) {
                    self.laserheadModelId(
                        self.settings.settings.plugins.mrbeam.laserhead.model_id()
                    );
                    self.laserheadModelSupported(
                        self.settings.settings.plugins.mrbeam.laserhead.model_supported()
                    );
                    $("#laserhead_changed").modal("show");
                }
            }
        };

        self.laserheadChangedNextStep = function () {
            if (!self.lastStep()) {
                self.step(self.step() + 1);
            }
        };

        self.laserheadChangedPreviousStep = function () {
            if (self.step() > 1) {
                self.step(self.step() - 1);
            }
        };

        self.laserheadChangeAcknowledged = function () {
            OctoPrint.simpleApiCommand(
                "mrbeam",
                "laserhead_change_acknowledged",
                {}
            )
                .done(function () {
                    console.log(
                        "simpleApiCall response for saving laser head change detection: "
                    );
                })
                .fail(function () {
                    self.settings.requestData();
                    console.error(
                        "Unable to save laser head change detection state: ",
                        data
                    );
                    new PNotify({
                        title: gettext(
                            "Error while saving laser head change detection!"
                        ),
                        text: _.sprintf(
                            gettext(
                                "Unable to save laser head change detection at the moment.%(br)sCheck connection to Mr Beam and try again."
                            ),
                            { br: "<br/>" }
                        ),
                        type: "error",
                        hide: true,
                    });
                });
        };

        self.shutdownDevice = function () {
            showConfirmationDialog({
                message: gettext("You are about to shutdown the device."),
                question: gettext(
                    "Do you want to continue to shut down the device?"
                ),
                cancel: gettext("Cancel"),
                proceed: gettext("Shutdown"),
                proceedClass: "primary",
                onproceed: function () {
                    OctoPrint.post("api/system/commands/core/shutdown").fail(
                        function (error) {
                            console.error(
                                "Unable to shut down device: ",
                                error
                            );
                            new PNotify({
                                title: gettext(
                                    "The device could not be shut down."
                                ),
                                text: gettext(
                                    "There was an error while shutting down the device. Please try again."
                                ),
                                type: "error",
                                hide: true,
                            });
                        }
                    );
                },
            });
        };
    }

    // view model class, parameters for constructor, container to bind to
    OCTOPRINT_VIEWMODELS.push([
        LaserheadChangedViewModel,

        // e.g. loginStateViewModel, settingsViewModel, ...
        ["settingsViewModel", "loginStateViewModel"],

        // e.g. #settings_plugin_mrbeam, #tab_plugin_mrbeam, ...
        ["#laserhead_changed"],
    ]);
});
