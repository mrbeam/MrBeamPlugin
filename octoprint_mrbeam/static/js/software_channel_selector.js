$(function () {
    function SoftwareChannelSelector(params) {
        var self = this;
        self.loginState = params[0];
        self.settings = params[1];

        self.selector = ko.observable("PROD");
        // self.selector = self.settings.settings.plugins.mrbeam.dev.softwareTier;

        self.onStartupComplete = function () {
            console.log("ANDYTEST SoftwareChannelSelector.onStartup");
            // self.onStartupComplete = function () {
            let elem = $('#'+DOM_ELEMENT_TO_BIND_TO).detach();
            $('#settings_plugin_softwareupdate > h3').before(elem);
            $('#'+DOM_ELEMENT_TO_BIND_TO).show();
        };

        self.onAfterBinding = function () {
            self.selector(self.settings.settings.plugins.mrbeam.dev.software_tier());
            self.selector = self.settings.settings.plugins.mrbeam.dev.software_tier;
        };

    };

    var DOM_ELEMENT_TO_BIND_TO = "software_channel_selector";

    // view model class, parameters for constructor, container to bind to
    OCTOPRINT_VIEWMODELS.push([
        SoftwareChannelSelector,

        // e.g. loginStateViewModel, settingsViewModel, ...
        ["loginStateViewModel", "settingsViewModel"],

        // e.g. #settings_plugin_mrbeam, #tab_plugin_mrbeam, ...
        [document.getElementById(DOM_ELEMENT_TO_BIND_TO)]
    ]);
});
