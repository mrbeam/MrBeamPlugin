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
                            self.onDiscoveryReceived();
                        } else if (event.data.event === 'token') {
                            console.log('# TOKEN');
                            self.onTokenReceived(event.data.payload);
                        } else if (event.data.event === 'svg') {
                            console.log('# SVG');
                            self.onSvgReceived(event.data.payload);
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

        self.onDiscoveryReceived = function () {
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

        self.onTokenReceived = function (payload) {
            console.log(payload.token);
            self.saveTokenInUserSettings(payload.token);
        };

        self.onSvgReceived = function (payload) {
            console.log(payload.svg_string);
            self.downloadSvgToMrBeam(payload.svg_string, payload.file_name);
        };

        self.saveTokenInUserSettings = function (token) {
            let oldToken = self.loginState.currentUser().settings.mrbeam.user_token;
            if (token !== '' && oldToken !== token) {
                let currentUserSettings = self.loginState.currentUser().settings;
                currentUserSettings['mrbeam']['user_token'] = token;
                self.navigation.usersettings.updateSettings(self.loginState.currentUser().name, currentUserSettings);
            }
        };

        self.downloadSvgToMrBeam = function (svg_string, file_name) {
            let data = {
                command: "save_svg",
                svg_string: svg_string,
                file_name: file_name,
            };
            let json = JSON.stringify(data);

            $.ajax({
                url: "plugin/mrbeam/save_store_bought_svg",
                type: "POST",
                dataType: "json",
                contentType: "application/json; charset=UTF-8",
                data: json,
                success: function (response) {
                    console.log("Store bought design saved.", response);

                    // todo iratxe: change button from "Downloading" to "Done" or whatever
                },
                error: function ( jqXHR, textStatus, errorThrown) {
                    console.error("Store bought design saving failed with status " + jqXHR.status, textStatus, errorThrown);
                    new PNotify({
                        title: gettext("Could not download design"),
                        text: gettext("The purchased design could not be downloaded. Please download again."),    //todo iratxe: specify this error
                        type: "error",
                        tag: "purchase_error",
                        hide: false
                    });
                }
            });

        }
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
