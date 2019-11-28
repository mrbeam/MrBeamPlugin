/* global ADDITIONAL_VIEWMODELS */

$(function () {

    function MaterialSettingsViewModel(params) {
        let self = this;
        self.MATERIAL_SETTINGS_RETRY_TIME = 5000;

        window.mrbeam.viewModels['materialSettingsViewModel'] = self;
        self.materialSettingsDatabase = {};
        self.laserSource = null;

        self.loadMaterialSettings = function (callback) {
            console.log("Loading standard materials");
            OctoPrint.simpleApiCommand("mrbeam", "material_settings", {})
                .done(function (response) {
                    let materialImportedSettings = response['materials'];
                    self.laserSource = response['laser_source'];
                    console.log("Loaded standard materials! LaserSource: ", self.laserSource);
                    console.log(response);

                    for (let materialKey in self.materialSettingsDatabase) {
                        if (materialKey in materialImportedSettings) {
                            self.materialSettingsDatabase[materialKey].colors = materialImportedSettings[materialKey].colors;
                        } else {
                            delete self.materialSettingsDatabase[materialKey]
                        }
                    }
                    if (callback) {
                        callback(self.materialSettingsDatabase);
                    }
                })
                .fail(function (response) {
                    setTimeout(self.loadMaterialSettings, self.MATERIAL_SETTINGS_RETRY_TIME, callback);
                    console.error("Unable to load material settings. Retrying in " + self.MATERIAL_SETTINGS_RETRY_TIME/1000 + " seconds.");
                });
        };

        self.materialSettingsDatabase = {
            ///// EDIT MATERIAL SETTINGS BELOW THIS LINE ////////
            'Acrylic': {
                name: gettext("Acrylic"),
                img: 'Acrylic.jpg',
                description: gettext("Acrylic"),
                hints: gettext("Acrylic"),
            },
            'Anodized Aluminum': {
                name: gettext("Anodized Aluminum"),
                img: 'Anodized-Aluminum.jpg',
                description: gettext("Dark anodized aluminum can be engraved. Works on iPhones."),
                hints: gettext("Requires very precise focus. Anodized aluminum turns brighter through laser engraving. Therefore we suggest to invert photos for engravings."),
                // colors: {
                //     '000000': {
                //             engrave: {eng_i: [0, 100], eng_f: [1000, 30], engrave_compressor_lvl: 0, eng_pierce: 0, dithering: false},
                //             cut: []
                //         }
                //     }
            },
            'Balsa Wood': {
                name: gettext("Balsa Wood"),
                img: 'Balsa-Wood.jpg',
                description: '',
                hints: '',
                safety_notes: gettext("Take care about ignitions. Never run a job slower than 300 mm/min!"),
                // colors: {
                //     'd4b26f': {
                //         engrave: {eng_i: [0, 20], eng_f: [2000, 350], engrave_compressor_lvl: 0, eng_pierce: 0, dithering: false},
                //         cut: [
                //             {thicknessMM: 1, cut_i: 80, cut_f: 525, cut_p: 2},
                //             {thicknessMM: 2, cut_i: 100, cut_f: 525, cut_p: 2},
                //             {thicknessMM: 3, cut_i: 100, cut_f: 525, cut_p: 2},
                //             {thicknessMM: 4, cut_i: 100, cut_f: 450, cut_p: 3},
                //             {thicknessMM: 5, cut_i: 100, cut_f: 225, cut_p: 3}
                //         ]
                //     }
                // }
            },
            'Bamboo': {
                name: gettext("Bamboo Wood"),
                img: 'Bamboo.jpg',
                description: '',
                hints: '',
                safety_notes: '',
            },
            'Cardboard, corrugated single wave': {
                name: gettext("Cardboard, single wave"),
                img: 'Cardboard-Single-Wave.jpg',
                description: gettext("Ordinary cardboard like most packaging is made of."),
                hints: gettext("Engraving looks great if just the first layer is lasered away, that the wave is visible underneath."),
                safety_notes: gettext("Take care about ignitions. Never run a job slower than 180 mm/min!"),
            },
            'Cardboard, corrugated double wave': {
                name: gettext("Cardboard, double wave"),
                img: 'Cardboard-Double-Wave.jpg',
                description: gettext("Ordinary cardboard like strong packaging is made of."),
                hints: gettext("Engraving looks great if just the first layer is lasered away, that the wave is visible underneath."),
                safety_notes: gettext("Take care about ignitions. Never run a job slower than 180 mm/min!"),
            },
            'Cork': {
                name: gettext("Cork"),
                img: 'Cork.jpg',
                description: gettext("Cork"),
                hints: gettext("Cork"),
            },
            'Fabric Cotton': null,
            'Fabric Polyester': null,
            'Finn Cardboard': {
                name: gettext("Finn Cardboard"),
                img: 'Finn-Cardboard.jpg',
                description: gettext("Made out of purely wooden fibres, often used for architectural models."),
                hints: '',
                safety_notes: '',
            },
            'Felt': { // took settings from IHM fair
                name: gettext("Felt"),
                img: 'Felt.jpg',
                description: gettext("Acrylic felt like the one sold in many arts and craft stores."),
                hints: gettext("Be aware that natural felt is something else."),
                safety_notes: '',
            },
            'Foam Rubber': {
                name: gettext("Foam Rubber"),
                img: 'Foam-Rubber.jpg',
                description: gettext("Consists of poly urethane foam."),
                hints: gettext("Laser parameters are highly color dependant, bright colors might need pierce time."),
                safety_notes: '',
            },
            'Grey Cardboard': {
                name: gettext("Grey Cardboard"),
                img: 'Grey-Cardboard.jpg',
                description: gettext("Grey Cardboard"),
                hints: gettext("Grey Cardboard"),
            },
            'Jersey Fabric': {
                name: gettext("Jersey Fabric"),
                img: 'Jersey-Fabric.jpg',
                description: gettext("Jersey Fabric"),
                hints: gettext("Jersey Fabric"),
            },
            'Kraftplex': {
                name: gettext("Kraftplex"),
                img: 'Kraftplex.jpg',
                description: gettext("100% natural fibers compressed under high temperature. Strong and bendable like metal."),
                hints: '',
                safety_notes: '',
            },
            'Kraftplex Wave': {
                name: gettext("Kraftplex Wave"),
                img: 'Kraftplex-Wave.jpg',
                description: gettext("Kraftplex Wave"),
                hints: gettext("Kraftplex (Wave)"),
            },
            'Latex':  {
                name: gettext("Latex"),
                img: 'Latex.jpg',
                description: gettext("Latex"),
                hints: gettext("Latex"),
            },
            'Leather': {
                name: gettext("Leather"),
                img: 'Leather.jpg',
                description: gettext("Leather"),
                hints: gettext("Leather"),
            },
            'Linoleum': {
                name: gettext("Linoleum"),
                img: 'Linoleum.jpg',
                description: gettext("Linoleum"),
                hints: gettext("Linoleum"),
            },
            'Mirror': {
                name: gettext("Mirror"),
                img: 'Mirror.jpg',
                description: gettext("Mirror"),
                hints: gettext("Mirror"),
            },
            'Paper': {
                name: gettext("Paper"),
                img: 'Paper.jpg',
                description: gettext("Ordinary paper like from an office printer."),
                hints: '',
                safety_notes: gettext("Very fine structures may be subject of ignition."),
            },
            // TODO : Choose between polyurethane and Polypropylene
            'Polyethylene Foam': {
                name: gettext("Polyethylene Foam"),
                img: 'Polyethylene-Foam.jpg',
                description: gettext("Polyethylene Foam"),
                hints: gettext("Polyethylene Foam"),
            },
            'Polyurethane Foam': {
                name: gettext("Polyurethane Foam"),
                img: 'Polyurethane-Foam.jpg',
                description: gettext("Polyurethane Foam"),
                hints: gettext("Polyurethane Foam"),
            },
            'Polypropylene': {
                name: gettext("Polypropylene"),
                img: 'Polypropylene.jpg',
                description: gettext("Polypropylene"),
                hints: gettext("Polypropylene"),
            },
            'Plywood Birch': {
                name: gettext("Plywood Birch"),
                img: 'Plywood-Birch.jpg',
                description: gettext("Plywood Birch"),
                hints: gettext("Plywood Birch"),
            },
            'Plywood Poplar': {
                name: gettext("Plywood Poplar"),
                img: 'Plywood-Poplar.jpg',
                description: gettext("Plywood from an ordinary hardware store or arts and craft supply."),
                hints: gettext("Watch out for dedicated laser plywood - it has better surface quality and only natural glue."),
                safety_notes: gettext("Very fine structures may be subject of ignition."),
            },
            'Slate': {
                name: gettext("Slate"),
                img: 'Slate.jpg',
                description: gettext("Slate"),
                hints: gettext("Slate"),
            },
            'Snappap': {
                name: gettext("Snappap"),
                img: 'Snappap.jpg',
                description: gettext("Snappap"),
                hints: gettext("Snappap"),
            },
            'Vegan Leather': {
                name: gettext("Vegan Leather"),
                img: 'Vegan-Leather.jpg',
                description: gettext("Vegan Leather"),
                hints: gettext("Vegan Leather"),
            },
            'Wellboard': {
                name: gettext("Wellboard"),
                img: 'Wellboard.jpg',
                description: gettext("100% natural fibers similar to Kraftplex, but wavy."),
                hints: gettext("Thickness is measured over the whole wave."),
                safety_notes: '',
            },
        };
        ///// EDIT MATERIAL SETTINGS ABOVE THIS LINE ////////`
    }


    ADDITIONAL_VIEWMODELS.push(
        [MaterialSettingsViewModel,
            [],
            [ /* ... */]
        ]);
});
