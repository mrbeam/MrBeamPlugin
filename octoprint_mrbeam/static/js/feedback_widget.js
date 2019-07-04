$(function () {
    function FeedbackWidgetViewModel(params) {
        let self = this;
        window.mrbeam.viewModels['feedbackWidgetViewModel'] = self;
        
        self.loginStateViewModel = params[0];

        self.removeFeedbackWidget = function(){
            $('#freshwidget-button').remove()
        };

        self.onStartupComplete = function () {
            let user = self.loginStateViewModel.username();

            let channel;
            if(MRBEAM_SW_TIER === 'BETA') {
                channel = 'Beta'
            } else {
                channel = 'Stable'
            }

            try{
                window.FreshWidget.init("", {
                    "queryString": "&widgetType=popup"
                        + "&helpdesk_ticket[custom_field][cf_serial_922577]=" + MRBEAM_SERIAL
                        + "&disable[custom_field][cf_serial_922577]=true"
                        + "&helpdesk_ticket[requester]=" + user
                        + "&helpdesk_ticket[custom_field][cf_software_version_922577]=" + BEAMOS_VERSION
                        + "&disable[custom_field][cf_software_version_922577]=true"
                        + "&helpdesk_ticket[custom_field][cf_software_channel_922577]=" + channel
                        + "&disable[custom_field][cf_software_channel_922577]=true",
                    "utf8": "✓",
                    "widgetType": "popup",
                    "buttonType": "text",
                    "buttonText": "Support",
                    "buttonColor": "#e25303",
                    "buttonBg": "white",
                    "alignment": "4",
                    "offset": "90%",
                    "formHeight": "500px",
                    "url": "https://mr-beam.freshdesk.com",
                    "loadOnEvent": "immediate"  // This will make the widget initialize immediately instead of waiting for a window.load
                });
            } catch (e) {
                console.log("The Freshdesk Widget could not be initialized")
            }

        };

        $( window ).on('beforeunload', function(){
            // do not show reloadingOverlay when it's a file download
            if (!event.target.activeElement.href) {
                self.removeFeedbackWidget();
            }
        });
    }

    // view model class, parameters for constructor, container to bind to
    OCTOPRINT_VIEWMODELS.push([
        FeedbackWidgetViewModel,

        // e.g. loginStateViewModel, settingsViewModel, ...
        ["loginStateViewModel"],

        // e.g. #settings_plugin_mrbeam, #tab_plugin_mrbeam, ...
        []
    ]);
});
