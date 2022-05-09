/* global Snap */

//    Matrix Oven - a snapsvg.io plugin to apply & remove transformations from svg files.
//    Copyright (C) 2015  Teja Philipp <osd@tejaphilipp.de>
//
//    based on work by https://gist.github.com/timo22345/9413158
//    and https://github.com/duopixel/Method-Draw/blob/master/editor/src/svgcanvas.js
//
//    This program is free software: you can redistribute it and/or modify
//    it under the terms of the GNU Affero General Public License as
//    published by the Free Software Foundation, either version 3 of the
//    License, or (at your option) any later version.
//
//    This program is distributed in the hope that it will be useful,
//    but WITHOUT ANY WARRANTY; without even the implied warranty of
//    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
//    GNU Affero General Public License for more details.
//
//    You should have received a copy of the GNU Affero General Public License
//    along with this program.  If not, see <http://www.gnu.org/licenses/>.

Snap.plugin(function (Snap, Element, Paper, global) {
    /**
     * bakes transformations of the element and all sub-elements into coordinates
     *
     * @param {Matrix} correctionMatrix : useful for applying additional transformations
     * @param {boolean} toCubics : use only cubic path segments
     * @param {integer} dec : number of digits after decimal separator. defaults to 5
     * @returns {undefined}
     */
    Element.prototype.bake_subtree = function (
        callback,
        correctionMatrix,
        toCubics,
        dec
    ) {
        var elem = this;
        var own_transformation = elem.parent().transform().totalMatrix;
        elem.bake(callback, own_transformation.invert(), toCubics, dec);
    };

    /**
     * bakes transformations of the element and all sub-elements into coordinates
     *
     * @param {Matrix} correctionMatrix : useful for applying additional transformations
     * @param {boolean} toCubics : use only cubic path segments
     * @param {integer} dec : number of digits after decimal separator. defaults to 5
     * @returns {undefined}
     */
    Element.prototype.bake = function (
        callback,
        correctionMatrix,
        toCubics,
        dec
    ) {
        if (!window._matrixOven) {
            window._matrixOven = {
                done: 0,
                total: 0,
            };
            window._matrixOven.total = Math.max(1, this.selectAll("*").length);
        }

        var elem = this;
        if (elem.type === "#text") return;
        var ignoredElements = [];

        window._matrixOven.done += 1;
        let percent = Math.min(
            100,
            (window._matrixOven.done / window._matrixOven.total) * 100
        );
        if (callback && typeof callback === "function")
            callback(
                percent,
                window._matrixOven.done,
                window._matrixOven.total
            );

        //		if (!elem || (!elem.paper && (elem.type !== "text" && elem.type !== "tspan" && elem.type !== "#text"))){
        //			return ignoredElements;
        //		} // don't handle unplaced elements. this causes double handling.

        if (toCubics === undefined) toCubics = false;
        if (dec === undefined) dec = 5;
        if (correctionMatrix === undefined)
            correctionMatrix = Snap.matrix(1, 0, 0, 1, 0, 0);

        var children = elem.children();
        if (children.length > 0) {
            // callback(0, children.length);
            for (var i = 0; i < children.length; i++) {
                var child = children[i];
                if (child.type !== "#text") {
                    // ignore plain text between xml tags (whitespace, linebreaks, no-markup plain text)
                    var ie = child.bake(
                        callback,
                        correctionMatrix,
                        toCubics,
                        dec
                    );
                    ignoredElements = ignoredElements.concat(ie);
                }
            }

            // if an element has children, but itself attributes to transform (like image, text, tspan) we need to continue and transform the element itself
            if (
                elem.type !== "image" &&
                elem.type !== "text" &&
                elem.type !== "tspan"
            ) {
                // elem.attr({transform: ''}); // sets transform="matrix(1.0,0,1,0,0)
                elem.node.removeAttribute("transform"); // removes attribute completely.
                return ignoredElements;
            }
        }
        if (
            elem.type !== "circle" &&
            elem.type !== "rect" &&
            elem.type !== "ellipse" &&
            elem.type !== "line" &&
            elem.type !== "polygon" &&
            elem.type !== "polyline" &&
            elem.type !== "image" &&
            elem.type !== "path" &&
            elem.type !== "text" // tspan will be ignored, it does not support presentation attr transform
        ) {
            console.info("Ignoring element ", elem.type);
            ignoredElements.push(elem.type);
            return ignoredElements;
        }

        if (elem.type === "image") {
            var x = parseFloat(elem.attr("x")),
                y = parseFloat(elem.attr("y")),
                w = parseFloat(elem.attr("width")),
                h = parseFloat(elem.attr("height"));

            // Validity checks from http://www.w3.org/TR/SVG/shapes.html#RectElement:
            // If 'x' and 'y' are not specified, then set both to default=0. // CorelDraw is creating that sometimes
            if (!isFinite(x)) {
                console.log("Image: No x value -> using 0 (SVG default)");
                x = 0;
            }
            if (!isFinite(y)) {
                console.log("Image: No y value -> using 0 (SVG default)");
                y = 0;
            }
            var transform = elem.transform();
            var matrix = transform["totalMatrix"].add(correctionMatrix);
            var transformedX = matrix.x(x, y);
            var transformedY = matrix.y(x, y);
            var transformedW = matrix.x(x + w, y + h) - transformedX;
            var transformedH = matrix.y(x + w, y + h) - transformedY;

            elem.attr({
                x: transformedX,
                y: transformedY,
                width: transformedW,
                height: transformedH,
            });
            elem.node.removeAttribute("transform"); // prefer less attributes.

            if (transformedH < 0) {
                elem.attr({
                    style: "transform: scale(1,-1); transform-origin: top",
                    height: -transformedH,
                    y: -transformedY,
                });
            }
            return ignoredElements;
        }

        // text is not supported -> just set a total matrix as surrounding groups will be baked.
        // this makes the text at least engravable and displays it at correct position
        if (elem.type === "text") {
            //			if(elem.node.getCTM !== undefined){ // not necessary anymore after not treating #text nodes?
            var transform = elem.transform();
            var matrix = transform["totalMatrix"].add(correctionMatrix);
            elem.attr({ transform: matrix.toString() });
            //			}
            return ignoredElements;
        }

        var path_elem = elem.convertToPath();

        if (
            !path_elem ||
            path_elem.attr("d") === "" ||
            path_elem.attr("d") === null
        )
            path_elem.attr("d", "M 0 0");

        // Rounding coordinates to dec decimals
        if (dec || dec === 0) {
            dec = Math.min(Math.max(0, Math.floor(dec)), 15);
        } else {
            dec = false;
        }

        function r(num) {
            if (dec !== false) {
                return Math.round(num * Math.pow(10, dec)) / Math.pow(10, dec);
            } else {
                return num;
            }
        }

        var arr;
        var arr_orig;
        var d = path_elem.attr("d");
        d = (d || "").trim();

        // trying to catch and handle bug in Snap.svg
        // We know this issue with SVGs from Vectornator (https://www.vectornator.io/)
        // which creates SVG paths which use a plus sign as separator between parameters. Snap.svg can not handle this.
        // Therefore if the path does not contain any whitespace nor comma but some plus signs, we replace these by commas.
        // Example: "M129.122+146.728L491.004+152.024L491.004+179.68..." => "M129.122,146.728L491.004,152.024L491.004,179.68..."
        if (d.indexOf(" ") < 0 && d.indexOf(",") < 0 && d.indexOf("+") > 0) {
            let dOld = d;
            d = d.replaceAll("+", ",");
            arr = Snap.parsePathString(d);
            console.warn(
                "matrix_oven: Handled potential Snap.svg bug: Path contains no whitespace and no comma but plus signs. " +
                    "After replacing all '+' by ',' the new path is " +
                    arr.length +
                    "\n\noriginal d:\n" +
                    dOld +
                    "\n\nfixed d:\n" +
                    d
            );
        } else {
            arr = Snap.parsePathString(d);
        }

        if (!toCubics) {
            arr_orig = arr;
            arr = Snap.path.toAbsolute(arr);
        } else {
            arr = Snap.path.toCubic(arr); // implies absolute coordinates
            arr_orig = arr;
        }

        // Get the transformation matrix between SVG root element and current element
        var transform = path_elem.transform();
        var matrix = transform["totalMatrix"].add(correctionMatrix);

        // apply the matrix transformation on the path segments
        var j;
        var m = arr.length;
        var letter = "";
        var letter_orig = "";
        var x = 0;
        var y = 0;
        var new_segments = [];
        var pt = { x: 0, y: 0 };
        var pt_baked = {};
        var subpath_start = {};
        var prevX = 0;
        var prevY = 0;
        subpath_start.x = null;
        subpath_start.y = null;
        for (var i = 0; i < m; i++) {
            letter = arr[i][0].toUpperCase();
            letter_orig = arr_orig[i][0];
            new_segments[i] = [];
            new_segments[i][0] = arr[i][0];

            if (letter === "A") {
                x = arr[i][6];
                y = arr[i][7];

                pt.x = arr[i][6];
                pt.y = arr[i][7];
                new_segments[i] = _arc_transform(
                    arr[i][1],
                    arr[i][2],
                    arr[i][3],
                    arr[i][4],
                    arr[i][5],
                    pt,
                    matrix
                );
            } else if (letter !== "Z") {
                // parse other segs than Z and A
                for (j = 1; j < arr[i].length; j = j + 2) {
                    if (letter === "V") {
                        y = arr[i][j];
                    } else if (letter === "H") {
                        x = arr[i][j];
                    } else {
                        x = arr[i][j];
                        y = arr[i][j + 1];
                    }
                    pt.x = x;
                    pt.y = y;
                    pt_baked.x = matrix.x(pt.x, pt.y);
                    pt_baked.y = matrix.y(pt.x, pt.y);

                    if (letter === "V" || letter === "H") {
                        new_segments[i][0] = "L";
                        new_segments[i][j] = pt_baked.x;
                        new_segments[i][j + 1] = pt_baked.y;
                    } else {
                        new_segments[i][j] = pt_baked.x;
                        new_segments[i][j + 1] = pt_baked.y;
                    }
                }
            }
            if (
                (letter !== "Z" && subpath_start.x === null) ||
                letter === "M"
            ) {
                subpath_start.x = x;
                subpath_start.y = y;
            }
            if (letter === "Z") {
                x = subpath_start.x;
                y = subpath_start.y;
            }
        }

        // Convert all that was relative back to relative
        // This could be combined to above, but to make code more readable
        // this is made separately.
        var prevXtmp = 0;
        var prevYtmp = 0;
        subpath_start.x = "";
        for (i = 0; i < new_segments.length; i++) {
            letter_orig = arr_orig[i][0];
            if (
                letter_orig === "A" ||
                letter_orig === "M" ||
                letter_orig === "L" ||
                letter_orig === "C" ||
                letter_orig === "S" ||
                letter_orig === "Q" ||
                letter_orig === "T" ||
                letter_orig === "H" ||
                letter_orig === "V"
            ) {
                var len = new_segments[i].length;
                var lentmp = len;
                if (letter_orig === "A") {
                    // rounding arc parameters
                    // only x,y are rounded,
                    // other parameters are left as they are
                    // because they are more sensitive to rounding
                    new_segments[i][6] = r(new_segments[i][6]);
                    new_segments[i][7] = r(new_segments[i][7]);
                } else {
                    lentmp--;
                    while (--lentmp) {
                        new_segments[i][lentmp] = r(new_segments[i][lentmp]);
                    }
                }
                prevX = new_segments[i][len - 2];
                prevY = new_segments[i][len - 1];
            } else {
                if (letter_orig === "a") {
                    // same rounding treatment as above for arcs
                    prevXtmp = new_segments[i][6];
                    prevYtmp = new_segments[i][7];
                    new_segments[i][0] = letter_orig;
                    new_segments[i][6] = r(new_segments[i][6] - prevX);
                    new_segments[i][7] = r(new_segments[i][7] - prevY);
                    prevX = prevXtmp;
                    prevY = prevYtmp;
                } else if (
                    letter_orig === "m" ||
                    letter_orig === "l" ||
                    letter_orig === "c" ||
                    letter_orig === "s" ||
                    letter_orig === "q" ||
                    letter_orig === "t" ||
                    letter_orig === "h" ||
                    letter_orig === "v"
                ) {
                    var len = new_segments[i].length;
                    prevXtmp = new_segments[i][len - 2];
                    prevYtmp = new_segments[i][len - 1];
                    for (j = 1; j < len; j = j + 2) {
                        if (letter_orig === "h" || letter_orig === "v") {
                            new_segments[i][0] = "l";
                        } else {
                            new_segments[i][0] = letter_orig;
                        }
                        new_segments[i][j] = r(new_segments[i][j] - prevX);
                        new_segments[i][j + 1] = r(
                            new_segments[i][j + 1] - prevY
                        );
                    }
                    prevX = prevXtmp;
                    prevY = prevYtmp;
                }
            }
            if (
                (letter_orig.toLowerCase() !== "z" && subpath_start.x === "") ||
                letter_orig.toLowerCase() === "m"
            ) {
                subpath_start.x = prevX;
                subpath_start.y = prevY;
            }
            if (letter_orig.toLowerCase() === "z") {
                prevX = subpath_start.x;
                prevY = subpath_start.y;
            }
        }

        var d_str = _convertToString(new_segments);
        path_elem.attr({ d: d_str });
        //path_elem.attr({transform: ''});
        path_elem.node.removeAttribute("transform"); // prefer less attributes.
        //console.log("baked matrix ", matrix, " of ", path_elem.attr('id'));

        return ignoredElements;
    };

    /**
     * Helper to apply matrix transformations to arcs.
     * From flatten.js (https://gist.github.com/timo22345/9413158), modified a bit.
     *
     * @param {type} a_rh : r1 of the ellipsis in degree
     * @param {type} a_rv : r2 of the ellipsis in degree
     * @param {type} a_offsetrot : x-axis rotation in degree
     * @param {type} large_arc_flag : 0 or 1
     * @param {int} sweep_flag : 0 or 1
     * @param {object} endpoint with properties x and y
     * @param {type} matrix : transformation matrix
     * @returns {Array} : representing the transformed path segment
     */
    function _arc_transform(
        a_rh,
        a_rv,
        a_offsetrot,
        large_arc_flag,
        sweep_flag,
        endpoint,
        matrix
    ) {
        function NEARZERO(B) {
            return Math.abs(B) < 0.0000000000000001;
        }

        var m = []; // matrix representation of transformed ellipse
        var A;
        var B;
        var C; // ellipse implicit equation:
        var ac;
        var A2;
        var C2; // helpers for angle and halfaxis-extraction.
        var rh = a_rh;
        var rv = a_rv;

        a_offsetrot = a_offsetrot * (Math.PI / 180); // deg->rad
        var rot = a_offsetrot;

        // sin/cos helper (the former offset rotation)
        var s = Math.sin(rot);
        var c = Math.cos(rot);

        // build ellipse representation matrix (unit circle transformation).
        // the 2x2 matrix multiplication with the upper 2x2 of a_mat is inlined.
        m[0] = matrix.a * +rh * c + matrix.c * rh * s;
        m[1] = matrix.b * +rh * c + matrix.d * rh * s;
        m[2] = matrix.a * -rv * s + matrix.c * rv * c;
        m[3] = matrix.b * -rv * s + matrix.d * rv * c;

        // to implict equation (centered)
        A = m[0] * m[0] + m[2] * m[2];
        C = m[1] * m[1] + m[3] * m[3];
        B = (m[0] * m[1] + m[2] * m[3]) * 2.0;

        // precalculate distance A to C
        ac = A - C;

        // convert implicit equation to angle and halfaxis:
        // disabled intentionally
        if (false && NEARZERO(B)) {
            // there is a bug in this optimization: does not work for path below
            a_offsetrot = 0;
            //			 d="M0,350 l 50,-25
            //           a25,25 -30 0,1 50,-25 l 50,-25
            //           a25,50 -30 0,1 50,-25 l 50,-25
            //           a25,75 -30 0,1 50,-25 l 50,-25
            //           a25,100 -30 0,1 50,-25 l 50,-25"
            //			with matrix transform="scale(0.5,2.0)"
            A2 = A;
            C2 = C;
        } else {
            if (NEARZERO(ac)) {
                A2 = A + B * 0.5;
                C2 = A - B * 0.5;
                a_offsetrot = Math.PI / 4.0;
            } else {
                // Precalculate radical:
                var K = 1 + (B * B) / (ac * ac);

                // Clamp (precision issues might need this.. not likely, but better save than sorry)
                K = K < 0 ? 0 : Math.sqrt(K);

                A2 = 0.5 * (A + C + K * ac);
                C2 = 0.5 * (A + C - K * ac);
                a_offsetrot = 0.5 * Math.atan2(B, ac);
            }
        }

        // This can get slightly below zero due to rounding issues.
        // it's save to clamp to zero in this case (this yields a zero length halfaxis)
        A2 = A2 < 0 ? 0 : Math.sqrt(A2);
        C2 = C2 < 0 ? 0 : Math.sqrt(C2);

        // now A2 and C2 are half-axis:
        if (ac <= 0) {
            a_rv = A2;
            a_rh = C2;
        } else {
            a_rv = C2;
            a_rh = A2;
        }

        // If the transformation matrix contain a mirror-component
        // winding order of the ellise needs to be changed.
        if (matrix.a * matrix.d - matrix.b * matrix.c < 0) {
            sweep_flag = !sweep_flag ? 1 : 0;
        }

        // Finally, transform arc endpoint. This takes care about the
        // translational part which we ignored at the whole math-showdown above.
        var baked_x = matrix.x(endpoint.x, endpoint.y);
        var baked_y = matrix.y(endpoint.x, endpoint.y);

        // Radians back to degrees
        a_offsetrot = (a_offsetrot * 180) / Math.PI;

        var r = [
            "A",
            a_rh,
            a_rv,
            a_offsetrot,
            large_arc_flag,
            sweep_flag,
            baked_x,
            baked_y,
        ];
        return r;
    }

    // just a helper
    //todo double code here and in path_convert, simplify
    var _p2s = /,?([achlmqrstvxz]),?/gi;
    var _convertToString = function (arr) {
        return arr.join(",").replace(_p2s, "$1");
    };

    /**
     * Replaces an element with a path of same shape.
     * Supports rect, ellipse, circle, line, polyline, polygon and of course path
     * The element will be replaced by the path with same id.
     *
     * @returns {path}
     */
    Element.prototype.convertToPath = function () {
        var old_element = this;
        var path = old_element.toPath();
        old_element.before(path);
        old_element.remove();
        return path;
    };
});
