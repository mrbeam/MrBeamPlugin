$(function() {
    function CoreWizardAclViewModel(parameters) {
        var self = this;

        self.loginStateViewModel = parameters[0];

        self.username = ko.observable(undefined);
        self.password = ko.observable(undefined);
        self.confirmedPassword = ko.observable(undefined);

        self.setup = ko.observable(false);
        self.decision = ko.observable();

        self.passwordMismatch = ko.pureComputed(function() {
            return self.password() != self.confirmedPassword();
        });

        self.validUsername = ko.pureComputed(function() {
            return self.username() && self.username().trim() != "";
        });

        self.validPassword = ko.pureComputed(function() {
            return self.password() && self.password().trim() != "";
        });

        self.validData = ko.pureComputed(function() {
            return !self.passwordMismatch() && self.validUsername() && self.validPassword();
        });

        self.keepAccessControl = function() {
            if (!self.validData()) return;

            var data = {
                "ac": true,
                "user": self.username(),
                "pass1": self.password(),
                "pass2": self.confirmedPassword()
            };
            self._sendData(data);
        };

        self.disableAccessControl = function() {
            var message = gettext("If you disable Access Control <strong>and</strong> your OctoPrint installation is accessible from the internet, your printer <strong>will be accessible by everyone - that also includes the bad guys!</strong>");
            showConfirmationDialog({
                message: message,
                onproceed: function (e) {
                    var data = {
                        "ac": false
                    };
                    self._sendData(data);
                }
            });
        };

        self._sendData = function(data, callback) {
            OctoPrint.postJson("plugin/mrbeam/acl", data)
                .done(function() {
                    self.setup(true);
                    self.decision(data.ac);
                    if (data.ac) {
                        // we now log the user in
                        var user = data.user;
                        var pass = data.pass1;
                        self.loginStateViewModel.login(user, pass, true)
                            .done(function() {
                                if (callback) callback();
                            });
                    } else {
                        if (callback) callback();
                    }
                });
        };

        self.onBeforeWizardTabChange = function(next, current) {
            if (current && _.startsWith(current, "wizard_plugin_corewizard_acl_")) {
                if (self.validData()) {
                    var data = {
                    "ac": true,
                    "user": self.username(),
                    "pass1": self.password(),
                    "pass2": self.confirmedPassword()
                    };
                    self._sendData(data);
                    return true;
                } else {
                    if (!self.validUsername()) {
                        showMessageDialog({
                            title: gettext("Invalid emtpy username"),
                            message: gettext("You need to enter a valid username.")
                        });
                    } else if (!self.validPassword()) {
                        showMessageDialog({
                            title: gettext("Invalid emtpy password"),
                            message: gettext("You need to enter a valid password.")
                        });
                    } else if (self.passwordMismatch()) {
                        showMessageDialog({
                            title: gettext("Passwords do not match"),
                            message: gettext("Please retype your password.")
                        });
                    }
                    return false;
                }
            }
            return true;
        };

        self.onWizardFinish = function() {
            if (!self.decision()) {
                return "reload";
            }
        };
    }

    OCTOPRINT_VIEWMODELS.push([
        CoreWizardAclViewModel,
        ["loginStateViewModel"],
        "#wizard_plugin_corewizard_acl"
    ]);
});
