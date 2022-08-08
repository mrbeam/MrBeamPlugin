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

        self.profiles = new ItemListHelper(
            "laserCutterProfiles",
            {
                name: function (a, b) {
                    // sorts ascending
                    if (
                        a["name"].toLocaleLowerCase() <
                        b["name"].toLocaleLowerCase()
                    )
                        return -1;
                    if (
                        a["name"].toLocaleLowerCase() >
                        b["name"].toLocaleLowerCase()
                    )
                        return 1;
                    return 0;
                },
            },
            {},
            "name",
            [],
            [],
            10
        );

        self.hasDataLoaded = false;

        self.defaultProfile = ko.observable();
        self.currentProfile = ko.observable();

        self.currentProfileData = ko.observable(
            ko.mapping.fromJS(self._cleanProfile())
        );

        self.editorNew = ko.observable(false);

        self.editorName = ko.observable();
        self.editorIdentifier = ko.observable();
        self.editorModel = ko.observable();

        self.editorVolumeWidth = ko.observable();
        self.editorVolumeDepth = ko.observable();
        self.editorVolumeHeight = ko.observable();

        self.editorZAxis = ko.observable();
        self.editorFocus = ko.observable();
        self.editorGlasses = ko.observable();

        self.editorAxisXSpeed = ko.observable();
        self.editorAxisYSpeed = ko.observable();
        self.editorAxisZSpeed = ko.observable();

        self.editorAxisXInverted = ko.observable(false);
        self.editorAxisYInverted = ko.observable(false);
        self.editorAxisZInverted = ko.observable(false);

        self.makeDefault = function (data) {
            var profile = {
                id: data.id,
                default: true,
            };

            self.updateProfile(profile);
        };

        self.requestData = function () {
            $.ajax({
                url: BASEURL + "plugin/mrbeam/profiles",
                type: "GET",
                dataType: "json",
                success: self.fromResponse,
            });
        };

        self.fromResponse = function (data) {
            var items = [];
            var defaultProfile = undefined;
            var currentProfile = undefined;
            var currentProfileData = undefined;
            _.each(data.profiles, function (entry) {
                if (entry.default) {
                    defaultProfile = entry.id;
                }
                if (entry.current) {
                    currentProfile = entry.id;
                    currentProfileData = ko.mapping.fromJS(
                        entry,
                        self.currentProfileData
                    );
                }
                entry["isdefault"] = ko.observable(entry.default);
                entry["iscurrent"] = ko.observable(entry.current);
                items.push(entry);
            });
            self.profiles.updateItems(items);
            self.defaultProfile(defaultProfile);
            self.currentProfile(currentProfile);
            self.currentProfileData(currentProfileData);

            self.hasDataLoaded = true;

            //TODO calculate MaxSpeed without Conversion
            // var maxSpeed = Math.min(self.currentProfileData().axes.x.speed(), self.currentProfileData().axes.y.speed());
            // self.conversion.maxSpeed(maxSpeed);
        };

        self.addProfile = function (callback) {
            var profile = self._editorData();
            $.ajax({
                url: BASEURL + "plugin/mrbeam/profiles",
                type: "POST",
                dataType: "json",
                contentType: "application/json; charset=UTF-8",
                data: JSON.stringify({ profile: profile }),
                success: function () {
                    if (callback !== undefined) {
                        callback();
                    }
                    self.requestData();
                },
            });
        };

        self.removeProfile = function (data) {
            $.ajax({
                url: data.resource,
                type: "DELETE",
                dataType: "json",
                success: self.requestData,
            });
        };

        self.updateProfile = function (profile, callback) {
            if (profile == undefined) {
                profile = self._editorData();
            }

            $.ajax({
                url: BASEURL + "plugin/mrbeam/profiles/" + profile.id,
                type: "PATCH",
                dataType: "json",
                contentType: "application/json; charset=UTF-8",
                data: JSON.stringify({ profile: profile }),
                success: function () {
                    if (callback !== undefined) {
                        callback();
                    }
                    self.requestData();
                },
            });
        };

        self.showEditProfileDialog = function (data) {
            var add = false;
            if (data == undefined) {
                data = self._cleanProfile();
                add = true;
            }

            self.editorNew(add);

            self.editorIdentifier(data.id);
            self.editorName(data.name);
            self.editorModel(data.model);

            self.editorVolumeWidth(data.volume.width);
            self.editorVolumeDepth(data.volume.depth);
            self.editorVolumeHeight(data.volume.height);

            self.editorZAxis(data.zAxis);
            self.editorFocus(data.focus);
            self.editorGlasses(data.glasses);

            self.editorAxisXSpeed(data.axes.x.speed);
            self.editorAxisXInverted(data.axes.x.inverted);
            self.editorAxisYSpeed(data.axes.y.speed);
            self.editorAxisYInverted(data.axes.y.inverted);
            self.editorAxisZSpeed(data.axes.z.speed);
            self.editorAxisZInverted(data.axes.z.inverted);

            var editDialog = $("#settings_laserCutterProfiles_editDialog");
            var confirmButton = $("button.btn-confirm", editDialog);
            var dialogTitle = $("h3.modal-title", editDialog);

            dialogTitle.text(
                add
                    ? "Add Profile"
                    : _.sprintf('Edit Profile "%(name)s"', { name: data.name })
            );
            confirmButton.unbind("click");
            confirmButton.bind("click", function () {
                self.confirmEditProfile(add);
            });
            editDialog.modal("show");
        };

        self.confirmEditProfile = function (add) {
            var callback = function () {
                $("#settings_laserCutterProfiles_editDialog").modal("hide");
            };

            if (add) {
                self.addProfile(callback);
            } else {
                self.updateProfile(undefined, callback);
            }
        };

        self.getMechanicalPerformanceData = function () {
            const fx = self.currentProfileData().axes.x.speed();
            const fy = self.currentProfileData().axes.y.speed();
            const maxF = Math.min(fx, fy);
            const ax = self
                .currentProfileData()
                .grbl.settings[self.grblKeys.max_acc_x]();
            const ay = self
                .currentProfileData()
                .grbl.settings[self.grblKeys.max_acc_y]();
            const maxAcc = Math.min(ax, ay);
            return {
                workingAreaWidth: self.currentProfileData().volume.width(),
                workingAreaHeight: self.currentProfileData().volume.depth(),
                maxFeedrateXY: maxF,
                accelerationXY: maxAcc,
            };
        };

        self._editorData = function () {
            var profile = {
                id: self.editorIdentifier(),
                name: self.editorName(),
                model: self.editorModel(),
                volume: {
                    width: parseFloat(self.editorVolumeWidth()),
                    depth: parseFloat(self.editorVolumeDepth()),
                    height: parseFloat(self.editorVolumeHeight()),
                },
                zAxis: self.editorZAxis(),
                focus: self.editorFocus(),
                glasses: self.editorGlasses(),
                axes: {
                    x: {
                        speed: parseInt(self.editorAxisXSpeed()),
                        inverted: self.editorAxisXInverted(),
                    },
                    y: {
                        speed: parseInt(self.editorAxisYSpeed()),
                        inverted: self.editorAxisYInverted(),
                    },
                    z: {
                        speed: parseInt(self.editorAxisZSpeed()),
                        inverted: self.editorAxisZInverted(),
                    },
                },
            };

            return profile;
        };

        self.onSettingsShown = self.requestData;
        self.onStartup = function () {
            self.requestData();
            self.control.showZAxis = ko.computed(function () {
                var has = self.currentProfileData()["zAxis"]();
                return has;
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
