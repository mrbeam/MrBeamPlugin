function cubicCoefficients(x0, x1, x2, x3) {
  return [x0, 3.0 * (x1 - x0), 3.0 * (x0 - 2.0 * x1 + x2), x3 - x0 + 3.0 * (x1 - x2)];
}

function cubicDerivativeCoefficients(x0, x1, x2, x3) {
    return [3.0 * (x1 - x0), 6.0 * (x0 - 2.0 * x1 + x2), 3.0 * (x3 - x0) + 9.0 * (x1 - x2)];
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
  pts[0] = { x: x0, y: y0 };
  pts[n] = { x: x3, y: y3 };

  // interpolate points
  for (i = 1; i < n; ++i) {
    var t = i * dt;
    var t2 = t * t;
    var t3 = t2 * t;

    x = a0 + a1 * t + a2 * t2 + a3 * t3;
    y = b0 + b1 * t + b2 * t2 + b3 * t3;

    pts[i] = { x: x, y: y };
  }

  return pts;
}

function cubicLength(x0, y0, x1, y1, x2, y2, x3, y3, tolerance=1e-8) {
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

// credits: https://github.com/scijs/integrate-adaptive-simpson
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

// credits: https://github.com/scijs/integrate-adaptive-simpson
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

var pointCount = 0;

function gcodeFromPath(pathString, settings) {
    pointCount = 0;

    // get segments from path
    var segments = Snap.path.toCubic(pathString);
    // TODO: Switch to:
    // var segments = Snap.path.toAbsolute(pathString);

    // storage for gcode commands
    gcodeCommands = [];

    // storage for current location
    var [currentX, currentY] = [0.0, 0.0];

    // helper for number formatting
    var fmt = function(number) { return number.toFixed(2); };

    segments.forEach(function (segment) {
        var command = segment[0];

        switch (command) {
            case 'M': // move
                var [_, x, y] = segment;

                gcodeCommands.push(`G0X${fmt(x)}Y${fmt(y)}`);

                // move to position
                [currentX, currentY] = [x, y];

                break;
            case 'C': // cubic spline
                var [_, x1, y1, x2, y2, x3, y3] = segment;

                // approximate cubic spline with polyline
                var pts = cubicDivide(currentX, currentY, x1, y1, x2, y2, x3, y3, settings.delta);

                // write gcode for segments
                pts.forEach(function (pt) {
                    gcodeCommands.push(`G1X${fmt(pt.x)}Y${fmt(pt.y)}`);
                    pointCount += 1;
                }, this);

                // move to end point
                [currentX, currentY] = [x3, y3];

                break;
        }
    }, this);

    var gcode = gcodeCommands.join('\n');

    console.log(`#Points = ${pointCount} with delta = ${settings.delta}`)

    return gcode;
}







/* global Snap */

//    GC plugin - a snapsvg.io plugin.
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
	
	Element.prototype.embed_gc = function(correctionMatrix, gc_options){
		this.selectAll('path').forEach(function(path) {
			var matrix = path.transform().totalMatrix;

			if (correctionMatrix !== undefined) {
				matrix = matrix.multLeft(correctionMatrix);
			}

			var pathString = path.attr('d');
			pathString = Snap.path.map(pathString, matrix);

			var gcode = gcodeFromPath(pathString, {delta: 0.1});

			path.attr('mb:gc', gcode);
		}, this);
	};
	
	Element.prototype.clean_gc = function(){
		this.selectAll('path').forEach(function(path) {
			path.attr('mb:gc', '');
		}, this);
	};
});
