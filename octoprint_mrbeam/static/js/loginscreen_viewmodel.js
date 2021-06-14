/**
 * Created by andy on 03/03/2017.
 */
$(function () {
    function LoginScreenViewModel(parameters) {
        var self = this;
        window.mrbeam.viewModels["loginScreenViewModel"] = self;

        self.loginState = parameters[0];
        self.users = parameters[1];

        self.dialogElement = undefined;
        self.loginButton = undefined;

        self.onStartup = function () {
            self.dialogElement = $("#loginscreen_dialog");
            self.loginButton = $("#loginscreen_dialog button");
        };

        self.onStartupComplete = function () {
            // if (window.mrbeam.isOctoPrintVersionMin("1.3.6")) {
            //     /**
            //      * New in OP 1.3.6:
            //      * No longer triggers onUserLoggedOut() in boot sequence. Only onUserLoggedIn() -if user is logged in.
            //      * But self.loginState.loggedIn() shows correct loggedIn state in onStartupComplete()
            //      */
            //     self.setLoginState(false);
            // }
            self.setLoginState(false);

            // MR_BEAM_OCTOPRINT_PRIVATE_API_ACCESS
            let header_elem = $("#mrb_settings_users_header").detach();
            $("#settings_users > table").before(header_elem);
            header_elem.show();

            // MR_BEAM_OCTOPRINT_PRIVATE_API_ACCESS
            self.loginState.loginUser.extend({ lowercase: true });
            self.users.editorUsername.extend({ lowercase: true });
        };

        /**
         * OP callback
         * Let's make sure login screen is set to correct visibility once user finishes setup wizard.
         */
        self.onWizardFinish = function () {
            // OctoPrint.coreui.wizardOpen is still true here (OP 1.3.6), so we have to set force
            self.setLoginState(true);
            self.enableDialogAnimation();
        };

        self.setLoginState = function (force) {
            if (self.loginState.loggedIn()) {
                self.onUserLoggedIn(null, force);
            } else {
                self.onUserLoggedOut(force);
            }
        };

        self.onUserLoggedIn = function (currentUser, force) {
            if (force || !OctoPrint.coreui.wizardOpen) {
                if (OctoPrint.coreui.wizardOpen) {
                    self.disableDialogAnimation();
                }
                self.hideDialog();
            }
        };

        self.onUserLoggedOut = function (force) {
            if (force || !OctoPrint.coreui.wizardOpen) {
                if (OctoPrint.coreui.wizardOpen) {
                    self.disableDialogAnimation();
                }
                self.showDialog();
            }
        };

        self.login = function (data, event) {
            self.loginButton.prop("disabled", true);

            if (event && event.preventDefault) {
                event.preventDefault();
            }

            var r = self.loginState.login();
            r.always(function () {
                self.loginButton.prop("disabled", false);
            });
        };

        self.showDialog = function () {
            if (!self.dialogElement.hasClass("in")) {
                self.dialogElement.modal("show");
            }
            self.loginButton.prop("disabled", false);
        };

        self.hideDialog = function () {
            if (self.dialogElement.hasClass("in")) {
                self.dialogElement.modal("hide");
            }
            self.loginButton.prop("disabled", false);
        };

        self.enableDialogAnimation = function () {
            self.dialogElement.removeClass("no-transition");
        };

        /**
         * During Setup Wizard, we don't want any animations b/c it's visible behind the wizard dialog.
         */
        self.disableDialogAnimation = function () {
            self.dialogElement.addClass("no-transition");
        };
    }

    OCTOPRINT_VIEWMODELS.push([
        LoginScreenViewModel,
        ["loginStateViewModel", "usersViewModel"],
        ["#loginscreen_dialog"],
    ]);
});
