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

        self.PROD = "prod"
        self.STAGING = "staging"
        self.DEV = "dev"
        self.LOCALHOST = "localhost"
        self.DEFAULT_LOCALHOST_PORT = "8080"
        self.DEFAULT_VERSION = "1-1-0"

        self.DESIGN_STORE_PRODUCTION_IFRAME_SRC = 'https://designs.cloud.mr-beam.org';
        self.DESIGN_STORE_LOCALHOST_IFRAME_SRC = "http://localhost";

        self.designStore = parameters[0];
        self.loginState = parameters[1];
        self.navigation = parameters[2];

        self.lastDsMail = null;

        self.devDsEmail = ko.observable();
        self.devDsVersion = ko.observable(self.DEFAULT_VERSION);
        self.devDsLocalhostPort = ko.observable(self.DEFAULT_LOCALHOST_PORT);
        self.authToken = ko.observable();
        self.devDsEmail.subscribe(function (newValue) {
            if (self.loginState.currentUser?.().settings?.mrbeam) {
                self.handleChange();
            }
        });

        self.selectedEnv = ko.observable(self.PROD);

        self.isStagingOrDev = ko.computed(function () {
            return self.selectedEnv() === self.DEV || self.selectedEnv() === self.STAGING;
        });

        self.isLocalhost = ko.computed(function () {
            return self.selectedEnv() === self.LOCALHOST;
        });

        self.design_store_staging_iframe_src = ko.computed(function () {
            return 'https://' + self.devDsVersion() + '-staging-dot-design-store-269610.appspot.com';
        });

        self.design_store_development_iframe_src = ko.computed(function () {
            return 'https://' + self.devDsVersion() + '-dev-dot-design-store-269610.appspot.com';
        });

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
            if (self.selectedEnv() === self.PROD) {
                self.designStore.DESIGN_STORE_IFRAME_SRC = self.DESIGN_STORE_PRODUCTION_IFRAME_SRC;
            } else if (self.selectedEnv() === self.STAGING) {
                self.designStore.DESIGN_STORE_IFRAME_SRC = self.design_store_staging_iframe_src();
            } else if (self.selectedEnv() === self.DEV) {
                self.designStore.DESIGN_STORE_IFRAME_SRC = self.design_store_development_iframe_src();
            } else if (self.selectedEnv() === self.LOCALHOST) {
                self.designStore.DESIGN_STORE_IFRAME_SRC = self.DESIGN_STORE_LOCALHOST_IFRAME_SRC + ":" + self.devDsLocalhostPort();
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
