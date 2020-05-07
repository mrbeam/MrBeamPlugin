$(function () {
    function SoftwareChannelSelector(params) {
        let self = this;
        window.mrbeam.viewModels['softwareChannelSelector'] = self;

        self.loginState = params[0];
        self.settings = params[1];
        self.softwareUpdate = params[2];

        self.selector = ko.observable("PROD");
        self.available_channels = ko.observableArray([]);

        self.waiting_for_update = 0;
        self.channel_display_names = {
            "PROD": gettext('Stable'),
            "BETA": gettext('Beta'),
            "DEV": gettext('Develop'),
            "DESIGN_STORE": "Design Store"
        };

        self.onAllBound = function () {
            // MR_BEAM_OCTOPRINT_PRIVATE_API_ACCESS
            let elem = $('#'+DOM_ELEMENT_TO_BIND_TO).detach();
            $('#settings_plugin_softwareupdate > h3').before(elem);
            $('#'+DOM_ELEMENT_TO_BIND_TO).show();
            $('#settings_plugin_softwareupdate > h3').hide();

            // MR_BEAM_OCTOPRINT_PRIVATE_API_ACCESS
            // remove warnings about OctoPrint unreleased version
            $('#settings_plugin_softwareupdate .alert').remove()

            let channels = self.settings.settings.plugins.mrbeam.dev.software_tiers_available();
            for (let i = 0; i < channels.length; i++) {
                let obj = {
                    id: channels[i]['id'](),
                    name: self.channel_display_names[channels[i]['id']()]
                };
                self.available_channels.push(obj);
            }

            self.selector(self.settings.settings.plugins.mrbeam.dev.software_tier());
            self.selector = self.settings.settings.plugins.mrbeam.dev.software_tier;

            self._make_settings_software_update_scrollable();
        };

        self.onStartupComplete = function() {
            self.waiting_for_update = 0;
        };

        self.onEventSettingsUpdated = function(data){
            if (self.waiting_for_update > 0) {
                self._trigger_refresh();
            }
            self.waiting_for_update = Math.max(self.waiting_for_update-1, 0);
        };

        self.onSettingsShown = function(){
            $('#software_channel_select').val(self.settings.settings.plugins.mrbeam.dev.software_tier());
        };

        self.setChannelAsync = function(channel, waitTime){
            waitTime = waitTime || 1500;
            setTimeout(function(){self.selection_changed(); self._setChannel(channel)}, waitTime );
            setTimeout(function(){self._trigger_refresh(channel)}, waitTime *10);
        };

        self.selection_changed = function (event) {
            self.waiting_for_update++;
        };

        self._setChannel = function(channel){
            self.settings.settings.plugins.mrbeam.dev.software_tier(channel);
            self.settings.saveData()
                .done(function(){
                    // console.log("settings.saveData DONE");
               });
        };

        self._trigger_refresh = function(){
            // MR_BEAM_OCTOPRINT_PRIVATE_API_ACCESS
            self.softwareUpdate.performCheck(true, false, true);
        };

        /**
         * This one wraps all content of the #settings_plugin_softwareupdate elem into a div
         * which makes the whole page scrollable. it's a bit tricky/dirty because the content comes from OP.
         * @private
         */
        self._make_settings_software_update_scrollable = function () {
            // MR_BEAM_OCTOPRINT_PRIVATE_API_ACCESS
            let id_scroll_wrapper = "settings_plugin_softwareupdate_scroll_wrapper";
            let elem_= $('#settings_plugin_softwareupdate');
            let children = elem_.children();
            elem_.append('<div class=\"scrollable\" style=\"overflow-y: auto; height: calc(100vh - 100px);\" id="'+id_scroll_wrapper+'">');
            children.detach();
            $('#'+id_scroll_wrapper).append(children);

            // "Check for update now" button sticky on page bottom
            let button = $('#settings_plugin_softwareupdate_scroll_wrapper > button');
            button.addClass('sticky-footer');

        };

    };

    let DOM_ELEMENT_TO_BIND_TO = "software_channel_selector";

    // view model class, parameters for constructor, container to bind to
    OCTOPRINT_VIEWMODELS.push([
        SoftwareChannelSelector,

        // e.g. loginStateViewModel, settingsViewModel, ...
        ["loginStateViewModel", "settingsViewModel", "softwareUpdateViewModel"],

        // e.g. #settings_plugin_mrbeam, #tab_plugin_mrbeam, ...
        [document.getElementById(DOM_ELEMENT_TO_BIND_TO)]
    ]);
});
