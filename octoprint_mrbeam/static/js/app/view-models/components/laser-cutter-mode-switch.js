ko.components.register('laser-cutter-mode-switch', {
    viewModel: function() {
        let self = this;

        // TODO: change to using LASER_CUTTER_MODE_NAME
        self.selectedMode = ko.observable('default');

        self.changeLaserCutterMode = function () {
            console.log("Changing laser cutter mode to", self.selectedMode());

            showConfirmationDialog({
                title: gettext("Change the laser cutter mode"),
                message: gettext(
                    "Keep in mind that the device will restart and the webpage will refresh after switching the laser cutter mode."
                ),
                question: gettext(
                    `Are you sure you want to switch the laser cutter mode into ${self.selectedMode()}?`
                ),
                proceed: gettext("Confirm"),
                proceedClass: "primary",
                cancel: gettext("Cancel"),
                onproceed: function () {
                    OctoPrint.simpleApiCommand(
                        "mrbeam",
                        "laser_cutter_mode_change",
                        { mode: self.selectedMode() }
                    )
                        .done(function (response) {
                            console.log("Laser cutter mode changed ", response);
                        })
                        .fail(function () {
                            console.log("Laser cutter mode change failed!");
                            new PNotify({
                                title: gettext(
                                    "Changing the laser cutter mode failed"
                                ),
                                text: gettext(
                                    `Changing the laser cutter mode to ${self.selectedMode()} failed. Please contact customer support.`
                                ),
                                type: "error",
                                hide: false,
                            });
                        });
                },
            });
        };
    },
    template: `
        <select id="laser_cutter_mode_select" data-test="laser-cutter-mode-select" data-bind="value: selectedMode, event:{ change: changeLaserCutterMode}">
            <option value="default">${ _('Default')}</option>
            <option value="rotary">${ _('Rotary')}</option>
        </select>
    `,
});
