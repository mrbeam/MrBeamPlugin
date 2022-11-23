$(function () {
    function MaterialStoreViewModel(params) {
        let self = this;

        const MATERIAL_STORE_EVENT_TYPE = {
            MR_BEAM_LOAD: "loadedFromMrBeamDevice",
            DISPLAY_PRODUCT: "displayProduct",
        };

        window.mrbeam.viewModels["materialStoreViewModel"] = self;
        self.material_store_iframe_src = "";

        self.loginState = params[0];
        self.navigation = params[1];
        self.analytics = params[2];
        self.settings = params[3];

        self.initialiseStore = function (url) {
            if (typeof url === "string" && url.trim().length !== 0) {
                if (url !== self.material_store_iframe_src) {
                    self.material_store_iframe_src = url;
                    $("#material_store_iframe").attr(
                        "src",
                        self.material_store_iframe_src
                    );
                }

                $.ajax({
                    url: self.material_store_iframe_src,
                    method: "HEAD",
                    timeout: 6000,
                    success: self.loadMaterialStore,
                    error: self.showConnectionError,
                });
            } else {
                self.showConnectionError();
            }
        };

        self.sendInitDetailsToMaterialStoreIframe = function () {
            self.sendMessageToMaterialStoreIframe(
                MATERIAL_STORE_EVENT_TYPE.MR_BEAM_LOAD
            );
        };

        self.onLoadMaterialStore = function () {
            self.sendInitDetailsToMaterialStoreIframe();
            $("#loading_spinner_wrapper").addClass("hidden");
            $("#connection_error").addClass("hidden");
        };

        self.showConnectionError = function () {
            $("#connection_error").removeClass("hidden");
            $("#loading_spinner_wrapper").addClass("hidden");
            $("#material_store_iframe").addClass("hidden");
        };

        self.loadMaterialStore = function () {
            if ($("#material_store_iframe").hasClass("hidden")) {
                $("#loading_spinner_wrapper").removeClass("hidden");
            }
            $("#material_store_iframe").removeClass("hidden");
        };

        self.displayDetailedProduct = function (url) {
            self.sendMessageToMaterialStoreIframe(
                MATERIAL_STORE_EVENT_TYPE.DISPLAY_PRODUCT,
                url
            );
        };

        self.sendMessageToMaterialStoreIframe = function (event, payload) {
            let data = {
                event: event,
                payload: payload,
            };

            document
                .getElementById("material_store_iframe")
                .contentWindow.postMessage(
                    data,
                    self.material_store_iframe_src
                );
        };

        $("#material_store_iframe").attr("src", self.material_store_iframe_src);
        $("#material_store_iframe").on("load", self.onLoadMaterialStore);
        $("#refresh_material_store_btn").click(() =>
            self.initialiseStore(self.material_store_iframe_src)
        );
    }

    OCTOPRINT_VIEWMODELS.push({
        construct: MaterialStoreViewModel,
        dependencies: [
            "loginStateViewModel",
            "navigationViewModel",
            "analyticsViewModel",
            "settingsViewModel",
        ],
        elements: ["#material_store_content"],
    });
});
