$(function() {
    function WizardWhatsnewViewModel(parameters) {
        var self = this;


         self.onStartup = function(){
             $('#wizard_dialog div.modal-header h3').text("✨ What's New ✨");
             $('#wizard_dialog div.modal-footer button.button-finish').text("Let's go!")
             $('#wizard_dialog div.modal-footer div.text-center').hide()
         }

    }

    OCTOPRINT_VIEWMODELS.push([
        WizardWhatsnewViewModel,
        [],
        "#wizard_plugin_corewizard_whatsnew_1"
    ]);
});
