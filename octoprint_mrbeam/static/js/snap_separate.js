/* global _, Snap */

//    Little snapsvg.io plugin to convenient splitting of fragments.
//    Dependencies: Snap, lodash
//    Copyright (C) 2019  Teja Philipp <osd@tejaphilipp.de>
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
     * Separates a fragment into n fragments.
     * Separation is determined by the parse order. Structure is preserved for each resulting fragment.
     *
     * Supports rect, ellipse, circle, line, polyline, polygon, text, tspan and of course path
     * Doesn't support use, symbol (use unref.js to avoid problems)
     *
     * @param {int} max_parts max number of groups this element is splitted to. 0 means unlimited (default)
     *
     * @returns {array} svg snippets (empty means not separatable)
     */
    Element.prototype.separate_by_native_elements = function (max_parts = 0) {
        const old_element = this;
        let native_elements = old_element.get_native_elements();
        let buckets =
            max_parts > 0
                ? Math.min(native_elements.length, max_parts)
                : native_elements.length;
        if (buckets <= 1) {
            console.info("Not separatable.");
            return [];
        }
        let max_elem_per_bucket = Math.ceil(native_elements.length / buckets);
        const ne_ids = _.map(native_elements, "node_id");
        const id_sets = _.chunk(ne_ids, max_elem_per_bucket);

        return old_element.separate_by_ids(id_sets);
    };

    /**
     * Separates a fragment into n fragments.
     * Separation is determined by stroke color. Structure is preserved for each resulting fragment.
     *
     * Supports rect, ellipse, circle, line, polyline, polygon, text, tspan and of course path
     * Doesn't support use, symbol (use unref.js to avoid problems)
     *
     * @returns {array} svg snippets (empty means not separatable)
     */
    Element.prototype.separate_by_stroke_colors = function () {
        const old_element = this;
        let native_elements = old_element.get_native_elements();

        let by_color = {};
        for (let i = 0; i < native_elements.length; i++) {
            const e = native_elements[i];
            const col = e.stroke;
            by_color[col] = by_color[col] || [];
            by_color[col].push(e.node_id);
        }

        const id_sets = _.values(by_color);
        return old_element.separate_by_ids(id_sets);
    };

    /**
     * Separates a fragment into n fragments.
     * Separation is determined by center x of elements bounding box. Structure is preserved for each resulting fragment.
     *
     * Supports rect, ellipse, circle, line, polyline, polygon, text, tspan and of course path
     * Doesn't support use, symbol (use unref.js to avoid problems)
     *
     * @returns {array} svg snippets (empty means not separatable)
     */
    Element.prototype.separate_vertically = function () {
        const old_element = this;
        const bbox = old_element.getBBox();
        const mat = old_element.transform().localMatrix.invert();
        const delimiter = mat.x(bbox.cx, bbox.cy);
        let native_elements = old_element.get_native_elements();

        let left_right = {};
        for (let i = 0; i < native_elements.length; i++) {
            const e = native_elements[i];
            const lr = e.bbox.cx > delimiter ? "r" : "l";
            left_right[lr] = left_right[lr] || [];
            left_right[lr].push(e.node_id);
        }
        const id_sets = _.values(left_right);
        return old_element.separate_by_ids(id_sets);
    };

    /**
     * Separates a fragment into n fragments.
     * Separation is determined by center x of elements bounding box. Structure is preserved for each resulting fragment.
     *
     * Supports rect, ellipse, circle, line, polyline, polygon, text, tspan and of course path
     * Doesn't support use, symbol (use unref.js to avoid problems)
     *
     * @returns {array} svg snippets (empty means not separatable)
     */
    Element.prototype.separate_horizontally = function () {
        const old_element = this;
        const bbox = old_element.getBBox();
        const mat = old_element.transform().localMatrix.invert();
        const delimiter = mat.y(bbox.cx, bbox.cy); // TODO: apply old elements matrix.
        let native_elements = old_element.get_native_elements();

        let above_below = {};
        for (let i = 0; i < native_elements.length; i++) {
            const e = native_elements[i];
            const ab = e.bbox.cy < delimiter ? "a" : "b";
            above_below[ab] = above_below[ab] || [];
            above_below[ab].push(e.node_id);
        }
        const id_sets = _.values(above_below);
        return old_element.separate_by_ids(id_sets);
    };

    /**
     * Separates a fragment into n fragments.
     * Separate non overlapping elements. Structure is preserved for each resulting fragment.
     *
     * Supports rect, ellipse, circle, line, polyline, polygon, text, tspan and of course path
     * Doesn't support use, symbol (use unref.js to avoid problems)
     *
     * @param {function} cancel separation will be cacelled, if this function returns true.
     * @param {function} progress_cb called frequently with progress (percent) as parameter.
     *
     * @returns {array} svg snippets (empty means not separatable)
     */
    Element.prototype.separate_by_non_intersecting_bbox = function (
        cancel = null,
        progress_cb = null
    ) {
        const old_element = this;
        let native_elements = old_element.get_native_elements();
        let progress_counter = 0;
        const progress_total = native_elements.length * 0.01; // directly calculate result in percent

        let by_bbox = [];
        for (let i = 0; i < native_elements.length; i++) {
            progress_counter++;
            const e = native_elements[i];

            let merge_candidates = [];
            for (let j = 0; j < by_bbox.length; j++) {
                if (cancel && typeof cancel === "function" && cancel())
                    return [];

                let bbObj = by_bbox[j];
                if (Snap.path.isBBoxIntersect(e.bbox, bbObj.bbox)) {
                    merge_candidates.push(j); // just remember the index
                }
            }

            // and merge here
            let to_merge = _.pullAt(by_bbox, merge_candidates);
            let ids = _.flatten(_.map(to_merge, "ids")); // _.chain this
            ids.push(e.node_id);
            let bbs = _.map(to_merge, "bbox");
            bbs.push(e.bbox);
            let merged_bb = _.reduce(bbs, function (bb, bb2add) {
                if (!bb) return bb2add;
                return Snap.path.merge_bbox(bb, bb2add);
            });

            by_bbox.push({ bbox: merged_bb, ids: ids });
            if (progress_cb && typeof progress_cb === "function")
                progress_cb(progress_counter / progress_total);
        }

        const id_sets = _.map(by_bbox, "ids");
        return old_element.separate_by_ids(id_sets);
    };

    /////////////////// private //////////////////////////

    /**
     * Separates a fragment into n fragments. Base for all other separate_methods
     * Separation is splitting all native elements according to id_sets. Structure is preserved for each resulting fragment.
     *
     * Supports rect, ellipse, circle, line, polyline, polygon, text, tspan and of course path
     * Doesn't support use, symbol (use unref.js to avoid problems)
     *
     * @param {array^2} id_sets Array of Arrays with node ids. e.g.: [['path10', 'path11'],['path12','path13'],['rect20']]
     *
     * @returns {object} keys: parts Array of svg snippets, overflow boolean indicating limitation by max_parts
     */
    Element.prototype.separate_by_ids = function (id_sets) {
        if (id_sets.length <= 1) return { parts: [], overflow: false }; // avoids unnecessary cloning

        const max_results = 10;
        const old_element = this;
        const resulting_parts = Math.min(id_sets.length, max_results);
        const overflow = id_sets.length > max_results;
        if (overflow)
            console.log(
                `${id_sets.length} parts are too much. Limited split result to ${max_results}. `
            );
        let parts = [];
        for (let i = 0; i < resulting_parts; i++) {
            console.log(`separate_by_ids ${i}/${resulting_parts}`);
            const exclude_list = id_sets[i];
            if (exclude_list.length > 0) {
                let n = old_element.clone();
                //				n.remove_native_elements(exclude_list);
                n.mark_native_elements(exclude_list, "delete_me_marker");
                let deletables = n.selectAll(".delete_me_marker");
                //				console.log("deleting elements: " + deletables.length);
                deletables.remove();

                for (var j = 0; j < exclude_list.length; j++) {
                    var id = "#" + exclude_list[j];
                    old_element.selectAll(id).remove();
                    //					console.log("removed id " + id);
                }
                parts.push(n);
            }
        }

        if (overflow) {
            parts.push(old_element.clone());
        }

        return { parts: parts, overflow: overflow };
    };

    /**
     * Removes native elements (rect, ellipse, circle, line, polyline, polygon, text, tspan, path)
     * except an array of elements referenced by attribute 'mb:id'
     * Doesn't support use, symbol (use unref.js to avoid problems)
     *
     * @param {array} exclude_mbids Array of mbids which are excluded when removing native elements.
     *
     * @returns {undefined}
     */
    Element.prototype.remove_native_elements = function (exclude_mbids) {
        let items = this.selectAll(
            "path, circle, rect, image, ellipse, line, polyline, polygon, text, tspan"
        );
        for (let i = 0; i < items.length; i++) {
            let e = items[i];
            if (exclude_mbids.indexOf(e.attr("mb:id")) < 0) {
                //				e.remove();
                e.addClass("deleteMe");
            }
        }
        this.selectAll(".deleteMe").remove();
    };

    /**
     * Marks native elements with a class name (rect, ellipse, circle, line, polyline, polygon, text, tspan, path)
     * except an array of elements referenced by attribute 'mb:id'
     * Doesn't support use, symbol (use unref.js to avoid problems)
     *
     * @param {array} exclude_mbids Array of mbids which are excluded when removing native elements.
     * @param {string} class_name class name which will be added and used as a marker
     *
     * @returns {undefined}
     */
    Element.prototype.mark_native_elements = function (
        exclude_mbids,
        class_name
    ) {
        let items = this.selectAll(
            "path, circle, rect, image, ellipse, line, polyline, polygon, text, tspan"
        );
        for (let i = 0; i < items.length; i++) {
            let e = items[i];
            if (exclude_mbids.indexOf(e.attr("mb:id")) < 0) {
                //				e.remove();
                e.addClass(class_name);
            }
        }
    };

    /**
     * Collects all native elements (rect, ellipse, circle, line, polyline, polygon, text, tspan, path)
     * and stores original node.id to attribute 'mb:id'. Metadata like bbox, type, stroke, fill are stored as well.
     * Doesn't support use, symbol (use unref.js to avoid problems)
     *
     * @returns {array} Array of Objects
     */
    Element.prototype.get_native_elements = function () {
        let natives = [];
        let native_elements = this.selectAll(
            "path, circle, ellipse, rect, line, polyline, polygon, image, text, tspan"
        );
        for (let i = 0; i < native_elements.length; i++) {
            let ne = native_elements[i];
            let id = ne.node.id;
            if (id === "") {
                id = ne.id; // fallback, take from snap
                ne.node.setAttribute("id", id);
                ne.node.setAttribute("mb:id", id);
                //				console.log("fallback", id);
            }
            ne.attr("mb:id", id);
            natives.push({
                element: ne,
                node_id: ne.node.id,
                bbox: ne.getBBox(),
                type: ne.type,
                id: ne.id,
                stroke: ne.attr()["stroke"],
                fill: ne.attr()["fill"],
            });
        }
        return natives;
    };
});
