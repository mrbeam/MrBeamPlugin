$(function () {
    function WizardAnalyticsViewModel(parameters) {
        var self = this;

        self.MY_WIZARD_TAB_NAME = "wizard_plugin_corewizard_analytics_link";

        self.analyticsInitialConsent = ko.observable(null);

        self.onAfterWizardTabChange = function (current) {
            if (current === self.MY_WIZARD_TAB_NAME) {
                if (self.analyticsInitialConsent() == null) {
                    $("#wizard_dialog div.modal-footer button.button-finish").prop("disabled", true);
                    $("#wizard_dialog div.modal-footer button.button-next").prop("disabled", true);
                    $("#wizard_dialog div.modal-footer button.button-finish").removeAttr("onclick");
                    $("#wizard_dialog div.modal-footer button.button-next").removeAttr("onclick");
                }
            }
        };

        // self.onBeforeWizardTabChange = function(next, current) {
        //     if (next !== self.MY_WIZARD_TAB_NAME && current === self.MY_WIZARD_TAB_NAME) {
        //         console.log("Leaving Analytics Wizard, removing click listeners");
        //         $("#wizard_dialog div.modal-footer button.button-finish").prop("disabled", false);
        //         $("#wizard_dialog div.modal-footer button.button-next").prop("disabled", false);
        //         $("#wizard_dialog div.modal-footer button.button-finish").removeAttr("onclick");
        //         $("#wizard_dialog div.modal-footer button.button-next").removeAttr("onclick");
        //         return true;
        //     }
        // };
        self.onWizardFinish = function(){
            console.log("AnalyticsWizardViewModel onWizardFinish");
        };

        self.prepareLetsGoButtonToSaveAnalytics = function () {
            $("#wizard_dialog div.modal-footer button.button-finish").prop("disabled", false);
            $("#wizard_dialog div.modal-footer button.button-next").prop("disabled", false);
            $("#wizard_dialog div.modal-footer button.button-finish").click(self.sendAnalyticsChoiceToServer);
            $("#wizard_dialog div.modal-footer button.button-next").click(self.sendAnalyticsChoiceToServer);
            return true; // "The click binding stops the default browser handler from running. In this case, the browser responds to canceling the "click" event by changing the radio buttons back to what they were before. The return true tells Knockout to allow the default behavior to happen."
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
                        title: "Error while saving settings!",
                        text: "Unable to save your analytics state at the moment.<br/>Check connection to Mr Beam II and try again.",
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
