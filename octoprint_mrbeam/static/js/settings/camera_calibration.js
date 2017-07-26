/*
 * View model for Mr_Beam
 *
 * Author: Teja
 * License: AGPLv3
 */
$(function() {
    function CameraCalibrationViewModel(parameters) {
        var self = this;


        self.onStartup = function(){
            console.log("TEJAMARKERS CameraCalibrationViewModel.onStartup()")
            // ok, maybe don't sent this onStartup()
            self._sendData({some:"data", goes:"here"})
        };

        self._sendData = function(data) {
            OctoPrint.simpleApiCommand("mrbeam", "camera_calibration_markers", data)
                .done(function(response) {
                    new PNotify({
                        title: gettext("BAM! markers are sent."),
                        text: gettext("Cool, eh?"),
                        type: "success",
                        hide: true
                    });
                })
                .fail(function(){
                    new PNotify({
                        title: gettext("Couldn't send image markers."),
                        text: gettext("...and I have no clue why."),
                        type: "warning",
                        hide: true
                    });
                });
        };
    };

    // view model class, parameters for constructor, container to bind to
    OCTOPRINT_VIEWMODELS.push([
        CameraCalibrationViewModel,

        // e.g. loginStateViewModel, settingsViewModel, ...
        ["settingsViewModel"],

        // e.g. #settings_plugin_mrbeam, #tab_plugin_mrbeam, ...
        [ "#settings_plugin_mrbeam_camera" ]
    ]);
});
