$(function() {
    function WizardAnalyticsViewModel(parameters) {
         var self = this;

         self.analyticsInitialConsent = ko.observable(null);

         self.saveAnalyticsConsent = function(){
		    let data = {analyticsInitialConsent: self.analyticsInitialConsent}
		    console.log("######################### save analytics consent: " + data)

		    OctoPrint.simpleApiCommand("mrbeam", "analytics_init", data)
                .done(function(response){
					console.log("simpleApiCall response: ", response);
				})
                .fail(function(){
					console.error("Unable to save analytics state: ", data);
					new PNotify({
                        title: "Error while saving settings!",
                        text: "Unable to save your analytics state at the moment.<br/>Check connection to Mr Beam II and try again.",
                        type: "error",
                        hide: true
                    });
				});
         }

         // self.onBeforeWizardTabChange = function(next, current) {
         //     if (current === 'wizard_plugin_corewizard_analytics_link') {
         //         $('#analytics_consent').remove();
         //     }
         // }

         self.onAfterWizardTabChange = function(current) {
             if (current === "wizard_plugin_corewizard_analytics_link") {
                 if (self.analyticsInitialConsent() == null) {
                     $("#wizard_dialog div.modal-footer button.button-finish").prop("disabled", true);
                     $("#wizard_dialog div.modal-footer button.button-finish").removeAttr("onclick");
                 }

                 // $("#wizard_dialog div.modal-footer button.button-finish").attr("data-bind", "enable: responded(), click: agree");
                 // let refuse = $('<input type="button" value="I do NOT agree" id="analytics_consent" class="btn btn-primarybutton-next"/>'); // style="background:#E74C3C"
                 // $("#wizard_dialog div.modal-footer").append(refuse);
                 // $('#wizard_dialog div.modal-footer button.button-finish').text("I agree")

                 // $('#wizard_dialog div.modal-footer button.button-finish').addClass('btn-success');
                 // $('#wizard_dialog div.modal-footer button.button-finish').removeClass('btn-primary');
                 // $('#wizard_dialog div.modal-footer button.button-finish').css("background","#2ECC71")

             }
         }

         self.is_bound = function(){
            var elem = document.getElementById(DOM_ELEMENT_TO_BIND_TO);
            return elem ? (!!ko.dataFor(elem)) : false;
         };

         self.enableLetsGoButton = function() {
             $("#wizard_dialog div.modal-footer button.button-finish").prop("disabled", false);
             $("#wizard_dialog div.modal-footer button.button-finish").click(function () {
                 let consent = self.analyticsInitialConsent()
                 let data = {analyticsInitialConsent: consent}
                 console.log("######################### save analytics consent: " + consent)
                 OctoPrint.simpleApiCommand("mrbeam", "analytics_init", data)
                     .done(function(response){
                         console.log("simpleApiCall response: ", response);
                     })
                     .fail(function(){
                         console.error("Unable to save analytics state: ", data);
                         new PNotify({
                             title: "Error while saving settings!",  text: "Unable to save your analytics state at the moment.<br/>Check connection to Mr Beam II and try again.",
                             type: "error",
                             hide: true
                         });
                     });

             });
             return true; // "The click binding stops the default browser handler from running. In this case, the browser responds to canceling the "click" event by changing the radio buttons back to what they were before. The return true tells Knockout to allow the default behavior to happen."
         }

    }

    var DOM_ELEMENT_TO_BIND_TO = "wizard_plugin_corewizard_analytics";
    OCTOPRINT_VIEWMODELS.push([
        WizardAnalyticsViewModel,
        [],
        "#"+DOM_ELEMENT_TO_BIND_TO
    ]);
});
