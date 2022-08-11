class WorkingAreaHelper {
    static getHumanReadableId(length) {
        length = length || 4;
        let out = [];
        for (let i = 0; i < length / 2; i++) {
            const cIdx = Math.floor(
                Math.random() * this.HUMAN_READABLE_IDS_CONSTANTS.length
            );
            const vIdx = Math.floor(
                Math.random() * this.HUMAN_READABLE_IDS_VOCALS.length
            );
            out.push(this.HUMAN_READABLE_IDS_CONSTANTS.charAt(cIdx));
            out.push(this.HUMAN_READABLE_IDS_VOCALS.charAt(vIdx));
        }
        return out.join("");
    }

    /**
     * Workaround of a firefox bug which breaks quotes / brackets.
     * Solution is pragmatic - just replacing bogus characters after things got wrong.
     *
     * @param {type} svgStr
     * @returns {string} svgStr
     */
    static fix_svg_string(svgStr) {
        // TODO: look for better solution to solve this Firefox bug problem
        svgStr = svgStr.replace('(\\"', "(");
        svgStr = svgStr.replace('\\")', ")");
        return svgStr;
    }

    static getHexColorStr(inputColor) {
        // TODO inputColor='none' => '#000000' <- this is a bug
        const c = new Color(inputColor);
        return c.getHex();
    }

    /**
     * Returns with what program and version the given svg file was created. E.g. 'coreldraw'
     *
     * @param fragment (result of Snaps .select() .selectAll() .parse(), ...
     * @returns {object} keys: generator, version
     */
    static getGeneratorInfo(fragment) {
        var gen = null;
        var version = null;
        var root_attrs;
        if (fragment.select("svg") === null) {
            root_attrs = fragment.node.attributes;
        } else {
            root_attrs = fragment.select("svg").node.attributes;
        }

        try {
            // detect BeamOS generated Files by attribute
            // <svg
            //    ...
            //    xmlns:mb="http://www.mr-beam.org"
            //    ...
            //    mb:beamOS_version="0.3.4"
            var beamOS_version = root_attrs["mb:beamOS_version"];
            if (beamOS_version !== undefined) {
                gen = "beamOS";
                version = version.value;
                //				console.log("Generator:", gen, version);
                return { generator: gen, version: version };
            }

            // detect Inkscape by attribute
            // <svg
            //    ...
            //    xmlns:sodipodi="http://sodipodi.sourceforge.net/DTD/sodipodi-0.dtd"
            //    xmlns:inkscape="http://www.inkscape.org/namespaces/inkscape"
            //    ...
            //    inkscape:version="0.92.4 (5da689c313, 2019-01-14)"
            //    sodipodi:docname="Mr. Beam Jack of Spades Project Cards Inkscape.svg">
            var inkscape_version = root_attrs["inkscape:version"];
            if (inkscape_version !== undefined) {
                gen = "inkscape";
                version = inkscape_version.value;
                //				console.log("Generator:", gen, version);
                return { generator: gen, version: version };
            }

            // <svg viewBox="0 0 500 500" xmlns="http://www.w3.org/2000/svg" xmlns:bx="https://boxy-svg.com">
            // if (root_attrs['xmlns:bx'] && root_attrs['xmlns:bx'].value.search("boxy-svg.com")>0) {
            //     return { generator: "boxy-svg", version: "unknown" };
            // }

            // detect Illustrator by comment (works with 'save as svg')
            // <!-- Generator: Adobe Illustrator 16.0.0, SVG Export Plug-In . SVG Version: 6.00 Build 0)  -->
            var children = fragment.node.childNodes;
            for (var i = 0; i < children.length; i++) {
                var node = children[i];
                if (node.nodeType === 8) {
                    // check for comment
                    if (node.textContent.indexOf("Illustrator") > -1) {
                        gen = "illustrator";
                        var matches = node.textContent.match(
                            /\d+\.\d+(\.\d+)*/g
                        );
                        version = matches.join("_");
                        //						console.log("Generator:", gen, version);
                        return { generator: gen, version: version };
                    }
                }
            }

            // detect Illustrator by data-name (for 'export as svg')
            if (root_attrs && root_attrs["data-name"]) {
                gen = "illustrator";
                version = "?";
                //				console.log("Generator:", gen, version);
                return { generator: gen, version: version };
            }

            // Affinity designer by Serif
            // <svg ... xmlns:serif="http://www.serif.com/" ...>
            if (
                root_attrs["xmlns:serif"] &&
                root_attrs["xmlns:serif"].value.search("serif.com") > 0
            ) {
                return { generator: "Serif Affinity", version: "unknown" };
            }

            // Vectornator (www.vectornator.io)
            // <svg ... xmlns:vectornator="http://vectornator.io" ...>
            if (
                root_attrs["xmlns:vectornator"] &&
                root_attrs["xmlns:vectornator"].value.search("vectornator.io") >
                    0
            ) {
                return { generator: "Vectornator", version: "unknown" };
            }

            // detect Corel Draw by comment
            // <!-- Creator: CorelDRAW X5 -->
            // or <!-- Creator: CorelDRAW -->
            var children = fragment.node.childNodes;
            for (var i = 0; i < children.length; i++) {
                var node = children[i];
                if (node.nodeType === 8) {
                    // check for comment
                    if (node.textContent.indexOf("CorelDRAW") > -1) {
                        gen = "coreldraw";
                        const match = node.textContent.match(
                            /(Creator: CorelDRAW) (\S+)/
                        );
                        version = match ? match[2] : "?";
                        //						console.log("Generator:", gen, version);
                        return { generator: gen, version: version };
                    }
                }
            }

            // detect Method Draw by comment
            // <!-- Created with Method Draw - http://github.com/duopixel/Method-Draw/ -->
            for (var i = 0; i < children.length; i++) {
                var node = children[i];
                if (node.nodeType === 8) {
                    // check for comment
                    if (node.textContent.indexOf("Method Draw") > -1) {
                        gen = "method draw";
                        version = "?";
                        //						console.log("Generator:", gen, version);
                        return { generator: gen, version: version };
                    }
                }
            }

            // detect Microsoft Visio generated svg
            // <svg ... xmlns:v="http://schemas.microsoft.com/visio/2003/SVGExtensions/" ...>
            if (
                root_attrs["xmlns:v"] &&
                root_attrs["xmlns:v"].value.search("microsoft.com/visio") > 0
            ) {
                let version = "unknown";
                const ns = root_attrs["xmlns:v"].value;
                const regex = /microsoft\.com\/visio\/(.+)\/SVGExtensions/gm;
                let m;

                while ((m = regex.exec(ns)) !== null) {
                    // This is necessary to avoid infinite loops with zero-width matches
                    if (m.index === regex.lastIndex) {
                        regex.lastIndex++;
                    }

                    // The result can be accessed through the `m`-variable.
                    m.forEach((match, groupIndex) => {
                        console.log(
                            `Found match, group ${groupIndex}: ${match}`
                        );
                        version = match;
                    });
                }
                return { generator: "Microsoft Visio", version: version };
            }

            // detect dxf.js generated svg
            // <!-- Created with dxf.js -->
            for (var i = 0; i < children.length; i++) {
                var node = children[i];
                if (node.nodeType === 8) {
                    // check for comment
                    if (node.textContent.indexOf("Created with dxf.js") > -1) {
                        gen = "dxf.js";
                        console.log("Generator:", gen, version);
                        return { generator: gen, version: version };
                    }
                }
            }
        } catch (e) {
            console.error(
                "Error while detecting svg generator and version:",
                e
            );
        }
        //			console.log("Generator:", gen, version);
        return { generator: "unknown", version: "unknown" };
    }

    static isBinaryData(str) {
        return /[\x00-\x08\x0E-\x1F]/.test(str);
    }

    static isEmptyFile(fragment) {
        // https://github.com/mrbeam/MrBeamPlugin/issues/787
        return fragment.node.querySelectorAll("svg > *").length <= 0;
    }

    static parseFloatTolerant(str) {
        return parseFloat(str.replace(",", "."));
    }

    /**
     * Parses two number values (float or int) from given string.
     * Tries to accept any comma and any delimiter between the two numbers
     * @param myString
     * @returns {null|[float,float]}
     */
    static splitStringToTwoValues(myString) {
        let res = null;
        if (
            myString &&
            !(myString.match(/[a-zA-Z]/) || myString.match(/^\d+$/))
        ) {
            let m =
                myString.match(/^(-?\d+)[^0-9-]*(-?\d+)$/) ||
                myString.match(/(-?\d+[.,]?\d*)[^0-9-]*(-?\d+[.,]?\d*)/);
            if (m) {
                let x = WorkingAreaHelper.parseFloatTolerant(m[1]);
                let y = WorkingAreaHelper.parseFloatTolerant(m[2]);
                if (!isNaN(x) && !isNaN(y)) {
                    res = [x, y];
                }
            }
        }
        return res;
    }

    /**
     * Bound via keydown to an input field, this function increases or decreases the value with up/down arrow keys (and shift/alt combinations)
     * @param {object} event
     * @param {object} options - unit: string to attach after increment / decrement ('', 'mm', '%', '°', ...)
     *                         - delimiter: for dual value input fields (e.g. "200.1, 33.2" => ', ' is the delimiter)
     *                         - digits: for formatting output with toFixed(digits)
     *                         - alt: increment / decrement factor when alt key is pressed
     *                         - shift: increment / decrement factor when shift key is pressed
     * @returns {Boolean} - false if up/down arrow was event.keyCode. Useful to control event bubbling / default prevention.
     */
    static arrowKeys(event, options = {}) {
        options.unit = options.unit || "";
        options.delimiter = options.delimiter || null;
        options.digits =
            !isNaN(options.digits) && options.digits >= 0 ? options.digits : 1;
        options.alt = options.alt || 0.1;
        options.shift = options.shift || 10;
        if (
            event.keyCode === 37 &&
            event.altKey &&
            event.target.nodeName === "INPUT"
        ) {
            event.cancelBubble = true;
            event.returnValue = false;
            event.preventDefault();
            console.info("Catched Alt-LeftArrow and prevented 'browser back'.");
        }

        if (event.keyCode === 38 || event.keyCode === 40) {
            // arrowUp, arrowDown
            event.preventDefault();
            // remember caret position
            const selStart = event.target.selectionStart;
            const selEnd = event.target.selectionEnd;
            let cursorShift = 0;
            let val = event.keyCode === 38 ? 1 : -1;
            if (event.altKey) {
                val = val * options.alt;
            }
            if (event.shiftKey) {
                val = val * options.shift;
            }
            if (options.delimiter === null) {
                const newVal =
                    WorkingAreaHelper.parseFloatTolerant(event.target.value) +
                    val;
                event.target.value = `${newVal.toFixed(options.digits)} ${
                    options.unit
                }`;
            } else {
                const v = event.target.value;
                let parts = this._getSubstringAtIndex(
                    v,
                    selStart,
                    options.delimiter
                );
                const newV1 = (parseFloat(parts[1]) + val).toFixed(
                    options.digits
                );
                event.target.value = `${parts[0]}${newV1}${parts[2]}`;
                // maintain cursor position
                if (selStart > parts[0].length) {
                    cursorShift = newV1.length - parts[1].length;
                }
            }
            // restore caret position
            event.target.selectionStart = selStart + cursorShift;
            event.target.selectionEnd = selEnd + cursorShift;
            return false; // swallow the default action
        }
        return true;
    }

    static _getSubstringAtIndex(input, index, delimiter = "[^a-zA-Z0-9.,]+") {
        const iter = input.matchAll(delimiter);
        let idx1 = 0;
        let idx2 = input.length;
        let del;
        while ((del = iter.next()) !== null) {
            if (del.done) break;
            if (del.value.index < index) {
                idx1 = del.value.index + del.value[0].length;
            } else {
                idx2 = del.value.index;
                break;
            }
        }
        const strBefore = input.substring(0, idx1);
        const v1 = input.substring(idx1, idx2);
        const strAfter = input.substring(idx2);
        //console.debug("idx, idx1 -> idx2", index, idx1, idx2);
        return [strBefore, v1, strAfter];
    }

    /**
     * Estimates the job run time based on path length, img histograms and job parameters
     *
     * @param {object} gcLengthSummary
     * @param {object} vectorData
     * @param {object} engravingData
     * @param {object} machineData
     * @returns {object} modified gcLengthSummary, durations are added
     */
    static get_estimated_gcode_duration(
        gcLengthSummary,
        vectorData,
        engravingData,
        machineData
    ) {
        // mechanical gantry parameters
        const workingAreaWidth = machineData.workingAreaWidth;
        const workingAreaHeight = machineData.workingAreaHeight;
        const maxFeedrate = machineData.maxFeedrateXY; // mm/min
        const maxAcceleration = machineData.accelerationXY; // mm/s²
        const variance = 0.07;

        // 1. Vectors
        // Principle:
        // Iterate over each stroke color and sum up...
        // time for moving along the path with the color's speed
        // time for positioning moves with maximum machine speed.
        // Acceleration is ignored in this estimation.
        let vector_lookup = {};
        vectorData.forEach(
            (d) =>
                (vector_lookup[d.color] = {
                    feedrate: d.feedrate,
                    passes: d.passes,
                    pierce_time: d.pierce_time,
                })
        );

        let sumVectorDur = 0;
        Object.keys(gcLengthSummary.vectors).forEach(function (color) {
            let duration = 0;
            const vd = vector_lookup[color];
            if (vd) {
                // Time for moving on the colored path
                duration = WorkingAreaHelper.get_gcode_path_duration_in_seconds(
                    gcLengthSummary.vectors[color].lengthInMM,
                    vd.feedrate,
                    vd.passes,
                    vd.pierce_time
                );
                // Time for positioning moves between paths of the same color
                duration += WorkingAreaHelper.get_gcode_path_duration_in_seconds(
                    gcLengthSummary.vectors[color].positioningInMM,
                    maxFeedrate,
                    1,
                    0
                );
            }
            gcLengthSummary.vectors[color].duration = { raw: duration };
            sumVectorDur += duration;
        });

        // 2. Rasters
        // Principle:
        // Iterate over each rastered bitmap cluster and sum up:
        //   Linefeed durations incl. overshoot travel (max machine speed)
        //   Acceleration duration: time for the total necessary acceleration, summed up across the whole bitmap
        //   Histogram duration: time for the total travel of each pixel brightness 0-254, 255 will be skipped
        // Assumptions:
        //   White pixels on the outside of the image are skipped, inside they are traveled with maximum machine speed
        const minSpeed = Math.min(
            engravingData.speed_black,
            engravingData.speed_white
        );
        const maxSpeed = Math.max(
            engravingData.speed_black,
            engravingData.speed_white
        );

        let sumBitmapDur = 0;
        if (engravingData.engraving_enabled) {
            gcLengthSummary.bitmaps.forEach(function (b, idx) {
                // basics
                const lineCount = b.h / engravingData.line_distance;
                const lineWidth = b.w;

                // Linefeed duration
                const linefeedLength =
                    b.h +
                    lineCount * (engravingData.extra_overshoot ? 3 * 2 : 1); // assumption: extra overshoot move is 6mm per line, standard 1mm
                const linefeedPathDur = WorkingAreaHelper.get_gcode_path_duration_in_seconds(
                    linefeedLength,
                    maxFeedrate,
                    engravingData.eng_passes,
                    0
                );

                const linefeedAccelerationDur =
                    lineCount *
                    WorkingAreaHelper.get_acceleration_duration_in_seconds(
                        engravingData.speed_white,
                        maxAcceleration
                    );

                const linefeedDur = Math.max(
                    linefeedPathDur,
                    linefeedAccelerationDur
                );

                // acceleration duration
                const deltaV =
                    (b.totalBrightnessChange * Math.abs(maxSpeed - minSpeed)) /
                    255; // feedrate difference of one brightness step
                const accelerationDur = WorkingAreaHelper.get_acceleration_duration_in_seconds(
                    deltaV,
                    maxAcceleration
                );

                // histogram duration
                let histogramDur = 0;
                let histogramLength = 0;
                for (
                    let brightness = 0;
                    brightness < b.histogram.length;
                    brightness++
                ) {
                    let pixelAmount = b.histogram[brightness];
                    let speed =
                        (Math.abs(minSpeed - maxSpeed) * brightness) / 255 +
                        minSpeed;
                    if (brightness === 255) {
                        speed = maxFeedrate;
                        pixelAmount -= b.whitePixelsOutside; // White pixels (brightness===255) are always skipped (means not lasered)!
                    }
                    const length = pixelAmount * engravingData.beam_diameter;
                    histogramLength += length;
                    histogramDur += WorkingAreaHelper.get_gcode_path_duration_in_seconds(
                        length,
                        speed,
                        engravingData.eng_passes,
                        engravingData.pierce_time
                    );
                }
                // engraving mode correction factor
                let modeCorrection = 1; // default: engraving_mode === "precise"
                if (engravingData.engraving_mode === "basic") {
                    modeCorrection = 1 + b.innerWhitePixelRatio * 0.25; // assumption. useless moves over inner white pixel are 25% more than in precise mode
                } else if (engravingData.engraving_mode === "fast") {
                    modeCorrection = 1;
                }

                const bitmapDur =
                    linefeedDur +
                    accelerationDur +
                    histogramDur * modeCorrection;
                sumBitmapDur += bitmapDur;
                gcLengthSummary.bitmaps[idx].duration = { raw: bitmapDur };
                gcLengthSummary.bitmaps[
                    idx
                ].histogramLengthInMM = histogramLength;
            });
        }

        // 3. Positioning moves
        // assumption: an average positioning move is half the diagonal of the working area
        // such an positioning move has to be done between each item (paths with same stroke color, bitmap)
        // additionally at the beginning and the end
        const avgPositioningLength =
            euclideanDistance([0, 0], [workingAreaWidth, workingAreaHeight]) /
            2;
        const itemsCount =
            Object.keys(gcLengthSummary.vectors).length +
            gcLengthSummary.bitmaps.length;
        const sumPosDur =
            WorkingAreaHelper.get_gcode_path_duration_in_seconds(
                avgPositioningLength,
                maxFeedrate,
                1,
                0
            ) *
            (itemsCount + 2); // +2 for begin and end of the job

        const sum = sumVectorDur + sumBitmapDur + sumPosDur;

        // the correction factor is determined by some real experiments.
        // It is chosen according to the total estimation length as longer estimations are more precise than shorter ones.
        const c = WorkingAreaHelper.get_jte_correction(sum);
        gcLengthSummary.estimationVariance = variance;
        gcLengthSummary.estimationCorrection = c;

        Object.keys(gcLengthSummary.vectors).forEach(function (color) {
            const vec = gcLengthSummary.vectors[color];
            WorkingAreaHelper.extend_duration_info(vec.duration, c, variance);
        });

        if (engravingData.engraving_enabled) {
            gcLengthSummary.bitmaps.forEach(function (b, idx) {
                const bmp = gcLengthSummary.bitmaps[idx];
                WorkingAreaHelper.extend_duration_info(
                    bmp.duration,
                    c,
                    variance
                );
            });
        }

        gcLengthSummary.total = {
            vector: { raw: sumVectorDur },
            raster: { raw: sumBitmapDur },
            positioning: { raw: sumPosDur },
            sum: { raw: sum },
        };
        Object.keys(gcLengthSummary.total).forEach(function (key) {
            const obj = gcLengthSummary.total[key];
            WorkingAreaHelper.extend_duration_info(obj, c, variance);
        });

        return gcLengthSummary;
    }

    /**
     * Calculates the duration of one path based on length, speed, passes, piercetime
     *
     * @param {Number} lengthInMM
     * @param {Number} feedrateInMMperMin
     * @param {Integer} passes
     * @param {Number} pierceTimeMS
     * @returns {Number}
     */
    static get_gcode_path_duration_in_seconds(
        lengthInMM,
        feedrateInMMperMin,
        passes,
        pierceTimeMS
    ) {
        const l = parseFloat(lengthInMM);
        const f = parseFloat(feedrateInMMperMin) / 60;
        const p = parseInt(passes);
        const pt = parseInt(pierceTimeMS) / 1000;
        return (l / f) * p + pt; // seconds
    }

    /**
     * Calculates the time needed to accelerate from v to v + deltaV where accerlation a is given
     *
     * @param {Number} deltaVinMMperMinute
     * @param {Number} accelerationMMperS
     * @returns {Number} seconds
     */
    static get_acceleration_duration_in_seconds(
        deltaVinMMperMinute,
        accelerationMMperS
    ) {
        const deltaV = deltaVinMMperMinute / 60;
        return deltaV / accelerationMMperS;
    }

    static get_jte_correction(durationInSeconds) {
        // correction factors, figured out by testing on mrbeam-7055
        const CORRECTION_FACTORS = {
            lt1m: 1.3,
            lt10m: 1.1,
            lt60m: 1.07,
            def: 1.04,
        };

        let factor = CORRECTION_FACTORS.def;

        if (durationInSeconds < 60) {
            factor = CORRECTION_FACTORS.lt1m;
        } else if (durationInSeconds < 60 * 10) {
            factor = CORRECTION_FACTORS.lt10m;
        } else if (durationInSeconds < 60 * 60) {
            factor = CORRECTION_FACTORS.lt60m;
        }

        return factor;
    }

    static apply_jte_variance(durationInSeconds, variance) {
        return {
            val: durationInSeconds,
            min: durationInSeconds * (1 - variance),
            max: durationInSeconds * (1 + variance),
            abs: durationInSeconds * variance,
        };
    }

    static extend_duration_info(obj, factor, variance) {
        const corrected = obj.raw * factor;
        const range = WorkingAreaHelper.apply_jte_variance(corrected, variance);
        obj.val = corrected;
        obj.range = range;
        obj.hr = formatFuzzyHHMM(range);
        return obj;
    }

    /* Get CSS Declarations of Quicktext fonts for embedding in SVG before rasterization
     *
     * @param {Set} whitelist List used for filtering result
     * @returns {Array} A list of css declarations
     */
    static getFontDeclarations = function (whitelist = null) {
        const result = [];
        const styleSheetArray = [...document.styleSheets];
        const fontRules = styleSheetArray
            .filter(
                (s) =>
                    s.href &&
                    (s.href.includes("quicktext-fonts.css") ||
                        s.href.includes("packed_plugins.css"))
            )
            .map((styleSheet) => {
                try {
                    return [...styleSheet.cssRules]
                        .filter(
                            (rule) =>
                                rule.constructor === CSSFontFaceRule &&
                                rule.style
                        )
                        .filter((rule) => {
                            if (whitelist === null) return true;
                            const fontname = rule.style
                                .getPropertyValue("font-family")
                                //                        .replace(/["']/g, "")
                                .trim();
                            return whitelist.has(fontname);
                        })
                        .forEach((rule) => result.push(rule.cssText));
                } catch (e) {
                    console.log(
                        "Access to stylesheet %s is denied. Ignoring...",
                        styleSheet.href
                    );
                }
            });
        return result;
    };

    static limitValue(fieldValue, maxValue) {
        return fieldValue < maxValue ? fieldValue : maxValue;
    }
}

WorkingAreaHelper.HUMAN_READABLE_IDS_CONSTANTS = "bcdfghjklmnpqrstvwxz";
WorkingAreaHelper.HUMAN_READABLE_IDS_VOCALS = "aeiouy";
window.WorkingAreaHelper = WorkingAreaHelper;
