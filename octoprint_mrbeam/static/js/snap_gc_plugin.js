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
    // settings
    var tolerance = gc_options.precision;
    var bounds = gc_options.clipRect;
                          
    this.selectAll("path").forEach(function (element) {
      // calculate transformation matrix
      var matrix = element.transform().totalMatrix;

      if (correctionMatrix !== undefined) {
        matrix = matrix.multLeft(correctionMatrix);
      }

      var xform = [
          matrix.a, matrix.b,
          matrix.c, matrix.d,
          matrix.e, matrix.f
      ];

      // parse path string
      var pathString = element.attr("d");
      var segments = Snap.path.toAbsolute(pathString);

      // generate paths
      var paths = mrbeam.path.parse(segments, tolerance);
      
      // simplify polylines
      paths = mrbeam.path.simplify(paths, tolerance);
      
      // apply transformation matrix
      paths = mrbeam.path.transform(paths, xform);
      
      // clip to boundaries
      var x = bounds[0];
      var y = bounds[1];
      var w = bounds[2] - bounds[0];
      var h = bounds[3] - bounds[1];

      var clip = [
        mrbeam.path.rectangle(x, y, w, h)
      ];

      paths = mrbeam.path.clip(paths, clip, 0.1 * tolerance);

      // generate gcode
      var gcode = mrbeam.path.gcode(paths);

      element.attr("mb:gc", gcode);
    });
  };

  Element.prototype.clean_gc = function () {
    var elements = this.selectAll("path");

    elements.forEach((element) => element.attr("mb:gc", ""));
  };
});
