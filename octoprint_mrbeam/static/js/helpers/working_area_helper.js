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
}

WorkingAreaHelper.HUMAN_READABLE_IDS_CONSTANTS = "bcdfghjklmnpqrstvwxz";
WorkingAreaHelper.HUMAN_READABLE_IDS_VOCALS = "aeiouy";
window.WorkingAreaHelper = WorkingAreaHelper;
