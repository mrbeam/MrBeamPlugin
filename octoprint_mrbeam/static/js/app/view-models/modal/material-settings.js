/* global ADDITIONAL_VIEWMODELS */

$(function () {
    function MaterialSettingsViewModel(params) {
        let self = this;
        self.MATERIAL_SETTINGS_RETRY_TIME = 5000;
        self.MATERIAL_SHOPIFY_LINK = gettext(
            "https://www.mr-beam.org/en/collections/mr-beam-materialstore"
        );

        window.mrbeam.viewModels["materialSettingsViewModel"] = self;

        self.loginState = params[0];

        self.materialSettingsDatabase = {};
        self.laserSource = null;

        self.loadMaterialSettings = function (callback) {
            console.log("Loading standard materials");
            OctoPrint.simpleApiCommand("mrbeam", "material_settings", {})
                .done(function (response) {
                    let materialImportedSettings = response["materials"];
                    self.laserSource = response["laser_source"];
                    console.log(
                        "Loaded standard materials. Laser source: ",
                        self.laserSource
                    );
                    console.debug(
                        "Loaded standard materials. data: ",
                        response
                    );

                    for (let materialKey in self.materialSettingsDatabase) {
                        if (materialKey in materialImportedSettings) {
                            self.materialSettingsDatabase[materialKey].colors =
                                materialImportedSettings[materialKey].colors;
                            self.materialSettingsDatabase[
                                materialKey
                            ].custom = false;
                            self.materialSettingsDatabase[materialKey].img =
                                "/plugin/mrbeam/static/img/materials/" +
                                self.materialSettingsDatabase[materialKey].img;
                        } else {
                            delete self.materialSettingsDatabase[materialKey];
                        }
                    }
                    if (callback) {
                        callback(self.materialSettingsDatabase);
                    }
                })
                .fail(function (response) {
                    if (self.loginState.loggedIn()) {
                        setTimeout(
                            self.loadMaterialSettings,
                            self.MATERIAL_SETTINGS_RETRY_TIME,
                            callback
                        );
                        console.error(
                            "Unable to load material settings. Retrying in " +
                                self.MATERIAL_SETTINGS_RETRY_TIME / 1000 +
                                " seconds."
                        );
                    } else {
                        console.log(
                            "Unable to load material settings. Not retrying because user is not logged in."
                        );
                    }
                });
        };

        self.materialSettingsDatabase = {
            ///// EDIT MATERIAL SETTINGS BELOW THIS LINE ////////
            Acrylic: {
                name: gettext("Acrylic"),
                img: "Acrylic.jpg",
                description: gettext(
                    "Use opaque acrylic in red or black to create nice objects and signs. Acrylic is great for outdoor applications."
                ),
                hints: "",
                type: "product",
                url: gettext(
                    "https://www.mr-beam.org/en/products/mr-beam-acryl-schwarz"
                ),
            },
            "Anodized Aluminum": {
                name: gettext("Anodized Aluminum"),
                img: "Anodized-Aluminum.jpg",
                description: gettext("Dark anodized aluminum can be engraved."),
                hints: gettext(
                    "Requires very precise focus. Anodized aluminum turns brighter through laser engraving. Therefore we suggest to invert photos for engravings."
                ),
                type: "product",
                url: gettext(
                    "https://www.mr-beam.org/en/products/eloxiertes-aluminium"
                ),
            },
            "Balsa Wood": {
                name: gettext("Balsa Wood"),
                img: "Balsa-Wood.jpg",
                description: gettext(
                    "Balsa wood is a very popular material for light, stiff structures in model making and in particular construction of model aircraft."
                ),
                hints: "",
                safety_notes: gettext(
                    "Caution sensitive material. If laser speed is too slow, balsa wood may ignite."
                ),
                type: null,
                url: null,
            },
            Bamboo: {
                name: gettext("Bamboo Wood"),
                img: "Bamboo.jpg",
                description: gettext(
                    "An individual engraving on a chopping board or a wooden spoon is the perfect spontaneous gift."
                ),
                hints: "",
                safety_notes: "",
                type: null,
                url: null,
            },
            "Cardboard, corrugated single wave": {
                name: gettext("Cardboard, single wave"),
                img: "Cardboard.jpg",
                description: gettext(
                    "Recycle cardboard from packagings to create precise prototypes and models ."
                ),
                hints: gettext(
                    "Dont use your Mr Beam packaging. Please keep it for transportation and storage!"
                ),
                safety_notes: gettext(
                    "Caution sensitive material. If laser speed is too slow, cardboard may ignite."
                ),
                type: null,
                url: null,
            },
            "Cardboard, corrugated double wave": {
                name: gettext("Cardboard, double wave"),
                img: "Cardboard.jpg",
                description: gettext(
                    "Recycle cardboard from packagings to create precise prototypes and models ."
                ),
                hints: gettext(
                    "Dont use your Mr Beam packaging. Please keep it for transportation and storage!"
                ),
                safety_notes: gettext(
                    "Caution sensitive material. If laser speed is too slow, cardboard may ignite."
                ),
                type: null,
                url: null,
            },
            Cork: {
                name: gettext("Cork"),
                img: "Cork.jpg",
                description: gettext(
                    "Create beautiful pin boards or coasters with individual engravings. "
                ),
                hints: "",
                type: null,
                url: null,
            },
            Felt: {
                // took settings from IHM fair
                name: gettext("Felt"),
                img: "Felt.jpg",
                description: gettext(
                    "Acrylic felt can be engraved and cut super fast with Mr Beam."
                ),
                hints: gettext(
                    "Be aware that natural felt is something else and smells very strong when you open the lid."
                ),
                safety_notes: "",
                type: "collection",
                url: gettext("https://www.mr-beam.org/en/collections/filz"),
            },
            "Fabric Cotton": null,
            "Fabric Polyester": null,
            "Finn Cardboard": {
                name: gettext("Finn Cardboard"),
                img: "Finn-Cardboard.jpg",
                description: gettext(
                    "Made out of purely wooden fibres, often used for architectural models."
                ),
                hints: "",
                safety_notes: gettext(
                    "Caution sensitive material. If laser speed is too slow, cardboard may ignite."
                ),
                type: null,
                url: null,
            },
            Foam: {
                name: gettext("Foam"),
                img: "Polyethylene-Foam.jpg",
                description: gettext(
                    "Use polyethylene or polyurethane foam to create nice prototypes and mock-ups. "
                ),
                hints: "",
                type: null,
                url: null,
            },
            "Foam Rubber": {
                name: gettext("Foam Rubber"),
                img: "Foam-Rubber.jpg",
                description: gettext(
                    "Mostly made out of polyurethane and can be engraved and cut super fast with Mr Beam."
                ),
                hints: gettext(
                    "Laser parameters are highly color dependant, bright colors might need pierce time."
                ),
                safety_notes: gettext(
                    "Make sure your foam is not made of PVC and does not contain chlorine!"
                ),
                type: null,
                url: null,
            },
            "Grey Cardboard": {
                name: gettext("Grey Cardboard"),
                img: "Grey-Cardboard.jpg",
                description: "",
                hints: "",
                type: null,
                url: null,
            },
            "Jersey Fabric": {
                name: gettext("Jersey Fabric"),
                img: "Fabric.jpg",
                description: gettext(
                    "Cutting fabric with Mr Beam is so much fun because it doesn't warp and the result is much more accurate than with scissors."
                ),
                hints: "",
                type: null,
                url: null,
            },
            Kraftplex: {
                name: gettext("Kraftplex"),
                img: "Kraftplex.jpg",
                description: gettext(
                    "100% natural fibers compressed under high temperature. Strong and bendable like metal."
                ),
                hints: "",
                safety_notes: "",
                type: "collection",
                url: gettext(
                    "https://www.mr-beam.org/en/collections/kraftplex"
                ),
            },
            "Kraftplex (wave)": {
                name: gettext("Kraftplex (wave)"),
                img: "Kraftplex-Wave.jpg",
                description: gettext(
                    " 100% natural fibers similar to Kraftplex, but wavy. Thickness is measured over the whole wave."
                ),
                type: null,
                url: null,
            },
            Latex: {
                name: gettext("Latex"),
                img: "Latex.jpg",
                description: "",
                hints: "",
                safety_notes: "",
                type: null,
                url: null,
            },
            Leather: {
                name: gettext("Leather"),
                img: "Leather.jpg",
                description: gettext(
                    "Use thin and hard leather to get the best result."
                ),
                hints: "",
                safety_notes: gettext(
                    "If you use artificial leather, make sure that it is not made of PVC and does not contain chlorine!"
                ),
                type: null,
                url: null,
            },
            Linoleum: {
                name: gettext("Linoleum"),
                img: "Linoleum.jpg",
                description: "",
                hints: "",
                type: null,
                url: null,
            },
            Mirror: {
                name: gettext("Mirror"),
                img: "Mirror.jpg",
                description: gettext(
                    "Engrave Mirrors only from the back side. But be aware of that you also need to mirror your design!"
                ),
                hints: "",
                safety_notes: gettext(
                    "Mirrors can only be engraved from the back, otherwise the laser would be reflected."
                ),
                type: "product",
                url: gettext(
                    "https://www.mr-beam.org/en/products/mr-beam-spiegelfliesen"
                ),
            },
            Paper: {
                name: gettext("Paper"),
                img: "Paper.jpg",
                description: gettext(
                    "White paper is difficult to engrave. Please do some testing if necessary."
                ),
                hints: gettext(
                    "Extremely thin paper can vibrate heavily or fly away if using the compressor. In that case, please reduce the power of the compressor."
                ),
                safety_notes: gettext(
                    "Caution sensitive material. Very fine structures may be subject of ignition."
                ),
                type: null,
                url: null,
            },
            "Plywood Birch": {
                name: gettext("Plywood Birch"),
                img: "Plywood-Birch.jpg",
                description: gettext(
                    "Plywood is greate fo all kinds of model making and decoration."
                ),
                hints: gettext(
                    "Watch out for dedicated laser plywood - it has better surface quality and better glue."
                ),
                type: "product",
                url: gettext(
                    "https://www.mr-beam.org/en/products/sperrholz-birke-5er-pack"
                ),
            },
            "Plywood Poplar": {
                name: gettext("Plywood Poplar"),
                img: "Plywood-Poplar.jpg",
                description: gettext(
                    "Plywood is greate fo all kinds of model making and decoration."
                ),
                hints: gettext(
                    "Watch out for dedicated laser plywood - it has better surface quality and better glue."
                ),
                safety_notes: "",
                type: "product",
                url: gettext(
                    "https://www.mr-beam.org/en/products/mr-beam-pappelsperrholz-bunt"
                ),
                variant: {
                    color: {
                        e7d27f: "40760806080623",
                    },
                },
            },
            Polypropylene: {
                name: gettext("Polypropylene"),
                img: "Polypropylene.jpg",
                description: gettext(
                    "Because of its flexibility and durability it is great for outdoor applications. On engraved lines you can easily fold and reinforce it."
                ),
                hints: gettext(
                    "For the best results, use opaque and dark colored polypropylene."
                ),
                type: null,
                url: null,
            },
            Slate: {
                name: gettext("Slate"),
                img: "Slate.jpg",
                description: gettext(
                    "Slate is greate to engrave and you can create beatiful objects, gifts and signs."
                ),
                hints: gettext(
                    "When engraving slate, the engraving becomes brighter than the original material. The images might need theirs colors inverted."
                ),
                type: "product",
                url: gettext(
                    "https://www.mr-beam.org/en/products/schiefer-platte-40x30-cm-2er-pack"
                ),
            },
            Snappap: {
                name: gettext("Snappap"),
                img: "Snappap.jpg",
                description: "",
                hints: "",
                type: null,
                url: null,
            },
            "Laser Leather": {
                name: gettext("Laser Leather"),
                img: "Laser-Leather.jpg",
                description: gettext(
                    "Laser leather is robust in everyday life, it can be washed, sewn and creatively processed with Mr Beam."
                ),
                hints: "",
                type: "collection",
                url: gettext(
                    "https://www.mr-beam.org/en/collections/laser-leder"
                ),
            },
            "Sign Material": {
                name: gettext("Sign Material"),
                img: "Sign-Material.jpg",
                description: "",
                hints: gettext(
                    "The material is supplied with a protective film. It can be removed before or after processing."
                ),
                safety_notes: "",
                type: "product",
                url: gettext(
                    "https://www.mr-beam.org/en/products/mr-beam-schilder-material"
                ),
                variant: {
                    color: {
                        f3de8d: "39842200944751",
                        dedede: "39842200977519",
                        d2a477: "39842201010287",
                    },
                },
            },
            "Stamp Rubber": {
                name: gettext("Stamp Rubber"),
                img: "Stamp-Rubber.jpg",
                description: "",
                hints: gettext(
                    "Repeat the engraving once ore twice for a better result."
                ),
                safety_notes: "",
                type: "product",
                url: gettext(
                    "https://www.mr-beam.org/en/products/stempelgummi"
                ),
            },
            "Swiss stone pine": {
                name: gettext("Swiss stone pine"),
                img: "Zirbenholz.jpg",
                description: "",
                hints: "",
                safety_notes: "",
                type: null,
                url: null,
            },
            "Wood Sticker": {
                name: gettext("Wood Sticker"),
                img: "Wood-Sticker.jpg",
                description: "",
                hints: "",
                safety_notes: "",
                type: "product",
                url: gettext(
                    "https://www.mr-beam.org/en/products/edelholzsticker"
                ),
            },
            "Solid Wood": {
                name: gettext("Solid Wood"),
                img: "Solid-Wood.jpg",
                description: "",
                hints: "",
                safety_notes: "",
                type: "collection",
                url: gettext("https://www.mr-beam.org/en/collections/holz"),
            },
            "Stainless Steel": {
                name: gettext("Stainless Steel"),
                img: "Stainless-Steel.jpg",
                description: "",
                hints: gettext(
                    'Engravings on stainless steel only work with our "mark solid" spray. Use line distance 0,1mm for the best result.'
                ),
                safety_notes: gettext(
                    "Do not engrave stainless steel without the application of laser marking color."
                ),
                type: null,
                url: null,
            },
        };
        ///// EDIT MATERIAL SETTINGS ABOVE THIS LINE ////////`

        self.constructShopifyURL = function (materialName, materialColor) {
            // Validate material name and URL
            if (
                self.validateMaterialName(materialName) &&
                self.validateMaterialUrl(materialName)
            ) {
                return self.addUrlReferral(
                    self.constructMaterialURL(materialName, materialColor)
                );
            }
            return self.addUrlReferral(self.MATERIAL_SHOPIFY_LINK);
        };

        self.validateMaterialName = function (materialName) {
            return materialName in self.materialSettingsDatabase;
        };

        self.validateMaterialUrl = function (materialName) {
            return (
                self.materialSettingsDatabase[materialName]["url"] &&
                typeof self.materialSettingsDatabase[materialName]["url"] ===
                    "string"
            );
        };

        self.constructMaterialURL = function (materialName, materialColor) {
            const url = self.materialSettingsDatabase[materialName]["url"];
            // Check if a color variant query parameter exists for this URL
            if (self.validateMaterialVariant(materialName, materialColor)) {
                const variantParameterKey = "variant";
                const variantParameterValue =
                    self.materialSettingsDatabase[materialName]["variant"][
                        "color"
                    ][materialColor];
                return (
                    url +
                    "?" +
                    variantParameterKey +
                    "=" +
                    variantParameterValue
                );
            } else {
                return url;
            }
        };

        self.validateMaterialVariant = function (materialName, materialColor) {
            return (
                "variant" in self.materialSettingsDatabase[materialName] &&
                "color" in
                    self.materialSettingsDatabase[materialName]["variant"] &&
                materialColor in
                    self.materialSettingsDatabase[materialName]["variant"][
                        "color"
                    ]
            );
        };

        self.addUrlReferral = function (url) {
            let param_separator = url.includes("?") ? "&" : "?";
            return url + param_separator + "utm_source=mrbeam_device_frontend";
        };
    }

    ADDITIONAL_VIEWMODELS.push([
        MaterialSettingsViewModel,
        ["loginStateViewModel"],
        [
            /* ... */
        ],
    ]);
});
