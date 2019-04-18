$(function () {
    function TourViewModel(params) {
        var self = this;
        self.login = params[0];
        self.settings = params[1];
        self.state = params[2];
        self.working_area = params[3];

        self.onStartupComplete = function () {
            hopscotch.endTour();
            setTimeout(self.start_tour, 1000);
        };

        self.onEventPrinterStateChanged = function () {
            console.log("onEventPrinterStateChanged: ", arguments);
            setTimeout(self._refresh_bubble_position, 100);
        };

        // window.onbeforeunload = function (event) {
        //     // do not show reloadingOverlay when it's a file download
        //     if (!event.target.activeElement.href) {
        //         hopscotch.endTour(false);
        //     }
        // };

        self.start_tour = function () {
            hopscotch.listen('show', function () {
                console.log("hopscotch show: ", hopscotch.getCurrTour()['steps'][hopscotch.getCurrStepNum()]['id']);
                setTimeout(self._refresh_bubble_position, 50);
            });
            let tour_def = self.get_tour_def();
            console.log("hopscotch start: ", tour_def);
            hopscotch.startTour(tour_def);
        };

        self.get_tour_def = function () {
<<<<<<< HEAD
            let tour = [];

            tour.push(new TourStepNoArrow({
                id: 'intro',
                title: ["Looks like you already set up your Mr Beam II - Congratulations!",
                        "Do you want to do the first laserjob with us?"],
                text: ["The only requirement is that you put the felt we provided in your Mr Beam II and then focus the laser head.",
                        "You can find how to do that in our <a href='/plugin/mrbeam/static/docs/" + gettext("QuickstartGuide_en.pdf") + "' target='_blank'>Quickstart Guide</a>"],
                width: 500,
                padding: 40,
            }));

            if ($("#homing_overlay_homing_btn").is(":visible")) {
                tour.push(new TourStep({
                    id: 'homing_action',
                    title: "First, do the homing cycle",
                    text: "This is important so the Mr Beam II knows where the laser head is located.",
                    target: "homing_overlay_homing_btn",
                    placement: "bottom",
                }));

                tour.push(new TourStepNoArrow({
                    id: 'homing_process',
                    title: "Look into your Mr Beam II",
                    text: ["The laser head is now moving to the upper right corner.",
                            "Click \"next\" to proceed."],
                }))
            }

            tour.push(new TourStep({
                id: 'designlib_button',
                title: "Ready to select our design?",
                text: ["Click on <strong>design library</strong>.",
                        "Here you can find some designs and later you will also be able to upload your own."],
                target: "designlib_tab_btn",
                placement: "bottom",
            }));

            tour.push(new TourStep({
                id: 'designlib_file',
                title: "For your first laser job, we thought you might like this nice key ring :)",
                text: ["Please click on this tile to place it on the <strong>working area</strong>."],
                target: $('.file_list_entry[mrb_name="Schlusselanhanger.svg"]')[0],
                placement: "bottom",
                width: 400,
            }));

            tour.push(new TourStep({
                id: 'arrange_on_working_area',
                title: "Great! You can now move the design",
                text: ["First click on it and then drag and drop it to place it on top of the material.",
                    "(You can also enter the coordinates directly in the left-side list.)"],
                target: $('#userContent > g')[0],
                placement: "right",
                nextOnTargetClick: false,
                showNextButton: true,
                delay: 50
            }));

            tour.push(new TourStep({
                id: 'laser_btn',
                title: "And... let’s proceed to select the parameters!",
                text: ["Don't worry, the laser won't fire immediately.",
                    "Just 3 quick steps..."],
                target: "job_print",
                placement: "right"
            }));

            tour.push(new TourStep({
                id: 'select_material',
                title: "Select the material",
                text: ["It’s felt in our case, but as you can see there are many different :)"],
                target: $('li .material_entry[mrb_name="felt.jpg"]')[0],
                placement: "bottom",
                delay: 700
            }));
=======
            console.log("homing_overlay_homing_btn visible: ", $("#homing_overlay_homing_btn").is(":visible"));

            let tour = [];

            tour.push({
                id: 'intro',
                title: "Let's Take a Tour Together!",
                content: "Let's checkout out how to use your Mr Beam II. I bet you're excited. So am I ;-)",
                target: "mrbeam-tabs",
                padding: 80,
                placement: "top",
                xOffset: 'center',
                yOffset: 'center',
                arrowOffset: 'center'
            });
>>>>>>> 699e93fdd13c3bc0cf406528480fa81d68ab8d45


            return {
                id: "hello-mrbeam",
<<<<<<< HEAD
                steps: tour
            };
=======
                steps: tour;
        }
            ;
            //     steps: [
            //         {
            //             id: 'intro',
            //             title: "Let's Take a Tour Together!",
            //             content: "Let's checkout out how to use your Mr Beam II. I bet you're excited. So am I ;-)",
            //             target: "mrbeam-tabs",
            //             padding: 80,
            //             placement: "top",
            //             xOffset: 'center',
            //             yOffset: 'center',
            //             arrowOffset: 'center'
            //         },
            //         {
            //             id: 'homing_action',
            //             title: "Homing",
            //             content: "First you need to to a Homing Cycle . Simply click this button.",
            //             target: $("#homing_overlay_homing_btn").is(":visible") ? $("#homing_overlay_homing_btn")[0] : null,
            //             placement: "bottom",
            //             nextOnTargetClick: true,
            //             showNextButton: false,
            //             skipIfNoElement: true,
            //             xOffset: 'center',
            //             arrowOffset: 'center',
            //             // onShow: function(){ if (!$("#homing_overlay_homing_btn").is(":visible")) {hopscotch.nextStep();} }
            //         },
            //         // {
            //         //     id: 'homing_waiting',
            //         //     title: "Wait for Mr Beam II",
            //         //     content: "Watch your mr Beam II moving it's laser head in the upper right corner. That's it's home position",
            //         //     target: "area_preview",
            //         //     placement: "top",
            //         //     xOffset: 'center',
            //         //     yOffset: 'center',
            //         //     arrowOffset: 'center',
            //         //     showNextButton: false,
            //         //     // onShow: function(){ console.log("ANDYTEST", hopscotch.getCurrTour()['steps'][hopscotch.getCurrStepNum()]);}
            //         // },
            //         {
            //             id: 'qt_open_window',
            //             title: "Add some text",
            //             content: "Click here to open the QuickText window.",
            //             target: "working_area_tab_text_btn",
            //             placement: "bottom",
            //             nextOnTargetClick: true,
            //             showNextButton: false
            //         },
            //         {
            //             id: 'qt_enter_text',
            //             title: "Type your name",
            //             content: "Use your computers keyboard to type in your name.",
            //             target: "quick_text_dialog_text_input",
            //             placement: "right",
            //             nextOnTargetClick: false,
            //             showNextButton: true,
            //             delay: 300
            //         },
            //         {
            //             id: 'qt_close_window',
            //             title: "Close the window",
            //             content: "Close the window by pressing OK.",
            //             target: "quick_text_text_done_btn",
            //             placement: "right",
            //             nextOnTargetClick: true,
            //             showNextButton: false
            //         },
            //
            //     ]
            // };
>>>>>>> 699e93fdd13c3bc0cf406528480fa81d68ab8d45
        };

        self._refresh_bubble_position = function (msg) {
            console.log("_refresh_bubble_position [" + msg + "]");
            hopscotch.refreshBubblePosition();
        }
    }

    var DOM_ELEMENT_TO_BIND_TO = "wizard_plugin_corewizard_analytics";
    OCTOPRINT_VIEWMODELS.push([
        TourViewModel,
        ["loginStateViewModel", "settingsViewModel", "printerStateViewModel", "workingAreaViewModel"],
        "#" + DOM_ELEMENT_TO_BIND_TO
    ]);
});







