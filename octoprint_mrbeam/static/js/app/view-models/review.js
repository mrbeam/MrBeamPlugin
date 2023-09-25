$(function () {
    /**
     * To debug the user review screen, set window.FORCE_REVIEW_SCREEN = true
     * This will trigger the review screen to come up during all laser jobs for debugging.
     * Review data is sent to the backend but will be marked with a 'debug' key set to true
     */
    function ReviewViewModel(params) {
        let self = this;
        self.REVIEW_NUMBER = 1;
        self.SHOW_AFTER_USAGE_H = 5 * 3600; // The usage is in seconds

        self.settings = params[0];
        self.analytics = params[1];
        self.loginState = params[2];

        window.mrbeam.viewModels["reviewViewModel"] = self;

        self.showReviewDialog = ko.observable(false);
        self.jobTimeEstimation = ko.observable(-1);

        self.ratingGiven = false;
        self.rating = ko.observable(0);
        self.dontShowAgain = ko.observable(false);
        self.justGaveReview = ko.observable(false);

        self.shouldAskForReview = ko.computed(function () {
            if (
                self.loginState.currentUser() &&
                self.loginState.currentUser().active
            ) {
                let totalUsage =
                    self.settings.settings.plugins.mrbeam.usage.totalUsage();
                let shouldAsk =
                    self.settings.settings.plugins.mrbeam.review.ask();
                let doNotAskAgain =
                    self.settings.settings.plugins.mrbeam.review.doNotAskAgain();
                let reviewGiven =
                    self.settings.settings.plugins.mrbeam.review.given();

                return (
                    totalUsage >= self.SHOW_AFTER_USAGE_H &&
                    shouldAsk &&
                    !doNotAskAgain &&
                    !reviewGiven &&
                    !self.justGaveReview()
                );
            } else {
                return false;
            }
        });

        self.onAllBound = function () {
            self.reviewDialog = $("#review_dialog");

            let links = ["give_review_link", "dont_ask_review_link"];
            links.forEach(function (linkId) {
                $("#" + linkId).click(function () {
                    let payload = {
                        link: linkId,
                    };
                    self.analytics.send_frontend_event("link_click", payload);
                });
            });
        };

        self.onEventJobTimeEstimated = function (payload) {
            self.jobTimeEstimation(payload["job_time_estimation_rounded"]);
        };

        self.onEventPrintStarted = function (payload) {
            self.enableRatingBtns();

            setTimeout(function () {
                // The short jobs are always estimated 60s, so has to be more
                if (
                    (self.shouldAskForReview() &&
                        self.jobTimeEstimation() >= 61) ||
                    (typeof FORCE_REVIEW_SCREEN !== "undefined" &&
                        FORCE_REVIEW_SCREEN)
                ) {
                    self.showReviewDialog(true);
                    self.reviewDialog.modal("show");
                }
            }, 5000);
        };

        self.enableRatingBtns = function () {
            $(".rating button").hover(
                function () {
                    $(this).addClass("rating-hover");
                    $(this).prevAll().addClass("rating-hover");
                },
                function () {
                    $(this).removeClass("rating-hover");
                    $(this).prevAll().removeClass("rating-hover");
                }
            );

            $(".rating button").click(function () {
                self.ratingGiven = true;
                let val = $(this).attr("value");
                self.rating(val);

                self.fillAndDisableRating(val);

                $("#dont_ask_review_link").hide();
                $("#review_question").hide();
                $("#rating_block").hide();

                $("#review_thank_you").show();
                $("#review_how_can_we_improve").show();
                $("#ask_user_details").show();
                $("#change_review").show();
            });
        };

        self.fillAndDisableRating = function (userRating) {
            let allBtns = $(".rating button");

            allBtns.each(function (i, obj) {
                $(this).prop("disabled", true);
                if (parseInt($(this).attr("value")) <= parseInt(userRating)) {
                    $(this).addClass("rating-hover");
                }
            });
        };

        self.exitOkBtn = function () {
            // "OK" button: we send the review but show it again if it was empty in the next session (no rating)
            if (self.ratingGiven) {
                self.dontShowAgain(true);
            }
            self.exitReview();
        };

        self.exitDontAskAgainLink = function () {
            // "don't ask me again" link: we send the review and never show it again
            self.dontShowAgain(true);
            self.exitReview();
        };

        self.changeReview = function () {
            // "Back" button: Go back to the rating bar for the user to change their answer
            $("#dont_ask_review_link").show();
            $("#review_question").show();
            $("#rating_block").show();
            $("#review_thank_you").hide();
            $("#review_how_can_we_improve").hide();
            $("#ask_user_details").hide();
            $("#change_review").hide();
            self.unfillAndEnableRating();
        };

        self.unfillAndEnableRating = function () {
            let allBtns = $(".rating button");

            allBtns.each(function (i, obj) {
                $(this).prop("disabled", false);
                $(this).removeClass("rating-hover");
            });
        };

        self.exitXBtn = function () {
            // "x" button in the corner: we send the review but show it again in the next session
            if (self.rating() !== 0 && self.ratingGiven) {
                self.ratingGiven = false;
                self.justGaveReview(true); // We show it only once per session
                self.sendReviewToServer();
            }
            self.closeReview();
        };

        self.exitReview = function () {
            if (self.rating() !== 0) {
                self.ratingGiven = false;
                self.justGaveReview(true); // We show it only once per session
                self.sendReviewToServer();

                $("#review_thank_you").hide();
                $("#review_how_can_we_improve").hide();
                $("#ask_user_details").hide();
                $("#change_review").hide();
                $("#review_done_btn").hide();

                if (self.rating() >= 7) {
                    $("#positive_review").show();
                } else if (self.rating() < 7) {
                    $("#negative_review").show();
                }

                $("#close_review_modal")
                    .removeClass("review_hidden_part")
                    .css("width", "20%");
            } else {
                self.sendReviewToServer();
                self.closeReview();
            }
        };

        self.closeReview = function () {
            self.reviewDialog.modal("hide");
        };

        self.sendReviewToServer = function () {
            let review = $("#review_textarea").val();
            let user_email_or_phone = $("#review_input_phone_email").val();
            let data = {
                // more data is added by the backend
                dontShowAgain: self.dontShowAgain(),
                rating: self.rating(),
                review: review,
                userEmailOrPhone: user_email_or_phone,
                ts: new Date().getTime(),
                number: self.REVIEW_NUMBER,
            };

            if (
                typeof FORCE_REVIEW_SCREEN !== "undefined" &&
                FORCE_REVIEW_SCREEN
            ) {
                data["debug"] = true;
            }

            OctoPrint.simpleApiCommand("mrbeam", "review_data", data)
                .done(function (response) {
                    self.settings.requestData();
                    console.log(
                        "simpleApiCall response for saving review: ",
                        response
                    );
                })
                .fail(function () {
                    self.settings.requestData();
                    console.error("Unable to save review state: ", data);
                    new PNotify({
                        title: gettext("Error while saving review!"),
                        text: _.sprintf(
                            gettext(
                                "Unable to save your review at the moment.%(br)sCheck connection to Mr Beam and try again."
                            ),
                            { br: "<br/>" }
                        ),
                        type: "error",
                        hide: true,
                    });
                });
        };
    }

    // view model class, parameters for constructor, container to bind to
    OCTOPRINT_VIEWMODELS.push([
        ReviewViewModel,

        // e.g. loginStateViewModel, settingsViewModel, ...
        ["settingsViewModel", "analyticsViewModel", "loginStateViewModel"],

        // e.g. #settings_plugin_mrbeam, #tab_plugin_mrbeam, ...
        ["#review_dialog"],
    ]);
});
