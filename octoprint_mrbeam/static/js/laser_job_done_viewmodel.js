/*
 * View model for Mr_Beam
 *
 * Author: Teja
 * License: AGPLv3
 */
$(function() {
    function LaserJobDoneViewmodel(parameters) {
        var self = this;
        self.is_print_done = ko.observable(false);
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
                console.log("Got event data: ", data);
                setTimeout(function(){ self.dialogElement.modal("hide"); }, 3000);
                self.is_job_done(true);
            }
        };

        self.onEventPrintDone = function (payload) {
            console.log("Got printdone: ", payload);
            self.dialogElement.modal("show");
            self.is_print_done(true);
        };
    };

    // view model class, parameters for constructor, container to bind to
    OCTOPRINT_VIEWMODELS.push([
        LaserJobDoneViewmodel,

        // e.g. loginStateViewModel, settingsViewModel, ...
        [ /* "loginStateViewModel", "settingsViewModel" */ ],

        // e.g. #settings_plugin_mrbeam, #tab_plugin_mrbeam, ...
        [ '#laser_job_done_dialog' ]
    ]);
});
