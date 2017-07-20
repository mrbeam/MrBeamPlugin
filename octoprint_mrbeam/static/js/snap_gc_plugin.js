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

  Element.prototype.embed_gc = function (correctionMatrix, gc_options) {
    this.selectAll('path').forEach(function (path) {
      // calculate transformation matrix
      var matrix = path.transform().totalMatrix;

      if (correctionMatrix !== undefined) {
        matrix = matrix.multLeft(correctionMatrix);
      }

      // parse path string
      var pathString = path.attr('d');
      var segments = Snap.path.toAbsolute(pathString);

      // settings
      var tolerance = gc_options.precision;
      var clippingResolution = 0.1 * gc_options.precision;
      var bounds = gc_options.clipRect;
      var transformation = [matrix.a, matrix.b,
                            matrix.c, matrix.d,
                            matrix.e, matrix.f]

      // generate polylines
      var polylines;
      // convert segments to polylines
      polylines = Polylines.fromSvgPathSegments(segments, tolerance);
      // simplify polylines
      polylines = Polylines.simplify(polylines, tolerance);
      // apply transformation matrix
      polylines = Polylines.transform(polylines, transformation);
      // clip to boundaries
      polylines = Polylines.clipRect(polylines, bounds, clippingResolution);

      // generate gcode
      var gcode = Polylines.gcode(polylines);

      path.attr('mb:gc', gcode);
    }, this);
  };

  Element.prototype.clean_gc = function () {
    var paths = this.selectAll('path');

    paths.forEach(function (path) {
      path.attr('mb:gc', '');
    }, this);
  };
});
