$(function() {
    function WizardSafetyViewModel(parameters) {
        var self = this;

        self.loginStateViewModel = parameters[0];


        self.checkbox1 = ko.observable(false);
        self.checkbox2 = ko.observable(false);
        self.checkbox3 = ko.observable(false);
        self.checkbox4 = ko.observable(false);
        self.checkbox5 = ko.observable(false);
        self.checkbox6 = ko.observable(false);

        self.showAgain = ko.observable(true);


        self.allChecked = ko.computed(function() {
            return (self.checkbox1() &&
                self.checkbox2() &&
                self.checkbox3() &&
                self.checkbox4() &&
                self.checkbox5() &&
                self.checkbox6());
        });

        // for stand alone dialog version
        self.agree = function() {
            var result = self._handleExit();
            if (result) {
                $('#laser_safety_overlay').modal("hide");
            }
		};

		// for wizard version
        self.onBeforeWizardTabChange = function(next, current) {
            if (current && _.startsWith(current, "wizard_plugin_corewizard_safety")) {
                var result = self._handleExit();
                return result;
            }
            return true;
        };

        self.onUserLoggedIn = function(currentUser){
            var enableCheckboxes = false;
            var showAgain = true;

            if (currentUser) {
                if (currentUser.settings && currentUser.settings.mrbeam) {
                    var beamSettings = currentUser.settings.mrbeam;

                    // HACK:
                    // this is because the first call of onUserLoggedIn() gives us a
                    // corrupted/incomplete version of the user settings.
                    if (!beamSettings.ts) {
                        console.log("This is not a valid user thingy... reloading");
                        self.loginStateViewModel.reloadUser();
                        return;
                    }
                    // end HACK

                    if (beamSettings.safety_wizard) {
                        var sent = beamSettings.safety_wizard.sent_to_cloud;
                        if (sent && sent > 0) {
                            enableCheckboxes = true;
                            if (beamSettings.safety_wizard.show_again == false) {
                                showAgain = false;
                            }
                        }
                    }
                }
            }
            self._setAll(enableCheckboxes);
            self.showAgain(showAgain);

            if ((!enableCheckboxes || showAgain) && !OctoPrint.coreui.wizardOpen) {
                self.showDialog();
            }
        };

        self.onUserLoggedOut = function(){
            self._setAll(false);
            self.showAgain(true);
        };

        self.showDialog = function() {
            if (!$('#laser_safety_overlay').hasClass('in')) {
                $('#laser_safety_overlay').modal("show");
            }
        }

        self._setAll = function(checked) {
            self.checkbox1(checked);
            self.checkbox2(checked);
            self.checkbox3(checked);
            self.checkbox4(checked);
            self.checkbox5(checked);
            self.checkbox6(checked);
        };

        self._handleExit = function(){
             if (self.allChecked()) {
                    var data = {
                        "username": self.loginStateViewModel.username(),
                        "ts": Date.now().toString(),
                        "showAgain": self.showAgain()
                    };
                    self._sendData(data);
                    return true;
                } else {
                    showMessageDialog({
                        title: gettext("You need to agree to all points"),
                        message: gettext("Please read the entire document and indicate that you understood and agree by checking all checkboxes.")
                    });
                    return false;
                }
        };

        self._sendData = function(data) {
            OctoPrint.simpleApiCommand("mrbeam", "safety_wizard_confirmation", data);
        };
    }

    OCTOPRINT_VIEWMODELS.push([
        WizardSafetyViewModel,
        ["loginStateViewModel"],
        ["#wizard_plugin_corewizard_safety", "#laser_safety_overlay"]
    ]);
});
