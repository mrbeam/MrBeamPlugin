$(function () {
    function DesignStoreViewModel(params) {
        let self = this;
        window.mrbeam.viewModels["designStoreViewModel"] = self;

        self.DESIGN_STORE_IFRAME_SRC =
            "https://design-store-269610.appspot.com"; // Don't write a "/" at the end!!
        // self.DESIGN_STORE_IFRAME_SRC = 'http://localhost:8080';

        self.loginState = params[0];
        self.navigation = params[1];
        self.analytics = params[2];
        self.settings = params[3];

        self.onUserLoggedIn = function () {
            if (window.mrbeam.isDev() || window.mrbeam.isBeta()) {
                self.prepareDesignStoreTab();
            }
        };

        self.getEmail = function () {
            return (
                self.loginState.currentUser().settings.mrbeam
                    .design_store_email || self.loginState.username()
            );
        };

        self.getAuthToken = function () {
            return (
                self.loginState.currentUser().settings.mrbeam
                    .design_store_auth_token ||
                self.loginState.currentUser().settings.mrbeam.user_token
            );
        };

        self.prepareDesignStoreTab = function () {
            let design_store_iframe = $("#design_store_iframe");
            design_store_iframe.on("load", function () {
                // When the iframe sends the discovery message, we respond with the user data.
                function receiveMessagesFromDesignStoreIframe(event) {
                    if (event.origin === self.DESIGN_STORE_IFRAME_SRC) {
                        switch (event.data.event) {
                            case "discovery":
                                self.onDiscoveryReceived();
                                break;
                            case "token":
                                self.onTokenReceived(event.data.payload);
                                break;
                            case "svg":
                                self.onSvgReceived(event.data.payload);
                                break;
                            case "viewLibrary":
                                $("#designlib_tab_btn").trigger("click");
                                break;
                            case "notification":
                                new PNotify(event.data.payload);
                                break;
                            case "analytics":
                                self.analytics.send_fontend_event(
                                    "store",
                                    event.data.payload
                                );
                        }
                    }
                }
                window.addEventListener(
                    "message",
                    receiveMessagesFromDesignStoreIframe,
                    false
                );
            });

            // Add iframe source
            design_store_iframe.attr("src", self.DESIGN_STORE_IFRAME_SRC);
        };

        self.sendMessageToDesignStoreIframe = function (event, payload) {
            let data = {
                event: event,
                payload: payload,
            };

            document
                .getElementById("design_store_iframe")
                .contentWindow.postMessage(data, self.DESIGN_STORE_IFRAME_SRC);
        };

        self.onDiscoveryReceived = function () {
            $("#design_store_iframe").show();
            $("#design_store_offline_placeholder").hide();

            let userData = {
                email: self.getEmail(),
                serial: MRBEAM_SERIAL,
                user_token: self.getAuthToken(),
                version: BEAMOS_VERSION,
                language: MRBEAM_LANGUAGE,
            };

            self.sendMessageToDesignStoreIframe("userData", userData);
        };

        self.onTokenReceived = function (payload) {
            self.saveTokenInUserSettings(payload.token);
        };

        self.onSvgReceived = function (payload) {
            self.downloadSvgToMrBeam(payload.svg_string, payload.file_name);
        };

        self.saveTokenInUserSettings = function (token) {
            let oldToken = self.getAuthToken();
            if (token !== "" && oldToken !== token) {
                let currentUserSettings = self.loginState.currentUser()
                    .settings;
                delete currentUserSettings["mrbeam"]["user_token"];
                currentUserSettings["mrbeam"][
                    "design_store_auth_token"
                ] = token;
                self.navigation.usersettings.updateSettings(
                    self.loginState.currentUser().name,
                    currentUserSettings
                );
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

                    // We still wait a couple of seconds before telling the store, because the design is not loaded yet.
                    // Note: the Octoprint events FileAdded and UpdatedFiles come before this, so they are not helpful in this case.
                    setTimeout(function () {
                        self.sendMessageToDesignStoreIframe("downloadOk", {});
                    }, 2000);
                },
                error: function (jqXHR, textStatus, errorThrown) {
                    console.error(
                        "Store bought design saving failed with status " +
                            jqXHR.status,
                        textStatus,
                        errorThrown
                    );
                    new PNotify({
                        title: gettext("Could not download design"),
                        text: gettext(
                            "The purchased design could not be downloaded. Please download again."
                        ),
                        type: "error",
                        tag: "purchase_error",
                        hide: false,
                    });
                },
            });
        };

        self.goToStore = function () {
            if ($("#designstore_tab_btn").parent().hasClass("active")) {
                self.sendMessageToDesignStoreIframe("goToStore", {});
            }
        };

        self.reloadDesignStoreIframe = function () {
            let refreshButtonElement = $(".refresh-connection");
            let refreshButtonText = refreshButtonElement.text();
            refreshButtonElement.text("...");
            setTimeout(function () {
                refreshButtonElement.text(refreshButtonText);
            }, 3000);
            document.getElementById("design_store_iframe").src =
                self.DESIGN_STORE_IFRAME_SRC;
        };
    }

    // view model class, parameters for constructor, container to bind to
    OCTOPRINT_VIEWMODELS.push([
        DesignStoreViewModel,
        // e.g. loginStateViewModel, settingsViewModel, ...
        [
            "loginStateViewModel",
            "navigationViewModel",
            "analyticsViewModel",
            "settingsViewModel",
        ],
        // e.g. #settings_plugin_mrbeam, #tab_plugin_mrbeam, ...
        ["#designstore"],
    ]);
});
