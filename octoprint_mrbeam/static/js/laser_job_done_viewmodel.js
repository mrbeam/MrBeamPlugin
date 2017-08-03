/*
 * View model for Mr_Beam
 *
 * Author: Teja
 * License: AGPLv3
 */
$(function() {
    function LaserJobDoneViewmodel(parameters) {
        var self = this;
        self.is_job_done = ko.observable(false);

        self.onStartupComplete = function(){
            self.dialogElement = $('#laser_job_done_dialog');
        };


        self.onDataUpdaterPluginMessage = function(plugin, data) {
            if (plugin != "mrbeam") {
                return;
            }

            if (!data) {
                console.warn("onDataUpdaterPluginMessage() received empty data for plugin '"+mrbeam+"'");
                return;
            }

            if ('event' in data && data['event'] == "LaserJobDone") {
                self.is_job_done(true);
                $('.modal-backdrop').onclick = function () {
                    self.dialogElement.modal("hide");
                };
            }
        };

        self.onEventPrintDone = function (payload) {
            if (!self.dialogElement.hasClass('in')) {
                self.dialogElement.modal({backdrop: 'static'});
            }
        };

        self.cancel_btn = function(){
            self.dialogElement.modal("hide");
            self.is_job_done(false);
        };
    }

    // view model class, parameters for constructor, container to bind to
    OCTOPRINT_VIEWMODELS.push([
        LaserJobDoneViewmodel,

        // e.g. loginStateViewModel, settingsViewModel, ...
        [ /* "loginStateViewModel", "settingsViewModel" */ ],

        // e.g. #settings_plugin_mrbeam, #tab_plugin_mrbeam, ...
        [ '#laser_job_done_dialog' ]
    ]);
});
