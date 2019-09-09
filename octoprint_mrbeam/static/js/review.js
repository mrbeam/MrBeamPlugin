$(function () {
    function ReviewViewModel(params) {
        let self = this;
        window.mrbeam.viewModels['reviewViewModel'] = self;
        self.window_load_ts = -1;

        self.showReviewDialog = ko.observable(false);
        self.askForReview = self.settings.settings.plugins.mrbeam.ask_for_review();


        setTimeout(function (){

            if
            self.showReviewDialog(true);

        }, 5000); // How long do you want the delay to be (in milliseconds)?

        self.sendReviewToServer = function () {
		    let noReview = true;//!self.dontRemindMeAgainChecked();
		    let review = '';
            let data = {noReview: noReview, review: review};

            OctoPrint.simpleApiCommand("mrbeam", "focus_reminder", data)
                .done(function (response) {
                    self.settings.requestData();
                    console.log("simpleApiCall response for saving focus reminder state: ", response);
                })
                .fail(function () {
                    self.settings.requestData();
                    console.error("Unable to save focus reminder state: ", data);
                    new PNotify({
                        title: gettext("Error while saving settings!"),
                        text: _.sprintf(gettext("Unable to save your focus reminder state at the moment.%(br)sCheck connection to Mr Beam II and try again."), {br: "<br/>"}),
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
        [],

        // e.g. #settings_plugin_mrbeam, #tab_plugin_mrbeam, ...
        ['#review_dialog']
    ]);
});
