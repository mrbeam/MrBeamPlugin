/*
 * View model for Mr Beam
 *
 * Author: Teja Philipp <teja@mr-beam.org>
 * License: AGPLv3
 */
/* global OctoPrint, OCTOPRINT_VIEWMODELS, INITIAL_CALIBRATION */

$(function () {
    function LabelPrinterViewModel(parameters) {
        let self = this;
        window.mrbeam.viewModels["labelPrinterViewModel"] = self;
        self.calibration = parameters[0];

        self.printLabel = function (labelType, event) {
            let button = $(event.target);
            let label = button.text().trim();
            button.prop("disabled", true);
            self.calibration.simpleApiCommand(
                "print_label",
                { labelType: labelType, blink: true },
                function () {
                    button.prop("disabled", false);
                    new PNotify({
                        title: gettext("Printed: ") + label,
                        type: "success",
                        hide: false,
                    });
                },
                function (response) {
                    button.prop("disabled", false);
                    let data = response.responseJSON;
                    new PNotify({
                        title: gettext("Print Error") + ": " + label,
                        text: data ? data.error : "",
                        type: "error",
                        hide: false,
                    });
                },
                "POST"
            );
        };
    }

    // view model class, parameters for constructor, container to bind to
    OCTOPRINT_VIEWMODELS.push([
        LabelPrinterViewModel,

        // e.g. loginStateViewModel, settingsViewModel, ...
        ["calibrationViewModel"],

        // e.g. #settings_plugin_mrbeam, #tab_plugin_mrbeam, ...
        ["#tab_done_print_labels"],
    ]);
});
