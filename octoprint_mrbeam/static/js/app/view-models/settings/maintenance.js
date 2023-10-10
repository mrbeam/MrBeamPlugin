$(function () {
    function Maintenance(params) {
        let self = this;
        window.mrbeam.viewModels["maintenance"] = self;

        self.settings = params[0];
        self.analytics = params[1];
        self.userSettings = params[2];
        self.loginState = params[3];
        self.mrb_state = params[4];

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
        self.GANTRY_LIFESPAN = 100;
        self.WARN_IF_CRITICAL_PERCENT = 70;
        self.WARN_IF_USED_PERCENT = 100;
        self.laserHeadLifespan = ko.observable(0);

        self.totalUsage = ko.observable(0);
        self.prefilterUsage = ko.observable(0);
        self.carbonFilterUsage = ko.observable(0);
        self.laserHeadUsage = ko.observable(0);
        self.gantryUsage = ko.observable(0);
        self.prefilterShopify = ko.observable(0);
        self.carbonfilterShopify = ko.observable(0);
        self.prefilterHeavyDutyShopify = ko.observable(0);

        self.needsGantryMaintenance = ko.observable(true);
        self.componentToReset = ko.observable("");
        self.laserHeadSerial = ko.observable("");
        self.heavyDutyPrefilterEnabled = ko.observable(false);
        self.airfilter3Used = ko.observable(false);

        self.heavyDutyPrefilterValue = ko.computed({
            read: function () {
                return self.heavyDutyPrefilterEnabled().toString();
            },
            write: function (newValue) {
                self.heavyDutyPrefilterEnabled(newValue === "true");
            },
            owner: self,
        });

        self.totalUsageHours = ko.computed(function () {
            return Math.floor(self.totalUsage() / 36) / 100;
        });
        self.laserHeadUsageHours = ko.computed(function () {
            return Math.floor(self.laserHeadUsage() / 3600);
        });
        self.gantryUsageHours = ko.computed(function () {
            return Math.floor(self.gantryUsage() / 3600);
        });

        self.optimizeParameterPercentageValues = function (
            val,
            tenthSteps = true
        ) {
            if (tenthSteps) {
                val = roundDownToNearest10(val);
            }
            return Math.max(0, Math.min(val, 100));
        };

        self.prefilterPercent = ko.computed(function () {
            const tenthSteps = !self.airfilter3Used();
            return self.optimizeParameterPercentageValues(
                self.prefilterUsage(),
                tenthSteps
            );
        });
        self.carbonFilterPercent = ko.computed(function () {
            const tenthSteps = !self.airfilter3Used();
            return self.optimizeParameterPercentageValues(
                self.carbonFilterUsage(),
                tenthSteps
            );
        });
        self.laserHeadPercent = ko.computed(function () {
            return self.optimizeParameterPercentageValues(
                (self.laserHeadUsageHours() / self.laserHeadLifespan()) * 100
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

        self.heavyDutyPrefilterEnabled.subscribe(function (newValue) {
            self.settings.settings.plugins.mrbeam.heavyDutyPrefilter(newValue);
            self.settings.saveData(undefined, function (newSettings) {
                const new_lifespan = self.prefilterLifespan(0);
                console.log(
                    "Prefilter lifespan changed to:",
                    newSettings.plugins.mrbeam.heavyDutyPrefilter,
                    new_lifespan
                );
            });
            self.settings.saveall(); //trigger saveinprogress class
        });

        self.mrb_state.airfilter_model.subscribe(function (model_id) {
            self._check_airfilter_model();
        });

        self._check_airfilter_model = function () {
            const airfilter_model = self.mrb_state.airfilter_model();
            if (airfilter_model === mrbeam.airfilter_model.AF3) {
                self.airfilter3Used(true);
            } else {
                self.airfilter3Used(false);
            }
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
                    self.analytics.send_frontend_event("link_click", payload);
                });
            });
            self.updateSettingsAbout();

            self._makePrefilterElementsClickable();
            self._addTooltipForPrefilterTitle();
            self._check_airfilter_model();
        };

        self._addTooltipForPrefilterTitle = function (element) {
            // Add mouseover event listeners to each prefilter title to add a tooltip with the grafik of the prefilter types
            const elementsWithAttribute = document.querySelectorAll(
                "[data-tooltip-image]"
            );
            elementsWithAttribute.forEach((element) => {
                const image = element.getAttribute("data-tooltip-image");
                $(element).tooltip({
                    title: "<img src='" + image + "' height='220px'>",
                    placement: "right",
                    html: true,
                    delay: { show: 400 },
                });
            });
        };

        self._makePrefilterElementsClickable = function () {
            const clickableContainers = document.querySelectorAll(
                ".prefilter-clickable"
            );
            // Add click event listeners to each container
            clickableContainers.forEach((container) => {
                container.addEventListener("click", (event) => {
                    // Find the radio input element within the container
                    const radioInput = container.querySelector(
                        'input[type="radio"]'
                    );
                    const clickedElement = event.target;

                    // Check if the clicked element is the "Buy now" link
                    if (clickedElement.id === "prefilter_shop_link") {
                        // Prevent the click event from propagating further
                        event.stopPropagation();
                    } else {
                        self.heavyDutyPrefilterEnabled(
                            radioInput.getAttribute("value")
                        );
                    }
                });
            });
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
                        { serial: self.mrb_state.airfilter_serial() }
                    ).fail(function () {
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
                        { serial: self.mrb_state.airfilter_serial() }
                    ).fail(function () {
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
                    ).fail(function () {
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
                self.needsGantryMaintenance(
                    window.mrbeam.model.is_mrbeam2() ||
                        window.mrbeam.model.is_mrbeam2_dreamcut_ready1()
                );
                self.updateSettingsAbout();
                self.heavyDutyPrefilterEnabled(
                    self.settings.settings.plugins.mrbeam.heavyDutyPrefilter()
                );
            });
        };

        self.shopifyLink = function (stagename, stageid) {
            let link;
            if (stagename === "prefilter") {
                link =
                    self.prefilterShopify() != null
                        ? self.prefilterShopify()[stageid]
                        : null;
            } else if (stagename === "carbonfilter") {
                link =
                    self.carbonfilterShopify() != null
                        ? self.carbonfilterShopify()[stageid]
                        : null;
            } else if (stagename === "prefilter_heavy_duty") {
                link =
                    self.prefilterHeavyDutyShopify() != null
                        ? self.prefilterHeavyDutyShopify()[stageid]
                        : null;
            } else {
                link = null;
            }
            return link;
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
                self.analytics.send_frontend_event("link_click", payload);
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

        self.onDataUpdaterPluginMessage = function (plugin, data) {
            if (plugin !== "mrbeam") {
                return;
            }
            if ("maintenance_information" in data) {
                const maintenanceInformation = data.maintenance_information;
                if (self.needsGantryMaintenance()) {
                    self.gantryUsage(maintenanceInformation.gantryUsage);
                } else {
                    self.gantryUsage(0);
                }

                self.totalUsage(maintenanceInformation.totalUsage);
                self.prefilterUsage(maintenanceInformation.prefilterUsage);
                self.carbonFilterUsage(
                    maintenanceInformation.carbonFilterUsage
                );
                self.laserHeadUsage(maintenanceInformation.laserHeadUsage);
                self.laserHeadSerial(maintenanceInformation.laserHeadSerial);
                self.laserHeadLifespan(
                    maintenanceInformation.laserHeadLifespan
                );

                self.carbonfilterShopify(
                    maintenanceInformation.carbonfilterShopify
                );
                self.prefilterShopify(maintenanceInformation.prefilterShopify);
                self.prefilterHeavyDutyShopify(
                    maintenanceInformation.prefilterHeavyDutyShopify
                );
            }
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
            "mrbStateViewModel",
        ],

        // e.g. #settings_plugin_mrbeam, #tab_plugin_mrbeam, ...
        ["#settings_maintenance"], // This is important!
    ]);
});
