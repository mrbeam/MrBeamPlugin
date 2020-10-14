$(function () {
    function WizardAnalyticsViewModel(parameters) {
        var self = this;
        window.mrbeam.viewModels["wizardAnalyticsViewModel"] = self;

        self.wizard = parameters[0];

        self.analyticsInitialConsent = ko.observable(null);
        self.containsAnalyticsTab = false;

        self.onAfterBinding = function () {
            if (self.is_bound()) {
                self.containsAnalyticsTab = true;
            }
        };

        self.onBeforeWizardTabChange = function (next, current) {
            // If the user goes from Analytics to the previous page, we don't check the input data
            if (current && current === self.wizard.ANALYTICS_TAB) {
                let letContinue = true;
                if (self.wizard.isGoingToPreviousTab(current, next)) {
                    // We need to do this here because it's mandatory step, so it's possible that we don't actually change tab
                    $("#" + current).attr("class", "wizard-nav-list-past");
                } else {
                    letContinue = self._handleAnalyticsTabExit();
                    if (letContinue) {
                        // We need to do this here because it's mandatory step, so it's possible that we don't actually change tab
                        $("#" + current).attr("class", "wizard-nav-list-past");
                    }
                }
                return letContinue;
            }
        };

        self.onBeforeWizardFinish = function () {
            if (!self.analyticsInitialConsent() && self.containsAnalyticsTab) {
                let result = self._handleAnalyticsTabExit();
                return result;
            }
        };

        self._handleAnalyticsTabExit = function () {
            if (!self.analyticsInitialConsent()) {
                showMessageDialog({
                    title: gettext("You need to select an option"),
                    message: _.sprintf(
                        gettext(
                            "Please make a choice about analytics.%(br)sYou will be able to change it later in the settings if you want."
                        ),
                        { br: "<br/>" }
                    ),
                });
                return false;
            } else {
                return true;
            }
        };

        self.onWizardFinish = function () {
            if (self.containsAnalyticsTab) {
                self.sendAnalyticsChoiceToServer();
            }
        };

        self.sendAnalyticsChoiceToServer = function () {
            let data = {
                analyticsInitialConsent: self.analyticsInitialConsent(),
            };
            OctoPrint.simpleApiCommand("mrbeam", "analytics_init", data)
                .done(function (response) {
                    console.log(
                        "simpleApiCall response for saving analytics state: ",
                        response
                    );
                })
                .fail(function () {
                    console.error("Unable to save analytics state: ", data);
                    new PNotify({
                        title: gettext("Error while saving settings!"),
                        text: _.sprintf(
                            gettext(
                                "Unable to save your analytics state at the moment.%(br)sCheck connection to Mr Beam and try again."
                            ),
                            { br: "<br/>" }
                        ),
                        type: "error",
                        hide: true,
                    });
                });
        };

        self.is_bound = function () {
            var elem = document.getElementById(DOM_ELEMENT_TO_BIND_TO);
            return elem ? !!ko.dataFor(elem) : false;
        };
    }

    var DOM_ELEMENT_TO_BIND_TO = "wizard_plugin_corewizard_analytics";
    OCTOPRINT_VIEWMODELS.push([
        WizardAnalyticsViewModel,
        ["wizardWhatsnewViewModel"],
        "#" + DOM_ELEMENT_TO_BIND_TO,
    ]);
});
