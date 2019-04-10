$(function () {
    function TourViewModel(params) {
        var self = this;
        // self.loginStateViewModel", "settingsViewModel", "printerStateViewModel", "workingAreaViewModel
        self.login = params[0];
        self.settings = params[1];
        self.state = params[2];
        self.working_area = params[3];

        self.onStartupComplete = function () {
            hopscotch.endTour();
            setTimeout(self.start_tour, 1000);
        };

        self.onEventPrinterStateChanged = function() {
            console.log("onEventPrinterStateChanged: ", arguments);
            setTimeout(self._refresh_bubble_position, 100);
        };

        window.onbeforeunload = function (event) {
            // do not show reloadingOverlay when it's a file download
            if (!event.target.activeElement.href) {
                hopscotch.endTour(false);
            }
        };

        self.start_tour = function(){
            hopscotch.listen('show', function () {
                console.log("hopscotch show: ", hopscotch.getCurrTour()['steps'][hopscotch.getCurrStepNum()]['id']);
                setTimeout(self._refresh_bubble_position, 50);
            });
            hopscotch.startTour(self.get_tour_def());
        };

        self.get_tour_def = function () {
            console.log("homing_overlay_homing_btn visible: ", $("#homing_overlay_homing_btn").is(":visible"))
            return {
                id: "hello-mrbeam",
                steps: [
                    {
                        id: 'intro',
                        title: "Let's Take a Tour Together!",
                        content: "Let's checkout out how to use your Mr Beam II. I bet you're excited. So am I ;-)",
                        target: "mrbeam-tabs",
                        padding: 80,
                        placement: "top",
                        xOffset: 'center',
                        yOffset: 'center',
                        arrowOffset: 'center'
                    },
                    {
                        id: 'homing_action',
                        title: "Homing",
                        content: "First you need to to a Homing Cycle . Simply click this button.",
                        target: $("#homing_overlay_homing_btn").is(":visible") ? $("#homing_overlay_homing_btn")[0] : null,
                        placement: "bottom",
                        nextOnTargetClick: true,
                        showNextButton: false,
                        skipIfNoElement: true,
                        xOffset: 'center',
                        arrowOffset: 'center',
                        // onShow: function(){ if (!$("#homing_overlay_homing_btn").is(":visible")) {hopscotch.nextStep();} }
                    },
                    // {
                    //     id: 'homing_waiting',
                    //     title: "Wait for Mr Beam II",
                    //     content: "Watch your mr Beam II moving it's laser head in the upper right corner. That's it's home position",
                    //     target: "area_preview",
                    //     placement: "top",
                    //     xOffset: 'center',
                    //     yOffset: 'center',
                    //     arrowOffset: 'center',
                    //     showNextButton: false,
                    //     // onShow: function(){ console.log("ANDYTEST", hopscotch.getCurrTour()['steps'][hopscotch.getCurrStepNum()]);}
                    // },
                    {
                        id: 'qt_open_window',
                        title: "Add some text",
                        content: "Click here to open the QuickText window.",
                        target: "working_area_tab_text_btn",
                        placement: "bottom",
                        nextOnTargetClick: true,
                        showNextButton: false
                    },
                    {
                        id: 'qt_enter_text',
                        title: "Type your name",
                        content: "Use your computers keyboard to type in your name.",
                        target: "quick_text_dialog_text_input",
                        placement: "right",
                        nextOnTargetClick: false,
                        showNextButton: true,
                        delay: 300
                    },
                    {
                        id: 'qt_close_window',
                        title: "Close the window",
                        content: "Close the window by pressing OK.",
                        target: "quick_text_text_done_btn",
                        placement: "right",
                        nextOnTargetClick: true,
                        showNextButton: false
                    },

                ]
            };
        };

        self._refresh_bubble_position = function (msg) {
            console.log("_refresh_bubble_position ["+msg+"]");
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
