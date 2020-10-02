//    SVG cleaner - a snapsvg.io plugin to normalize and clean SVGs.
//    Copyright (C) 2016  Florian Becker <florian@mr-beam.org>
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
     * deletes all unnecessary elements and normalizes other stuff
     *
     * @param {none}
     * @returns {undefined}
     */
    Element.prototype.clean = function () {
        var elem = this;

        var children = elem.children();
        if (children.length > 0) {
            for (var i = 0; i < children.length; i++) {
                var child = children[i];
                child.clean();
            }
        }

        if (elem.type.includes("metadata") || elem.type.includes("sodipodi")) {
            elem.remove();
        }

        for (var property in elem.attr()) {
            if (elem.attr().hasOwnProperty(property)) {
                if (
                    property.includes("sodipodi:") ||
                    property.includes("inkscape:") ||
                    property.includes("dc:") ||
                    property.includes("cc:") ||
                    property.includes("rdf:")
                ) {
                    elem.attr(property, "");
                }
            }
        }

        if (
            elem.type === "path" ||
            elem.type === "circle" ||
            elem.type === "ellipse" ||
            elem.type === "rect" ||
            elem.type === "line" ||
            elem.type === "polyline" ||
            elem.type === "polygon" ||
            elem.type === "path"
        ) {
            for (var property in elem.attr()) {
                if (elem.attr().hasOwnProperty(property)) {
                    if (property === "style") {
                        // entpackt den style attribute und entfernt default Werte
                        elem.unwrap_style_attr();
                    }
                }
            }

            if (!elem.attr().hasOwnProperty("stroke")) {
                var stroke = elem.attr("stroke");
                if (stroke !== "none") {
                    elem.attr("stroke", stroke);
                }
            }
            if (elem.attr("stroke") === "none") {
                elem.attr("stroke", "");
            }
        }
    };

    /**
     * extracts all non default style attributes and deletes it afterwards.
     *
     * @param {none}
     * @returns {undefined}
     */
    Element.prototype.unwrap_style_attr = function () {
        var elem = this;

        var defaults = {
            "baseline-shift": "baseline",
            "clip-path": "none",
            "clip-rule": "nonzero",
            color: "#000",
            "color-interpolation-filters": "linearRGB",
            "color-interpolation": "sRGB",
            direction: "ltr",
            display: "inline",
            "enable-background": "accumulate",
            fill: "#000",
            "fill-opacity": "1",
            "fill-rule": "nonzero",
            filter: "none",
            "flood-color": "#000",
            "flood-opacity": "1",
            "font-size-adjust": "none",
            "font-size": "medium",
            "font-stretch": "normal",
            "font-style": "normal",
            "font-variant": "normal",
            "font-weight": "normal",
            "glyph-orientation-horizontal": "0deg",
            "letter-spacing": "normal",
            "lighting-color": "#fff",
            marker: "none",
            "marker-start": "none",
            "marker-mid": "none",
            "marker-end": "none",
            mask: "none",
            opacity: "1",
            "pointer-events": "visiblePainted",
            "stop-color": "#000",
            "stop-opacity": "1",
            stroke: "none",
            "stroke-dasharray": "none",
            "stroke-dashoffset": "0",
            "stroke-linecap": "butt",
            "stroke-linejoin": "miter",
            "stroke-miterlimit": "4",
            "stroke-opacity": "1",
            "stroke-width": "1",
            "text-anchor": "start",
            "text-decoration": "none",
            "unicode-bidi": "normal",
            visibility: "visible",
            "word-spacing": "normal",
            "writing-mode": "lr-tb",
            // SVG 1.2 tiny properties
            "audio-level": "1",
            "solid-color": "#000",
            "solid-opacity": "1",
            "text-align": "start",
            "vector-effect": "none",
            "viewport-fill": "none",
            "viewport-fill-opacity": "1",
        };

        var style = elem.attr("style");
        style.split(";").forEach(function (item, index) {
            var attr = item.split(":");
            if (attr[0] in defaults && defaults[attr[0]] !== attr[1]) {
                elem.attr(attr[0], attr[1]);
                elem.attr("style", "");
            }
        });
    };
});
