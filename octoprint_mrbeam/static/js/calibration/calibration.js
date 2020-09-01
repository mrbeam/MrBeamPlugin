/*
 * View model for Mr Beam
 *
 * Author: Teja Philipp <teja@mr-beam.org>
 * License: AGPLv3
 */
/* global OctoPrint, OCTOPRINT_VIEWMODELS, INITIAL_CALIBRATION */


$(function () {
	function CalibrationViewModel(parameters) {
		let self = this;
		window.mrbeam.viewModels['calibrationViewModel'] = self;
		self.cameraSettings = parameters[0]

        self.calibrationScreenShown = ko.observable(false);
		self.startupComplete = ko.observable(false);

		// calibrationState is constantly refreshed by the backend
		// as an immutable array that contains the whole state of the calibration
		self.calibrationState = ko.observable({})

		self.onStartupComplete = function () {
		    self.calibrationScreenShown(true); // todo user lens calibration: when should we do this?
            self.startupComplete(true);

			$('#settings_plugin_mrbeam_camera_link').click(function(){
                self.resetUserView()
            });
		};

		self.resetUserView = function() {
			self.cameraSettings.changeUserView('settings')
		}

		self.resetView = function () {
			self.focusX(0);
			self.focusY(0);
			self.calSvgScale(1);
			self.currentMarker = 0;

			self.resetUserView()
		};

		self.simpleApiCommand = function(command, data, successCallback, errorCallback, type) {
			data = data || {}
			data.command = command
			if (window.mrbeam.isWatterottMode()) {
				$.ajax({
					url: "/plugin/mrbeam/" + command,
					type: type, // POST, GET
					headers: {
						"Accept": "application/json; charset=utf-8",
						"Content-Type": "application/json; charset=utf-8"
					},
					data: JSON.stringify(data),
					dataType: "json",
					success: successCallback,
					error: errorCallback
				});
			}
			else {
				OctoPrint.simpleApiCommand("mrbeam", command, data)
						.done(successCallback)
						.fail(errorCallback);
			}
		}

		// ---------------- CAMERA ALIGNMENT ----------------
		self.qa_cameraalignment_image_loaded = ko.observable(false);
		$('#qa_cameraalignment_image').load(function(){
		    self.qa_cameraalignment_image_loaded(true)
        })

		// todo iratxe: put this somewhere else?
        self.printLabel = function (labelType, event) {
			let button = $(event.target)
			let label = button.text().trim()
			button.prop("disabled", true);
			self.simpleApiCommand('print_label',
				{labelType: labelType,
                        blink: true},
				function () {
					button.prop("disabled", false);
					new PNotify({
						title: gettext("Printed: ") + label,
						type: "success",
						hide: false
					})
				},
				function (response) {
					button.prop("disabled", false);
					let data = response.responseJSON
					new PNotify({
						title: gettext("Print Error") + ': ' + label,
						text: data ? data.error : '',
						type: "error",
						hide: false
					})
				},
				'POST')
		}


		// todo iratxe: delete?
		self.engrave_markers_without_gui = function () {
			var intensity = $('#initialcalibration_intensity').val()
			var feedrate = $('#initialcalibration_feedrate').val()
            self.simpleApiCommand(
                "engrave_calibration_markers/" + intensity + "/" + feedrate,
                {},
                function (data) {
					console.log("Success", url, data);

				},
                function (jqXHR, textStatus, errorThrown) {
					new PNotify({
						title: gettext("Error"),
						text: _.sprintf(gettext("Marker engraving failed: <br>%(errmsg)s<br>Error:<br/>%(code)s %(status)s - %(errorThrown)s"),
								{errmsg: jqXHR.responseText, code: jqXHR.status, status: textStatus, errorThrown: errorThrown}),
						type: "error",
						hide: false
					})
				}
            )
		};
	}

	// view model class, parameters for constructor, container to bind to
	OCTOPRINT_VIEWMODELS.push([
		CalibrationViewModel,

		// e.g. loginStateViewModel, settingsViewModel, ...
		["cameraSettingsViewModel"],

		// e.g. #settings_plugin_mrbeam, #tab_plugin_mrbeam, ...
		["#settings_plugin_mrbeam_camera"]
	]);
});
