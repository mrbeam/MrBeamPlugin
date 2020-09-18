/* global Snap */

//    Path convert - a snapsvg.io plugin to convert svg native elements to paths.
//    Copyright (C) 2015  Teja Philipp <osd@tejaphilipp.de>
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
    // just a helper
    var _p2s = /,?([achlmqrstvxz]),?/gi;
    var _convertToString = function (arr) {
        return arr.join(",").replace(_p2s, "$1");
    };
    var _isDefault = function (attrName, attrValue) {
        let defaults = {
            "alignment-baseline": "auto",
            "baseline-shift": "0px",
            clip: "auto",
            "clip-path": "none",
            "clip-rule": "evenodd",
            color: "rgb(0, 0, 0)",
            "color-interpolation": "srgb",
            "color-interpolation-filters": "linearrgb",
            "color-profile": "",
            "color-rendering": "auto",
            cursor: "auto",
            direction: "ltr",
            display: "inline",
            "dominant-baseline": "auto",
            "enable-background": "",
            fill: "rgb(0, 0, 0)",
            "fill-opacity": "1",
            "fill-rule": "nonzero",
            filter: "none",
            "flood-color": "rgb(0, 0, 0)",
            "flood-opacity": "1",
            "font-family": '"Helvetica Neue", Helvetica, Arial, sans-serif', // not really default value, but set in the html body tag
            "font-size": "",
            "font-size-adjust": "",
            "font-stretch": "100%",
            "font-style": "normal",
            "font-variant": "normal",
            "font-weight": "400",
            "glyph-orientation-horizontal": "",
            "glyph-orientation-vertical": "",
            "image-rendering": "auto",
            kerning: "",
            "letter-spacing": "normal",
            "lighting-color": "rgb(255, 255, 255)",
            "marker-end": "none",
            "marker-mid": "none",
            "marker-start": "none",
            mask: "none",
            opacity: "1",
            overflow: "visible",
            "pointer-events": "auto",
            "shape-rendering": "auto",
            "stop-color": "rgb(0, 0, 0)",
            "stop-opacity": "1",
            stroke: "none",
            "stroke-dasharray": "none",
            "stroke-dashoffset": "0px",
            "stroke-linecap": "butt",
            "stroke-linejoin": "miter",
            "stroke-miterlimit": "4",
            "stroke-opacity": "1",
            "stroke-width": "1px",
            "text-anchor": "start",
            "text-decoration": "none",
            "text-rendering": "auto",
            "unicode-bidi": "normal",
            visibility: "visible",
            "word-spacing": "0px",
            "writing-mode": "horizontal-tb",
            class: "",
            style: "clip-rule: evenodd;",
            transform: "matrix(1,0,0,1,0,0)",
        };
        return defaults[attrName] !== null && defaults[attrName] === attrValue;
    };

    Element.prototype.toPath = function (with_attrs) {
        var old_elem = this;
        if (
            old_elem.type !== "circle" &&
            old_elem.type !== "rect" &&
            old_elem.type !== "ellipse" &&
            old_elem.type !== "line" &&
            old_elem.type !== "polygon" &&
            old_elem.type !== "polyline" &&
            old_elem.type !== "path"
        )
            return;

        var d = old_elem.getPathAttr(with_attrs);

        // Create new path element
        var new_path_attributes = {};

        //set attributes that should be copied to new path
        var attrs = with_attrs;
        if (attrs === undefined) {
            // All attributes that path element can have
            attrs = [
                "requiredFeatures",
                "requiredExtensions",
                "systemLanguage",
                "id",
                "xml:base",
                "xml:lang",
                "xml:space",
                "clip",
                "clip-path",
                "clip-rule",
                "fill",
                "fill-opacity",
                "fill-rule",
                "filter",
                "flood-color",
                "flood-opacity",
                "image-rendering",
                "marker-end",
                "marker-mid",
                "marker-start",
                "mask",
                "opacity",
                "overflow",
                "shape-rendering",
                "stop-color",
                "stop-opacity",
                "stroke",
                "stroke-dasharray",
                "stroke-dashoffset",
                "stroke-linecap",
                "stroke-linejoin",
                "stroke-miterlimit",
                "stroke-opacity",
                "stroke-width",
                "text-anchor",
                "text-decoration",
                "text-rendering",
                "unicode-bidi",
                "visibility",
                "class",
                "style",
                "externalResourcesRequired",
                "transform",
                "d",
                "pathLength",
            ];
        }

        // Copy attributes of old_element to path
        for (var attrIdx in attrs) {
            var attrName = attrs[attrIdx];
            var attrValue;
            if (attrName === "transform") {
                attrValue = old_elem.transform()["localMatrix"];
            } else {
                attrValue = old_elem.attr(attrName);
            }
            if (attrValue && !_isDefault(attrName, attrValue)) {
                new_path_attributes[attrName] = attrValue;
            }
        }

        if (d) {
            new_path_attributes.d = d;
        }
        // TODO? try catch snap errors here in case d is bogus. remove element, to avoid crashes in the conversion.
        let path = old_elem.paper.path(new_path_attributes);

        // get computed stroke of path and add as mb:color
        var stroke = old_elem.attr("stroke");
        if (stroke !== "none" && stroke !== undefined && stroke !== "") {
            path.attr({ "mb:color": Snap.getRGB(stroke).hex });
            //			console.log("Snap.getRGB: '" + Snap.getRGB(stroke).hex + "'");
        }

        return path;
    };

    /**
     * Creates a path in the same shape as the origin element
     * Supports rect, ellipse, circle, line, polyline, polygon and of course path
     *
     * based on
     * https://github.com/duopixel/Method-Draw/blob/master/editor/src/svgcanvas.js
     * Modifications: Timo (https://github.com/timo22345)
     *
     * @returns {path} path element
     */
    Element.prototype.getPathAttr = function () {
        var old_element = this;
        var d = "";

        var validRadius = function (val) {
            return isFinite(val) && val >= 0;
        };

        var validCoordinate = function (val) {
            return isFinite(val);
        };

        // Possibly the cubed root of 6, but 1.81 works best
        var num = 1.81;
        var tag = old_element.type;

        // TODO: capsule unit conversion and make it working for other units beside mm
        var convertMMtoPixel = function (val) {
            attrList = [
                "rx",
                "ry",
                "r",
                "cx",
                "cy",
                "x1",
                "x2",
                "y1",
                "y2",
                "x",
                "y",
                "width",
                "height",
            ];
            for (var attrIdx in attrList) {
                if (
                    val.attr(attrList[attrIdx]) !== null &&
                    val.attr(attrList[attrIdx]).indexOf("mm") > -1
                ) {
                    var tmp = parseFloat(val.attr(attrList[attrIdx])) * 3.5433;
                    val.attr(attrList[attrIdx], tmp);
                }
            }
        };

        convertMMtoPixel(old_element);

        switch (tag) {
            case "ellipse":
            case "circle":
                var rx = +parseFloat(old_element.attr("rx")),
                    ry = +parseFloat(old_element.attr("ry")),
                    cx = +parseFloat(old_element.attr("cx")),
                    cy = +old_element.attr("cy");
                if (tag === "circle") {
                    rx = ry = +old_element.attr("r");
                }

                // If 'x' and 'y' are not specified, then set both to 0. // CorelDraw is creating that sometimes
                if (!validCoordinate(cx)) cx = 0;
                if (!validCoordinate(cy)) cy = 0;

                d += _convertToString([
                    ["M", cx - rx, cy],
                    [
                        "C",
                        cx - rx,
                        cy - ry / num,
                        cx - rx / num,
                        cy - ry,
                        cx,
                        cy - ry,
                    ],
                    [
                        "C",
                        cx + rx / num,
                        cy - ry,
                        cx + rx,
                        cy - ry / num,
                        cx + rx,
                        cy,
                    ],
                    [
                        "C",
                        cx + rx,
                        cy + ry / num,
                        cx + rx / num,
                        cy + ry,
                        cx,
                        cy + ry,
                    ],
                    [
                        "C",
                        cx - rx / num,
                        cy + ry,
                        cx - rx,
                        cy + ry / num,
                        cx - rx,
                        cy,
                    ],
                    ["Z"],
                ]);
                break;
            case "path":
                d = old_element.attr("d");
                break;
            case "line":
                var x1 = parseFloat(old_element.attr("x1")),
                    y1 = parseFloat(old_element.attr("y1")),
                    x2 = parseFloat(old_element.attr("x2")),
                    y2 = old_element.attr("y2");
                d = "M" + x1 + "," + y1 + "L" + x2 + "," + y2;
                break;
            case "polyline":
                let points = old_element.attr().points;
                if (points && points.length > 0) {
                    d = "M" + old_element.attr().points.trim();
                }
                break;
            case "polygon":
                let pts = old_element.attr().points;
                //				if(pts && pts.length > 0){
                d = "M" + old_element.attr().points.trim() + "Z";
                //				}
                break;
            case "rect":
                var rx = parseFloat(old_element.attr("rx")),
                    ry = parseFloat(old_element.attr("ry")),
                    x = parseFloat(old_element.attr("x")),
                    y = parseFloat(old_element.attr("y")),
                    w = parseFloat(old_element.attr("width")),
                    h = parseFloat(old_element.attr("height"));

                // Validity checks from http://www.w3.org/TR/SVG/shapes.html#RectElement:
                // If 'x' and 'y' are not specified, then set both to 0. // CorelDraw is creating that sometimes
                if (!validCoordinate(x)) x = 0;
                if (!validCoordinate(y)) y = 0;
                // If neither ‘rx’ nor ‘ry’ are properly specified, then set both rx and ry to 0. (This will result in square corners.)
                if (!validRadius(rx) && !validRadius(ry)) {
                    rx = ry = 0;
                    // Otherwise, if a properly specified value is provided for ‘rx’, but not for ‘ry’, then set both rx and ry to the value of ‘rx’.
                } else if (validRadius(rx) && !validRadius(ry)) {
                    ry = rx;
                    // Otherwise, if a properly specified value is provided for ‘ry’, but not for ‘rx’, then set both rx and ry to the value of ‘ry’.
                } else if (validRadius(ry) && !validRadius(rx)) {
                    rx = ry;
                } else {
                    // cap values for rx/ry to half of w/h
                    rx = Math.min(rx, w / 2);
                    ry = Math.min(ry, h / 2);
                }

                if (!rx && !ry) {
                    d += _convertToString([
                        ["M", x, y],
                        ["L", x + w, y],
                        ["L", x + w, y + h],
                        ["L", x, y + h],
                        ["L", x, y],
                        ["Z"],
                    ]);
                } else {
                    var num = 2.19;
                    if (!ry) {
                        ry = rx;
                    }
                    d += _convertToString([
                        ["M", x, y + ry],
                        ["C", x, y + ry / num, x + rx / num, y, x + rx, y],
                        ["L", x + w - rx, y],
                        [
                            "C",
                            x + w - rx / num,
                            y,
                            x + w,
                            y + ry / num,
                            x + w,
                            y + ry,
                        ],
                        ["L", x + w, y + h - ry],
                        [
                            "C",
                            x + w,
                            y + h - ry / num,
                            x + w - rx / num,
                            y + h,
                            x + w - rx,
                            y + h,
                        ],
                        ["L", x + rx, y + h],
                        [
                            "C",
                            x + rx / num,
                            y + h,
                            x,
                            y + h - ry / num,
                            x,
                            y + h - ry,
                        ],
                        ["L", x, y + ry],
                        ["Z"],
                    ]);
                }
                break;
            default:
                break;
        }

        return d;
    };
});
