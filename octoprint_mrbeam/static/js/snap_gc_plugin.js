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
	
	/**
	 * generates gc from d attr
	 * 
	 * @param {float} correction_matrix : matrix to be applied on resulting points
	 * @param {float} max_derivation : how precise curves are approximated
	 * @param {float} max_segment_length : maximum length of G1 commands
	 * @returns {undefined}
	 */
	Element.prototype.generate_gc = function (correction_matrix, max_derivation, min_segment_length, max_segment_length) {
		var elem = this;
		
		var max_derivation = max_derivation || .1; // TODO - real dist, not manhattan dist.
		var min_segment_length = min_segment_length || .1; 
		var max_segment_length = max_segment_length || 10; 

		if(max_segment_length < min_segment_length){
			max_segment_length = min_segment_length;
			console.warn("max_segment_length can't be smaller than min_segment_length!");
		}

		if(elem.type !== 'path'){
			console.log('Only path elemts are supported. This is ', elem.type);
			return;
		}

		var transformed_path_array = Snap.path.map(elem.attr('d'), correction_matrix);
		var temp = elem.paper.path(transformed_path_array).attr('opacity',0);

		var length = temp.getTotalLength();
		var progress_callback = function(position){ 
			console.log('progress', position/length); 
		};
		var points = temp.approximateArray(0, length, max_derivation, min_segment_length, max_segment_length, progress_callback);
		
		temp.remove();
		var gc = 'G0X'+points[0].x.toFixed(2)+'Y'+points[0].y.toFixed(2)+"\n";
		for (var i = 1; i < points.length; i++) {
			var p = points[i];
			gc += 'G1X'+p.x.toFixed(2)+'Y'+p.y.toFixed(2)+"\n";
//			DEBUG visualization
			elem.parent().append(elem.paper.circle(p.x, p.y, 1.0).attr({fill:'green'}));
		}
		elem.attr('gc', gc);
	};
	
	


		
	Element.prototype.approximateArray = function(start, end, max_derivation, min_segment_length, max_segment_length, progress){
		var elem = this;
		if(start === undefined) start = 0;
		if(end === undefined) end = elem.getTotalLength();
		if(max_derivation === undefined) max_derivation = 5;
		var length = end - start;
		var center = start + length/2;
		var start_point = elem.getPointAtLength(start);
		var end_point = elem.getPointAtLength(end);
//		var angle_rad = start_point.alpha * Math.PI/180;
		var projection_point_x = start_point.x - length * Snap.cos(start_point.alpha);
		var projection_point_y = start_point.y - length * Snap.sin(start_point.alpha);
//		DEBUG visualization
//		elem.parent().append(elem.paper.circle(start_point.x,start_point.y, 0.3).attr({fill:'blue'}));
//		elem.parent().append(elem.paper.circle(end_point.x, end_point.y, 0.3).attr({fill:'cyan'}));
//		elem.parent().append(elem.paper.circle(projection_point_x, projection_point_y, 0.3).attr({fill:'red'}));
		
		var subdivide = false;
		if(length > min_segment_length*2){ // divide segment only if long enough
			if(length > max_segment_length){
				subdivide = true;
			}
			if(Math.abs(projection_point_x - end_point.x) > max_derivation ||
				Math.abs(projection_point_y - end_point.y) > max_derivation){ // Manhattan dist
				subdivide = true;
			} else { // real euclidean dist
				if(Math.pow(projection_point_x - end_point.x,2) + Math.pow(projection_point_y - end_point.y,2) > Math.pow(max_derivation,2)){
					subdivide = true;
				} 
			}
		}
		var points = [];
		if(subdivide){
			var points_first_half = elem.approximateArray(start, center, max_derivation, min_segment_length, max_segment_length, progress);
			var points_second_half = elem.approximateArray(center, end, max_derivation, min_segment_length, max_segment_length, progress); 
			points_second_half.shift(); // drop first, it is the last from the first_half
			points = points_first_half.concat(points_second_half);
		} else {
			points = [start_point, end_point];
		}
		if(typeof progress === 'function'){
			progress(end);
		}
		return points;
	};
	

});

