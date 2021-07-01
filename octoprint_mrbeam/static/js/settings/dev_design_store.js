/*
 * View model for Mr Beam
 *
 * Author: Andy Werner <andy@mr-beam.org>
 */
/* global OctoPrint, OCTOPRINT_VIEWMODELS */

$(function () {
    function DevDesignStoreViewModel(parameters) {
        var self = this;
        window.mrbeam.viewModels["devDesignStoreViewModel"] = self;

        self.designStore = parameters[0];
        self.loginState = parameters[1];
        self.navigation = parameters[2];

        self.lastDsMail = null;
        self.devDsEmail = ko.observable();
        self.authToken = ko.observable();
        self.devDsEmail.subscribe(function (newValue) {
            self.handleChange();
        });

        self.selectedEnv = ko.observable('prod');

        self.onUserLoggedIn = function () {
            self.lastDsMail = self.designStore.getEmail();
            self.devDsEmail(self.designStore.getEmail());
            self.authToken(self.designStore.getAuthToken());
        };

        self.onSettingsShown = function () {
            self.lastDsMail = self.designStore.getEmail();
            self.devDsEmail(self.designStore.getEmail());
            self.showAuthToken();
        };

        self.handleChange = function () {
            self.devDsEmail(self.devDsEmail().trim());
            let currentUserSettings = self.loginState.currentUser().settings;
            currentUserSettings["mrbeam"]["design_store_email"] =
                self.devDsEmail() || null;

            // if email has really changed
            if (self.devDsEmail() != self.lastDsMail) {
                // if different email, we need to delete auth token.
                delete currentUserSettings["mrbeam"]["user_token"];
                currentUserSettings["mrbeam"]["design_store_auth_token"] = null;
                // hacky way to reload iframe
                $("#design_store_iframe").attr("src", function (i, val) {
                    return val;
                });
            }
            self.navigation.usersettings.updateSettings(
                self.loginState.currentUser().name,
                currentUserSettings
            );
            self.lastDsMail = self.designStore.getEmail();
            self.showAuthToken();
        };

        self.changeEnv = function () {
            if (self.selectedEnv() === 'prod') {
                self.designStore.DESIGN_STORE_IFRAME_SRC = 'https://designs.cloud.mr-beam.org';
            } else if (self.selectedEnv() === 'staging') {
                self.designStore.DESIGN_STORE_IFRAME_SRC = 'https://1-0-0-staging-dot-design-store-269610.appspot.com';
            } else if (self.selectedEnv() === 'dev') {
                self.designStore.DESIGN_STORE_IFRAME_SRC = 'https://1-0-0-dev-dot-design-store-269610.appspot.com';
            }
            self.designStore.reloadDesignStoreIframe();
        }

        self.showAuthToken = function () {
            if (self.designStore.getAuthToken()) {
                self.authToken(self.designStore.getAuthToken());
                $("#settings-mrbeam-design-store-auth-token").css(
                    "text-decoration",
                    "none"
                );
            } else {
                $("#settings-mrbeam-design-store-auth-token").css(
                    "text-decoration",
                    "line-through"
                );
            }
        };
    }

    // view model class, parameters for constructor, container to bind to
    OCTOPRINT_VIEWMODELS.push([
        DevDesignStoreViewModel,

        // e.g. loginStateViewModel, settingsViewModel, ...
        ["designStoreViewModel", "loginStateViewModel", "navigationViewModel"],

        // e.g. #settings_plugin_mrbeam, #tab_plugin_mrbeam, ...
        ["#settings_plugin_mrbeam_dev_design_store"],
    ]);
});
