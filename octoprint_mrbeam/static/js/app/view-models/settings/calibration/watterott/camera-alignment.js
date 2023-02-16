/*
 * View model for Mr Beam
 *
 * Author: Teja Philipp <teja@mr-beam.org>
 * License: AGPLv3
 */
/* global OctoPrint, OCTOPRINT_VIEWMODELS, INITIAL_CALIBRATION */

$(function () {
    function CameraAlignmentViewModel(parameters) {
        let self = this;
        window.mrbeam.viewModels["cameraAlignmentViewModel"] = self;
        self.calibration = parameters[0];
        self.camera = parameters[1];
        self.lensCalibration = parameters[2];

        self.qa_cameraalignment_image_loaded = ko.observable(false);
        $("#qa_cameraalignment_image").load(function () {
            self.qa_cameraalignment_image_loaded(true);
        });
    }

    // view model class, parameters for constructor, container to bind to
    OCTOPRINT_VIEWMODELS.push([
        CameraAlignmentViewModel,

        // e.g. loginStateViewModel, settingsViewModel, ...
        ["calibrationViewModel", "cameraViewModel", "lensCalibrationViewModel"],

        // e.g. #settings_plugin_mrbeam, #tab_plugin_mrbeam, ...
        ["#tab_camera_alignment", "#tab_camera_alignment_wrap"],
    ]);
});
