$(function () {
    function FeedbackWidgetViewModel(params) {
        let self = this;
        window.mrbeam.viewModels['feedbackWidgetViewModel'] = self;

        self.loginStateViewModel = params[0];

        self.freshWidgetUrl = "https://widget.freshworks.com/widgets/43000001170.js";

        self.isCurtainOpen = false;

        self.onStartup = function () {
            console.log("FreshWidget: onStartUp()");

            window.fwSettings={
                'widget_id':43000001170,
                'locale': LOCALE
            };
            !function(){if("function"!=typeof window.FreshworksWidget){var n=function(){n.q.push(arguments)};n.q=[],window.FreshworksWidget=n}}();

            $.ajax({
                url: self.freshWidgetUrl,
                dataType: "script",
                cache: false
            }).done(function (script, textStatus) {
                window.FreshworksWidget('hide', 'launcher');
                if (self.isCurtainOpen) {
                    self.onCurtainOpened();
                }
            }).fail(function (jqxhr, settings, exception) {
                console.log("FreshWidget: not available");
            });
        };

        self.onCurtainOpened = function () {
            self.isCurtainOpen = true;
            if (window.FreshworksWidget) {
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
                window.FreshworksWidget('prefill', 'ticketForm', {
                  email: user,
                  custom_fields: {
                      cf_serial: MRBEAM_SERIAL,
                      cf_software_version: BEAMOS_VERSION,
                      cf_software_channel: channel
                  }
                });
                window.FreshworksWidget('disable', 'ticketForm',
                    ['custom_fields.cf_serial', 'custom_fields.cf_software_version','custom_fields.cf_software_channel']);
                window.FreshworksWidget("setLabels", {
                  'de': {
                    banner: "Help & Support",
                    launcher: "Support",
                    contact_form: {
                      title: "Help & Support",
                      submit: "Send feedback",
                      confirmation: "Thank you for your feedback.",
                    }
                  }
                });
                window.FreshworksWidget('show', 'launcher');
                console.log("FreshWidget: Shown")
            } catch (e) {
                console.log("FreshWidget: Could not be initialized")
            }
        };

        self.removeFeedbackWidget = function () {
            window.FreshworksWidget('destroy');
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
