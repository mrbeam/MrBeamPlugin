var mrbeam = mrbeam || {};

(function () {
    "use strict";

    ////////////////////////////
    // gcode_nextgen
    // version:
    var VERSION = "0.2";
    //
    //
    ////////////////////////////

    // NICE TO HAVE REWORK
    // * remove duplicate code in snap_jsclipper_plugin.js and path_magic.js (e.g. toIntPaths(), fromIntPaths(), toSvgPathString(), ...)
    // * move gcode generation stuff to snap_gc_plugin.js
    // * use clipping from app/snap-plugins/jsclipper.js
    // * equalize naming in snap_jsclipper_plugin.js, path_magic.js, snap_gc_plugin.js (path = svgpath, poly = jsclipper array, ... )

    var mrbeam = window.mrbeam;
    mrbeam.path = {};
    var module = mrbeam.path;

    module.version = VERSION;

    function point(x, y) {
        return { X: x, Y: y };
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

        let h = b - a;
        let f1 = f(a + h * 0.25);
        let f2 = f(b - h * 0.25);

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

        let sl = (h * (fa + 4 * f1 + fm)) / 12;
        let sr = (h * (fm + 4 * f2 + fb)) / 12;
        let s2 = sl + sr;
        let err = (s2 - V0) / 15;

        if (depth > maxdepth) {
            state.maxDepthCount += 1;
            return s2 + err;
        } else if (Math.abs(err) < tol) {
            return s2 + err;
        } else {
            let m = a + h * 0.5;

            let V1 = adsimp(
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

            let V2 = adsimp(
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
        let state = {
            maxDepthCount: 0,
            nanEncountered: false,
        };

        if (tol === undefined) {
            tol = 1e-8;
        }
        if (maxdepth === undefined) {
            maxdepth = 20;
        }

        let fa = f(a);
        let fm = f(0.5 * (a + b));
        let fb = f(b);

        let V0 = ((fa + 4 * fm + fb) * (b - a)) / 6;

        let result = adsimp(f, a, b, fa, fm, fb, V0, tol, maxdepth, 1, state);

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
        const r = x + width;
        const b = y + height;

        return [
            { X: x, Y: y },
            { X: x, Y: b },
            { X: r, Y: b },
            { X: r, Y: y },
            { X: x, Y: y },
        ];
    };

    // --- circle

    module.circle = function (cx, cy, r, delta) {
        // circumference
        const length = 2.0 * r * Math.PI;

        // number of segments
        const n = Math.ceil(length / delta) | 0;

        // allocate memory
        const pts = [];
        pts.length = n + 1;

        pts[0] = point(cx + r, cy);
        pts[n] = point(cx + r, cy);

        for (let i = 1; i < n; ++i) {
            const t = (i * 2.0 * Math.PI) / n;

            pts[i] = point(cx + r * Math.cos(t), cy + r * Math.sin(t));
        }

        return pts;
    };

    // --- ellipse

    module.ellipse = function (cx, cy, rx, ry, delta) {
        // approximate circumference
        const length = 2.0 * Math.PI * Math.sqrt((rx ** 2 + ry ** 2) / 2.0);

        // number of segments
        const n = Math.ceil(length / delta) | 0;

        // allocate memory
        const pts = [];
        pts.length = n + 1;

        pts[0] = point(cx + rx, cy);
        pts[n] = point(cx + rx, cy);

        for (let i = 1; i < n; ++i) {
            const t = (i * 2.0 * Math.PI) / n;

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
        const adt = quadraticDerivativeCoefficients(p1.X, p2.X, p3.X);
        const bdt = quadraticDerivativeCoefficients(p1.Y, p2.Y, p3.Y);

        const length = integrate(
            function (t) {
                const dx = adt[0] + adt[1] * t;
                const dy = bdt[0] + bdt[1] * t;

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
        const a = quadraticCoefficients(p1.X, p2.X, p3.X);
        const b = quadraticCoefficients(p1.Y, p2.Y, p3.Y);

        // calculate real curve length
        // ALTERNATIVE: direct distance P1->P2->P3
        const length = quadraticLength(p1, p2, p3, delta);

        // required number of segment
        const n = Math.ceil(length / delta) | 0;

        // divide parameter space
        const dt = 1.0 / n;

        // allocate memory for points
        const pts = [];
        pts.length = n + 1;

        // set first and last point explicit to avoid rounding errors
        pts[0] = p1;
        pts[n] = p3;

        // interpolate points
        for (let i = 1; i < n; ++i) {
            const t = i * dt;
            const t2 = t * t;

            pts[i] = {
                X: a[0] + a[1] * t + a[2] * t2,
                Y: b[0] + b[1] * t + b[2] * t2,
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
        const adt = cubicDerivativeCoefficients(p1.X, p2.X, p3.X, p4.X);
        const bdt = cubicDerivativeCoefficients(p1.Y, p2.Y, p3.Y, p4.Y);

        length = integrate(
            function (t) {
                const t2 = t * t;

                const dx = adt[0] + adt[1] * t + adt[2] * t2;
                const dy = bdt[0] + bdt[1] * t + bdt[2] * t2;

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
        const a = cubicCoefficients(p1.X, p2.X, p3.X, p4.X);
        const b = cubicCoefficients(p1.Y, p2.Y, p3.Y, p4.Y);

        // calculate real curve length
        // ALTERNATIVE: direct distance P1->P2->P3->P4
        const length = cubicLength(p1, p2, p3, p4, delta);

        // required number of segment
        const n = Math.ceil(length / delta) | 0;

        // divide parameter space
        const dt = 1.0 / n;

        // allocate memory for points
        const pts = [];
        pts.length = n + 1;

        // set first and last point explicit to avoid rounding errors
        pts[0] = p1;
        pts[n] = p4;

        // interpolate points
        for (let i = 1; i < n; ++i) {
            const t = i * dt;
            const t2 = t * t;
            const t3 = t2 * t;

            pts[i] = {
                X: a[0] + a[1] * t + a[2] * t2 + a[3] * t3,
                Y: b[0] + b[1] * t + b[2] * t2 + b[3] * t3,
            };
        }

        return pts;
    };

    // --- arc

    function dot(u, v) {
        return u.X * v.X + u.Y * v.Y;
    }

    function norm(u) {
        return Math.sqrt(u.X ** 2 + u.Y ** 2);
    }

    function angle(u, v) {
        return (
            Math.acos((dot(u, v) / (norm(u) * norm(v))).toFixed(8)) *
            (u.X * v.Y - u.Y * v.X < 0 ? -1.0 : 1.0)
        );
    }

    function arc(p1, p2, rx, ry, phi, fa, fs, delta) {
        // https://www.w3.org/TR/SVG/implnote.html#ArcImplementationNotes

        const cosPhi = Math.cos(phi);
        const sinPhi = Math.sin(phi);

        const x1_ =
            (cosPhi * (p1.X - p2.X)) / 2.0 + (sinPhi * (p1.Y - p2.Y)) / 2.0;
        const y1_ =
            (-sinPhi * (p1.X - p2.X)) / 2.0 + (cosPhi * (p1.Y - p2.Y)) / 2.0;

        const Delta = x1_ ** 2 / rx ** 2 + y1_ ** 2 / ry ** 2;

        if (Delta > 1.0) {
            const f = Math.sqrt(Delta);
            rx *= f;
            ry *= f;
        }

        let s =
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

        const cx_ = (s * rx * y1_) / ry;
        const cy_ = (-s * ry * x1_) / rx;

        const cx = cosPhi * cx_ - sinPhi * cy_ + (p1.X + p2.X) / 2.0;
        const cy = sinPhi * cx_ + cosPhi * cy_ + (p1.Y + p2.Y) / 2.0;

        const theta1 = angle(
            {
                X: 1.0,
                Y: 0.0,
            },
            {
                X: (x1_ - cx_) / rx,
                Y: (y1_ - cy_) / ry,
            }
        );

        let deltaTheta =
            angle(
                {
                    X: (x1_ - cx_) / rx,
                    Y: (y1_ - cy_) / ry,
                },
                {
                    X: (-x1_ - cx_) / rx,
                    Y: (-y1_ - cy_) / ry,
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
        const length = Math.max(rx, ry) * Math.abs(deltaTheta);

        // required number of segment
        const n = Math.ceil(length / delta) | 0;

        // divide parameter space
        const dt = deltaTheta / n;

        // allocate memory for points
        const pts = [];
        pts.length = n + 1;

        // set first and last point explicit to avoid rounding errors
        pts[0] = p1;
        pts[n] = p2;

        // interpolate points
        for (let i = 1; i < n; ++i) {
            const t = theta1 + i * dt;

            const a = rx * Math.cos(t);
            const b = ry * Math.sin(t);

            pts[i] = {
                X: a * cosPhi - b * sinPhi + cx,
                Y: a * sinPhi + b * cosPhi + cy,
            };
        }

        return pts;
    }

    // --- convertes for clipper

    function toIntPaths(paths, tolerance) {
        return paths.map((path) =>
            path.map(
                (pt) =>
                    new ClipperLib.IntPoint(pt.X / tolerance, pt.Y / tolerance)
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
        const polylines = [];

        for (let i = 0; i < segments.length; ++i) {
            const segment = segments[i];

            const command = segment[0];

            switch (command) {
                case "M": // move
                    polylines.push([
                        {
                            X: segment[1],
                            Y: segment[2],
                        },
                    ]);
                    break;
                case "Z": // close path
                case "z":
                    if (polylines.length > 0) {
                        // more robust against d="MZ" (=> polylines=[]), sometimes crashed here.
                        let polyline = peek(polylines);
                        polyline.push({
                            X: polyline[0].X,
                            Y: polyline[0].Y,
                        });
                    } else {
                        console.warn(
                            "Closing path attempt while path was empty."
                        );
                    }
                    break;
                case "L": // line
                    let polyline = peek(polylines);
                    polyline.push({
                        X: segment[1],
                        Y: segment[2],
                    });
                    break;
                case "H": // horizontal line
                    let polyline = peek(polylines);
                    polyline.push({
                        X: segment[1],
                        Y: peek(polyline).Y,
                    });
                    break;
                case "V": // vertical line
                    let polyline = peek(polylines);
                    polyline.push({
                        X: peek(polyline).X,
                        Y: segment[1],
                    });
                    break;
                case "C": // cubic bezier
                    let polyline = peek(polylines);

                    let p1 = peek(polyline);
                    let p2 = { X: segment[1], Y: segment[2] };
                    let p3 = { X: segment[3], Y: segment[4] };
                    let p4 = { X: segment[5], Y: segment[6] };

                    // approximate cubic bezier with polyline
                    let pts = module.cubicBezier(p1, p2, p3, p4, delta);

                    Array.prototype.push.apply(polyline, pts);
                    break;
                case "S": // "Smooth" cubic bezier
                    let polyline = peek(polylines);
                    let prev = segments[i - 1];

                    let p1 = peek(polyline);
                    let p2;
                    if (prev[0] === "C" || prev[0] === "S") {
                        let [prevX, prevY] = prev.slice(-4, -2);
                        p2 = {
                            X: 2 * p1.X - prevX,
                            Y: 2 * p1.Y - prevY,
                        };
                    } else {
                        p2 = p1;
                    }
                    let p3 = { X: segment[1], Y: segment[2] };
                    let p4 = { X: segment[3], Y: segment[4] };

                    // approximate cubic bezier with polyline
                    let pts = module.cubicBezier(p1, p2, p3, p4, delta);

                    Array.prototype.push.apply(polyline, pts);
                    break;
                case "Q": // quadratic bezier
                    let polyline = peek(polylines);

                    let p1 = peek(polyline);
                    let p2 = { X: segment[1], Y: segment[2] };
                    let p3 = { X: segment[3], Y: segment[4] };

                    // approximate quadratic bezier with polyline
                    let pts = module.quadraticBezier(p1, p2, p3, delta);

                    Array.prototype.push.apply(polyline, pts);
                    break;
                case "T": // "Smooth" quadratic bezier
                    let polyline = peek(polylines);

                    let [prevX, prevY] = segments[i - 1].slice(-4, -2);

                    let p1 = peek(polyline);
                    let p2 = {
                        X: 2 * p1.X - prevX,
                        Y: 2 * p1.Y - prevY,
                    };
                    let p3 = { X: segment[1], Y: segment[2] };

                    // approximate quadratic bezier with polyline
                    let pts = module.quadraticBezier(p1, p2, p3, delta);

                    Array.prototype.push.apply(polyline, pts);
                    break;
                case "A": // Arc
                    let polyline = peek(polylines);

                    let p1 = peek(polyline);
                    let p2 = { X: segment[6], Y: segment[7] };
                    let rx = segment[1];
                    let ry = segment[2];
                    let phi = (segment[3] / 180.0) * Math.PI;
                    let fa = segment[4];
                    let fs = segment[5];

                    let pts = arc(p1, p2, rx, ry, phi, fa, fs, delta);

                    Array.prototype.push.apply(polyline, pts);

                    break;
                default:
                    console.error(`Unsupported SVG path command: ${command}`);
            }
        }

        return polylines;
    };

    module.parsePoints = function (pointsString, closed) {
        // TODO: ATTENTION: Maybe not so safe (Minus as delimiter,…)
        const xy = pointsString
            .split(/,|\s/g)
            .filter((s) => s.length > 0)
            .map(Number);

        const pts = [];

        for (let i = 0; i < xy.length; i += 2) {
            pts.push(point(xy[i], xy[i + 1]));
        }

        if (closed) {
            pts.push(pts[0]);
        }

        return pts;
    };

    module.transform = function (paths, matrix) {
        const [m11, m12, m21, m22, tx, ty] = matrix;

        return paths.map((path) =>
            path.map((pt) =>
                point(
                    pt.X * m11 + pt.Y * m21 + tx,
                    pt.X * m12 + pt.Y * m22 + ty
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
        const pathStrings = [];

        // helper for number formatting
        const fmt = (number) => number.toFixed(2);

        paths.forEach(function (path) {
            let pt = path[0];

            pathStrings.push(`M ${fmt(pt.X)},${fmt(pt.Y)}`);

            for (let i = 1; i < path.length; i += 1) {
                pt = path[i];
                pathStrings.push(`L ${fmt(pt.X)},${fmt(pt.Y)}`);
            }
        });

        const pathString = pathStrings.join(" ");

        return pathString;
    };

    module.gcode = function (paths, id, mb_meta) {
        if (paths.length === 0) {
            console.warn("No paths to generate gcode!");
            //            return null;
        }
        const commands = [];
        let first_point = null;
        let last_point = {};

        mb_meta = mb_meta || {};
        let meta_str = "";
        for (let key in mb_meta) {
            let val =
                mb_meta[key].replace === "function"
                    ? mb_meta[key].replace(" ", "_")
                    : mb_meta[key];
            meta_str += "," + key + ":" + val;
        }
        let my_id = id ? id.replace(" ", "_") : "null";
        commands.push(";_gc_nextgen_svg_id:" + my_id + meta_str);

        // helper for number formatting
        const fmt = (number) => number.toFixed(2);

        let length = 0;
        let areas = [];
        paths.forEach(function (path) {
            const area = ClipperLib.Clipper.Area(path);
            areas.push(area);
            let pt = path[0];
            first_point = first_point || pt;
            last_point = first_point;
            commands.push(`G0X${fmt(pt.X)}Y${fmt(pt.Y)}`);
            commands.push(";_laseron_");

            for (let i = 1; i < path.length; i += 1) {
                pt = path[i];
                const dist = Math.sqrt(
                    Math.pow(pt.X - last_point.X, 2) +
                        Math.pow(pt.Y - last_point.Y, 2)
                );
                commands.push(`G1X${fmt(pt.X)}Y${fmt(pt.Y)}`);
                last_point = pt;
                length += dist;
            }

            commands.push(";_laseroff_");
        });

        const gcode = commands.join(" ");

        return {
            gcode: gcode,
            begin: first_point,
            end: last_point,
            areas: areas.join("|"),
            gc_length: length,
        };
    };

    module.clip = function (paths, clip, tolerance) {
        ClipperLib.use_lines = true;
        const pathCountBeforeClip = paths.length;

        const subj = toIntPaths(paths, tolerance);
        const clip = toIntPaths(clip, tolerance);

        const solution = new ClipperLib.PolyTree();
        const c = new ClipperLib.Clipper();

        subj.forEach((path) => {
            if (path.length === 0) return;

            const startPoint = path[0];
            const endPoint = path[path.length - 1];

            const isClosed =
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

        const clipped = [];
        let polynode = solution.GetFirst();

        while (polynode) {
            let path = fromIntPaths([polynode.Contour()], tolerance)[0];

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

        const subj = toIntPaths(paths, tolerance);

        const solution = new ClipperLib.PolyTree();
        const c = new ClipperLib.Clipper();

        subj.forEach(function (sub) {
            const a = sub[0];
            const b = sub.slice(-1)[0];

            const isClosed = a.X === b.X && a.Y === b.Y;

            if (isClosed) {
                c.AddPath(sub, ClipperLib.PolyType.ptSubject, true);
            } else {
                c.AddPath(sub, ClipperLib.PolyType.ptSubject, false);
            }
        }, this);

        c.Execute(ClipperLib.ClipType.ctDifference, solution);

        const optimized = [];

        let polynode = solution.GetFirst();

        while (polynode) {
            const path = fromIntPaths([polynode.Contour()], tolerance)[0];

            if (!polynode.IsOpen) {
                path.push(path[0]);
            }

            optimized.push(path);

            polynode = polynode.GetNext();
        }

        return optimized.reverse();
    };

    module.pp_paths = function (paths) {
        const ppaths = paths.map((p) => module.pp_path(p)).join(", ");
        return `[${ppaths}]`;
    };

    module.pp_path = function (path) {
        const points = path.map((p) => module.pp_point(p)).join(",");
        return `[${points}]`;
    };

    module.pp_point = function (point) {
        return `(x${point.X},y${point.Y})`;
    };
})();
