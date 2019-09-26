$(function () {
    function ReviewViewModel(params) {
        let self = this;
        self.settings = params[0];

        window.mrbeam.viewModels['reviewViewModel'] = self;

        self.showReviewDialog = ko.observable(false);
        self.jobTimeEstimation = ko.observable(-1);

        self.rating = ko.observable(0);
        self.askAgain = ko.observable(true);

        self.onAllBound = function () {
            self.reviewDialog = $('#review_dialog');
            self.askForReview = ko.observable(self.settings.settings.plugins.mrbeam.ask_for_review());

            let links = ['give_review_link', 'dont_ask_review_link'];
            links.forEach(function (linkId) {
                $('#' + linkId).click(function () {
                    let payload = {
                        link: linkId
                    };
                    self.analytics.send_fontend_event('link_click', payload)
                })
            });

            $('.star').click(function(){
                let val = $( this ).attr('value');
                console.log("Clicked "+val+" Stars");
                self.rating(val);
                $('#dont_ask_review_link').hide();


                // $('#rating_value').html(val);
                if (val >= 4) {
                    $('#review_thank_you').show();
                } else if (val < 4) {
                    // todo iratxe: show stars
                    $('#rating_block').hide();
                    $('#review_how_can_we_improve').show();
                }
            })
        };

        self.onEventJobTimeEstimated = function (payload) {
            self.jobTimeEstimation(payload['job_time_estimation']);
        };

        self.onEventPrintStarted = function(payload) {
            setTimeout(function () {
                if (self.askForReview() && self.jobTimeEstimation() >= 61) {
                    self.showReviewDialog(true);
                    self.reviewDialog.modal("show");
                }
            }, 5000);
        };

        self.exitBtn = function(){
            self.reviewDialog.modal("hide");
            // todo iratxe send analytics

            if (self.rating() !== 0) {
                self.sendReviewToServer()
            }
        };

        self.exitAndDontShowAgain = function() {
            // todo iratxe: save this
            // todo iratxe: do we want to send the info if they said don't ask me again? I think we should
            self.exitBtn()
        };

        self.sendReviewToServer = function () {
		    let review = $('#review_textarea').val();
            let data = {
                askAgain: self.askAgain(),
                rating: self.rating(),
                review: review,
                ts: new Date().getTime()
            };

            self.askForReview(false);

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
        ['settingsViewModel'],

        // e.g. #settings_plugin_mrbeam, #tab_plugin_mrbeam, ...
        ['#review_dialog']
    ]);
});
