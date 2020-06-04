$(function () {
    function ReviewViewModel(params) {
        let self = this;
        self.REVIEW_NUMBER = 1;

        self.settings = params[0];
        self.analytics = params[1];
        self.loginState = params[2];

        window.mrbeam.viewModels['reviewViewModel'] = self;

        self.showReviewDialog = ko.observable(false);
        self.jobTimeEstimation = ko.observable(-1);

        self.ratingGiven = false;
        self.rating = ko.observable(0);
        self.dontShowAgain = ko.observable(false);
        self.justGaveReview = ko.observable(false);

        // TODO IRATXE: handle the first use case (review does not exist in the user settings)
        self.shouldAskForReview = ko.computed(function(){
            if (self.loginState.currentUser() && self.loginState.currentUser().active) {
                let numSuccJobs = self.loginState.currentUser().settings.mrbeam.review.num_succ_jobs;
                let reviewGiven = self.loginState.currentUser().settings.mrbeam.review.given;

                return numSuccJobs >= 5 && !reviewGiven && !self.justGaveReview()
            } else {
                return false
            }
        });

        self.onAllBound = function () {
            self.reviewDialog = $('#review_dialog');

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
                // The short jobs are always estimated 60s, so has to be more
                if (self.shouldAskForReview() && self.jobTimeEstimation() >= 61) {
                    self.showReviewDialog(true);
                    self.reviewDialog.modal("show");
                }
            }, 5000);
        };

        self.enableRatingStars = function() {
            $('.star').click(function(){
                self.ratingGiven = true;
                let val = $( this ).attr('value');
                console.log("Clicked "+val+" Stars");
                self.rating(val);

                self.fillAndDisableRatingStars(val);
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

        self.fillAndDisableRatingStars = function(userRating) {
            let allStars = $('.star');
            allStars.off("click");

            allStars.each(function(i, obj) {
                $( this ).addClass('disabled');
                if ($( this ).attr('value') <= userRating) {
                    $( this ).addClass('filled');
                }
            });

        };

        self.exitOkBtn = function() {
            // "OK" button: we send the review but show it again if it was empty in the next session (no rating)
            if (self.ratingGiven) {
                self.dontShowAgain(true);
            }
            self.exitReview();  //We
        };

        self.exitDontAskAgainLink = function() {
            // "don't ask me again" link: we send the review and never show it again
            self.dontShowAgain(true);
            self.exitReview();
        };

        self.exitXBtn = function() {
            // "x" button in the corner: we send the review but show it again in the next session
            self.exitReview();
        };

        self.exitReview = function (){
            self.ratingGiven = false;
            self.reviewDialog.modal("hide");
            self.justGaveReview(true);  // We show it only once per session
            self.sendReviewToServer()
        };

        self.exitAndDontShowAgain = function() {
            self.dontShowAgain(true);
            self.exitReview()
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
                user: self.loginState.username().hashCode(),
                number: self.REVIEW_NUMBER
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
                        text: _.sprintf(gettext("Unable to save your review at the moment.%(br)sCheck connection to Mr Beam and try again."), {br: "<br/>"}),
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
