$(function () {
    function AnalyticsViewModel(params) {
        let self = this;
        window.mrbeam.viewModels['analyticsViewModel'] = self;

        self.send_fontend_event = function (event, payload) {
            payload['ts'] = payload['ts'] || new Date().getTime();
            return self._send(event, payload);
        };

        self._send = function (event, payload) {
            data = {
                event: event,
                payload: payload || {}
            };
            return OctoPrint.simpleApiCommand("mrbeam", "analytics_data", data);
        }
    }

    // view model class, parameters for constructor, container to bind to
    OCTOPRINT_VIEWMODELS.push([
        AnalyticsViewModel,

        // e.g. loginStateViewModel, settingsViewModel, ...
        [],

        // e.g. #settings_plugin_mrbeam, #tab_plugin_mrbeam, ...
        []
    ]);
});
