/* global _, Snap */

//    Little snapsvg.io plugin with lots of small helpers.
//    Dependencies: Snap, lodash
//    Copyright (C) 2021  Teja Philipp <osd@tejaphilipp.de>
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
    // Making accessible
    // https://github.com/adobe-webplatform/Snap.svg/blob/b365287722a72526000ac4bfcf0ce4cac2faa015/src/path.js#L44
    Snap.path.getBox = function (x, y, width, height) {
        return {
            x: x,
            y: y,
            width: width,
            w: width,
            height: height,
            h: height,
            x2: x + width,
            y2: y + height,
            cx: x + width / 2,
            cy: y + height / 2,
            r1: Math.min(width, height) / 2,
            r2: Math.max(width, height) / 2,
            r0: Math.sqrt(width * width + height * height) / 2,
            //            path: rectPath(x, y, width, height),
            vb: [x, y, width, height].join(" "),
        };
    };

    // just a helper
    Snap.path.merge_bbox = function (bb1, bb2) {
        const x = Math.min(bb2.x, bb1.x);
        const y = Math.min(bb2.y, bb1.y);
        const x2 = Math.max(bb2.x2, bb1.x2);
        const y2 = Math.max(bb2.y2, bb1.y2);
        const w = x2 - x;
        const h = y2 - y;
        return Snap.path.getBox(x, y, w, h);
    };

    Snap.path.enlarge_bbox = function (bbox, factorX, factorY, cropBB = null) {
        const enlargement_x = factorX / 2; // percentage of the width added to each side
        const enlargement_y = factorY / 2; // percentage of the height added to each side
        const deltaW = bbox.width * enlargement_x;
        const deltaH = bbox.height * enlargement_y;
        let x1 = bbox.x - deltaW;
        let x2 = bbox.x2 + deltaW;
        let y1 = bbox.y - deltaH;
        let y2 = bbox.y2 + deltaH;

        if (cropBB !== null) {
            x1 = Math.max(cropBB.x, x1);
            x2 = Math.min(cropBB.x2, x2);
            y1 = Math.max(cropBB.y, y1);
            y2 = Math.min(cropBB.y2, y2);
        }
        const w = x2 - x1;
        const h = y2 - y1;

        return Snap.path.getBox(x1, y1, w, h);
    };

    /**
     *
     * @param {type} bb bounding box from el.getBBox()
     * @param {type} matrix
     * @returns {object} new BBox around the transformed element
     */
    Snap.path.getBBoxWithTransformation = function (bb, matrix) {
        const ax = matrix.x(bb.x, bb.y);
        const ay = matrix.y(bb.x, bb.y);
        const bx = matrix.x(bb.x2, bb.y);
        const by = matrix.y(bb.x2, bb.y);
        const cx = matrix.x(bb.x2, bb.y2);
        const cy = matrix.y(bb.x2, bb.y2);
        const dx = matrix.x(bb.x, bb.y2);
        const dy = matrix.y(bb.x, bb.y2);

        const x = Math.min(ax, bx, cx, dx);
        const x2 = Math.max(ax, bx, cx, dx);
        const y = Math.min(ay, by, cy, dy);
        const y2 = Math.max(ay, by, cy, dy);
        const w = Math.abs(x2 - x);
        const h = Math.abs(y2 - y);

        return Snap.path.getBox(x, y, w, h);
    };

    Element.prototype.get_total_bbox = function () {
        const el = this;
        const mat = el.transform().totalMatrix;
        let bb;
        if (el.type === "tspan") {
            bb = Snap._.box(el.node.getBBox()); // work around snap's bug: https://github.com/adobe-webplatform/Snap.svg/blob/c8e483c9694517e24b282f8f59f985629f4994ce/src/element.js#L51
        } else {
            bb = el.getBBox(true); // true: getBBox without transforms as totalMatrix is applied afterwards;
        }
        return Snap.path.getBBoxWithTransformation(bb, mat);
    };

    Element.prototype.toWorkingAreaSvgStr = function (
        w,
        h,
        fontDecl = "",
        styles = "",
        filter = null
    ) {
        const elem = this;
        const paper = elem.paper;
        const att = paper.attr();
        // TODO Bug! viewbox is wrong when zoom / pan was used.
        const vb = ""; //att.viewBox.split(" ");
        const width = w; //vb[2];
        const height = h; // vb[3];
        if (Array.isArray(fontDecl)) {
            fontDecl = fontDecl.join("\n");
        }
        const namespaces = new Set([
            'xmlns="http://www.w3.org/2000/svg"',
            'xmlns:xlink="http://www.w3.org/1999/xlink"',
        ]);
        Object.keys(att)
            .filter((key) => key.startsWith("xmlns"))
            .map((key) => `${key}="${att[key]}"`)
            .forEach((ns) => namespaces.add(ns));
        const defs = paper.select("defs").innerSVG();
        let elements = [];
        if (filter === null) {
            elements.push(elem);
        } else {
            elem.selectAll(filter).forEach((e) => elements.push(e));
        }
        const cnt = elements
            .map((e) => {
                const transform = e.transform().totalMatrix.toString();
                const clone = e.clone().attr("transform", transform);
                const str = clone.toRenderedElementString();
                clone.remove();
                return str;
            })
            .join("\n")
            .replaceAll('\\"', "'"); // <text style="font-family: \"Allerta Stencil\"; "> => <text style="font-family: 'Allerta Stencil'; ">
        const svg = `
<svg version="1.1"
    ${[...namespaces].join(" ")}
    width="${width}" height="${height}"
    viewBox="${att.viewBox}">
    <defs>
        ${defs}
        <style>${fontDecl}</style>
        <style>${styles}</style>
    </defs>
    ${cnt}
</svg>
`;

        return svg;
    };

    Element.prototype.toRenderedElementString = function () {
        const element = this;

        // Create a new parent element to hold the SVG
        const parentElement = document.createElement("div");

        // Append the parent element to the document body (but don't show it)
        parentElement.style.display = "none";
        parentElement.appendChild(element.node);

        // Append the element to the hidden parent element
        document.body.appendChild(parentElement);

        // Get innerHTML of the parent element
        const elementInnerHTML = parentElement.innerHTML;

        // Remove the parent element from the DOM
        document.body.removeChild(parentElement);

        return elementInnerHTML.toString();
    };

    Element.prototype.toWorkingAreaDataURL = function (
        w,
        h,
        fontDecl = "",
        styles = "",
        filter = null
    ) {
        if (window && window.btoa) {
            const elem = this;
            const svg = elem.toWorkingAreaSvgStr(
                w,
                h,
                fontDecl,
                styles,
                filter
            );
            const dataurl =
                "data:image/svg+xml;base64," +
                btoa(unescape(encodeURIComponent(svg)));
            return dataurl;
        } else {
            console.error("Browser not supported: (window.btoa not present).");
            return "";
        }
    };

    /*
     * @returns {Set} set of font names in use
     */
    Element.prototype.getUsedFonts = function () {
        const elem = this;
        let result = new Set();
        if (elem.type === "text") {
            const fnt = window.getComputedStyle(elem.node)["font-family"];
            result.add(fnt);
        }

        elem.selectAll("text").forEach((el) => {
            const fnt = window.getComputedStyle(el.node)["font-family"];
            result.add(fnt);
        });
        return result;
    };

    /**
     * Selects upstream in the DOM like https://developer.mozilla.org/en-US/docs/Web/API/Element/closest
     *
     * @param {String} selector : a css selector
     * @returns {Object} : a Snap Element or Snap Paper
     */
    Element.prototype.closest = function (selector) {
        const elem = this;
        const node = elem.node.closest(selector);
        return Snap._.wrap(node);
    };

    /**
     * Removes the stroke and its styling from vector elements and saves them in a 'stroke' key in the same element
     *
     * @returns {Object} : a Snap Element with no stroke
     */
    Element.prototype.removeStrokeDetails = function () {
        const element = this;
        const strokeStyle = $(element.node).getAllStylesIncluding("stroke");
        const strokeAttr = element.attr("stroke");
        element.stroke = {
            strokeStyling: strokeStyle,
            strokeAttr: strokeAttr,
        };
        strokeStyle.forEach(function (propertyValue, style) {
            $(element.node).setDefaultStyleValue(style);
        });
        element.attr("stroke", "none");
    };
});
