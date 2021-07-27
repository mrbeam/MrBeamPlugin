var mrbeam = mrbeam || {};

(function () {
    "use strict";

    ////////////////////////////
    // gcode_nextgen
    // version:
    var VERSION = "0.1";
    //
    //
    ////////////////////////////

    var mrbeam = window.mrbeam;
    mrbeam.path = {};
    var module = mrbeam.path;

    module.version = VERSION;

    function point(x, y) {
        return { x: x, y: y };
    }

    function peek(array) {
        return array[array.length - 1];
    }

    // integrate-adaptive-simpson
    // https://github.com/scijs/integrate-adaptive-simpson
    // (c) 2015 Scijs Authors. MIT License.
    function adsimp(f, a, b, fa, fm, fb, V0, tol, maxdepth, depth, state) {
        if (state.nanEncountered) {
            return NaN;
        }

        var h = b - a;
        var f1 = f(a + h * 0.25);
        var f2 = f(b - h * 0.25);

        // Simple check for NaN:
        if (Number.isNaN(f1)) {
            state.nanEncountered = true;
            return;
        }

        // Simple check for NaN:
        if (Number.isNaN(f2)) {
            state.nanEncountered = true;
            return;
        }

        var sl = (h * (fa + 4 * f1 + fm)) / 12;
        var sr = (h * (fm + 4 * f2 + fb)) / 12;
        var s2 = sl + sr;
        var err = (s2 - V0) / 15;

        if (depth > maxdepth) {
            state.maxDepthCount += 1;
            return s2 + err;
        } else if (Math.abs(err) < tol) {
            return s2 + err;
        } else {
            var m = a + h * 0.5;

            var V1 = adsimp(
                f,
                a,
                m,
                fa,
                f1,
                fm,
                sl,
                tol * 0.5,
                maxdepth,
                depth + 1,
                state
            );

            if (Number.isNaN(V1)) {
                state.nanEncountered = true;
                return NaN;
            }

            var V2 = adsimp(
                f,
                m,
                b,
                fm,
                f2,
                fb,
                sr,
                tol * 0.5,
                maxdepth,
                depth + 1,
                state
            );

            if (Number.isNaN(V2)) {
                state.nanEncountered = true;
                return NaN;
            }

            return V1 + V2;
        }
    }

    // integrate-adaptive-simpson
    // https://github.com/scijs/integrate-adaptive-simpson
    // (c) 2015 Scijs Authors. MIT License.
    function integrate(f, a, b, tol, maxdepth) {
        var state = {
            maxDepthCount: 0,
            nanEncountered: false,
        };

        if (tol === undefined) {
            tol = 1e-8;
        }
        if (maxdepth === undefined) {
            maxdepth = 20;
        }

        var fa = f(a);
        var fm = f(0.5 * (a + b));
        var fb = f(b);

        var V0 = ((fa + 4 * fm + fb) * (b - a)) / 6;

        var result = adsimp(f, a, b, fa, fm, fb, V0, tol, maxdepth, 1, state);

        if (state.maxDepthCount > 0 && console && console.warn) {
            console.warn(
                "integrate-adaptive-simpson: Warning: maximum recursion depth (" +
                    maxdepth +
                    ") reached " +
                    state.maxDepthCount +
                    " times"
            );
        }

        if (state.nanEncountered && console && console.warn) {
            console.warn(
                "integrate-adaptive-simpson: Warning: NaN encountered. Halting early."
            );
        }

        return result;
    }

    // --- rectangle

    module.rectangle = function (x, y, width, height) {
        var r = x + width;
        var b = y + height;

        return [
            { x: x, y: y },
            { x: x, y: b },
            { x: r, y: b },
            { x: r, y: y },
            { x: x, y: y },
        ];
    };

    // --- circle

    module.circle = function (cx, cy, r, delta) {
        // circumference
        var length = 2.0 * r * Math.PI;

        // number of segments
        var n = Math.ceil(length / delta) | 0;

        // allocate memory
        var pts = [];
        pts.length = n + 1;

        pts[0] = point(cx + r, cy);
        pts[n] = point(cx + r, cy);

        for (let i = 1; i < n; ++i) {
            var t = (i * 2.0 * Math.PI) / n;

            pts[i] = point(cx + r * Math.cos(t), cy + r * Math.sin(t));
        }

        return pts;
    };

    // --- ellipse

    module.ellipse = function (cx, cy, rx, ry, delta) {
        // approximate circumference
        var length = 2.0 * Math.PI * Math.sqrt((rx ** 2 + ry ** 2) / 2.0);

        // number of segments
        var n = Math.ceil(length / delta) | 0;

        // allocate memory
        var pts = [];
        pts.length = n + 1;

        pts[0] = point(cx + rx, cy);
        pts[n] = point(cx + rx, cy);

        for (let i = 1; i < n; ++i) {
            var t = (i * 2.0 * Math.PI) / n;

            pts[i] = point(cx + rx * Math.cos(t), cy + ry * Math.sin(t));
        }

        return pts;
    };

    // --- line

    module.line = function (x1, y1, x2, y2) {
        return [point(x1, y1), point(x2, y2)];
    };

    // --- quadratic bezier curves

    function quadraticCoefficients(x0, x1, x2) {
        return [x0, 2.0 * (x1 - x0), x0 - 2.0 * x1 + x2];
    }

    function quadraticDerivativeCoefficients(x0, x1, x2) {
        return [2.0 * (x1 - x0), 2.0 * (x0 - 2.0 * x1 + x2)];
    }

    function quadraticLength(p1, p2, p3, tolerance) {
        // Quadratic Bezier derivative function:
        //
        //   dx(t)/dt = adt0 + adt1 * t
        //   dy(t)/dt = bdt0 + bdt1 * t
        //
        //   with t = 0..1

        // calculate coefficients for x- and y-direction
        var adt = quadraticDerivativeCoefficients(p1.x, p2.x, p3.x);
        var bdt = quadraticDerivativeCoefficients(p1.y, p2.y, p3.y);

        var length = integrate(
            function (t) {
                var dx = adt[0] + adt[1] * t;
                var dy = bdt[0] + bdt[1] * t;

                return Math.sqrt(dx * dx + dy * dy);
            },
            0.0,
            1.0,
            tolerance
        );

        return length;
    }

    module.quadraticBezier = function (p1, p2, p3, delta) {
        // Quadratic Bezier function:
        //
        //   x(t) = a0 + a1 * t + a2 * t^2
        //   y(t) = b0 + b1 * t + b2 * t^2
        //
        //   with t = 0..1

        // calculate coefficients for x- and y-direction
        var a = quadraticCoefficients(p1.x, p2.x, p3.x);
        var b = quadraticCoefficients(p1.y, p2.y, p3.y);

        // calculate real curve length
        // ALTERNATIVE: direct distance P1->P2->P3
        var length = quadraticLength(p1, p2, p3, delta);

        // required number of segment
        var n = Math.ceil(length / delta) | 0;

        // divide parameter space
        var dt = 1.0 / n;

        // allocate memory for points
        var pts = [];
        pts.length = n + 1;

        // set first and last point explicit to avoid rounding errors
        pts[0] = p1;
        pts[n] = p3;

        // interpolate points
        for (let i = 1; i < n; ++i) {
            var t = i * dt;
            var t2 = t * t;

            pts[i] = {
                x: a[0] + a[1] * t + a[2] * t2,
                y: b[0] + b[1] * t + b[2] * t2,
            };
        }

        return pts;
    };

    // --- cubic bezier curves

    function cubicCoefficients(x0, x1, x2, x3) {
        return [
            x0,
            3.0 * (x1 - x0),
            3.0 * (x0 - 2.0 * x1 + x2),
            x3 - x0 + 3.0 * (x1 - x2),
        ];
    }

    function cubicDerivativeCoefficients(x0, x1, x2, x3) {
        return [
            3.0 * (x1 - x0),
            6.0 * (x0 - 2.0 * x1 + x2),
            3.0 * (x3 - x0) + 9.0 * (x1 - x2),
        ];
    }

    function cubicLength(p1, p2, p3, p4, tolerance) {
        // Cubic Bezier derivative function:
        //
        //   dx(t)/dt = da0 + da1 * t + da2 * t^2
        //   dy(t)/dt = db0 + db1 * t + db2 * t^2
        //
        //   with t = 0..1

        // calculate coefficients for x- and y-direction
        var adt = cubicDerivativeCoefficients(p1.x, p2.x, p3.x, p4.x);
        var bdt = cubicDerivativeCoefficients(p1.y, p2.y, p3.y, p4.y);

        length = integrate(
            function (t) {
                var t2 = t * t;

                var dx = adt[0] + adt[1] * t + adt[2] * t2;
                var dy = bdt[0] + bdt[1] * t + bdt[2] * t2;

                return Math.sqrt(dx * dx + dy * dy);
            },
            0.0,
            1.0,
            tolerance
        );

        return length;
    }

    module.cubicBezier = function (p1, p2, p3, p4, delta) {
        // Cubic Bezier function:
        //
        //   x(t) = a0 + a1 * t + a2 * t^2 + a3 * t^3
        //   y(t) = b0 + b1 * t + b2 * t^2 + b3 * t^3
        //
        //   with t = 0..1

        // calculate coefficients for x- and y-direction
        var a = cubicCoefficients(p1.x, p2.x, p3.x, p4.x);
        var b = cubicCoefficients(p1.y, p2.y, p3.y, p4.y);

        // calculate real curve length
        // ALTERNATIVE: direct distance P1->P2->P3->P4
        var length = cubicLength(p1, p2, p3, p4, delta);

        // required number of segment
        var n = Math.ceil(length / delta) | 0;

        // divide parameter space
        var dt = 1.0 / n;

        // allocate memory for points
        var pts = [];
        pts.length = n + 1;

        // set first and last point explicit to avoid rounding errors
        pts[0] = p1;
        pts[n] = p4;

        // interpolate points
        for (let i = 1; i < n; ++i) {
            var t = i * dt;
            var t2 = t * t;
            var t3 = t2 * t;

            pts[i] = {
                x: a[0] + a[1] * t + a[2] * t2 + a[3] * t3,
                y: b[0] + b[1] * t + b[2] * t2 + b[3] * t3,
            };
        }

        return pts;
    };

    // --- arc

    function dot(u, v) {
        return u.x * v.x + u.y * v.y;
    }

    function norm(u) {
        return Math.sqrt(u.x ** 2 + u.y ** 2);
    }

    function angle(u, v) {
        return (
            Math.acos((dot(u, v) / (norm(u) * norm(v))).toFixed(8)) *
            (u.x * v.y - u.y * v.x < 0 ? -1.0 : 1.0)
        );
    }

    function arc(p1, p2, rx, ry, phi, fa, fs, delta) {
        // https://www.w3.org/TR/SVG/implnote.html#ArcImplementationNotes

        var cosPhi = Math.cos(phi);
        var sinPhi = Math.sin(phi);

        var x1_ =
            (cosPhi * (p1.x - p2.x)) / 2.0 + (sinPhi * (p1.y - p2.y)) / 2.0;
        var y1_ =
            (-sinPhi * (p1.x - p2.x)) / 2.0 + (cosPhi * (p1.y - p2.y)) / 2.0;

        var Delta = x1_ ** 2 / rx ** 2 + y1_ ** 2 / ry ** 2;

        if (Delta > 1.0) {
            var f = Math.sqrt(Delta);
            rx *= f;
            ry *= f;
        }

        var s =
            Math.sqrt(
                (rx ** 2 * ry ** 2 - rx ** 2 * y1_ ** 2 - ry ** 2 * x1_ ** 2) /
                    (rx ** 2 * y1_ ** 2 + ry ** 2 * x1_ ** 2)
            ) * (fa === fs ? -1.0 : 1.0);

        // few times the 3 lines above return NaN.
        // When the ellipsis is a circle, the top of the fraction gets negative due rounding errors.
        // In all my (Teja) observations, the negative number was supersmall (e.g. -#.#####e-16)
        // Therefore this Hack was introduced, setting s to 0.
        // Otherwise the code does not fail - but returning only a straight line from start to end point.
        if (isNaN(s)) s = 0; // HACK

        var cx_ = (s * rx * y1_) / ry;
        var cy_ = (-s * ry * x1_) / rx;

        var cx = cosPhi * cx_ - sinPhi * cy_ + (p1.x + p2.x) / 2.0;
        var cy = sinPhi * cx_ + cosPhi * cy_ + (p1.y + p2.y) / 2.0;

        var theta1 = angle(
            {
                x: 1.0,
                y: 0.0,
            },
            {
                x: (x1_ - cx_) / rx,
                y: (y1_ - cy_) / ry,
            }
        );

        var deltaTheta =
            angle(
                {
                    x: (x1_ - cx_) / rx,
                    y: (y1_ - cy_) / ry,
                },
                {
                    x: (-x1_ - cx_) / rx,
                    y: (-y1_ - cy_) / ry,
                }
            ) %
            (2.0 * Math.PI);

        if (fs === 0 && deltaTheta > 0.0) {
            deltaTheta -= 2.0 * Math.PI;
        }
        if (fs !== 0 && deltaTheta < 0.0) {
            deltaTheta += 2.0 * Math.PI;
        }

        // approximate real curve length with circle arc R=max(rx, ry)
        var length = Math.max(rx, ry) * Math.abs(deltaTheta);

        // required number of segment
        var n = Math.ceil(length / delta) | 0;

        // divide parameter space
        var dt = deltaTheta / n;

        // allocate memory for points
        var pts = [];
        pts.length = n + 1;

        // set first and last point explicit to avoid rounding errors
        pts[0] = p1;
        pts[n] = p2;

        // interpolate points
        for (let i = 1; i < n; ++i) {
            var t = theta1 + i * dt;

            var a = rx * Math.cos(t);
            var b = ry * Math.sin(t);

            pts[i] = {
                x: a * cosPhi - b * sinPhi + cx,
                y: a * sinPhi + b * cosPhi + cy,
            };
        }

        return pts;
    }

    // --- convertes for clipper

    function toIntPaths(paths, tolerance) {
        return paths.map((path) =>
            path.map(
                (pt) =>
                    new ClipperLib.IntPoint(pt.x / tolerance, pt.y / tolerance)
            )
        );
    }

    function fromIntPaths(paths, tolerance) {
        return paths.map((path) =>
            path.map((pt) => point(pt.X * tolerance, pt.Y * tolerance))
        );
    }

    // --- path methods

    module.parse = function (segments, delta) {
        var polylines = [];

        for (let i = 0; i < segments.length; ++i) {
            var segment = segments[i];

            var command = segment[0];

            switch (command) {
                case "M": // move
                    polylines.push([
                        {
                            x: segment[1],
                            y: segment[2],
                        },
                    ]);
                    break;
                case "Z": // close path
                    if (polylines.length > 0) {
                        // more robust against d="MZ" (=> polylines=[]), sometimes crashed here.
                        var polyline = peek(polylines);
                        polyline.push({
                            x: polyline[0].x,
                            y: polyline[0].y,
                        });
                    } else {
                        console.warn(
                            "Closing path attempt while path was empty."
                        );
                    }
                    break;
                case "L": // line
                    var polyline = peek(polylines);
                    polyline.push({
                        x: segment[1],
                        y: segment[2],
                    });
                    break;
                case "H": // horizontal line
                    var polyline = peek(polylines);
                    polyline.push({
                        x: segment[1],
                        y: peek(polyline).y,
                    });
                    break;
                case "V": // vertical line
                    var polyline = peek(polylines);
                    polyline.push({
                        x: peek(polyline).x,
                        y: segment[1],
                    });
                    break;
                case "C": // cubic bezier
                    var polyline = peek(polylines);

                    var p1 = peek(polyline);
                    var p2 = { x: segment[1], y: segment[2] };
                    var p3 = { x: segment[3], y: segment[4] };
                    var p4 = { x: segment[5], y: segment[6] };

                    // approximate cubic bezier with polyline
                    var pts = module.cubicBezier(p1, p2, p3, p4, delta);

                    Array.prototype.push.apply(polyline, pts);
                    break;
                case "S": // "Smooth" cubic bezier
                    var polyline = peek(polylines);
                    var prev = segments[i - 1];

                    var p1 = peek(polyline);
                    var p2;
                    if (prev[0] === "C" || prev[0] === "S") {
                        var [prevX, prevY] = prev.slice(-4, -2);
                        p2 = {
                            x: 2 * p1.x - prevX,
                            y: 2 * p1.y - prevY,
                        };
                    } else {
                        p2 = p1;
                    }
                    var p3 = { x: segment[1], y: segment[2] };
                    var p4 = { x: segment[3], y: segment[4] };

                    // approximate cubic bezier with polyline
                    var pts = module.cubicBezier(p1, p2, p3, p4, delta);

                    Array.prototype.push.apply(polyline, pts);
                    break;
                case "Q": // quadratic bezier
                    var polyline = peek(polylines);

                    var p1 = peek(polyline);
                    var p2 = { x: segment[1], y: segment[2] };
                    var p3 = { x: segment[3], y: segment[4] };

                    // approximate quadratic bezier with polyline
                    var pts = module.quadraticBezier(p1, p2, p3, delta);

                    Array.prototype.push.apply(polyline, pts);
                    break;
                case "T": // "Smooth" quadratic bezier
                    var polyline = peek(polylines);

                    var [prevX, prevY] = segments[i - 1].slice(-4, -2);

                    var p1 = peek(polyline);
                    var p2 = {
                        x: 2 * p1.x - prevX,
                        y: 2 * p1.y - prevY,
                    };
                    var p3 = { x: segment[1], y: segment[2] };

                    // approximate quadratic bezier with polyline
                    var pts = module.quadraticBezier(p1, p2, p3, delta);

                    Array.prototype.push.apply(polyline, pts);
                    break;
                case "A": // Arc
                    var polyline = peek(polylines);

                    var p1 = peek(polyline);
                    var p2 = { x: segment[6], y: segment[7] };
                    var rx = segment[1];
                    var ry = segment[2];
                    var phi = (segment[3] / 180.0) * Math.PI;
                    var fa = segment[4];
                    var fs = segment[5];

                    var pts = arc(p1, p2, rx, ry, phi, fa, fs, delta);

                    Array.prototype.push.apply(polyline, pts);

                    break;
                default:
                    console.error(`Unsupported SVG path command: ${command}`);
            }
        }

        return polylines;
    };

    module.parsePoints = function (pointsString, closed) {
        // ATTENTION: Maybe not so safe (Minus as delimiter,…)
        var xy = pointsString
            .split(/,|\s/g)
            .filter((s) => s.length > 0)
            .map(Number);

        var pts = [];

        for (let i = 0; i < xy.length; i += 2) {
            pts.push(point(xy[i], xy[i + 1]));
        }

        if (closed) {
            pts.push(pts[0]);
        }

        return pts;
    };

    module.transform = function (paths, matrix) {
        var [m11, m12, m21, m22, tx, ty] = matrix;

        return paths.map((path) =>
            path.map((pt) =>
                point(
                    pt.x * m11 + pt.y * m21 + tx,
                    pt.x * m12 + pt.y * m22 + ty
                )
            )
        );
    };

    module.pointCount = function (paths) {
        return paths.reduce((act, cur) => act + cur.length, 0);
    };

    module.simplify = function (paths, tolerance) {
        return paths.map((path) => simplify(path, tolerance));
    };

    module.toSvgPathString = function (paths) {
        var pathStrings = [];

        // helper for number formatting
        var fmt = (number) => number.toFixed(2);

        paths.forEach(function (path) {
            var pt = path[0];

            pathStrings.push(`M ${fmt(pt.x)},${fmt(pt.y)}`);

            for (let i = 1; i < path.length; i += 1) {
                pt = path[i];
                pathStrings.push(`L ${fmt(pt.x)},${fmt(pt.y)}`);
            }
        });

        var pathString = pathStrings.join(" ");

        return pathString;
    };

    module.gcode = function (paths, id, mb_meta) {
        if (paths.length === 0) {
            console.warn("No paths to generate gcode!");
            //            return null;
        }
        var commands = [];
        let first_point = null;
        let last_point = {};

        mb_meta = mb_meta || {};
        var meta_str = "";
        for (var key in mb_meta) {
            var val =
                mb_meta[key].replace === "function"
                    ? mb_meta[key].replace(" ", "_")
                    : mb_meta[key];
            meta_str += "," + key + ":" + val;
        }
        let my_id = id ? id.replace(" ", "_") : "null";
        commands.push(";_gc_nextgen_svg_id:" + my_id + meta_str);

        // helper for number formatting
        var fmt = (number) => number.toFixed(2);

        let length = 0;
        paths.forEach(function (path) {
            var pt = path[0];
            first_point = first_point || pt;
            last_point = first_point;
            commands.push(`G0X${fmt(pt.x)}Y${fmt(pt.y)}`);
            commands.push(";_laseron_");

            for (let i = 1; i < path.length; i += 1) {
                pt = path[i];
                const dist = Math.sqrt(
                    Math.pow(pt.x - last_point.x, 2) +
                        Math.pow(pt.y - last_point.y, 2)
                );
                commands.push(`G1X${fmt(pt.x)}Y${fmt(pt.y)}`);
                last_point = pt;
                length += dist;
            }

            commands.push(";_laseroff_");
        });

        var gcode = commands.join(" ");

        return {
            gcode: gcode,
            begin: first_point,
            end: last_point,
            gc_length: length,
        };
    };

    module.clip = function (paths, clip, tolerance) {
        ClipperLib.use_lines = true;
        const pathCountBeforeClip = paths.length;

        var subj = toIntPaths(paths, tolerance);
        var clip = toIntPaths(clip, tolerance);

        var solution = new ClipperLib.PolyTree();
        var c = new ClipperLib.Clipper();

        subj.forEach((path) => {
            if (path.length === 0) return;

            var startPoint = path[0];
            var endPoint = path[path.length - 1];

            var isClosed =
                startPoint.X == endPoint.X && startPoint.Y == endPoint.Y;

            c.AddPath(path, ClipperLib.PolyType.ptSubject, isClosed);
        });

        c.AddPaths(clip, ClipperLib.PolyType.ptClip, true);
        c.Execute(
            ClipperLib.ClipType.ctIntersection,
            solution,
            ClipperLib.PolyFillType.pftNonZero,
            ClipperLib.PolyFillType.pftNonZero
        );

        var clipped = [];
        var polynode = solution.GetFirst();

        while (polynode) {
            var path = fromIntPaths([polynode.Contour()], tolerance)[0];

            if (!polynode.IsOpen) {
                path.push(path[0]);
            }

            clipped.push(path);

            polynode = polynode.GetNext();
        }
        const pathCountAfterClip = clipped.length;
        if (pathCountAfterClip < pathCountBeforeClip) {
            console.info(
                "clipped path: " +
                    pathCountBeforeClip +
                    " nodes => " +
                    pathCountAfterClip
            );
        }

        return clipped.reverse();
    };

    module.optimize = function (paths, tolerance) {
        ClipperLib.use_lines = true;

        var subj = toIntPaths(paths, tolerance);

        var solution = new ClipperLib.PolyTree();
        var c = new ClipperLib.Clipper();

        subj.forEach(function (sub) {
            var a = sub[0];
            var b = sub.slice(-1)[0];

            var isClosed = a.X === b.X && a.Y === b.Y;

            if (isClosed) {
                c.AddPath(sub, ClipperLib.PolyType.ptSubject, true);
            } else {
                c.AddPath(sub, ClipperLib.PolyType.ptSubject, false);
            }
        }, this);

        c.Execute(ClipperLib.ClipType.ctDifference, solution);

        var optimized = [];

        var polynode = solution.GetFirst();

        while (polynode) {
            var path = fromIntPaths([polynode.Contour()], tolerance)[0];

            if (!polynode.IsOpen) {
                path.push(path[0]);
            }

            optimized.push(path);

            polynode = polynode.GetNext();
        }

        return optimized.reverse();
    };

    module.pp_paths = function (paths) {
        var ps = [];
        for (var i = 0; i < paths.length; i++) {
            ps.push(module.pp_path(paths[i]));
        }
        return "[" + ps.join(", ") + "]";
    };

    module.pp_path = function (path) {
        var ps = [];
        for (var i = 0; i < path.length; i++) {
            ps.push(module.pp_point(path[i]));
        }
        return "[" + ps.join(",") + "]";
    };

    module.pp_point = function (point) {
        return "(x" + point.x + ",y" + point.y + ")";
    };
})();
