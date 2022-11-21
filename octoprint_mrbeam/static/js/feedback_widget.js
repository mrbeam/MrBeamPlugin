$(function () {
    function FeedbackWidgetViewModel(params) {
        let self = this;
        window.mrbeam.viewModels["feedbackWidgetViewModel"] = self;

        self.loginStateViewModel = params[0];

        self.freshWidgetUrl =
            "https://widget.freshworks.com/widgets/43000001170.js";

        self.isCurtainOpen = false;

        self.onStartup = function () {
            console.log("FreshWidget: onStartUp()");

            window.fwSettings = {
                widget_id: 43000001170,
                locale: LOCALE,
            };
            !(function () {
                if ("function" != typeof window.FreshworksWidget) {
                    var n = function () {
                        n.q.push(arguments);
                    };
                    (n.q = []), (window.FreshworksWidget = n);
                }
            })();

            $.ajax({
                url: self.freshWidgetUrl,
                dataType: "script",
                cache: false,
            })
                .done(function (script, textStatus) {
                    window.FreshworksWidget("hide", "launcher");
                    if (self.isCurtainOpen) {
                        self.showWidget();
                    }
                })
                .fail(function (jqxhr, settings, exception) {
                    console.log("FreshWidget: not available");
                });
        };

        self.onCurtainOpened = function () {
            self.isCurtainOpen = true;
            if (window.FreshworksWidget) {
                self.showWidget();
            }
        };

        self.onCurtainClosed = function () {
            self.removeFeedbackWidget();
        };

        self.showWidget = function () {
            let user = self.loginStateViewModel.username();

            let channel;
            if (MRBEAM_SW_TIER === "BETA") {
                channel = "Beta";
            } else {
                channel = "Stable";
            }

            try {
                window.FreshworksWidget("prefill", "ticketForm", {
                    email: user,
                    custom_fields: {
                        cf_serial: MRBEAM_SERIAL,
                        cf_software_version: MRBEAM_PLUGIN_VERSION,
                        cf_software_channel: channel,
                    },
                });
                window.FreshworksWidget("disable", "ticketForm", [
                    "custom_fields.cf_serial",
                    "custom_fields.cf_software_version",
                    "custom_fields.cf_software_channel",
                ]);
                window.FreshworksWidget("hide", "ticketForm", ["name"]);
                window.FreshworksWidget("setLabels", {
                    de: {
                        banner: "Hilfe & Support",
                        launcher: "Support",
                        contact_form: {
                            title: "Hilfe & Support",
                            submit: "Nachricht abschicken",
                            confirmation: "Danke für Deine Nachricht.",
                        },
                    },
                });
                $("body").prepend(
                    '<div id="freshwidget-button" ' +
                        'data-html2canvas-ignore="true" ' +
                        'class="freshwidget-button fd-btn-left" ' +
                        'style="display: none; top: 90%;"><a href="javascript:void(0)" ' +
                        'class="freshwidget-theme" style="color: rgb(226, 83, 3); ' +
                        'background-color: white; border-color: rgb(226, 83, 3);">Support</a></div>'
                );

                $("#freshwidget-button").click(function () {
                    if ($("#freshworks-frame-wrapper")[0]) {
                        FreshworksWidget("close");
                    } else {
                        FreshworksWidget("open");
                    }
                });
                console.log("FreshWidget: Shown");
            } catch (e) {
                console.log("FreshWidget: Could not be initialized");
            }
        };

        self.removeFeedbackWidget = function () {
            window.FreshworksWidget("destroy");
        };
    }

    // view model class, parameters for constructor, container to bind to
    OCTOPRINT_VIEWMODELS.push([
        FeedbackWidgetViewModel,

        // e.g. loginStateViewModel, settingsViewModel, ...
        ["loginStateViewModel"],

        // e.g. #settings_plugin_mrbeam, #tab_plugin_mrbeam, ...
        [],
    ]);
});
