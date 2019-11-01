$(function () {
    function AnalyticsViewModel(params) {
        let self = this;
        window.mrbeam.viewModels['analyticsViewModel'] = self;
        self.window_load_ts=-1;

        self.send_fontend_event = function (event, payload) {
            payload['ts'] = payload['ts'] || new Date().getTime();
            payload['browser_time'] = new Date().toLocaleString('en-GB');  //GB so that we don't get AM/PM
            return self._send(event, payload);
        };

        self._send = function (event, payload) {
            let data = {
                event: event,
                payload: payload || {}
            };

            $.ajax({
                url: "plugin/mrbeam/analytics",
                type: "POST",
                dataType: "json",
                contentType: "application/json; charset=UTF-8",
                data: JSON.stringify(data)
            });
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
