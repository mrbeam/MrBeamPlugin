$(function () {
    function Maintenance(params) {
        let self = this;
        window.mrbeam.viewModels['maintenance'] = self;

        self.settings = params[0];

        self.prefilter_usage = ko.observable(0);
        self.carbon_filter_usage = ko.observable(0);
        self.laserhead_usage = ko.observable(0);
        self.rail_usage = ko.observable(0);
        self.component_to_reset = ko.observable("");

        // self.prefilter_usage_hours = ko.computed(function() {
        //     return Math.floor(self.prefilter_usage()/3600);
        // });



        self.onBeforeBinding = function() {
            self.prefilter_usage(self.settings.settings.plugins.mrbeam.airFilterUsage());
            self.carbon_filter_usage(self.settings.settings.plugins.mrbeam.airFilterUsage());
            self.laserhead_usage(self.settings.settings.plugins.mrbeam.airFilterUsage());
            self.rail_usage(self.settings.settings.plugins.mrbeam.airFilterUsage());
        };


        self.resetPrefilterUsage = function() {
            self.component_to_reset(gettext('prefilter'));
            $('#reset_counter_are_you_sure').modal({
                backdrop: 'static',
                keyboard: false
            })
            .on('click', '#reset_counter_btn', function() {
                console.log("Resetting air filter usage counter");
                OctoPrint.simpleApiCommand("mrbeam", "reset_air_filter_usage", {})
                    .done(function(){
                        self.air_filter_usage(0);
                    })
                    .fail(function(){
                        console.error("Unable to reset air filter usage counter.");
                    });
            });
        };

        self.onSettingsShown = function() {
            self.settings.requestData()
                .done(function(){
                    self.prefilter_usage(self.settings.settings.plugins.mrbeam.airFilterUsage());
                    self.carbon_filter_usage(self.settings.settings.plugins.mrbeam.airFilterUsage());
                    self.laserhead_usage(self.settings.settings.plugins.mrbeam.airFilterUsage());
                    self.rail_usage(self.settings.settings.plugins.mrbeam.airFilterUsage());
                }
            )
        };

    }


    // view model class, parameters for constructor, container to bind to
    OCTOPRINT_VIEWMODELS.push([
        Maintenance,

        // e.g. loginStateViewModel, settingsViewModel, ...
        ["settingsViewModel"],

        // e.g. #settings_plugin_mrbeam, #tab_plugin_mrbeam, ...
        ["#settings_maintenance"]  // This is important!
    ]);
});
