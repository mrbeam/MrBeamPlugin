$(function () {
    function SoftwareChannelSelector(params) {
        var self = this;
        self.loginState = params[0];
        self.settings = params[1];
        self.softwareUpdate = params[2];

        self.selector = ko.observable("PROD");
        self.available_channels    =   ko.observableArray([]);
        self.available_channel_ids =   ko.observableArray([]);
        self.available_channel_names = ko.observableArray([]);

        self.onStartupComplete = function () {
            let elem = $('#'+DOM_ELEMENT_TO_BIND_TO).detach();
            $('#settings_plugin_softwareupdate > h3').before(elem);
            $('#'+DOM_ELEMENT_TO_BIND_TO).show();
        };

        self.onBeforeBinding = function () {
            let channels = self.settings.settings.plugins.mrbeam.dev.software_tiers_available();
            for (let i = 0; i < channels.length; i++) {
                let obj = {
                    id: channels[i]['id'](),
                    name: channels[i]['name']()
                };
                self.available_channels.push(obj);
            }

            self.selector(self.settings.settings.plugins.mrbeam.dev.software_tier());
            self.selector = self.settings.settings.plugins.mrbeam.dev.software_tier;
        };

        self.selection_changed = function(event){
            console.log("selection_changed: ", event);
            setTimeout(self._trigger_refresh, 3000);
        };

        self._trigger_refresh = function(){
            self.softwareUpdate.performCheck(true, false, true);
        };

    };

    var DOM_ELEMENT_TO_BIND_TO = "software_channel_selector";

    // view model class, parameters for constructor, container to bind to
    OCTOPRINT_VIEWMODELS.push([
        SoftwareChannelSelector,

        // e.g. loginStateViewModel, settingsViewModel, ...
        ["loginStateViewModel", "settingsViewModel", "softwareUpdateViewModel"],

        // e.g. #settings_plugin_mrbeam, #tab_plugin_mrbeam, ...
        [document.getElementById(DOM_ELEMENT_TO_BIND_TO)]
    ]);
});
