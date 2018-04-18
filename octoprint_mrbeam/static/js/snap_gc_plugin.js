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

  Element.prototype.embed_gc = function (correctionMatrix, gc_options, mb_meta) {
    if (!gc_options || !gc_options.enabled) {
        return;
    }
    mb_meta = mb_meta || {};

    var mrbeam = window.mrbeam;

    // settings
    var bounds = gc_options.clipRect;

      this.selectAll("path").forEach(function (element) {

      var id = element.attr('id');


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

      // clip working area borders - only if item is a misfit
      if (gc_options.clip_working_area && element.hasClass('misfit')) {
          var x = bounds[0];
          var y = bounds[1];
          var w = bounds[2] - bounds[0];
          var h = bounds[3] - bounds[1];
          var clip = [
              mrbeam.path.rectangle(x, y, w, h)
          ];
          var clip_tolerance = 0.1 * tolerance

          if (id.toLowerCase().indexOf('debug') !== -1 || id.toLowerCase().indexOf('andytest') !== -1) {
            console.log("mrbeam.path.clip() id:'"+id+"'"
                +", paths: " + mrbeam.path.pp_paths(paths)
                +", clip:" + mrbeam.path.pp_paths(clip)
                +", clip_tolerance:"+clip_tolerance
            );
          }
          paths = mrbeam.path.clip(paths, clip, clip_tolerance);

          mb_meta[id]['clip_working_area_clipped'] = true;
      } else {
          mb_meta[id]['clip_working_area_clipped'] = false;
      }

      // generate gcode
      var gcode = mrbeam.path.gcode(paths, id, mb_meta[id]);

      element.attr("mb:gc", gcode || " ");
    });
  };

  Element.prototype.clean_gc = function () {
    var elements = this.selectAll("path");

    elements.forEach((element) => element.attr("mb:gc", ""));
  };


});
