/*
 * View model for Mr Beam
 *
 * Author: Andy Werner <andy@mr-beam.org>
 */
/* global OctoPrint, OCTOPRINT_VIEWMODELS */

$(function () {
    function CustomMaterialViewModel(parameters) {
        var self = this;
        window.mrbeam.viewModels["customMaterialViewModel"] = self;

        self.settings = parameters[0];
        self.conversion = parameters[1];

        $("#settings_mrbeam_custom_material_restore_input").on(
            "change",
            function (ev) {
                console.log(ev.target.files[0]);
                self.readLocalFile(ev, function (data) {
                    if (data && "custom_materials" in data) {
                        console.log("Loaded material settings: ", data);
                        // TODO: add more sanity checks here
                        self.conversion.restore_material_settings(
                            data.custom_materials
                        );
                    } else {
                        console.error(
                            "Unable to load custom material settings from file."
                        );
                        new PNotify({
                            title: gettext("Failed to load file"),
                            text: _.sprintf(
                                gettext(
                                    "Unable to load custom material settings from given file. Please make sure that it is a Mr Beam Custom Material Settings backup file."
                                )
                            ),
                            type: "error",
                            hide: true,
                        });
                    }
                });
            }
        );

        self.backupDataUrl = ko.computed(function () {
            var payload = {
                v: MRBEAM_PLUGIN_VERSION,
                ts: Date.now(),
                custom_materials: self.conversion.custom_materials(),
            };
            return (
                "data:text/json;charset=utf-8," +
                encodeURIComponent(JSON.stringify(payload))
            );
        });

        self.getBackupFilename = function () {
            var dateStr = new Date(Date.now()).toISOString().substring(0, 10); // "2020-03-05
            return "MrBeam-CustomMaterialBackup-" + dateStr + ".json";
        };

        self.readLocalFile = function (e, callback) {
            var file = e.target.files[0];
            if (!file) {
                return;
            }
            var reader = new FileReader();
            reader.onload = function (e) {
                var contents = null;
                try {
                    contents = JSON.parse(e.target.result);
                } catch (e) {
                }
                if (callback) {
                    callback(contents);
                }
            };
            reader.readAsText(file);
        };
    }

    // view model class, parameters for constructor, container to bind to
    OCTOPRINT_VIEWMODELS.push([
        CustomMaterialViewModel,

        // e.g. loginStateViewModel, settingsViewModel, ...
        ["settingsViewModel", "vectorConversionViewModel"],

        // e.g. #settings_plugin_mrbeam, #tab_plugin_mrbeam, ...
        ["#settings_plugin_mrbeam_custom_material"],
    ]);
});
