$(function() {
    function WizardWhatsnewViewModel(parameters) {
         var self = this;

         self.onAfterBinding = function(){
             $('#wizard_dialog div.modal-footer button.button-finish').text(gettext("Let's go!"));
             $('#wizard_dialog div.modal-footer div.text-center').hide();
             if (self.is_bound()) {
                // test if bound, only then it's a what's new wizard
                 $('#wizard_dialog div.modal-header h3').text("✨ " + gettext("What's New") + " ✨");
             } else{
                 // welcome wizard
             }
         };

         self.is_bound = function(){
            var elem = document.getElementById(DOM_ELEMENT_TO_BIND_TO);
            return elem ? (!!ko.dataFor(elem)) : false;
         };

    }

    var DOM_ELEMENT_TO_BIND_TO = "wizard_plugin_corewizard_whatsnew_0";
    OCTOPRINT_VIEWMODELS.push([
        WizardWhatsnewViewModel,
        [],
        "#"+DOM_ELEMENT_TO_BIND_TO
    ]);
});
