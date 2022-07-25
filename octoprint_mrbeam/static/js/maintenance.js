$(function () {
    function Maintenance(params) {
        let self = this;
        window.mrbeam.viewModels["maintenance"] = self;

        self.settings = params[0];
        self.analytics = params[1];
        self.userSettings = params[2];
        self.loginState = params[3];

        self.PREFILTER = gettext("pre-filter");
        self.PREFILTER_WARNING_TITLE = gettext(
            "Pre-Filter capacity reached 70%"
        );
        self.PREFILTER_WARNING_TEXT = gettext(
            "At this level, we highly recommend having a visual check on the pre-filter to make sure the estimation is representing the fill level of your filter. This heavily depends on the material you are processing with your device."
        );
        self.CARBON_FILTER = gettext("main filter");
        self.CARBON_FILTER_WARNING_TITLE = gettext(
            "Main-Filter capacity reached 70%"
        );
        self.CARBON_FILTER_WARNING_TEXT = gettext(
            "At this level, we highly recommend to have a visual check on the main-filter to make sure the estimation is representing the fill level of your filter. This heavily depends on the material you are processing with your device."
        );
        self.LASER_HEAD = gettext("laser head");
        self.GANTRY = gettext("mechanics");
        self.PREFILTER_LIFESPAN = 40;
        self.CARBON_FILTER_LIFESPAN = 280;
        self.LASER_HEAD_LIFESPAN = 40;
        self.GANTRY_LIFESPAN = 100;
        self.WARN_IF_CRITICAL_PERCENT = 70;
        self.WARN_IF_USED_PERCENT = 100;

        self.totalUsage = ko.observable(0);
        self.prefilterUsage = ko.observable(0);
        self.carbonFilterUsage = ko.observable(0);
        self.laserHeadUsage = ko.observable(0);
        self.gantryUsage = ko.observable(0);

        self.needsGantryMaintenance = ko.observable(true);
        self.componentToReset = ko.observable("");
        self.laserHeadSerial = ko.observable("");

        self.prefilterLifespanHours = _.sprintf(gettext("/%(lifespan)s hrs"), {
            lifespan: self.PREFILTER_LIFESPAN,
        });
        self.carbonFilterLifespanHours = _.sprintf(
            gettext("/%(lifespan)s hrs"),
            { lifespan: self.CARBON_FILTER_LIFESPAN }
        );
        self.laserHeadLifespanHours = _.sprintf(gettext("/%(lifespan)s hrs"), {
            lifespan: self.LASER_HEAD_LIFESPAN,
        });
        self.gantryLifespanHours = _.sprintf(gettext("/%(lifespan)s hrs"), {
            lifespan: self.GANTRY_LIFESPAN,
        });

        self.totalUsageHours = ko.computed(function () {
            return Math.floor(self.totalUsage() / 36) / 100;
        });
        self.prefilterUsageHours = ko.computed(function () {
            return Math.floor(self.prefilterUsage() / 3600);
        });
        self.carbonFilterUsageHours = ko.computed(function () {
            return Math.floor(self.carbonFilterUsage() / 3600);
        });
        self.laserHeadUsageHours = ko.computed(function () {
            return Math.floor(self.laserHeadUsage() / 3600);
        });
        self.gantryUsageHours = ko.computed(function () {
            return Math.floor(self.gantryUsage() / 3600);
        });

        self.optimizeParameterPercentageValues = function (val) {
            return Math.min(roundDownToNearest10(val), 100);
        };
        self.prefilterPercent = ko.computed(function () {
            return self.optimizeParameterPercentageValues(
                (self.prefilterUsageHours() / self.PREFILTER_LIFESPAN) * 100
            );
        });
        self.carbonFilterPercent = ko.computed(function () {
            return self.optimizeParameterPercentageValues(
                (self.carbonFilterUsageHours() / self.CARBON_FILTER_LIFESPAN) *
                    100
            );
        });
        self.laserHeadPercent = ko.computed(function () {
            return self.optimizeParameterPercentageValues(
                (self.laserHeadUsageHours() / self.LASER_HEAD_LIFESPAN) * 100
            );
        });
        self.gantryPercent = ko.computed(function () {
            return self.optimizeParameterPercentageValues(
                (self.gantryUsageHours() / self.GANTRY_LIFESPAN) * 100
            );
        });

        self.prefilterShowEarlyWarning = ko.computed(function () {
            return self.prefilterPercent() >= self.WARN_IF_CRITICAL_PERCENT;
        });
        self.carbonFilterShowEarlyWarning = ko.computed(function () {
            return self.carbonFilterPercent() >= self.WARN_IF_CRITICAL_PERCENT;
        });
        self.prefilterShowWarning = ko.computed(function () {
            return self.prefilterPercent() >= self.WARN_IF_USED_PERCENT;
        });
        self.carbonFilterShowWarning = ko.computed(function () {
            return self.carbonFilterPercent() >= self.WARN_IF_USED_PERCENT;
        });
        self.laserHeadShowWarning = ko.computed(function () {
            return self.laserHeadPercent() >= self.WARN_IF_USED_PERCENT;
        });
        self.gantryShowWarning = ko.computed(function () {
            return self.gantryPercent >= self.WARN_IF_USED_PERCENT;
        });

        self.needsMaintenance = ko.computed(function () {
            return (
                self.prefilterShowWarning() ||
                self.carbonFilterShowWarning() ||
                self.laserHeadShowWarning() ||
                self.gantryShowWarning()
            );
        });
        self.needsprefilterEarlyWarning = ko.computed(function () {
            return self.prefilterShowEarlyWarning();
        });
        self.needsCarbonFilterEarlyWarning = ko.computed(function () {
            return self.carbonFilterShowEarlyWarning();
        });

        self.componentResetQuestion = ko.computed(function () {
            if (self.componentToReset() === self.PREFILTER) {
                return gettext("Did you change the pre-filter?");
            } else if (self.componentToReset() === self.CARBON_FILTER) {
                return gettext("Did you change the main filter?");
            } else if (self.componentToReset() === self.LASER_HEAD) {
                return gettext("Did you clean the laser head?");
            } else if (self.componentToReset() === self.GANTRY) {
                return gettext("Did you clean the mechanics?");
            }
        });

        // The settings are already loaded here, Gina confirmed.
        self.onBeforeBinding = function () {
            self.loadUsageValues();
        };

        self.onUserLoggedIn = function (user) {
            if (
                self.needsprefilterEarlyWarning() &&
                !user?.settings?.mrbeam?.filterWarnings?.prefilter
            ) {
                self.notifyFilterWarning(
                    self.PREFILTER_WARNING_TITLE,
                    self.PREFILTER_WARNING_TEXT
                );
                self.saveUserSettings({
                    prefilter: true,
                });
            }
            if (
                self.needsCarbonFilterEarlyWarning() &&
                !user?.settings?.mrbeam?.filterWarnings?.carbonFilter
            ) {
                self.notifyFilterWarning(
                    self.CARBON_FILTER_WARNING_TITLE,
                    self.CARBON_FILTER_WARNING_TEXT
                );
                self.saveUserSettings({
                    carbonFilter: true,
                });
            }
            if (self.needsMaintenance()) {
                self.notifyMaintenanceRequired();
            }
        };

        self.onAllBound = function () {
            // Add here the new links to have analytics of the clicks:
            let links = [
                "prefilter_shop_link",
                "carbon_filter_shop_link",
                "laser_head_shop_link",
                "laser_head_kb_link",
                "mechanical_parts_kb_link",
            ];

            links.forEach(function (linkId) {
                $("#" + linkId).click(function () {
                    let payload = {
                        link: linkId,
                    };
                    self.analytics.send_fontend_event("link_click", payload);
                });
            });
            self.updateSettingsAbout();
        };

        self.resetPrefilterUsage = function () {
            // Set the warning message key to false so that it will show again when the value reaches 70%
            self.saveUserSettings({
                prefilter: false,
            });

            // Reset all existing click listeners (in case the user exited the "are you sure" modal before without clicking on Yes)
            $("#reset_counter_are_you_sure").off("click");

            self.componentToReset(self.PREFILTER);
            $("#reset_counter_are_you_sure")
                .modal({
                    backdrop: "static",
                    keyboard: false,
                })
                .one("click", "#reset_counter_btn", function () {
                    console.log("Resetting pre-filter usage counter");
                    OctoPrint.simpleApiCommand(
                        "mrbeam",
                        "reset_prefilter_usage",
                        {}
                    )
                        .done(function () {
                            self.prefilterUsage(0);
                        })
                        .fail(function () {
                            console.error(
                                "Unable to reset pre-filter usage counter."
                            );
                        });
                });
        };

        self.resetCarbonFilterUsage = function () {
            // Set the warning message key to false so that it will show again when the value reaches 70%
            self.saveUserSettings({
                carbonFilter: false,
            });

            // Reset all existing click listeners (in case the user exited the "are you sure" modal before without clicking on Yes)
            $("#reset_counter_are_you_sure").off("click");

            self.componentToReset(self.CARBON_FILTER);
            $("#reset_counter_are_you_sure")
                .modal({
                    backdrop: "static",
                    keyboard: false,
                })
                .one("click", "#reset_counter_btn", function () {
                    console.log("Resetting carbon filter usage counter");
                    OctoPrint.simpleApiCommand(
                        "mrbeam",
                        "reset_carbon_filter_usage",
                        {}
                    )
                        .done(function () {
                            self.carbonFilterUsage(0);
                        })
                        .fail(function () {
                            console.error(
                                "Unable to reset carbon filter usage counter."
                            );
                        });
                });
        };

        self.resetLaserHeadUsage = function () {
            // Reset all existing click listeners (in case the user exited the "are you sure" modal before without clicking on Yes)
            $("#reset_counter_are_you_sure").off("click");

            self.componentToReset(self.LASER_HEAD);
            $("#reset_counter_are_you_sure")
                .modal({
                    backdrop: "static",
                    keyboard: false,
                })
                .one("click", "#reset_counter_btn", function () {
                    console.log("Resetting laser head usage counter");
                    OctoPrint.simpleApiCommand(
                        "mrbeam",
                        "reset_laser_head_usage",
                        {}
                    )
                        .done(function () {
                            self.laserHeadUsage(0);
                        })
                        .fail(function () {
                            console.error(
                                "Unable to reset laser head usage counter."
                            );
                        });
                });
        };

        self.resetGantryUsage = function () {
            // Reset all existing click listeners (in case the user exited the "are you sure" modal before without clicking on Yes)
            $("#reset_counter_are_you_sure").off("click");

            self.componentToReset(self.GANTRY);
            $("#reset_counter_are_you_sure")
                .modal({
                    backdrop: "static",
                    keyboard: false,
                })
                .one("click", "#reset_counter_btn", function () {
                    console.log("Resetting gantry usage counter");
                    OctoPrint.simpleApiCommand(
                        "mrbeam",
                        "reset_gantry_usage",
                        {}
                    )
                        .done(function () {
                            self.gantryUsage(0);
                        })
                        .fail(function () {
                            console.error(
                                "Unable to reset gantry usage counter."
                            );
                        });
                });
        };

        self.onSettingsShown = function () {
            self.settings.requestData().done(function () {
                self.loadUsageValues();
                self.updateSettingsAbout();
            });
        };

        self.loadUsageValues = function () {
            self.needsGantryMaintenance(
                window.mrbeam.model.is_mrbeam2() ||
                    window.mrbeam.model.is_mrbeam2_dreamcut_ready1()
            );

            if (self.needsGantryMaintenance()) {
                self.gantryUsage(
                    self.settings.settings.plugins.mrbeam.usage.gantryUsage()
                );
            } else {
                self.gantryUsage(0);
            }

            self.totalUsage(
                self.settings.settings.plugins.mrbeam.usage.totalUsage()
            );
            self.prefilterUsage(
                self.settings.settings.plugins.mrbeam.usage.prefilterUsage()
            );
            self.carbonFilterUsage(
                self.settings.settings.plugins.mrbeam.usage.carbonFilterUsage()
            );
            self.laserHeadUsage(
                self.settings.settings.plugins.mrbeam.usage.laserHeadUsage()
            );
            self.laserHeadSerial(
                self.settings.settings.plugins.mrbeam.laserhead.serial()
            );
        };

        self.notifyMaintenanceRequired = function () {
            new PNotify({
                title: gettext("Maintenance required"),
                text: _.sprintf(
                    gettext(
                        "Regular maintenance on your Mr Beam is due.%(br)s Please check the %(open)smaintenance settings%(close)s for details."
                    ),
                    {
                        br: "<br>",
                        open: '<a href=\'#\' data-toggle="tab" id="settings_maintenance_link" style="font-weight:bold">',
                        close: "</a>",
                    }
                ),
                type: "warn",
                hide: false,
            });

            $("#settings_maintenance_link").on("click", function (event) {
                // Prevent url change
                event.preventDefault();
                // Open the "Settings" menu
                $("#settings_tab_btn").tab("show");
                // Go to the "Maintenance" tab
                $(
                    '[data-toggle="tab"][href="#settings_plugin_mrbeam_maintenance"]'
                ).trigger("click");
                // Close notification
                $('[title="Close"]')[0].click();

                // Write to analytics
                let payload = {
                    link: "settings_maintenance_link",
                };
                self.analytics.send_fontend_event("link_click", payload);
            });
        };

        self.notifyFilterWarning = function (
            NotificationTitle,
            NotificationText
        ) {
            new PNotify({
                title: NotificationTitle,
                text: NotificationText,
                type: "warn",
                hide: false,
            });
        };

        self.saveUserSettings = function (earlyWarningShown) {
            // save to user settings
            if (self.loginState?.currentUser()) {
                let mrbSettings = self.loginState.currentUser().settings.mrbeam;
                if (!("filterWarnings" in mrbSettings)) {
                    mrbSettings.filterWarnings = {};
                }
                if ("prefilter" in earlyWarningShown) {
                    mrbSettings.filterWarnings.prefilter =
                        earlyWarningShown.prefilter;
                } else if ("carbonFilter" in earlyWarningShown) {
                    mrbSettings.filterWarnings.carbonFilter =
                        earlyWarningShown.carbonFilter;
                }
                let userName = self.loginState.currentUser().name;
                self.userSettings.updateSettings(userName, {
                    mrbeam: mrbSettings,
                });
            }
        };

        self.updateSettingsAbout = function () {
            $("#settings_mrbeam_about_support_total_usage_hours").html(
                self.totalUsageHours()
            );
        };
    }

    // view model class, parameters for constructor, container to bind to
    OCTOPRINT_VIEWMODELS.push([
        Maintenance,

        // e.g. loginStateViewModel, settingsViewModel, ...
        [
            "settingsViewModel",
            "analyticsViewModel",
            "userSettingsViewModel",
            "loginStateViewModel",
        ],

        // e.g. #settings_plugin_mrbeam, #tab_plugin_mrbeam, ...
        ["#settings_maintenance"], // This is important!
    ]);
});
