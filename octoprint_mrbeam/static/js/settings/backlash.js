/*
 * View model for Mr Beam
 *
 * Author: Teja Philipp <teja@mr-beam.org>
 * License: AGPLv3
 */
/* global OctoPrint, OCTOPRINT_VIEWMODELS */

$(function () {
    function BacklashViewModel(parameters) {
        var self = this;
        window.mrbeam.viewModels["backlashViewModel"] = self;

        self.settings = parameters[0];
        self.files = parameters[1];
        self.workingArea = parameters[2];
        self.backlash_compensation_x = 0.0;

        self.backlash_compensation_x = ko.observable(
            self.backlash_compensation_x
        );
        self.backlash_compensation_x.extend({
            rateLimit: { timeout: 500, method: "notifyWhenChangesStop" },
        });
        self.backlash_compensation_x.subscribe(function (inputStr) {
            let val = parseFloat(inputStr);
            if (!isNaN(val)) {
                self.settings.settings.plugins.mrbeam.machine.backlash_compensation_x(
                    val
                );
            } else {
                console.warn(
                    `Value Error: ${val} is not a Number. Nothing saved.`
                );
                return;
            }
            self.settings.saveData(undefined, function (newSettings) {
                console.log(
                    "Saved backlash compensation x",
                    newSettings.plugins.mrbeam.machine.backlash_compensation_x
                );
            });
        });

        // set config values once settings have been loaded.
        self.onAllBound = function (data) {
            let backlash_x = self.settings.settings.plugins.mrbeam.machine.backlash_compensation_x();
            self.backlash_compensation_x(backlash_x);
        };

        self.engrave_calibration_pattern = function () {
            // fake upload: copy file into uploads folder.
            let data = {}; // TODO material selection or intensity & feedrate selection
            OctoPrint.simpleApiCommand(
                "mrbeam",
                "generate_backlash_compenation_pattern_gcode",
                data
            )
                .done(function (response) {
                    let file = {
                        path: response.calibration_pattern,
                        origin: response.target,
                    };
                    self.files.startGcodeWithSafetyWarning(file);
                })
                .fail(function (response) {
                    console.error("Something failed:", response);
                });
        };
    }

    // view model class, parameters for constructor, container to bind to
    OCTOPRINT_VIEWMODELS.push([
        BacklashViewModel,

        // e.g. loginStateViewModel, settingsViewModel, ...
        ["settingsViewModel", "gcodeFilesViewModel", "workingAreaViewModel"],

        // e.g. #settings_plugin_mrbeam, #tab_plugin_mrbeam, ...
        ["#settings_plugin_mrbeam_backlash"],
    ]);
});
