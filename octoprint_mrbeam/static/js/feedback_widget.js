$(function () {
    function FeedbackWidget(params) {
        let self = this;
        self.loginStateViewModel = params[0];

        self.removeFeedbackWidget = function(){
            $('#freshwidget-button').remove()
        };

        self.onStartupComplete = function () {
            let user = self.loginStateViewModel.username();

            try{
                window.FreshWidget.init("", {
                    "queryString": "&widgetType=popup&helpdesk_ticket[custom_field][cf_serial_922577]=" + MRBEAM_SERIAL
                        + "&disable[custom_field][cf_serial_922577]=true&helpdesk_ticket[requester]=" + user,
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
    }

    // view model class, parameters for constructor, container to bind to
    OCTOPRINT_VIEWMODELS.push([
        FeedbackWidget,

        // e.g. loginStateViewModel, settingsViewModel, ...
        ["loginStateViewModel"],

        // e.g. #settings_plugin_mrbeam, #tab_plugin_mrbeam, ...
        []
    ]);
});
