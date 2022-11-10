$(function () {
    function MaterialStoreViewModel(params) {
        let self = this;
        window.mrbeam.viewModels["designStoreViewModel"] = self;
        self.material_store_iframe_src = "http://localhost:3000";
        $("#material_store_iframe").attr("src", self.material_store_iframe_src);

        self.loginState = params[0];
        self.navigation = params[1];
        self.analytics = params[2];
        self.settings = params[3];

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
