$(function () {
    function ReviewViewModel(params) {
        console.log('################### REVIEW VIEW MODEL');
        let self = this;
        self.settings = params[0];

        window.mrbeam.viewModels['reviewViewModel'] = self;
        self.window_load_ts = -1;

        self.showReviewDialog = ko.observable(false);
        self.jobTimeEstimation = ko.observable(-1);


        self.onAllBound = function () {
            self.reviewDialog = $('#review_dialog');
            self.askForReview = ko.observable(self.settings.settings.plugins.mrbeam.ask_for_review());
        };

        self.onEventJobTimeEstimated = function (payload) {
            self.jobTimeEstimation(payload['job_time_estimation']);
        };

        self.onEventPrintStarted = function(payload) {
            setTimeout(function () {
                if (self.askForReview) {
                    console.log('################### SHOW!');
                    self.showReviewDialog(true);
                    self.reviewDialog.modal("show");
                }
            }, 5000);
        };

        self.exitBtn = function(){
            self.reviewDialog.modal("hide");
            // todo iratxe send analytics
            self.sendReviewToServer()
        };

        self.sendReviewToServer = function () {
		    let noReview = true;//!self.dontRemindMeAgainChecked();
            let score = 4;
		    let review = $('#review_textarea').val();
            let data = {
                noReview: noReview,
                score: score,
                review: review
            };

            OctoPrint.simpleApiCommand("mrbeam", "review_data", data)
                .done(function (response) {
                    self.settings.requestData();
                    console.log("simpleApiCall response for saving review: ", response);
                })
                .fail(function () {
                    self.settings.requestData();
                    console.error("Unable to save review state: ", data);
                    new PNotify({
                        title: gettext("Error while saving review!"),
                        text: _.sprintf(gettext("Unable to save your review at the moment.%(br)sCheck connection to Mr Beam II and try again."), {br: "<br/>"}),
                        type: "error",
                        hide: true
                    });
                });
        };

        $(window).load(function() {
            self.window_load_ts = new Date().getTime()
        });
    }

    // view model class, parameters for constructor, container to bind to
    OCTOPRINT_VIEWMODELS.push([
        ReviewViewModel,

        // e.g. loginStateViewModel, settingsViewModel, ...
        ['settingsViewModel'],

        // e.g. #settings_plugin_mrbeam, #tab_plugin_mrbeam, ...
        ['#review_dialog']
    ]);
});
