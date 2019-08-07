$(function () {
    function FeedbackWidgetViewModel(params) {
        let self = this;
        window.mrbeam.viewModels['feedbackWidgetViewModel'] = self;

        self.loginStateViewModel = params[0];

        self.freshWidgetUrl = "https://s3.amazonaws.com/assets.freshdesk.com/widget/freshwidget.js";

        self.isCurtainOpen = false;


        self.onStartup = function () {
            console.log("FreshWidget: onStartUp()");
            $.ajax({
                url: self.freshWidgetUrl,
                dataType: "script",
                cache: false
            }).done(function (script, textStatus) {
                if (self.isCurtainOpen) {
                    self.showWidget();
                }
            }).fail(function (jqxhr, settings, exception) {
                console.log("FreshWidget: not available");
            });
        };

        self.onCurtainOpened = function () {
            self.isCurtainOpen = true;
            if (window.FreshWidget) {
                self.showWidget();
            }
        };

        self.onCurtainClosed = function() {
            self.removeFeedbackWidget();
        };

        self.showWidget = function () {
            let user = self.loginStateViewModel.username();

            let channel;
            if (MRBEAM_SW_TIER === 'BETA') {
                channel = 'Beta'
            } else {
                channel = 'Stable'
            }

            try {
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
                console.log("FreshWidget: Shown")
            } catch (e) {
                console.log("FreshWidget: Could not be initialized")
            }
        };

        self.removeFeedbackWidget = function () {
            $('#freshwidget-button').remove()
        };

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
