/*
 * View model for Mr Beam About Settings Page
 *
 * Author: Josef Finkl <josef@mr-beam.org>
 * License: AGPLv3
 */
/* global OctoPrint, OCTOPRINT_VIEWMODELS */

$(function () {
    function AboutSettingsViewModel(params) {
        let self = this;
        window.mrbeam.viewModels["aboutSettingsViewModel"] = self;
        self.mrb_state = params[0];
        self.airfilter_serial = self.mrb_state.airfilter_serial;
        self.airfilter_model = self.mrb_state.airfilter_model;
    }

    OCTOPRINT_VIEWMODELS.push([
        AboutSettingsViewModel,

        // e.g. loginStateViewModel, settingsViewModel, ...
        ["mrbStateViewModel"],

        // e.g. #settings_plugin_mrbeam, #tab_plugin_mrbeam, ...
        ["#settings_mrbeam_about"], // This is important!
    ]);
});
