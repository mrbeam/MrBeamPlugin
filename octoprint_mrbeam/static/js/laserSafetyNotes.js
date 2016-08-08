$(function() {
    
	function LaserSafetyNotesViewModel(params) {
		var self = this;

		self.settings = params[0];

		self.onAllBound = function() {
			if (self.settings.settings.plugins.mrbeam.showlasersafety() == true) {
				$('#laser_safety_overlay').modal("show");
			}

		};
		
		self.agree = function(){
			$('#laser_safety_overlay').modal("hide");
		}
	}

	
    // view model class, identifier, parameters for constructor, container to bind to
    ADDITIONAL_VIEWMODELS.push([LaserSafetyNotesViewModel,
		["settingsViewModel"],
		document.getElementById("laser_safety_overlay")]);
	
});
