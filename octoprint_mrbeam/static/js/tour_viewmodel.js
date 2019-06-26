$(function () {
    function TourViewModel(params) {
        var self = this;
        window.mrbeam.viewModels['tourViewModel'] = self;
        self.login = params[0];
        self.settings = params[1];
        self.state = params[2];
        self.files = params[3];

        self.tourDef = null;

        // self.onStartupComplete = function () {
        //     setTimeout(self.startTour, 200);
        // };

        self.btn_startTour = function () {
            self.startTour();
        };

        self.startTour = function () {

            self._setPreConditions();
            self._registerListeners();

            if (mrbeam.viewModels.workingAreaViewModel && !mrbeam.viewModels.workingAreaViewModel.working_area_empty()) {
                self.tourDef = self._getPreTourDefinitions();
            } else {
                self.tourDef = self._getTourDefinitions();
            }

            console.log("hopscotch tour START: ", self.tourDef);
            hopscotch.configure({skipIfNoElement: true});
            hopscotch.startTour(self.tourDef, 0);
        };


        self._getTourDefinitions = function () {
            let tour = [];

            ///// intro /////
            tour.push(new TourStepNoArrow({
                id: 'intro',
                title: ["Step-by-Sepp Tour Guide To Your First Laser Job"],
                text: ["Looks like you already set up your Mr Beam II - Congratulations!",
                    "Do you want us to guide you through your first laser job with this step-by-step tour?",
                    "<strong>What do you need for this tour:</strong>",
                    "<ul>" +
                        "<li>Have a piece of felt by hand. Best to use the one that came with your Mr Beam II.</li>" +
                        "<li>The laser head of your Mr Beam II has to be focused according to the thickness of the felt. "+
                            "You can find how to do that in this <a href='https://mr-beam.freshdesk.com/support/solutions/articles/43000073345' target='_blank'>Knowledge base article</a>." +
                            // " or in our <a href='/plugin/mrbeam/static/docs/" + gettext("QuickstartGuide_en.pdf") + "' target='_blank'>Quickstart Guide</a>" +
                        "</li>" +
                        "<li>About 5-10 minutes of your time.</li>" +
                    "</ul>",
                    "<br/>"],
                width: 550,
                padding: 40,
                nextLabel: "Yes, let's go!",
                ctaLabel: "Maybe later",
                showCTAButton: true,
                onCTA: function () {
                    hopscotch.endTour();
                },
            }));

            ///// homing /////
            tour.push(new TourStep({
                id: 'homing_action',
                title: "First, do the homing cycle",
                text: "This is important so the Mr Beam II knows where the laser head is located.",
                target: "homing_overlay_homing_btn",
                placement: "bottom",
                condition: function () {
                    return $("#homing_overlay_homing_btn").is(":visible");
                }
            }));

            tour.push(new TourStepNoArrow({
                id: 'homing_process',
                title: "Look into your Mr Beam II",
                text: ["The laser head is now moving to the upper right corner.",
                    "Click \"next\" to proceed."],
                condition: function () {
                    return $("#homing_overlay_homing_btn").is(":visible");
                }
            }));

            tour.push(new TourStep({
                id: 'take_picture',
                title: "Place the felt material inside Mr Beam II",
                text: ["<ul>" +
                        "<li>First open the orange lid of your Mr Beam II.</li>" +
                        "<li>Then place the felt for the laser job somewhere in the middle of Mr Beam II's working area.</li>" +
                        "<li>Wait for the camera to take a picture. You will see a black and white picture of your felt here in your browser.</li>" +
                        "<li>Once you have a good picture, close the lid of your Mr Beam II and click \"next\".</li>" +
                        "</ul>"],
                target: 'area_preview',
                placement: "left",
                xOffset: 150,
                yOffset: 300,
                width: 400,
                nextOnTargetClick: false,
                showNextButton: true,
            }));

            ///// design lib /////
            tour.push(new TourStep({
                id: 'designlib_button',
                title: "Ready to select our design?",
                text: ["Click on <strong>design library</strong>.",
                    "Here you can find some designs and later you will also be able to upload your own."],
                target: "designlib_tab_btn",
                placement: "bottom",
                xOffset: 30,
                onNext: function () {
                    self._onNext();
                    console.log("designlib_button: onNext: scroll down");
                    $('#files_list').scrollTop(1E10);
                },
            }));

            tour.push(new TourStep({
                id: 'designlib_file',
                title: "Select this design file to place it on the working area.",
                text: ["For your first laser job, we thought you might like this nice key ring :)",
                    "Please click on this tile to place it on the <strong>working area</strong>."],
                target: $('.file_list_entry[mrb_name="Schlusselanhanger.svg"]')[0] || $('.file_list_entry').last()[0],
                additionalJQueryTargets: '.file_list_entry',
                placement: $('.file_list_entry').length <= 8 ? "bottom" : "top",
                width: 400,
                xOffset: -250,
                yOffset: 30,
                arrowOffset: 300,
                delay: 50,
            }));

            ///// working area /////
            tour.push(new TourStep({
                id: 'arrange_on_working_area',
                title: "Great! You can now move the design",
                text: ["First click on it and then drag and drop it to place it on top of the material.",
                    "Click \"next\" when you're done.",
                    "Hint: You can also type the coordinates directly into the left-side list."],
                target: '#userContent > g',
                delay: 500,
                retryOnError: true,
                placement: "left",
                nextOnTargetClick: false,
                showNextButton: true,
                yOffset: -20,
            }));

            tour.push(new TourStep({
                id: 'laser_btn',
                title: "And... let’s proceed to select the parameters!",
                text: ["Don't worry, the laser won't fire immediately.",
                    "Just 3 quick steps..."],
                target: "job_print",
                placement: "right",
                yOffset: -15
            }));

            ///// material screen /////
            tour.push(new TourStep({
                id: 'select_material',
                title: "Select the material",
                text: ["For this guide we want to use felt.", "However as you can see there are many different options. :)"],
                target: $('li.material_entry[mrb_name="felt.jpg"]')[0] || $('li.material_entry')[0],
                additionalJQueryTargets: 'li.material_entry',
                placement: "bottom",
                delay: 400,
                xOffset: 'center',
                arrowOffset: 'center',
            }));

            tour.push(new TourStep({
                id: 'select_color',
                title: "Select the color of the material",
                text: ["This is important because different colors absorb the laser differently."],
                target: ["#material_color_F49A39", "#color_list :first-child"],
                additionalJQueryTargets: '#color_list > ',
                placement: "bottom",
                delay: 100,
                xOffset: 'center',
                arrowOffset: 'center',
            }));

            tour.push(new TourStep({
                id: 'select_thickness',
                title: "Select the thickness of the material",
                text: ["Select 3mm.",
                    "Today we want our felt to be cut as well as engraved. Therefore we have to select its thickness.",
                    "(If you want to engrave only, the thickness doesn't matter.)"],
                target: ["material_thickness_3", "div.thickness_sample:first"],
                additionalJQueryTargets: 'div.thickness_sample',
                placement: "right",
                delay: 100,
                yOffset: -23,
            }));

            tour.push(new TourStep({
                id: 'material_ok',
                title: "We’re ready to go!",
                text: ["Press Start and your Mr&nbsp;Beam&nbsp;II will prepare your laser job.",
                    "Should our pre-configured material settings not really cut it (pun intended), you can tweak them in the lower section of this screen."],
                target: "start_job_btn",
                placement: "top",
                xOffset: -260,
                yOffset: -10,
                arrowOffset: 270
            }));

            tour.push(new TourStep({
                id: 'focus_reminder',
                title: "Reminder: Is your laser head focused?",
                text: ["The height of the laser head needs to be adjusted according to your material.",
                    "We assumed that it is already focused.",
                    "<strong>If it is focused</strong> click on \"It's focused!\"",
                    "<strong>If it's NOT focused</strong>, you should cancel this tour here and focus it. " +
                    "<a href='https://mr-beam.freshdesk.com/support/solutions/articles/43000073345-focusing-the-laser-head-' target='_blank'>Learn how to do this.</a>"],
                target: "start_job_btn_focus_reminder",
                placement: "right",
                delay: 200,
                fixedElement: true,
                yOffset: -150,
                arrowOffset: 145,
                condition: function () {
                    return self.settings.settings.plugins.mrbeam.focusReminder();
                }
            }));

            ///// rtl /////
            tour.push(new TourStepNoArrow({
                id: 'preparing_laserjob',
                title: "Mr Beam II is now preparing your laser job",
                text: ["This takes a few seconds. Just relax."],
                showNextButton: false,
                nextOnTargetClick: true,
                delay: 100,
            }));

            tour.push(new TourStep({
                id: 'start_laserjob',
                title: "Done! As soon as you click the start button on your Mr&nbsp;Beam&nbsp;II, the magic will begin 🎉",
                text: ["Thank you for doing this first laser job with us.",
                    "For more in-depth information you can check our <a href='http://mr-beam.org/faq' target='_blank'>knowledge base</a>, where you will find a lot of articles about Mr Beam II."],
                target: "ready_to_laser_dialog",
                placement: 'right',
                delay: 200,
                fixedElement: true,
                showNextButton: true,
                nextLabel: "Done!",
                nextOnTargetClick: false,
                xOffset: -100,
                yOffset: 200,
            }));

            return {
                id: "hello-mrbeam",
                steps: tour
            };
        };

        self._getPreTourDefinitions = function () {
            let tour = [];

            ///// intro /////
            tour.push(new TourStep({
                id: 'empty_woringarea',
                title: ["Working area has to be empty to start this tour."],
                text: ["Click here to remove all designs from your working area."],
                target: "clear_working_area_btn",
                placement: 'right',
                nextOnTargetClick: true,
                yOffset: -15,
                showNextButton: true,
                nextLabel: "Cancel",
            }));

            return {
                id: "pre-tour",
                steps: tour
            };
        };

        self._setPreConditions = function () {
            // switch to working area
            $('#wa_tab_btn').tab('show');

            // sort design lib by upload and scroll to bottom
            self.files.listHelper.changeSorting('upload');

            // reset any material selection
            try {
                window.mrbeam.viewModels.vectorConversionViewModel.set_material();
            } catch (e) {
                console.warn("Not abel to access window.mrbeam.viewModels.vectorConversionViewModel");
            }
        };

        self._restartTour = function (timeout, step) {
            timeout = parseInt(timeout) || 50;
            step = step || (hopscotch.getCurrStepNum());
            // console.log("Restarting tour at step #" + step + " in " + timeout);
            setTimeout(self._restart_tour_timeout, timeout, step);
        };

        self._restart_tour_timeout = function (step) {
            // console.log("Restarting tour at step #" + step);
            hopscotch.startTour(self.tourDef, step);
        };

        self._getCurrStepProp = function (property) {
            if (hopscotch.getCurrTour()) {
                return hopscotch.getCurrTour()['steps'][hopscotch.getCurrStepNum()][property];
            } else {
                return null;
            }
        };

        self._getCurrTourId = function () {
            return hopscotch.getCurrTour() ? hopscotch.getCurrTour().id : null;
        };

        self._registerListeners = function () {

            hopscotch.listen('next', self._onNext);
            hopscotch.listen('error', self._onError);
            hopscotch.listen('show', self._onShow);
            hopscotch.listen('end', self._onEnd);


            // remove bubbles because they're visible over the curtain
            $(window).on('beforeunload', function () {
                if (!event.target.activeElement.href) {
                    console.log("hopscotch tour END: ", self.tourDef);
                    hopscotch.endTour();
                }
            });

            self.onEventReadyToLaserStart = function (payload) {
                let id = self._getCurrStepProp('id')
                if (id == 'preparing_laserjob') {
                    hopscotch.nextStep();
                } else if (id == 'start_laserjob') {
                    // hopscotch.refreshBubblePosition();
                    self._restartTour(200);
                }
            };
        };

        self._onNext = function () {
            // console.log("hopscotch _onNext: #" + hopscotch.getCurrStepNum() + ", " + self._getCurrStepProp('id'));
            if (self._getCurrStepProp('condition')) {
                if (!self._getCurrStepProp('condition')()) {
                    console.log("hopscotch _onNext: " + self._getCurrTourId() + " #" + hopscotch.getCurrStepNum() + ", " + self._getCurrStepProp('id') + " - condition: skip");
                    hopscotch.nextStep();
                } else {
                    console.log("hopscotch _onNext: " + self._getCurrTourId() + " #" + hopscotch.getCurrStepNum() + ", " + self._getCurrStepProp('id') + " - condition: true");
                }
            }
            self._restartTour(self._getCurrStepProp('restartTour'));
        };

        self._onError = function () {
            if (self._getCurrStepProp('retryOnError')) {
                // console.log("hopscotch _onError: " + self._getCurrTourId() + " #" + hopscotch.getCurrStepNum() + ", " + self._getCurrStepProp('id') + " - retrying...");
                self._restartTour();
            } else {
                console.log("hopscotch _onError: " + self._getCurrTourId() + " #" + hopscotch.getCurrStepNum() + ", " + self._getCurrStepProp('id') + " - skipping...");
                hopscotch.nextStep();
            }
        };

        self._onShow = function () {
            // console.log("hopscotch _onShow: " + self._getCurrTourId() + " #" + hopscotch.getCurrStepNum() + ", " + self._getCurrStepProp('id'));
            if (self._getCurrStepProp('nextLabel')) {
                // console.log("hopscotch _onShow: setting next label to: " + self._getCurrStepProp('nextLabel'));
                $('.hopscotch-next').html(self._getCurrStepProp('nextLabel'));
            }
            if (self._getCurrStepProp('additionalJQueryTargets')) {
                let additionalJQueryTargets = self._getCurrStepProp('additionalJQueryTargets')
                let myStepNum = hopscotch.getCurrStepNum()
                // console.log("hopscotch _onShow: additionalJQueryTargets for step #"+ myStepNum +": " + additionalJQueryTargets);
                $(additionalJQueryTargets).one('click', function () {
                    if (hopscotch.getCurrStepNum() == myStepNum) {
                        // console.log("additionalJQueryTargets: hopscotch.nextStep()");
                        hopscotch.nextStep();
                    } else {
                        // console.log("additionalJQueryTargets: step does not match!");
                    }
                })
            }
        };

        self._onEnd = function () {
            // console.log("hopscotch _onEnd: " + self._getCurrTourId() + " #" + hopscotch.getCurrStepNum() + ", " + self._getCurrStepProp('id'));
            if (self._getCurrTourId() == 'pre-tour' && mrbeam.viewModels.workingAreaViewModel && mrbeam.viewModels.workingAreaViewModel.working_area_empty()) {
                setTimeout(function () {
                    if (self._getCurrTourId() == null) {
                        self.startTour();
                    }
                }, 10);

            }
        };

    }

    var DOM_ELEMENT_TO_BIND_TO = "tour_start_btn";
    OCTOPRINT_VIEWMODELS.push([
        TourViewModel,
        ["loginStateViewModel", "settingsViewModel", "printerStateViewModel", "filesViewModel"],
        // ["loginStateViewModel", "settingsViewModel", "printerStateViewModel", "filesViewModel", "vectorConversionViewModel"],
        [/* */]
    ]);
});


