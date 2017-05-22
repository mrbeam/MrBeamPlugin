$(function() {
    function LaserSafetyViewModel(parameters) {
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
                self.hideDialog();
            }
		};

		// for wizard version
        self.onBeforeWizardTabChange = function(next, current) {
            if (current && _.startsWith(current, "wizard_plugin_corewizard_lasersafety")) {
                var result = self._handleExit();
                return result;
            }
            return true;
        };

        self.onUserLoggedIn = function(currentUser){
            if (OctoPrint.coreui.wizardOpen) return;

            var enableCheckboxes = false;
            var showAgain = true;

            if (currentUser) {
                if (currentUser.settings && currentUser.settings.mrbeam) {
                    var beamSettings = currentUser.settings.mrbeam;

                    // HACK:
                    // // ANDYTEST TODO: this should be fixed in OctoPrint 1.3.2
                    // this is because the first call of onUserLoggedIn() gives us a
                    // corrupted/incomplete version of the user settings.
                    if (!beamSettings.ts) {
                        console.log("This is not a valid user thingy... reloading");
                        self.loginStateViewModel.reloadUser();
                        return;
                    }
                    // end HACK

                    if (beamSettings.lasersafety) {
                        var sent = beamSettings.lasersafety.sent_to_cloud;
                        if (sent && sent > 0) {
                            enableCheckboxes = true;
                            if (beamSettings.lasersafety.show_again == false) {
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

        // if we get this, there must be a Setup Wizard active....
        // so remove this one quickly
        self.onWizardShow = function(){
            if (OctoPrint.coreui.wizardOpen) {
                self.hideDialog();
            }
        }

        self.showDialog = function() {
            if (!$('#lasersafety_overlay').hasClass('in')) {
                $('#lasersafety_overlay').modal("show");
            }
        }

        self.hideDialog = function() {
            $('#lasersafety_overlay').modal("hide");
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
            OctoPrint.simpleApiCommand("mrbeam", "lasersafety_confirmation", data)
                .fail(function(){
                    new PNotify({
                        title: gettext("Laser Safety notice will show again."),
                        text: gettext("Device needs to have a working internet connection to submit your confirmation. We aren't able to reach our servers therefore we'll show this warning again."),
                        type: "warning",
                        hide: true
                    });
                });
        };
    }

    OCTOPRINT_VIEWMODELS.push([
        LaserSafetyViewModel,
        ["loginStateViewModel"],
        ["#wizard_plugin_corewizard_lasersafety", "#lasersafety_overlay"]
    ]);
});
