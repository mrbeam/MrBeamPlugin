/*
 * View model for Mr_Beam
 *
 * Author: Teja
 * License: AGPLv3
 */
$(function() {
    function LaserJobDoneViewmodel(parameters) {
        var self = this;


        self.onStartup = function(){
            console.log("LaserJobDoneViewmodel loaded!");
        };

        self.onDataUpdaterPluginMessage = function(plugin, data) {
            if (plugin != "mrbeam") {
                return;
            }

            if (!data) {
                console.warn("onDataUpdaterPluginMessage() received empty data for plugin '"+mrbeam+"'");
                return;
            }

            if ('event' in data) {
                console.log("Got event data: ", data);
            }
        };

        self.onEventPrintDone = function (payload) {
            console.log("Got printdone: ", payload);
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
