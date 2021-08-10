/* global _, Snap */

//    Little snapsvg.io plugin with lots of small helpers.
//    Dependencies: Snap, lodash
//    Copyright (C) 2021  Teja Philipp <osd@tejaphilipp.de>

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
        const bb = el.getBBox();
        return Snap.path.getBBoxWithTransformation(bb, mat);
    };
});
