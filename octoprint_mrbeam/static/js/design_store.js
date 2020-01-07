$(function () {
    function DesignStore(params) {
        let self = this;
        window.mrbeam.viewModels['designStore'] = self;

        self.DESIGN_STORE_IFRAME_SRC = 'http://127.0.0.1';

        self.loginState = params[0];
        self.navigation = params[1];

        self.onAllBound = function () {
            self.prepareDesignStoreTab();
        };

        self.prepareDesignStoreTab = function() {
            let design_store_iframe = $('#design_store_iframe');
			design_store_iframe.on('load', function(){
                // When the iframe sends the discovery message, we respond with the user data.
                function receiveMessagesFromDesignStoreIframe(event) {
                    if (event.origin === self.DESIGN_STORE_IFRAME_SRC) {
                        console.log('## Plugin receiving ##');
                        if (event.data.event === 'discovery') {
                            console.log('# DISCOVERY');
                            self.onDesignStoreDiscovery();
                        } else if (event.data.event === 'token') {
                            console.log('# TOKEN');
                            self.onDesignStoreTokenReceived(event.data.payload);
                        }
                    }
                }
                window.addEventListener('message', receiveMessagesFromDesignStoreIframe, false);
			});

			// Add iframe source
            design_store_iframe.attr('src', self.DESIGN_STORE_IFRAME_SRC);
        };

        self.sendMessageToDesignStoreIframe = function (event, payload) {
            console.log('## Plugin sending ##');
            let data = {
                event: event,
                payload: payload,
            };

            document.getElementById('design_store_iframe').contentWindow.postMessage(data, self.DESIGN_STORE_IFRAME_SRC);
        };

        self.onDesignStoreDiscovery = function () {
            $('#design_store_iframe').show();
            $('#design_store_offline_placeholder').hide();

            let userData = {
                email: self.loginState.username(),
                serial: MRBEAM_SERIAL,
                user_token: self.loginState.currentUser().settings.mrbeam.user_token,
                version: BEAMOS_VERSION,
            };

            self.sendMessageToDesignStoreIframe('userData', userData)
        };

        self.onDesignStoreTokenReceived = function (payload) {
            console.log(payload.token);
            self.saveTokenInUserSettings(payload.token)
        };

        self.saveTokenInUserSettings = function (token) {
            let oldToken = self.loginState.currentUser().settings.mrbeam.user_token;
            if (token !== '' && oldToken !== token) {
                let currentUserSettings = self.loginState.currentUser().settings;
                currentUserSettings['mrbeam']['user_token'] = token;
                self.navigation.usersettings.updateSettings(self.loginState.currentUser().name, currentUserSettings);
            }
        };
    }

    // view model class, parameters for constructor, container to bind to
    OCTOPRINT_VIEWMODELS.push([
        DesignStore,
        // e.g. loginStateViewModel, settingsViewModel, ...
        ["loginStateViewModel", "navigationViewModel"],
        // e.g. #settings_plugin_mrbeam, #tab_plugin_mrbeam, ...
        ["#designstore"]
    ]);
});
