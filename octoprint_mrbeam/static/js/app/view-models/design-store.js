$(function () {
    function DesignStoreViewModel(params) {
        let self = this;
        window.mrbeam.viewModels["designStoreViewModel"] = self;

        // // Don't write a "/" at the end!! //
        // prod
        self.DESIGN_STORE_IFRAME_SRC = "https://designs.cloud.mr-beam.org";
        // staging:
        // 'https://1-0-0-staging-dot-design-store-269610.appspot.com'
        // 'http://localhost:8080';
        self.DESIGN_STORE_IFRAME_HEALTHCHECK_SRC =
            self.DESIGN_STORE_IFRAME_SRC + "/api/healthcheck";
        self.DESIGN_STORE_TAB_ELEMENT = $("#designstore_tab_btn");
        self.DESIGN_STORE_NOTIFY_ICON_ELEMENT =
            self.DESIGN_STORE_TAB_ELEMENT.find("span.notify-icon");

        self.loginState = params[0];
        self.navigation = params[1];
        self.analytics = params[2];
        self.settings = params[3];
        self.laserheadChangedVM = params[4];

        self.lastUploadedDate = ko.observable("");
        self.eventListenerAdded = ko.observable(false);

        self.onUserLoggedIn = function () {
            if (self.laserheadChangedVM.laserHeadXDetected()) {
                self.showNotifyIcon();
            }
        };

        self.initialiseStore = function () {
            let designStoreIframeElement = $("#design_store_iframe");
            if (
                designStoreIframeElement.attr("src") !==
                self.DESIGN_STORE_IFRAME_SRC
            ) {
                self.prepareDesignStoreTab();
                self.lazyLoadStore();
                // Handle design store if offline
                // This will show the network issue page if the device is offline
                // However, if the device gets online afterwards, this will not change
                // until the user refreshes the page
                if (!window.mrbeam.isOnline) {
                    $("#designstore > .loading_spinner_wrapper").hide();
                    $("#design_store_iframe").hide();
                    $("#design_store_offline_placeholder").show();
                }
            }
        };

        self.getUserSettings = function () {
            return self.loginState.currentUser?.()?.settings;
        };

        self.getEmail = function () {
            const userSettings = self.getUserSettings();
            if (userSettings?.mrbeam?.design_store_email) {
                return userSettings.mrbeam.design_store_email;
            } else {
                return self.loginState.username();
            }
        };

        self.getAuthToken = function () {
            const userSettings = self.getUserSettings();
            if (
                userSettings?.mrbeam?.design_store_auth_token ||
                userSettings?.mrbeam?.user_token
            ) {
                return (
                    userSettings.mrbeam.design_store_auth_token ||
                    userSettings.mrbeam.user_token
                );
            } else {
                return undefined;
            }
        };

        // TODO: use this to get user settings in SW-2817
        self.getLastUploadedDate = function () {
            const userSettings = self.getUserSettings();
            if (userSettings?.mrbeam?.design_store_last_uploaded) {
                return userSettings.mrbeam.design_store_last_uploaded;
            } else {
                return undefined;
            }
        };

        self.prepareDesignStoreTab = function () {
            let design_store_iframe = $("#design_store_iframe");
            design_store_iframe.on("load", function () {
                // When the iframe sends the discovery message, we respond with the user data.
                function receiveMessagesFromDesignStoreIframe(event) {
                    // Check for startsWith to ignore the port, eg. localhost:80
                    if (self.DESIGN_STORE_IFRAME_SRC.startsWith(event.origin)) {
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
                                self.analytics.send_frontend_event(
                                    "store",
                                    event.data.payload
                                );
                        }
                    }
                }

                if (!self.eventListenerAdded()) {
                    window.addEventListener(
                        "message",
                        receiveMessagesFromDesignStoreIframe,
                        false
                    );
                    self.eventListenerAdded(true);
                }
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
            $("#designstore > .loading_spinner_wrapper").hide();

            // TODO: remove the following Version sanitization once the version
            //  comparative methods support "pep440" versioning (SW-1047)
            // Regex to extract the  base version from a version string
            // 0.10.2-alpha --> 0.10.2  (SemVer)
            // 0.11.78a0    --> 0.11.78 (PEP440)
            // 0+unknown    --> 0       (No version info)
            let regexp = /([0-9]+(?:\.[0-9]+)*)/g;
            let mrbeamPluginVersion = MRBEAM_PLUGIN_VERSION.match(regexp)[0];
            console.log(
                "Design store: Mr Beam Plugin Version: " + mrbeamPluginVersion
            );

            let userData = {
                email: self.getEmail(),
                serial: MRBEAM_SERIAL,
                user_token: self.getAuthToken(),
                version: mrbeamPluginVersion,
                language: MRBEAM_LANGUAGE,
                // TODO: remove this once the design store is updated after SW-2537
                last_uploaded: self.getLastUploadedDate(),
            };

            self.sendMessageToDesignStoreIframe("userData", userData);

            if (self.laserheadChangedVM.laserHeadChanged()) {
                self.sendMessageToDesignStoreIframe("laserheadChanged", {
                    laserheadModelId:
                        self.laserheadChangedVM.laserheadModelId(),
                });
            }
        };

        self.onTokenReceived = function (payload) {
            self.saveTokenInUserSettings(payload.token);
        };

        // TODO: use this to show 'new designs' notification in SW-2817
        self.onLastUploadedDateReceived = function (payload) {
            let oldLastUploaded = self.getLastUploadedDate();
            if (
                payload.last_uploaded &&
                oldLastUploaded &&
                oldLastUploaded !== payload.last_uploaded
            ) {
                self.showNotifyIcon();
            }
            self.lastUploadedDate(payload.last_uploaded);
        };

        self.removeNotifyIcon = function () {
            if (self.DESIGN_STORE_NOTIFY_ICON_ELEMENT.length !== 0) {
                self.DESIGN_STORE_NOTIFY_ICON_ELEMENT.remove();
            }
        };

        self.showNotifyIcon = function () {
            if (self.DESIGN_STORE_NOTIFY_ICON_ELEMENT.length === 0) {
                self.DESIGN_STORE_TAB_ELEMENT.append(
                    '<span class="notify-icon"></span>'
                );
            }
        };

        self.onSvgReceived = function (payload) {
            self.downloadSvgToMrBeam(payload.svg_string, payload.file_name);
        };

        self.saveTokenInUserSettings = function (token) {
            let oldToken = self.getAuthToken();
            let currentUserSettings = self.getUserSettings();
            if (
                token !== "" &&
                oldToken !== token &&
                currentUserSettings?.mrbeam
            ) {
                delete currentUserSettings["mrbeam"]["user_token"];
                currentUserSettings["mrbeam"]["design_store_auth_token"] =
                    token;
                self.navigation.usersettings.updateSettings(
                    self.loginState.currentUser().name,
                    currentUserSettings
                );
            }
        };

        // TODO: use this to update user settings in SW-2817
        self.saveLastUploadedInUserSettings = function (lastUploaded) {
            let oldLastUploaded = self.getLastUploadedDate();
            let currentUserSettings = self.getUserSettings();
            if (
                lastUploaded !== "" &&
                oldLastUploaded !== lastUploaded &&
                currentUserSettings?.mrbeam
            ) {
                currentUserSettings["mrbeam"]["design_store_last_uploaded"] =
                    lastUploaded;
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

        self.lazyLoadStore = function () {
            // Lazy load the iframe
            $("#design_store_iframe").attr("loading", "eager");
            // TODO: use this to handle user being notified "event" in SW-2817
            self.onUserNotified();
        };

        self.onUserNotified = function () {
            // Handle the 'new designs' notification icon
            self.removeNotifyIcon();
            // Update user settings
            let oldLastUploaded = self.getLastUploadedDate();
            if (
                self.lastUploadedDate() &&
                self.lastUploadedDate() !== "" &&
                oldLastUploaded !== self.lastUploadedDate()
            ) {
                self.saveLastUploadedInUserSettings(self.lastUploadedDate());
            }
        };

        self.reloadDesignStoreIframe = function () {
            let refreshButtonElement = $(".refresh-connection");
            let refreshButtonText = refreshButtonElement.text();
            refreshButtonElement.text("...");
            setTimeout(function () {
                refreshButtonElement.text(refreshButtonText);
            }, 3000);
            document.getElementById("design_store_iframe").src = "#";
            self.initialiseStore();
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
            "laserheadChangedViewModel",
        ],
        // e.g. #settings_plugin_mrbeam, #tab_plugin_mrbeam, ...
        ["#designstore"],
    ]);
});
