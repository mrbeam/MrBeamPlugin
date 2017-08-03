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
    if (!gc_options || !gc_options.enabled) {
        return;
    }

    // settings
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

      var norm = (x, y) => Math.sqrt(x**2 + y**2);

      var scaleX = norm(matrix.a, matrix.b);
      var scaleY = norm(matrix.c, matrix.d);

      var scale = Math.max(scaleX, scaleY);

      var tolerance = gc_options.precision / scale;

      // parse path string
      var pathString = element.attr("d");
      var segments = Snap.path.toAbsolute(pathString);

      // generate paths
      var paths = mrbeam.path.parse(segments, tolerance);

      // simplify polylines
      paths = mrbeam.path.simplify(paths, tolerance);

      // apply transformation matrix
      paths = mrbeam.path.transform(paths, xform);

      // clip working area borders
      if (gc_options.clip_working_area) {
          var x = bounds[0];
          var y = bounds[1];
          var w = bounds[2] - bounds[0];
          var h = bounds[3] - bounds[1];
          var clip = [
              mrbeam.path.rectangle(x, y, w, h)
          ];
          var clip_tolerance = 0.1 * tolerance

          // ANDYTEST this needs to go...
          var first = true;
          var str = "[[";
          for (var i = 0; i < clip[0].length; i++) {
              if (!first) {
                  str += ",";
              } else {
                  first = false;
              }
              str += "(x"+clip[0][i]['x']+",y"+clip[0][i]['y']+")";
           }
           str += "]]";
          // ANDYTEST...till here

          console.log("clip_working_area: clip_tolerance:"+clip_tolerance+", clip rectangle:" + str);
          paths = mrbeam.path.clip(paths, clip, clip_tolerance);
      }

      // generate gcode
      var gcode = mrbeam.path.gcode(paths);

      element.attr("mb:gc", gcode || " ");
    });
  };

  Element.prototype.clean_gc = function () {
    var elements = this.selectAll("path");

    elements.forEach((element) => element.attr("mb:gc", ""));
  };
});
