$(function () {
    function ReviewViewModel(params) {
        let self = this;
        self.settings = params[0];
        self.analytics = params[1];
        self.loginState = params[2];

        window.mrbeam.viewModels['reviewViewModel'] = self;

        self.showReviewDialog = ko.observable(false);
        self.jobTimeEstimation = ko.observable(-1);

        self.rating = ko.observable(0);
        self.dontShowAgain = ko.observable(false);
        self.reviewGiven = ko.observable(false);
        self.shouldAskForReview = ko.observable(false);

        self.onAllBound = function () {
            self.reviewDialog = $('#review_dialog');
            self.shouldAskForReview(self.settings.settings.plugins.mrbeam.should_ask_for_review());

            let links = ['give_review_link', 'dont_ask_review_link'];
            links.forEach(function (linkId) {
                $('#' + linkId).click(function () {
                    let payload = {
                        link: linkId
                    };
                    self.analytics.send_fontend_event('link_click', payload)
                })
            });
        };

        self.onEventJobTimeEstimated = function (payload) {
            self.jobTimeEstimation(payload['job_time_estimation']);
        };

        self.onEventPrintStarted = function(payload) {
            self.enableRatingStars();

            setTimeout(function () {
                if (self.shouldAskForReview() && self.jobTimeEstimation() >= 61) {
                    self.showReviewDialog(true);
                    self.reviewDialog.modal("show");
                }
            }, 5000);
        };

        self.enableRatingStars = function() {
            $('.star').click(function(){
                let val = $( this ).attr('value');
                console.log("Clicked "+val+" Stars");
                self.rating(val);

                self.disableRatingStars();
                $('#dont_ask_review_link').hide();
                $('#review_question').hide();

                if (val >= 4) {
                    $('#review_thank_you').show();
                } else if (val < 4) {
                    $('#rating_block').hide();
                    $('#review_how_can_we_improve').show();
                }
            })
        };

        self.disableRatingStars = function() {
            $('.star').off("click");
        };

        self.exitBtn = function(){
            self.reviewDialog.modal("hide");
            self.shouldAskForReview(false);
            self.sendReviewToServer()
        };

        self.exitAndDontShowAgain = function() {
            self.dontShowAgain(true);
            self.exitBtn()
        };

        self.sendReviewToServer = function () {
		    let review = $('#review_textarea').val();
            let data = {
                dontShowAgain: self.dontShowAgain(),
                rating: self.rating(),
                review: review,
                ts: new Date().getTime(),
                env: MRBEAM_ENV_LOCAL,
                sw_tier: MRBEAM_SW_TIER,
                user: self.loginState.username().hashCode()
            };

            self.reviewGiven(true);  // We show it only once per session

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
    }

    // view model class, parameters for constructor, container to bind to
    OCTOPRINT_VIEWMODELS.push([
        ReviewViewModel,

        // e.g. loginStateViewModel, settingsViewModel, ...
        ['settingsViewModel', 'analyticsViewModel', 'loginStateViewModel'],

        // e.g. #settings_plugin_mrbeam, #tab_plugin_mrbeam, ...
        ['#review_dialog']
    ]);
});
