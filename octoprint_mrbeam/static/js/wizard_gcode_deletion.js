$(function () {
    function WizardGcodeDeletionViewModel(parameters) {
        var self = this;
        window.mrbeam.viewModels["WizardGcodeDeletionViewModel"] = self;

        self.wizard = parameters[0];
        self.settings = parameters[1];

        self.gcodeAutoDeletion = ko.observable(false);
        self.containsGcodeDeletionTab = false;

        self.onAfterBinding = function () {
            if (self.is_bound()) {
                self.containsGcodeDeletionTab = true;
            }
        };

        self.onWizardDetails = function() {
            if(self.settings.settings.plugins.mrbeam.gcodeAutoDeletion() && $("#wizard_plugin_corewizard_news_gcode.active").length){
                $('#wizard_plugin_corewizard_news_gcode input[type="checkbox"]').prop('checked', true);
                $('#wizard_dialog .button-next').click();
            }
        };

        self.onWizardFinish = function () {
            if (self.containsGcodeDeletionTab) {
                self.sendGcodeDeletionChoiceToServer();
            }
        };

        self.sendGcodeDeletionChoiceToServer = function () {
            let data = {
                gcodeAutoDeletionConsent: self.gcodeAutoDeletion(),
            };

            OctoPrint.simpleApiCommand("mrbeam", "gcode_deletion_init", data)
                .done(function (response) {
                    console.log(
                        "simpleApiCall response for saving gcode deletion state: ",
                        response
                    );
                })
                .fail(function () {
                    console.error(
                        "Unable to save gcode deletion state: ",
                        data
                    );
                    new PNotify({
                        title: gettext("Error while saving settings!"),
                        text: _.sprintf(
                            gettext(
                                "Unable to save your Gcode deletion state at the moment.%(br)sCheck connection to Mr Beam and try again."
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

    var DOM_ELEMENT_TO_BIND_TO = "wizard_plugin_corewizard_news_gcode";
    OCTOPRINT_VIEWMODELS.push([
        WizardGcodeDeletionViewModel,
        ["wizardWhatsnewViewModel", "settingsViewModel"],
        "#" + DOM_ELEMENT_TO_BIND_TO,
    ]);
});
