$(function () {
    function MaterialStoreViewModel(params) {
        let self = this;

        const MATERIAL_STORE_EVENT_TYPE = {
            MR_BEAM_LOAD: "loadedFromMrBeamDevice",
            DISPLAY_PRODUCT: "displayProduct",
        };

        window.mrbeam.viewModels["materialStoreViewModel"] = self;
        self.material_store_iframe_src = "http://localhost:3000";

        self.loginState = params[0];
        self.navigation = params[1];
        self.analytics = params[2];
        self.settings = params[3];

        self.initialiseStore = function () {
            $("#material_store_iframe").attr("loading", "eager");
        };

        self.sendInitDetailsToMaterialStoreIframe = function () {
            self.sendMessageToMaterialStoreIframe(
                MATERIAL_STORE_EVENT_TYPE.MR_BEAM_LOAD
            );
        };

        self.onLoadMaterialStore = function () {
            self.sendInitDetailsToMaterialStoreIframe();
            $("#loading_spinner").addClass("hidden");
        };

        self.showConnectionError = function () {
            $("#connection_error").removeClass("hidden");
            $("#loading_spinner").addClass("hidden");
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
        $("#material_store_iframe").on("error", self.showConnectionError);
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
