$(function () {
    function LaserheadChangedViewModel(params) {
        let self = this;
        window.mrbeam.viewModels["LaserheadChangedViewModel"] = self;

        self.settings = params[0];
        self.loginState = params[1];
        self.laserhead_model_id = ko.observable();
        self.laserhead_model_supported = ko.observable();
        self.step = ko.observable(1);

        self.laserhead_changed_step1_laserhead_s_show = ko.computed(
            function () {
                return (
                    self.laserhead_model_id() === mrbeam.laserhead_model.S &&
                    self.step() === 1
                );
            }
        );

        self.laserhead_changed_step1_laserhead_x_show = ko.computed(
            function () {
                return (
                    self.laserhead_model_id() === mrbeam.laserhead_model.X &&
                    self.step() === 1
                );
            }
        );
        self.laserhead_changed_step2_laserhead_x_show = ko.computed(
            function () {
                return (
                    self.laserhead_model_id() === mrbeam.laserhead_model.X &&
                    self.step() === 2
                );
            }
        );
        self.laserhead_changed_step3_laserhead_x_show = ko.computed(
            function () {
                return (
                    self.laserhead_model_id() === mrbeam.laserhead_model.X &&
                    self.step() === 3
                );
            }
        );
        self.laserhead_changed_show_previous_button = ko.computed(function () {
            return self.step() > 1;
        });

        self.maxSteps = ko.computed(function () {
            if (self.laserhead_model_id() === mrbeam.laserhead_model.X) {
                return 3;
            } else {
                return 1;
            }
        });

        self.lastStep = ko.computed(function () {
            return self.step() >= self.maxSteps();
        });

        self.onUserLoggedIn = function () {
            if (self.loginState.currentUser?.()?.active) {
                if (self.settings.settings.plugins.mrbeam.laserheadChanged()) {
                    self.laserhead_model_id(
                        self.settings.settings.plugins.mrbeam.laserhead.model_id()
                    );
                    self.laserhead_model_supported(
                        self.settings.settings.plugins.mrbeam.laserhead.model_supported()
                    );
                    $("#laserhead_changed").modal("show");
                }
            }
        };

        self.laserhead_changed_next_step = function () {
            if (!self.lastStep()) {
                self.step(self.step() + 1);
            }
        };

        self.laserhead_changed_previous_step = function () {
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
                        "simpleApiCall response for saving laserhead change detection: "
                    );
                })
                .fail(function () {
                    self.settings.requestData();
                    console.error(
                        "Unable to save laserhead change detection state: ",
                        data
                    );
                    new PNotify({
                        title: gettext(
                            "Error while saving laserhead change detection!"
                        ),
                        text: _.sprintf(
                            gettext(
                                "Unable to save laserhead change detection at the moment.%(br)sCheck connection to Mr Beam and try again."
                            ),
                            { br: "<br/>" }
                        ),
                        type: "error",
                        hide: true,
                    });
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
