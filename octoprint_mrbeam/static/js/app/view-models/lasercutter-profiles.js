$(function () {
    function LaserCutterProfilesViewModel(params) {
        var self = this;

        self.control = params[0];

        self._cleanProfile = function () {
            return {
                id: "",
                name: "",
                model: "",
                volume: {
                    formFactor: "rectangular",
                    width: 216,
                    depth: 297,
                    height: 0,
                    origin_offset_x: 1,
                    origin_offset_y: 1,
                },
                zAxis: false,
                focus: false,
                glasses: true,
                axes: {
                    x: { speed: 6000, inverted: false },
                    y: { speed: 6000, inverted: false },
                    z: { speed: 200, inverted: false },
                },
            };
        };

        self.grblKeys = {
            step_pulse: 0,
            step_idle_delay: 1, //	Step idle delay, milliseconds
            step_port_invert_mask: 2, //	Step port invert, mask
            dir_port_invert_mask: 3, //	Direction port invert, mask
            step_enable_invert: 4, //	Step enable invert, boolean
            limit_pins_invert: 5, //	Limit pins invert, boolean
            probe_pin_invert: 6, //	Probe pin invert, boolean
            status_report_mask: 10, //	Status report, mask
            juction_deviation: 11, //	Junction deviation, mm
            arc_tolerance: 12, //	Arc tolerance, mm
            report_inches: 13, //	Report inches, boolean
            soft_limits: 20, //	Soft limits, boolean
            hard_limits: 21, //	Hard limits, boolean
            homing_cycle: 22, //	Homing cycle, boolean
            homing_dir_invert_mask: 23, //	Homing dir invert, mask
            homing_feed: 24, //	Homing feed, mm / min
            homing_seek: 25, //	Homing seek, mm / min
            homing_debounce: 26, //	Homing debounce, milliseconds
            homing_pulloff: 27, //	Homing pull - off, mm
            max_spindle: 30, //	Max spindle speed, RPM
            min_spindle: 31, //	Min spindle speed, RPM
            laser_mode: 32, //	Laser mode, boolean
            steps_per_mm_x: 100, //	X steps / mm
            steps_per_mm_y: 101, //	Y steps / mm
            steps_per_mm_z: 102, //	Z steps / mm
            max_feedrate_x: 110, //	X Max rate, mm / min
            max_feedrate_y: 111, //	Y Max rate, mm / min
            max_feedrate_z: 112, //	Z Max rate, mm / min
            max_acc_x: 120, //	X Acceleration, mm / sec ^ 2
            max_acc_y: 121, //	Y Acceleration, mm / sec ^ 2
            max_acc_z: 122, //	Z Acceleration, mm / sec ^ 2
            max_travel_x: 130, //	X Max travel, mm
            max_travel_y: 131, //	Y Max travel, mm
            max_travel_z: 132, //	Z Max travel, mm
        };

        self.hasDataLoaded = false;

        self.currentProfile = ko.observable();

        self.currentProfileData = ko.observable(self._cleanProfile());

        self.requestData = function () {
            $.ajax({
                url: BASEURL + "plugin/mrbeam/currentProfile",
                type: "GET",
                dataType: "json",
                success: self.fromResponse,
            });
        };

        self.fromResponse = function (data) {
            self.currentProfile(data.id);
            self.currentProfileData(data);
            self.hasDataLoaded = true;

            //TODO calculate MaxSpeed without Conversion
            // var maxSpeed = Math.min(self.currentProfileData().axes.x.speed, self.currentProfileData().axes.y.speed);
            // self.conversion.maxSpeed(maxSpeed);
        };

        self.getMechanicalPerformanceData = function () {
            const fx = self.currentProfileData().axes.x.speed;
            const fy = self.currentProfileData().axes.y.speed;
            const maxF = Math.min(fx, fy);
            const ax =
                self.currentProfileData().grbl.settings[
                    self.grblKeys.max_acc_x
                ];
            const ay =
                self.currentProfileData().grbl.settings[
                    self.grblKeys.max_acc_y
                ];
            const maxAcc = Math.min(ax, ay);
            return {
                workingAreaWidth: self.currentProfileData().volume.width,
                workingAreaHeight: self.currentProfileData().volume.depth,
                maxFeedrateXY: maxF,
                accelerationXY: maxAcc,
            };
        };

        self.onSettingsShown = self.requestData;
        self.onStartup = function () {
            self.requestData();
            self.control.showZAxis = ko.computed(function () {
                return self.currentProfileData()["zAxis"];
            }); // dependency injection
        };
    }

    // view model class, identifier, parameters for constructor, container to bind to
    ADDITIONAL_VIEWMODELS.push([
        LaserCutterProfilesViewModel,
        ["controlViewModel"],
        document.getElementById("lasercutterprofiles"),
    ]);
});