class TourStep{

    constructor(definitions) {
        this.id = definitions.id;
        this.target = null;
        this.title = null;
        this.content = null;
        this.placement = 'bottom';
        this.nextOnTargetClick = true;
        this.showNextButton = false;
        // this.xOffset = 'center';
        // this.yOffset = 'center';
        // this.arrowOffset = 'center';

        this._titles = [];
        this._descLines = [];

        for (let key in definitions){
            this[key] = definitions[key];
        }

        if ('title' in definitions){
            if (Array.isArray(definitions.title)) {
                this._titles = this._titles.concat(definitions.title);
            } else {
                this.addTitle(definitions.title);
            }
        }

        if ('text' in definitions){
            if (Array.isArray(definitions.text)) {
                this._descLines = this._descLines.concat(definitions.text);
            } else {
                this.addDesc(definitions.text);
            }
        }
        this._renderDescription();
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

    _renderDescription(){
        let tmp_title = [];
        for (let i=0; i<this._titles.length; i++) {
            tmp_title.push("<p>"+ this._titles[i]+"</p>");
        }
        this.title = tmp_title.join("\n");

        let tmp_desc = []
        for (let i=0; i<this._descLines.length; i++) {
            tmp_desc.push("<p>"+ this._descLines[i]+"</p>");
        }
        this.content = tmp_desc.join("\n");;
    }

}

class TourStepNoArrow extends TourStep{

    constructor(definitions) {
        super(definitions);

        this.target = "mrbeam-tabs";
        this.placement = "top";
        this.nextOnTargetClick = false;
        this.showNextButton = true;
        this.xOffset = 'center';
        this.yOffset = 'center';
        this.arrowOffset = 10000;
    }

}




