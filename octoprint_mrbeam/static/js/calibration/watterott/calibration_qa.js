/*
 * View model for Mr Beam
 *
 * Author: Teja Philipp <teja@mr-beam.org>
 * License: AGPLv3
 */
/* global OctoPrint, OCTOPRINT_VIEWMODELS, INITIAL_CALIBRATION */

$(function () {
    function CalibrationQAViewModel(parameters) {
        let self = this;
        window.mrbeam.viewModels["cameraAlignmentViewModel"] = self;
        self.calibration = parameters[0];
        self.camera = parameters[1];
        self.cornerCalibration = parameters[2];
        self.workingArea = parameters[3];
    }

    // view model class, parameters for constructor, container to bind to
    OCTOPRINT_VIEWMODELS.push([
        CalibrationQAViewModel,

        // e.g. loginStateViewModel, settingsViewModel, ...
        [
            "calibrationViewModel",
            "cameraViewModel",
            "cornerCalibrationViewModel",
            "workingAreaViewModel",
        ],

        // e.g. #settings_plugin_mrbeam, #tab_plugin_mrbeam, ...
        ["#tab_calibration_qa"],
    ]);
});
