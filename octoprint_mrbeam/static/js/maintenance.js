$(function () {
    function Maintenance(params) {
        let self = this;
        window.mrbeam.viewModels['maintenance'] = self;

        self.settings = params[0];

        self.PREFILTER = gettext('pre-filter');
        self.CARBON_FILTER = gettext('carbon filter');
        self.LASER_HEAD = gettext('laser head');
        self.GANTRY = gettext('gantry');
        self.PREFILTER_LIFESPAN = 100;
        self.CARBON_FILTER_LIFESPAN = 400;
        self.LASER_HEAD_LIFESPAN = 100; // TODO IRATXE: which value should it be?
        self.GANTRY_LIFESPAN = 10000;


        self.prefilterUsage = ko.observable(0);
        self.carbonFilterUsage = ko.observable(0);
        self.laserHeadUsage = ko.observable(0);
        self.gantryUsage = ko.observable(0);

        self.componentToReset = ko.observable("");
        self.laserHeadSerial = ko.observable("");

        self.prefilterLifespanHours = _.sprintf(gettext("/%(lifespan)s h"), {lifespan: self.PREFILTER_LIFESPAN});
        self.carbonFilterLifespanHours = _.sprintf(gettext("/%(lifespan)s h"), {lifespan: self.CARBON_FILTER_LIFESPAN});
        self.laserHeadLifespanHours = _.sprintf(gettext("/%(lifespan)s h"), {lifespan: self.LASER_HEAD_LIFESPAN});
        self.gantryLifespanHours = _.sprintf(gettext("/%(lifespan)s h"), {lifespan: self.GANTRY_LIFESPAN});

        self.prefilterUsageHours = ko.computed(function() {
            return Math.floor(self.prefilterUsage()/3600);
        });
        self.carbonFilterUsageHours = ko.computed(function() {
            return Math.floor(self.carbonFilterUsage()/3600);
        });
        self.laserHeadUsageHours = ko.computed(function() {
            return Math.floor(self.laserHeadUsage()/3600);
        });
        self.gantryUsageHours = ko.computed(function() {
            return Math.floor(self.gantryUsage()/3600);
        });

        self.prefilterShowWarning = ko.computed(function() {
            let usedPercent = self.prefilterUsageHours()/self.PREFILTER_LIFESPAN*100;
            return usedPercent > 90;
        });
        self.carbonFilterShowWarning = ko.computed(function() {
            let usedPercent = self.carbonFilterUsageHours()/self.CARBON_FILTER_LIFESPAN*100;
            return usedPercent > 90;
        });
        self.laserHeadShowWarning = ko.computed(function() {
            let usedPercent = self.laserHeadUsageHours()/self.LASER_HEAD_LIFESPAN*100;
            return usedPercent > 90;
        });
        self.gantryShowWarning = ko.computed(function() {
            let usedPercent = self.gantryUsageHours()/self.GANTRY_LIFESPAN*100;
            return usedPercent > 90;
        });

        self.actionToReset = ko.computed(function () {
            if(self.componentToReset() === self.LASER_HEAD) {
                return 'clean'
            } else {
                return 'change'
            }
        });

        self.onBeforeBinding = function() {
            self.loadUsageValues()
        };

        self.resetPrefilterUsage = function() {
            self.componentToReset(self.PREFILTER);
            $('#reset_counter_are_you_sure').modal({
                backdrop: 'static',
                keyboard: false
            })
            .one('click', '#reset_counter_btn', function() {
                console.log("Resetting pre-filter usage counter");
                OctoPrint.simpleApiCommand("mrbeam", "reset_prefilter_usage", {})
                    .done(function(){
                        self.prefilterUsage(0);
                    })
                    .fail(function(){
                        console.error("Unable to reset pre-filter usage counter.");
                    });
            });
        };

        self.resetCarbonFilterUsage = function() {
            self.componentToReset(self.CARBON_FILTER);
            $('#reset_counter_are_you_sure').modal({
                backdrop: 'static',
                keyboard: false
            })
            .one('click', '#reset_counter_btn', function() {
                console.log("Resetting carbon filter usage counter");
                OctoPrint.simpleApiCommand("mrbeam", "reset_carbon_filter_usage", {})
                    .done(function(){
                        self.carbonFilterUsage(0);
                    })
                    .fail(function(){
                        console.error("Unable to reset carbon filter usage counter.");
                    });
            });
        };

        self.resetLaserHeadUsage = function() {
            self.componentToReset(self.LASER_HEAD);
            $('#reset_counter_are_you_sure').modal({
                backdrop: 'static',
                keyboard: false
            })
            .one('click', '#reset_counter_btn', function() {
                console.log("Resetting laser head usage counter");
                OctoPrint.simpleApiCommand("mrbeam", "reset_laser_head_usage", {})
                    .done(function(){
                        self.laserHeadUsage(0);
                    })
                    .fail(function(){
                        console.error("Unable to reset laser head usage counter.");
                    });
            });
        };

        self.resetGantryUsage = function() {
            self.componentToReset(self.GANTRY);
            $('#reset_counter_are_you_sure').modal({
                backdrop: 'static',
                keyboard: false
            })
            .one('click', '#reset_counter_btn', function() {
                console.log("Resetting gantry usage counter");
                OctoPrint.simpleApiCommand("mrbeam", "reset_gantry_usage", {})
                    .done(function(){
                        self.gantryUsage(0);
                    })
                    .fail(function(){
                        console.error("Unable to reset gantry usage counter.");
                    });
            });
        };

        self.onSettingsShown = function() {
            self.settings.requestData()
                .done(function(){
                    self.loadUsageValues()
                }
            )
        };

        self.loadUsageValues = function() {
            self.prefilterUsage(self.settings.settings.plugins.mrbeam.usage.prefilterUsage());
            self.carbonFilterUsage(self.settings.settings.plugins.mrbeam.usage.carbonFilterUsage());
            self.laserHeadUsage(self.settings.settings.plugins.mrbeam.usage.laserHeadUsage());
            self.gantryUsage(self.settings.settings.plugins.mrbeam.usage.gantryUsage());
            self.laserHeadSerial(self.settings.settings.plugins.mrbeam.laserHeadSerial())
        }

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
