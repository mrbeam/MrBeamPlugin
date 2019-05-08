$(function () {
    function TourViewModel(params) {
        var self = this;
        window.mrbeam.viewModels['tourViewModel'] = self;
        self.login = params[0];
        self.settings = params[1];
        self.state = params[2];
        self.working_area = params[3];

        self.tourDef = null;

        // self.onStartupComplete = function () {
        //     setTimeout(self.startTour, 200);
        // };

        self.btn_startTour = function () {
            self.startTour();
        };

        self.startTour = function () {
            // remove design file from working area, otherwise the tour won't work
            $('div.remove-design-btn[mrb_name="Schlusselanhanger.svg"]').click();

            self._registerListeners();

            self.tourDef = self._getTourDefinitions();
            console.log("hopscotch tour START: ", self.tourDef);
            hopscotch.configure({skipIfNoElement: true});
            hopscotch.startTour(self.tourDef);
        };


        self._getTourDefinitions = function () {
            let tour = [];

            ///// intro /////
            tour.push(new TourStepNoArrow({
                id: 'intro',
                title: ["Looks like you already set up your Mr Beam II - Congratulations!",
                    "Do you want to do the first laserjob with us?"],
                text: ["The only requirement is that you put the felt we provided in your Mr Beam II and then focus the laser head.",
                    "You can find how to do that in our <a href='/plugin/mrbeam/static/docs/" + gettext("QuickstartGuide_en.pdf") + "' target='_blank'>Quickstart Guide</a>"],
                width: 500,
                padding: 40,
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
            }))

            ///// design lib /////
            tour.push(new TourStep({
                id: 'designlib_button',
                title: "Ready to select our design?",
                text: ["Click on <strong>design library</strong>.",
                    "Here you can find some designs and later you will also be able to upload your own."],
                target: "designlib_tab_btn",
                placement: "bottom",
                xOffset: 30
            }));

            tour.push(new TourStep({
                id: 'designlib_file',
                title: "For your first laser job, we thought you might like this nice key ring :)",
                text: ["Please click on this tile to place it on the <strong>working area</strong>."],
                target: $('.file_list_entry[mrb_name="Schlusselanhanger.svg"]')[0],
                placement: "bottom",
                width: 400,
                xOffset: 'center',
                arrowOffset: 'center'
            }));

            ///// working area /////
            tour.push(new TourStep({
                id: 'arrange_on_working_area',
                title: "Great! You can now move the design",
                text: ["First click on it and then drag and drop it to place it on top of the material.",
                    "Click \"next\" when you're done.",
                    "(You can also enter the coordinates directly in the left-side list.)"],
                target: '#userContent > g',
                delay: 100,
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
                text: ["It’s felt in our case, but as you can see there are many different :)"],
                target: $('li.material_entry[mrb_name="felt.jpg"]')[0],
                placement: "bottom",
                delay: 400,
                xOffset: 'center',
                arrowOffset: 'center'
            }));

            tour.push(new TourStep({
                id: 'select_color',
                title: "Select the color of the material",
                text: ["This is important because different colors absorb the laser differently."],
                target: "material_color_F49A39",
                placement: "bottom",
                delay: 100,
                xOffset: 'center',
                arrowOffset: 'center'
            }));

            tour.push(new TourStep({
                id: 'select_thickness',
                title: "Select the thickness of the material",
                text: ["Select 3mm.",
                    "Today we want our felt to be cut as well as engraved. Therefor we have to select its thickness.",
                    "(If you want to engrave only, the thickness doesn't matter.)"],
                target: "material_thickness_3",
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
                    "We assumed that it is already focused. If so click on \"It's focused!\"",
                    "(If it's not focused, you should cancel this tour here and focus it."],
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
                showNextButton: false,
                nextOnTargetClick: true,
                yOffset: 200,
            }));

            return {
                id: "hello-mrbeam",
                steps: tour
            };
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

        self._registerListeners = function () {

            hopscotch.listen('next', function () {
                // console.log("hopscotch next: #" + hopscotch.getCurrStepNum() + ", " + self._getCurrStepProp('id'));
                if (self._getCurrStepProp('condition')) {
                    if (!self._getCurrStepProp('condition')()) {
                        // console.log("hopscotch next: #" + hopscotch.getCurrStepNum() + ", " + self._getCurrStepProp('id') + " - condition: skip");
                        hopscotch.nextStep();
                    } else {
                        // console.log("hopscotch next: #" + hopscotch.getCurrStepNum() + ", " + self._getCurrStepProp('id') + " - condition: true");
                    }
                }
                self._restartTour(self._getCurrStepProp('restartTour'));
            });

            hopscotch.listen('error', function (err) {
                if (self._getCurrStepProp('retryOnError')) {
                    // console.log("hopscotch error: #" + hopscotch.getCurrStepNum() + ", " + self._getCurrStepProp('id') + " - retrying...");
                    self._restartTour();
                } else {
                    // console.log("hopscotch error: #" + hopscotch.getCurrStepNum() + ", " + self._getCurrStepProp('id') + " - skipping...");
                    hopscotch.nextStep();
                }
            });

            // hopscotch.listen('show', function () {
            //     console.log("hopscotch show: #" + hopscotch.getCurrStepNum() + ", " + self._getCurrStepProp('id'));
            // });
            // hopscotch.listen('end', function () {
            //     console.log("hopscotch end: #" + hopscotch.getCurrStepNum() + ", " + self._getCurrStepProp('id'));
            // });
            // hopscotch.listen('close', function () {
            //     console.log("hopscotch close: #" + hopscotch.getCurrStepNum() + ", " + self._getCurrStepProp('id'));
            // });

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

    }

    var DOM_ELEMENT_TO_BIND_TO = "tour_start_btn";
    OCTOPRINT_VIEWMODELS.push([
        TourViewModel,
        ["loginStateViewModel", "settingsViewModel", "printerStateViewModel"],
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




