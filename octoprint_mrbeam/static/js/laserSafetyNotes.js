$(function() {
    
	function LaserSafetyNotesViewModel() {
		var self = this;

		self.onStartup = function(){
			$('#laser_safety_overlay').modal("show");
		};
		
		self.agree = function(){
			$('#laser_safety_overlay').modal("hide");
		}
	}

	
    // view model class, identifier, parameters for constructor, container to bind to
    ADDITIONAL_VIEWMODELS.push([LaserSafetyNotesViewModel,
		[], 
		document.getElementById("laser_safety_overlay")]);
	
});
