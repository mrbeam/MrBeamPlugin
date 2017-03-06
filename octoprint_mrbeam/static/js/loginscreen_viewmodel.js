/**
 * Created by andy on 03/03/2017.
 */
$(function() {
    function LoginScreenViewModel(parameters) {
        var self = this;

        self.loginState = parameters[0];

        self.dialogElement = undefined;
        self.loginButton = undefined;


        self.onStartup = function() {
            self.dialogElement = $('#loginscreen_dialog');
            self.loginButton = $('#loginscreen_dialog button');
        }

        self.onUserLoggedIn = function(currentUser){
            if (!OctoPrint.coreui.wizardOpen) {
                self.hideDialog();
            }
        };

        self.onUserLoggedOut = function(){
            if (!OctoPrint.coreui.wizardOpen) {
                self.showDialog();
            }
        };

        self.login = function (data, event) {
            self.loginButton.prop('disabled', true);

            if (event && event.preventDefault) {
                event.preventDefault();
            }

            var r = self.loginState.login();
            r.always(function () {
                self.loginButton.prop('disabled', false);
            });
        };

        self.showDialog = function() {
            if (!self.dialogElement.hasClass('in')) {
                self.dialogElement.modal("show");
            }
            self.loginButton.prop('disabled', false);
        }

        self.hideDialog = function() {
            if (self.dialogElement.hasClass('in')) {
                self.dialogElement.modal("hide");
            }
            self.loginButton.prop('disabled', false);
        }

    }

    OCTOPRINT_VIEWMODELS.push([
        LoginScreenViewModel,
        ["loginStateViewModel"],
        ["#loginscreen_dialog"]
    ]);
});
