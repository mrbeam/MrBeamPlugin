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
        self.settings = params[0];
        self.airfilter_serial = ko.observable(undefined);
        self.airfilter_model = ko.observable(undefined);

        self.onSettingsShown = function () {
            self.refreshData();
        };
        self.onDataUpdaterPluginMessage = function (plugin, data) {
            if (plugin !== MRBEAM.PLUGIN_IDENTIFIER) {
                return;
            }
            if (MRBEAM.STATE_KEY in data) {
                self._fromData(data, "onDataUpdaterPluginMessage");
            }
        };
        self._fromData = function (payload, event) {
            if (
                !payload ||
                !(MRBEAM.STATE_KEY in payload) ||
                !payload[MRBEAM.STATE_KEY]
            ) {
                return;
            }
            let mrb_state = payload[MRBEAM.STATE_KEY];
            if (mrb_state) {
                self.refreshData(mrb_state);
            }
        };
        self.refreshData = function (mrb_state) {
            console.log(
                "AboutSettingsViewModel: refreshData",
                mrb_state?.airfilter_serial,
                mrb_state?.airfilter_model
            );
            if (mrb_state?.airfilter_serial) {
                self.airfilter_serial(mrb_state?.airfilter_serial);
            } else {
                self.airfilter_serial(undefined);
            }
            if (mrb_state?.airfilter_model) {
                self.airfilter_model(mrb_state?.airfilter_model);
            } else {
                self.airfilter_model(undefined);
            }
        };
    }

    OCTOPRINT_VIEWMODELS.push([
        AboutSettingsViewModel,

        // e.g. loginStateViewModel, settingsViewModel, ...
        [],

        // e.g. #settings_plugin_mrbeam, #tab_plugin_mrbeam, ...
        ["#settings_mrbeam_about"], // This is important!
    ]);
});
