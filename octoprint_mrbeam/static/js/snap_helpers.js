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
    // just a helper
    Snap.path.merge_bbox = function (bb1, bb2) {
        let r = _.clone(bb1);
        r.x = Math.min(bb2.x, bb1.x);
        r.y = Math.min(bb2.y, bb1.y);
        r.x2 = Math.max(bb2.x2, bb1.x2);
        r.y2 = Math.max(bb2.y2, bb1.y2);
        r.w = r.x2 - r.x;
        r.h = r.y2 - r.y;
        r.width = r.w;
        r.height = r.h;
        return r;
    };

    /**
     *
     * @param {type} bb bounding box from el.getBBox()
     * @param {type} matrix
     * @returns {object} new BBox around the transformed element
     */
    Snap.path.getBBoxWithTransformation = function (bb, matrix) {
        let r = _.clone(bb);
        const ax = matrix.x(bb.x, bb.y);
        const ay = matrix.y(bb.x, bb.y);
        const bx = matrix.x(bb.x2, bb.y);
        const by = matrix.y(bb.x2, bb.y);
        const cx = matrix.x(bb.x2, bb.y2);
        const cy = matrix.y(bb.x2, bb.y2);
        const dx = matrix.x(bb.x, bb.y2);
        const dy = matrix.y(bb.x, bb.y2);
        r.x = Math.min(ax, bx, cx, dx);
        r.x2 = Math.max(ax, bx, cx, dx);
        r.y = Math.min(ay, by, cy, dy);
        r.y2 = Math.max(ay, by, cy, dy);

        r.w = Math.abs(r.x2 - r.x);
        r.h = Math.abs(r.y2 - r.y);
        r.width = r.w;
        r.height = r.h;
        return r;
    };

    Element.prototype.get_total_bbox = function () {
        const el = this;
        const mat = el.transform().totalMatrix;
        const bb = el.getBBox();
        return Snap.path.getBBoxWithTransformation(bb, mat);
    };
});
