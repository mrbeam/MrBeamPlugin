$(function () {
    function AirFilterUsage(params) {
        let self = this;

        self.settings = params[0];
        self.air_filter_usage = ko.observable(0);
        self.air_filter_usage_hours = ko.computed(function() {
            return Math.floor(self.air_filter_usage()/3600);
        });


        self.onBeforeBinding = function () {
            self.air_filter_usage(self.settings.settings.plugins.mrbeam.airFilterUsage());
        };


        self.resetAirFilterUsage = function () {
            console.log("Resetting air filter usage counter");
            OctoPrint.simpleApiCommand("mrbeam", "reset_air_filter_usage", {})
                .done(function(response){
                    self.air_filter_usage(0);
                })
                .fail(function(){
                    console.error("Unable to reset air filter usage counter.");
                });
        }

    }


    // view model class, parameters for constructor, container to bind to
    OCTOPRINT_VIEWMODELS.push([
        AirFilterUsage,

        // e.g. loginStateViewModel, settingsViewModel, ...
        ["settingsViewModel"],

        // e.g. #settings_plugin_mrbeam, #tab_plugin_mrbeam, ...
        ["#settings_mrbeam_air_filter"]  // This is important!
    ]);
});
