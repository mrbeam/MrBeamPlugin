$(function () {
    function WizardAnalyticsViewModel(parameters) {
        var self = this;

        self.MY_WIZARD_TAB_NAME = "wizard_plugin_corewizard_analytics_link";

        self.analyticsInitialConsent = ko.observable(null);
        self.containsAnalyticsTab = false;

        self.onBeforeWizardTabChange = function(next, current) {
            if (next !== self.MY_WIZARD_TAB_NAME && current === self.MY_WIZARD_TAB_NAME) {
                let result = self._handleAnalyticsTabExit();
                self.containsAnalyticsTab = true;
                return result;
            }
        };

        self.onBeforeWizardFinish = function() {
            if (!self.analyticsInitialConsent() && self.containsAnalyticsTab) {
                let result = self._handleAnalyticsTabExit();
                return result;
            }
        };

        self._handleAnalyticsTabExit = function(){
             if (!self.analyticsInitialConsent()) {
                 showMessageDialog({
                     title: gettext("You need to select an option"),
                     message: _.sprintf(gettext("Please make a choice about analytics.%(br)sYou will be able to change it later in the settings if you want."), {br: "<br/>"})
                 });
                 return false;
             }
        };

        self.onWizardFinish = function(){
            if(self.containsAnalyticsTab) {
                self.sendAnalyticsChoiceToServer();
            }
        };

        self.sendAnalyticsChoiceToServer = function () {
            let data = {analyticsInitialConsent: self.analyticsInitialConsent()};
            OctoPrint.simpleApiCommand("mrbeam", "analytics_init", data)
                .done(function (response) {
                    console.log("simpleApiCall response for saving analytics state: ", response);
                })
                .fail(function () {
                    console.error("Unable to save analytics state: ", data);
                    new PNotify({
                        title: gettext("Error while saving settings!"),
                        text: _.sprintf(gettext("Unable to save your analytics state at the moment.%(br)sCheck connection to Mr Beam II and try again."), {br: "<br/>"}),
                        type: "error",
                        hide: true
                    });
                });
        };

    }

    var DOM_ELEMENT_TO_BIND_TO = "wizard_plugin_corewizard_analytics";
    OCTOPRINT_VIEWMODELS.push([
        WizardAnalyticsViewModel,
        [],
        "#" + DOM_ELEMENT_TO_BIND_TO
    ]);
});
