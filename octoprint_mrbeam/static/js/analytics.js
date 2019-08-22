$(function () {
    function AnalyticsViewModel(params) {
        let self = this;
        window.mrbeam.viewModels['analyticsViewModel'] = self;
        self.window_load_ts=-1;

        self.send_fontend_event = function (event, payload) {
            payload['ts'] = payload['ts'] || new Date().getTime();
            return self._send(event, payload);
        };

        self._send = function (event, payload) {
            let data = {
                event: event,
                payload: payload || {}
            };
            return OctoPrint.simpleApiCommand("mrbeam", "analytics_data", data);
        };

        $(window).load(function() {
            self.window_load_ts = new Date().getTime()
        });

        self.onCurtainOpened = function () {
            let now = new Date().getTime();
            let payload = {
                window_load: (self.window_load_ts-INIT_TS_MS)/1000,
                curtain_open: (now-INIT_TS_MS)/1000
            };
            self.send_fontend_event('loading_dur', payload);
        };
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