class TourStep {

    constructor(definition, skipDefinitions) {
        this.id = definition.id;
        this.target = null;
        this.title = null;
        this.content = null;
        this.placement = 'bottom';
        this.nextOnTargetClick = true;
        this.showNextButton = false;

        this._titles = [];
        this._descLines = [];

        if (!skipDefinitions) {
            this._setDefinition(definition);
        }
    }

    addTitle(title) {
        this._titles.push(title);
        this._renderDescription();
        return this;
    }

    addDesc(line) {
        this._descLines.push(line);
        this._renderDescription();
        return this;
    }

    _setDefinition(definition) {
        for (let key in definition) {
            this[key] = definition[key];
        }

        if ('title' in definition) {
            if (Array.isArray(definition.title)) {
                this._titles = this._titles.concat(definition.title);
            } else {
                this.addTitle(definition.title);
            }
        }

        if ('text' in definition) {
            if (Array.isArray(definition.text)) {
                this._descLines = this._descLines.concat(definition.text);
            } else {
                this.addDesc(definition.text);
            }
        }
        this._renderDescription();
    }

    _renderDescription() {
        let tmp_title = [];
        for (let i = 0; i < this._titles.length; i++) {
            tmp_title.push("<p>" + this._titles[i] + "</p>");
        }
        this.title = tmp_title.join("\n");

        let tmp_desc = []
        for (let i = 0; i < this._descLines.length; i++) {
            tmp_desc.push("<p>" + this._descLines[i] + "</p>");
        }
        this.content = tmp_desc.join("\n");
    }

}

class TourStepNoArrow extends TourStep {

    constructor(definition) {
        super(definition, true);

        this.target = "mrbeam-tabs";
        this.placement = "top";
        this.nextOnTargetClick = false;
        this.showNextButton = true;
        this.xOffset = 'center';
        this.yOffset = 'center';
        this.arrowOffset = 10000;

        this._setDefinition(definition);
    }

}




