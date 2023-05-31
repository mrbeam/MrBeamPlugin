/* global Snap, ClipperLib */

//    jsClipperAndSnap - a snapsvg.io plugin to include the jsclipper library. Purpose is boolean path clipping and to calculate path offsets.
//    Copyright (C) 2023  Teja Philipp <osd@tejaphilipp.de> based on the work of https://github.com/TNG/SnapToJsClipper
//    For jsclipper docs, see https://sourceforge.net/p/jsclipper/wiki/documentation/

Snap.plugin(function (Snap, Element, Paper, global) {
    /**
     *
     *
     */

    /**
     * Applies clipping to subject and clipping polygon
     *
     * @param {Array} subjectPath, in jsclipper format
     * @param {Array} clippingPath, in jsclipper format
     * @param {any} sss : not used
     * @param {ClipperLib.ClipType} clipType : {ctIntersection: 0, ctUnion: 1, ctDifference: 2, ctXor: 3};
     * @returns {Array} in jsclipper format
     */
    function makeClip(subjectPath, clippingPath, sss, clipType) {
        // scale up to maintain precision - jsclipper internally works with integers
        const scale = 1000;
        ClipperLib.JS.ScaleUpPaths(subjectPath, scale);
        ClipperLib.JS.ScaleUpPaths(clippingPath, scale);

        const clipper = new ClipperLib.Clipper();
        let output = new ClipperLib.Paths();
        const subj = { fillType: ClipperLib.PolyFillType.pftNonZero }; // ClipperLib.PolyFillType = {pftEvenOdd: 0, pftNonZero: 1, pftPositive: 2, pftNegative: 3};
        const clip = { fillType: ClipperLib.PolyFillType.pftNonZero };
        const delta = null;
        const miterLimit = 2.0;
        const joinType = ClipperLib.JoinType.jtRound; // ClipperLib.JoinType.jtSquare; ClipperLib.JoinType.jtRound; ClipperLib.JoinType.jtMiter;

        clipper.Clear();
        clipper.AddPaths(
            subjectPath,
            ClipperLib.PolyType.ptSubject,
            _isClosed(subjectPath)
        );
        clipper.AddPaths(
            clippingPath,
            ClipperLib.PolyType.ptClip,
            _isClosed(clippingPath)
        );
        // Actual offset operation
        clipper.Execute(clipType, output, subj.fillType, clip.fillType);

        //        // TODO figure out what this block was meant for or remove it.
        //        if (delta) {
        //            clipper.Clear();
        //            const paramDelta = _.round(delta, 3);
        //            const paramMiterLimit = _.round(miterLimit, 3);
        //            output = clipper.OffsetPaths(
        //                output,
        //                paramDelta,
        //                joinType,
        //                paramMiterLimit,
        //                autoFix
        //            ); // autoFix?
        //        }

        // scale down to original coordinates
        ClipperLib.JS.ScaleDownPaths(output, scale);

        return output;
    }

    /**
     * Calculates a path offset to shrink or blow up a path
     *
     * @param {Array} inputPolygons path in jsclipper format
     * @param {Number} offset positive numbers blow up, negative numbers shrink the path
     * @returns {Array} offsetted path in jsclipper format
     */
    function makePathOffset(inputPolygons, offset, options = {}) {
        options.joinType ||= ClipperLib.JoinType.jtRound; // ClipperLib.JoinType = {jtSquare: 0, jtRound: 1, jtMiter: 2}
        options.miterLimit ||= 2; // only for jtMiter, miterlimit is specified as a multiple of delta
        options.arcTolerance ||= 0.25;
        options.clean ||= true;
        options.cleandelta ||= 0.1; // 0.1 should be the appropriate delta in different cases
        options.simplify ||= true;

        // scale up to maintain precision - jsclipper internally works with integers
        const scale = 1000;
        ClipperLib.JS.ScaleUpPaths(inputPolygons, scale);

        // simplifying is optional
        if (options.simplify) {
            inputPolygons = ClipperLib.Clipper.SimplifyPolygons(
                inputPolygons,
                ClipperLib.PolyFillType.pftNonZero
            ); // or ClipperLib.PolyFillType.pftEvenOdd
        }

        // cleaning is optional
        if (options.clean) {
            inputPolygons = ClipperLib.JS.Clean(
                inputPolygons,
                options.cleandelta * scale
            );
        }

        // offsetting parameters
        var co = new ClipperLib.ClipperOffset(
            options.miterLimit,
            options.arcTolerance
        );
        co.AddPaths(
            inputPolygons,
            options.joinType,
            ClipperLib.EndType.etClosedPolygon
        );

        let outputPolygons = new ClipperLib.Paths();
        // var offsetted_paths = new ClipperLib.PolyTree();
        co.Execute(outputPolygons, offset * scale);

        // scale down to original coordinates
        ClipperLib.JS.ScaleDownPaths(outputPolygons, scale);

        return outputPolygons;
    }

    /**
     * read all 'path' element from a Snap.Element and create ClipperPolygons from each path's 'd' attribute
     *
     * @param {SnapElement} el
     * @param {Boolean} applyTransform : should the totalMatrix of the el applied before clipping?
     * @returns {Array}
     */
    function getClipperPolygons(el, applyTransform = true) {
        let polygons = [];
        if (el.type === "path") {
            const m = _getTotalMatrix(el, applyTransform);
            polygons.push(SVGPathToClipperPolygonsPM(el.attr("d"), m));
        } else {
            el.selectAll("path").forEach((p) => {
                const m = _getTotalMatrix(el, applyTransform);
                polygons.push(SVGPathToClipperPolygonsPM(p.attr("d"), m));
            });
        }
        polygons = polygons.flat();

        return polygons;
    }

    /**
     * Helper to get totalMatrix or null
     *
     * @param {SnapElement} el
     * @param {Boolean} applyTransform
     * @returns {SnapMatrix}
     */
    function _getTotalMatrix(el, applyTransform) {
        if (applyTransform) {
            return el.transform().totalMatrix;
        } else {
            return null;
        }
    }

    /**
     * Converts svg paths' d attibute to pure polygons in jsclipper format. Requires path_magic.js
     * jsclipper format of a polygon is an Array of Arrays, containing point objects: [[{X: ..., Y: ...}, ... ], ...]
     *
     * @param {String} d : d-attribute of a svg path
     * @param {Snap.Matrix} matrix : transform matrix to apply on poly coordinates
     * @returns {Array} : array of array of points
     */
    function SVGPathToClipperPolygonsPM(d, matrix = null) {
        const delta = 0.2; // precision to polygonize cubics, arcs, ...

        let paths = d
            .replace(/M/g, "|M")
            .split("|")
            .filter((p) => p !== ""); // split at moveTo
        paths = paths.map((path) => {
            let segments = Snap.parsePathString(path.trim());
            segments = Snap.path.toAbsolute(segments);
            return segments;
        });

        const polygons = [];
        paths.forEach((segment) => {
            // mrbeam.path is the path_magic.js lib
            // We're using the path_magic.js parse, as it handles all curves (CQSTA) and polygonizes them properly.
            let segArr = mrbeam.path.parse(segment, delta); // returns lower case coord keys: [{x: ..., y: ...}, ...]
            if (matrix !== null) {
                const m = [
                    matrix.a,
                    matrix.b,
                    matrix.c,
                    matrix.d,
                    matrix.e,
                    matrix.f,
                ];
                segArr = mrbeam.path.transform(segArr, m);
            }

            segArr.forEach((p) => {
                polygons.push(p);
            });

            // basically everything is already done now. This just transforms path_magic.js format into jsclipper format.
            //###const jsclipperPolygons = mrbeam.path.pm_to_jsclipper(segArr, 1);
            //###jsclipperPolygons.forEach(p => { polygons.push(p) });
        });

        return polygons;
    }

    /**
     * generates a svg path d attribute from a jsclipper style polygon
     *
     * @param {Array} poly : polygon in jsclipper format
     * @returns {String} : d attribute of svg path
     */
    function clipperPolygonsToSVGPath(poly) {
        let path = "",
            d;
        poly.forEach((p) => {
            d = "M" + p[0].X + ", " + p[0].Y;
            p.slice(1, p.length + 1).forEach((c) => {
                d += "L" + c.X + ", " + c.Y;
            });
            d += "Z";
            path += d;
        });
        if (path.trim() === "Z") path = "";

        return path;
    }

    /**
     * compares first and last point of a jsclipper polygon
     *
     * @param {type} poly in jsclipper format
     * @returns {Boolean}
     */
    function _isClosed(poly) {
        const startPoint = poly[0];
        const endPoint = poly[poly.length - 1];

        const isClosed =
            startPoint.X === endPoint.X && startPoint.Y === endPoint.Y;

        return isClosed;
    }

    Element.prototype.getAllPaths = function () {
        return clipperPolygonsToSVGPath(this.getClipperPolygons());
    };

    Element.prototype.getClipperPolygons = function () {
        return getClipperPolygons(this);
    };

    /**
     * crops an element to fit into boundaries
     *
     * @param {Array} bounds : [left, bottom, right, top]
     * @returns {String} d attribute
     */
    Element.prototype.crop = function (bounds) {
        const subjectPolygons = getClipperPolygons(this);
        const clipPolygons = [
            [
                { X: bounds[0], Y: bounds[1] },
                { X: bounds[2], Y: bounds[1] },
                { X: bounds[2], Y: bounds[3] },
                { X: bounds[0], Y: bounds[3] },
                { X: bounds[0], Y: bounds[1] },
            ],
        ];
        return clipperPolygonsToSVGPath(
            makeClip(
                subjectPolygons,
                clipPolygons,
                [[]],
                ClipperLib.ClipType.ctIntersection
            )
        );
    };

    /**
     * calculates boolean intersection of this element with another
     *
     * @param {SnapElement} clip the clipping snapsvg path element
     * @returns {String} d attribute
     */
    Element.prototype.intersectClip = function (clip) {
        const subjectPolygons = getClipperPolygons(this);
        const clipPolygons = getClipperPolygons(clip);
        return clipperPolygonsToSVGPath(
            makeClip(
                subjectPolygons,
                clipPolygons,
                [[]],
                ClipperLib.ClipType.ctIntersection
            )
        );
    };

    /**
     * calculates boolean union of this element with another
     *
     * @param {SnapElement} clip the snapsvg path element to melt together
     * @returns {String} d attribute
     */
    Element.prototype.unionClip = function (clip) {
        const subjectPolygons = getClipperPolygons(this);
        const clipPolygons = getClipperPolygons(clip);
        return clipperPolygonsToSVGPath(
            makeClip(
                subjectPolygons,
                clipPolygons,
                [[]],
                ClipperLib.ClipType.ctUnion
            )
        );
    };

    /**
     * calculates boolean difference of this element with another
     *
     * @param {SnapElement} clip the clipping snapsvg path element
     * @returns {String} d attribute
     */
    Element.prototype.differenceClip = function (clip) {
        const subjectPolygons = getClipperPolygons(this);
        const clipPolygons = getClipperPolygons(clip);
        return clipperPolygonsToSVGPath(
            makeClip(
                subjectPolygons,
                clipPolygons,
                [[]],
                ClipperLib.ClipType.ctDifference
            )
        );
    };

    /**
     * calculates boolean exclusive or of this element with another
     *
     * @param {SnapElement} clip the clipping snapsvg path element
     * @returns {String} d attribute
     */
    Element.prototype.xorClip = function (clip) {
        const subjectPolygons = getClipperPolygons(this);
        const clipPolygons = getClipperPolygons(clip);
        return clipperPolygonsToSVGPath(
            makeClip(
                subjectPolygons,
                clipPolygons,
                [[]],
                ClipperLib.ClipType.ctXor
            )
        );
    };

    /**
     * generates offset path by adding the value of the offset parameter to the path
     * ClipperLib.JoinType = {jtSquare: 0, jtRound: 1, jtMiter: 2}
     *
     * @param {Numeric} offset : offset to be applied on the path element
     * @param {Object} options : defaults are {joinType = 1 (round), miterLimit = 2, arcTolerance = 0.25, clean = true, cleandelta = 0.1, simplify = true}
     * @param {boolean} replacePath : replace this element with the offsetted path, default=false
     * @returns {Object} : the new path
     */
    Element.prototype.pathOffset = function (
        offset,
        options = {},
        replacePath = false
    ) {
        let elem = this;
        if (elem.type !== "path") {
            console.error(
                `pathOffset() is not supporting element ${elem.type}. Skip!`
            );
            return;
        }

        const inputPoly = getClipperPolygons(this);
        const offsettedPolys = makePathOffset(inputPoly, offset, options);
        const offsettedPathD = clipperPolygonsToSVGPath(offsettedPolys);

        if (replacePath) {
            const originalD = elem.attr("mb:original_d") || elem.attr("d");
            elem.attr({ d: offsettedPathD, "mb:original_d": originalD });
        }
        return offsettedPathD;
    };

    Element.prototype._test_pathOffset = function (max, step) {
        const elem = this;
        const h = elem.getBBox().height;
        const dist = h + max * 2 + 3;

        // blow up
        for (let i = 1; i <= max; i += step) {
            const d_jtRound = elem.pathOffset(i, { joinType: 1 });
            elem.paper.path(d_jtRound).attr({
                fill: "none",
                stroke: "#999900",
                transform: `translate(0, 0)`,
            });
            const d_jtSquare = elem.pathOffset(i, { joinType: 0 });
            elem.paper.path(d_jtSquare).attr({
                fill: "none",
                stroke: "#009900",
                transform: `translate(0, ${-dist})`,
            });
            const d_jtMiter = elem.pathOffset(i, { joinType: 2 });
            elem.paper.path(d_jtMiter).attr({
                fill: "none",
                stroke: "#ff9900",
                transform: `translate(0, ${dist})`,
            });
        }

        // shrink
        for (let i = 1; i <= max; i += step) {
            const d_jtRound = elem.pathOffset(-i, { joinType: 1 });
            elem.paper.path(d_jtRound).attr({
                fill: "none",
                stroke: "#999999",
                transform: `translate(0, 0)`,
            });
            const d_jtSquare = elem.pathOffset(-i, { joinType: 0 });
            elem.paper.path(d_jtSquare).attr({
                fill: "none",
                stroke: "#009999",
                transform: `translate(0,${-dist})`,
            });
            const d_jtMiter = elem.pathOffset(-i, { joinType: 2 });
            elem.paper.path(d_jtMiter).attr({
                fill: "none",
                stroke: "#ff9999",
                transform: `translate(0, ${dist})`,
            });
        }
    };
});
