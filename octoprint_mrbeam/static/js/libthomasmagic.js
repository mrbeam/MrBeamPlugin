//    library with the purpose to do parallel geometric calculations
//    Copyright (C) 2017  Mr Beam Lasers UG <info@mr-beam.org>
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

(function () {

// --- Helpers

function last(array) {
  return array[array.length - 1];
}

var timer = function (name) {
  var start = new Date();
  return {
    stop: function () {
      var end = new Date();
      var time = end.getTime() - start.getTime();
      console.log('Timer:', name, 'finished in', time, 'ms');
    }
  }
};

// --- Geometry: Quadratic Spline

function quadraticCoefficients(x0, x1, x2) {
	return [x0, 2.0 * (x1 - x0), x0 - 2.0 * x1 + x2];
}

function quadraticDerivativeCoefficients(x0, x1, x2) {
	return [2.0 * (x1 - x0), 2.0 * (x0 - 2.0 * x1 + x2)];
}

function quadraticLength(x0, y0, x1, y1, x2, y2) {
  return 4.0 / 3.0 * (x0 ** 2 + x1 ** 2 - x1 * x2 + x2 ** 2 - x0 * (x1 + x2) + y0 ** 2 + y1 ** 2 - y0 * y1 + y2 ** 2 - y2 * (y0 + y1));
}

function quadraticDivide(x0, y0, x1, y1, x2, y2) {
  // Quadratic Spline function:
  // 
  //   x(t) = a0 + a1 * t + a2 * t^2
  //   y(t) = b0 + b1 * t + b2 * t^2
  //
  //   with t = 0..1

  // calculate coefficients for x- and y-direction
  var [a0, a1, a2] = quadraticCoefficients(x0, x1, x2);
  var [b0, b1, b2] = quadraticCoefficients(y0, y1, y2);

  // calculate real curve length
  var length = quadraticLength(x0, y0, x1, y1, x2, y2);

  // required number of segment
  var n = ~~Math.ceil(length / delta);

  // divide parameter space
  var dt = 1.0 / n;

  // allocate memory for points
  var pts = [];
  pts.length = n + 1;

  // set first and last point explicit to avoid rounding errors
  pts[0] = [x0, y0];
  pts[n] = [x2, y2];

  // interpolate points
  for (i = 1; i < n; ++i) {
    var t = i * dt;
    var t2 = t * t;

    x = a0 + a1 * t + a2 * t2;
    y = b0 + b1 * t + b2 * t2;

    pts[i] = [x, y];
  }

  return pts;
}

// --- Geometry: Cubic Spline

function cubicCoefficients(x0, x1, x2, x3) {
  return [x0, 3.0 * (x1 - x0), 3.0 * (x0 - 2.0 * x1 + x2), x3 - x0 + 3.0 * (x1 - x2)];
}

function cubicDerivativeCoefficients(x0, x1, x2, x3) {
  return [3.0 * (x1 - x0), 6.0 * (x0 - 2.0 * x1 + x2), 3.0 * (x3 - x0) + 9.0 * (x1 - x2)];
}

function cubicLength(x0, y0, x1, y1, x2, y2, x3, y3, tolerance = 1e-8) {
  // Cubic Spline derivative function:
  // 
  //   dx(t)/dt = da0 + da1 * t + da2 * t^2
  //   dy(t)/dt = db0 + db1 * t + db2 * t^2
  //
  //   with t = 0..1

  // calculate coefficients for x- and y-direction
  var [da0, da1, da2] = cubicDerivativeCoefficients(x0, x1, x2, x3);
  var [db0, db1, db2] = cubicDerivativeCoefficients(y0, y1, y2, y3);

  var length = integrate(function (t) {
    var t2 = t * t

    var dx = da0 + da1 * t + da2 * t2
    var dy = db0 + db1 * t + db2 * t2

    return Math.sqrt(dx * dx + dy * dy)
  }, 0.0, 1.0, tolerance);

  return length;
}

function cubicDivide(x0, y0, x1, y1, x2, y2, x3, y3, delta) {
  // Cubic Spline function:
  // 
  //   x(t) = a0 + a1 * t + a2 * t^2 + a3 * t^3
  //   y(t) = b0 + b1 * t + b2 * t^2 + b3 * t^3
  //
  //   with t = 0..1

  // calculate coefficients for x- and y-direction
  var [a0, a1, a2, a3] = cubicCoefficients(x0, x1, x2, x3);
  var [b0, b1, b2, b3] = cubicCoefficients(y0, y1, y2, y3);

  // calculate real curve length
  var length = cubicLength(x0, y0, x1, y1, x2, y2, x3, y3, delta);

  // required number of segment
  var n = ~~Math.ceil(length / delta);

  // divide parameter space
  var dt = 1.0 / n;

  // allocate memory for points
  var pts = [];
  pts.length = n + 1;

  // set first and last point explicit to avoid rounding errors
  pts[0] = [x0, y0];
  pts[n] = [x3, y3];

  // interpolate points
  for (i = 1; i < n; ++i) {
    var t = i * dt;
    var t2 = t * t;
    var t3 = t2 * t;

    x = a0 + a1 * t + a2 * t2 + a3 * t3;
    y = b0 + b1 * t + b2 * t2 + b3 * t3;

    pts[i] = [x, y];
  }

  return pts;
}

// --- Math: Integration

// integrate-adaptive-simpson
// https://github.com/scijs/integrate-adaptive-simpson
// (c) 2015 Scijs Authors. MIT License.
function adsimp(f, a, b, fa, fm, fb, V0, tol, maxdepth, depth, state) {
  if (state.nanEncountered) {
    return NaN;
  }

  var h, f1, f2, sl, sr, s2, m, V1, V2, err;

  h = b - a;
  f1 = f(a + h * 0.25);
  f2 = f(b - h * 0.25);

  // Simple check for NaN:
  if (isNaN(f1)) {
    state.nanEncountered = true;
    return;
  }

  // Simple check for NaN:
  if (isNaN(f2)) {
    state.nanEncountered = true;
    return;
  }

  sl = h * (fa + 4 * f1 + fm) / 12;
  sr = h * (fm + 4 * f2 + fb) / 12;
  s2 = sl + sr;
  err = (s2 - V0) / 15;

  if (depth > maxdepth) {
    state.maxDepthCount++;
    return s2 + err;
  } else if (Math.abs(err) < tol) {
    return s2 + err;
  } else {
    m = a + h * 0.5;

    V1 = adsimp(f, a, m, fa, f1, fm, sl, tol * 0.5, maxdepth, depth + 1, state);

    if (isNaN(V1)) {
      state.nanEncountered = true;
      return NaN;
    }

    V2 = adsimp(f, m, b, fm, f2, fb, sr, tol * 0.5, maxdepth, depth + 1, state);

    if (isNaN(V2)) {
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
    nanEncountered: false
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

  var V0 = (fa + 4 * fm + fb) * (b - a) / 6;

  var result = adsimp(f, a, b, fa, fm, fb, V0, tol, maxdepth, 1, state);

  if (state.maxDepthCount > 0 && console && console.warn) {
    console.warn('integrate-adaptive-simpson: Warning: maximum recursion depth (' + maxdepth + ') reached ' + state.maxDepthCount + ' times');
  }

  if (state.nanEncountered && console && console.warn) {
    console.warn('integrate-adaptive-simpson: Warning: NaN encountered. Halting early.');
  }

  return result;
}

// --- Geometry: Paths

Polylines = function () { }

Polylines.toInt = function (polylines, tol) {
  return polylines.map(
    polyline => polyline.map(
      pt => new ClipperLib.IntPoint(pt[0] / tol, pt[1] / tol)
    )
  );
}

Polylines.fromInt = function (paths, tol) {
  return paths.map(
    path => path.map(
      pt => [pt.X * tol, pt.Y * tol]
    )
  );
}

Polylines.clipRect = function (polylines, rect, tol) {
  ClipperLib.use_lines = true;

  var [x0, y0, x1, y1] = rect;

  var rectPolyline = [[
    [x0, y0],
    [x0, y1],
    [x1, y1],
    [x1, y0],
    [x0, y0]
  ]];

  var subj = Polylines.toInt(polylines, tol);
  var clip = Polylines.toInt(rectPolyline, tol);

  var solution = new ClipperLib.PolyTree();
  var c = new ClipperLib.Clipper();
  
  // subj.forEach(function (sub) {
  //   var a = sub[0];
  //   var b = sub.slice(-1)[0];

  //   var isClosed = (a.X === b.X && a.Y === b.Y);

  //   if (isClosed) {
  //     c.AddPath(sub, ClipperLib.PolyType.ptSubject, true);
  //   } else {
  //     c.AddPath(sub, ClipperLib.PolyType.ptSubject, false);
  //   }
  // }, this);

  c.AddPaths(subj, ClipperLib.PolyType.ptSubject, false);
  c.AddPaths(clip, ClipperLib.PolyType.ptClip, true);
  c.Execute(ClipperLib.ClipType.ctIntersection, solution);

  var clipped = [];

  var polynode = solution.GetFirst();

  while (polynode) {
    var polyline = Polylines.fromInt([polynode.Contour()], tol)[0];

    if (!polynode.IsOpen) {
      polyline.push(polyline[0]);
    }

    clipped.push(polyline);

    polynode = polynode.GetNext();
  }

  return clipped.reverse();
}

Polylines.simplify = function (polylines, tol) {
  return polylines.map(
    polyline => simplify(polyline, tol)
  );
}

Polylines.pointCount = function (polylines) {
  return polylines.reduce((act, cur) => act + cur.length, 0);
}

Polylines.transform = function (polylines, matrix) {
  var [m11, m12, m21, m22, tx, ty] = matrix;

  return polylines.map(
    polyline => polyline.map(
      pt => [pt[0] * m11 + pt[1] * m21 + tx,
      pt[0] * m12 + pt[1] * m22 + ty]
    )
  );
}

Polylines.gcode = function (polylines) {
  var commands = [];

  // helper for number formatting
  var fmt = (number) => number.toFixed(2);

  polylines.forEach(function (polyline) {
    var [x, y] = polyline[0];

    commands.push(`G0X${fmt(x)}Y${fmt(y)}`);
    commands.push(";hallo");
    commands.push(";_laseron_");

    for (var i = 1; i < polyline.length; i++) {
      [x, y] = polyline[i];
      commands.push(`G1X${fmt(x)}Y${fmt(y)}`);
    }

    commands.push(";_laseroff_");
  }, this);

  var gcode = commands.join('\n');

  return gcode;
}

Polylines.fromSvgPathSegments = function (segments, delta) {
  var polylines = [];

  for (var i = 0; i < segments.length; i++) {
    var segment = segments[i];

    var command = segment[0];

    switch (command) {
      case 'M': // move
        var [_, x, y] = segment;

        polylines.push([[x, y]]);

        break;
      case 'Z': // close path
        var polyline = last(polylines);
        var [x, y] = polyline[0];

        polyline.push([x, y]);

        break;
      case 'L': // line
        var [_, x, y] = segment;

        var polyline = last(polylines);

        polyline.push([x, y]);

        break;
      case 'H': // horizontal line
        var [_, x] = segment;

        var polyline = last(polylines);
        var [x0, y0] = last(polyline);

        polyline.push([x, y0]);

        break;
      case 'V': // vertical line
        var [_, y] = segment;

        var polyline = last(polylines);
        var [x0, y0] = last(polyline);

        polyline.push([x0, y]);

        break;
      case 'C': // cubic spline
        var [_, x1, y1, x2, y2, x3, y3] = segment;

        var polyline = last(polylines);
        var [x0, y0] = last(polyline);

        // approximate cubic spline with polyline
        var pts = cubicDivide(x0, y0, x1, y1, x2, y2, x3, y3, delta);

        // write gcode for segments
        for (var j = 1; j < pts.length; ++j) {
          var pt = pts[j];
          polyline.push(pt);
        }

        break;
      case 'S': // 'Smooth' cubic spline
        var [_, x2, y2, x3, y3] = segment;

        var polyline = last(polylines);
        var [x0, y0] = last(polyline);

        // calculate [x1, y1] from previous segment
        var x1, y1;
        var prevSegment = segments[i - 1];

        if (prevSegment[0] === 'C' || prevSegment[0] === 'S') {
          var [prevX2, prevY2] = prevSegment.slice(-4, -2);
          x1 = 2 * x0 - prevX2;
          y1 = 2 * y0 - prevY2;
        } else {
          [x1, y1] = [x0, y0];
        }

        // approximate cubic spline with polyline
        var pts = cubicDivide(x0, y0, x1, y1, x2, y2, x3, y3, delta);

        // write gcode for segments
        for (var j = 1; j < pts.length; ++j) {
          var pt = pts[j];
          polyline.push(pt);
        }

        break;
      case 'Q': // quadratic spline
        var [_, x1, y1, x2, y2] = segment;

        var polyline = last(polylines);
        var [x0, y0] = last(polyline);

        // approximate quadratic spline with polyline
        var pts = quadraticDivide(x0, y0, x1, y1, x2, y2, delta);

        // write gcode for segments
        for (var j = 1; j < pts.length; ++j) {
          var pt = pts[j];
          polyline.push(pt);
        }

        break;
      case 'T': // 'Smooth' quadratic spline
        var [_, x2, y2] = segment;

        var polyline = last(polylines);
        var [x0, y0] = last(polyline);

        // calculate [x1, y1] from previous segment
        var x1, y1;
        var prevSegment = segments[i - 1];
        var [prevX2, prevY2] = prevSegment.slice(-4, -2);
        x1 = 2 * x0 - prevX2;
        y1 = 2 * y0 - prevY2;

        // approximate quadratic spline with polyline
        var pts = quadraticDivide(x0, y0, x1, y1, x2, y2, delta);

        // write gcode for segments
        for (var j = 1; j < pts.length; ++j) {
          var pt = pts[j];
          polyline.push(pt);
        }

        break;
      default:
        console.error(`Unsupported SVG path command: ${command}`);
        break;
    }
  }

  return polylines;
}

Polylines.svgPath = function (polylines) {
  var pathStrings = [];

  // helper for number formatting
  var fmt = number => number.toFixed(2);

  polylines.forEach(function (polyline) {
    var [x, y] = polyline[0];

    pathStrings.push(`M ${fmt(x)},${fmt(y)}`);

    for (var i = 1; i < polyline.length; i++) {
      [x, y] = polyline[i];
      pathStrings.push(`L ${fmt(x)},${fmt(y)}`);
    }
  }, this);

  var pathString = pathStrings.join(' ');

  return pathString;
}

Polylines.optimize = function (polylines, tol) {
  ClipperLib.use_lines = true;

  var subj = Polylines.toInt(polylines, tol);

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

  // c.AddPath([], ClipperLib.PolyType.ptClip, true);
  c.Execute(ClipperLib.ClipType.ctDifference, solution);

  var optimized = [];

  var polynode = solution.GetFirst();

  while (polynode) {
    var polyline = Polylines.fromInt([polynode.Contour()], tol)[0];

    if (!polynode.IsOpen) {
      polyline.push(polyline[0]);
    }

    optimized.push(polyline);

    polynode = polynode.GetNext();
  }

  return optimized.reverse();
};

// export
window.Polylines = Polylines;

console.log('Polylines module imported!')

})();