class WorkingAreaHelper {
    static versionCompare(v1, v2, options) {
        var lexicographical = options && options.lexicographical,
            zeroExtend = options && options.zeroExtend,
            v1parts = v1.split("."),
            v2parts = v2.split(".");

        function isValidPart(x) {
            return (lexicographical ? /^\d+[A-Za-z]*$/ : /^\d+$/).test(x);
        }

        if (!v1parts.every(isValidPart) || !v2parts.every(isValidPart)) {
            return NaN;
        }

        if (zeroExtend) {
            while (v1parts.length < v2parts.length) v1parts.push("0");
            while (v2parts.length < v1parts.length) v2parts.push("0");
        }

        if (!lexicographical) {
            v1parts = v1parts.map(Number);
            v2parts = v2parts.map(Number);
        }

        for (var i = 0; i < v1parts.length; ++i) {
            if (v2parts.length === i) {
                return 1;
            }

            if (v1parts[i] === v2parts[i]) {
            } else if (v1parts[i] > v2parts[i]) {
                return 1;
            } else {
                return -1;
            }
        }

        if (v1parts.length !== v2parts.length) {
            return -1;
        }

        return 0;
    }

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

    static get_estimated_gcode_duration(
        gc_length_summary,
        vector_data,
        engraving_data
    ) {
        // Vectors
        let vector_lookup = {};
        vector_data.forEach(
            (d) =>
                (vector_lookup[d.color] = {
                    feedrate: d.feedrate,
                    passes: d.passes,
                    pierce_time: d.pierce_time,
                })
        );

        // TODO: without material selected, vector_data is empty.

        let total_vector_duration = 0;
        Object.keys(gc_length_summary.vectors).forEach(function (col) {
            let duration = 0;
            const vd = vector_lookup[col];
            if (vd) {
                duration = WorkingAreaHelper.get_gcode_path_duration_in_seconds(
                    gc_length_summary.vectors[col].lengthInMM,
                    vd.feedrate,
                    vd.passes,
                    vd.pierce_time
                );
            }
            gc_length_summary.vectors[col].duration = duration;
            total_vector_duration += duration;
        });

        // Rasters
        const min_speed = Math.min(
            engraving_data.speed_black,
            engraving_data.speed_white
        );
        const max_speed = Math.max(
            engraving_data.speed_black,
            engraving_data.speed_white
        );
        const avg_speed =
            (engraving_data.speed_black + engraving_data.speed_white) / 2;
        let total_bitmap_duration = 0;
        gc_length_summary.bitmaps.forEach(function (b, idx) {
            const lineCount = b.h / engraving_data.line_distance;
            const lineWidth = engraving_data.extra_overshoot ? b.w + 3.5 : b.w; // assumption overshoot move is 3.5mm extra per line
            let whitePxFactor = 1 - b.whitePixelRatio; // engraving_mode === "precise" (default)
            if (engraving_data.engraving_mode === "basic") {
                whitePxFactor = 1 - b.whitePixelRatio / 3; // assumption: 66% of white px are between two black pixels
            }
            if (engraving_data.engraving_mode === "fast") {
                whitePxFactor = 1 - b.whitePixelRatio; // assumption: could be faster or worser
            }
            const brightnessChanges = b.brightnessChanges; // how often the speed changes and respectively piercetime is applied
            const l = (lineWidth * lineCount + b.h) * whitePxFactor;

            let histogramDuration = 0;
            for (
                let brightness = 0;
                brightness < b.histogram.length;
                brightness++
            ) {
                const pixelAmount = b.histogram[brightness];
                const length = pixelAmount * engraving_data.beam_diameter;
                const speed =
                    (Math.abs(min_speed - max_speed) * brightness) / 255 +
                    min_speed;
                histogramDuration += WorkingAreaHelper.get_gcode_path_duration_in_seconds(
                    length,
                    speed,
                    engraving_data.eng_passes,
                    engraving_data.pierce_time
                );
            }
            const avgDuration = WorkingAreaHelper.get_gcode_path_duration_in_seconds(
                l,
                avg_speed,
                engraving_data.eng_passes,
                engraving_data.pierce_time
            );
            gc_length_summary.bitmaps[idx].duration = avgDuration;
            gc_length_summary.bitmaps[idx].lengthInMM = l;
            total_bitmap_duration += avgDuration;
        });

        // Positioning moves // TODO get from machine settings
        const workingAreaWidth = 500;
        const workingAreaHeight = 390;
        const maxFeedrate = 3000;
        const avgPositioningLength =
            Math.sqrt(
                Math.pow(workingAreaWidth, 2) + Math.pow(workingAreaHeight, 2)
            ) / 2; // assumption: average positioning move is half the diagonal of the working area
        const itemsCount =
            Object.keys(gc_length_summary.vectors).length +
            gc_length_summary.bitmaps.length;
        const positioningDuration =
            WorkingAreaHelper.get_gcode_path_duration_in_seconds(
                avgPositioningLength,
                maxFeedrate,
                1,
                0
            ) * itemsCount;

        gc_length_summary.positioningDuration = positioningDuration;
        gc_length_summary.totalDuration =
            total_vector_duration + total_bitmap_duration + positioningDuration;

        return gc_length_summary;
    }

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
}

WorkingAreaHelper.HUMAN_READABLE_IDS_CONSTANTS = "bcdfghjklmnpqrstvwxz";
WorkingAreaHelper.HUMAN_READABLE_IDS_VOCALS = "aeiouy";
window.WorkingAreaHelper = WorkingAreaHelper;
