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
	 * @param {float} max_derivation : how precise curves are approximated
	 * @param {float} max_segment_length : maximum length of G1 commands
	 * @returns {undefined}
	 */
	Element.prototype.generate_gc = function (max_derivation, max_segment_length) {
		var elem = this;
		
		var max_derivation = max_derivation || .1; // TODO - real dist, not manhattan dist.
		var max_segment_length = max_segment_length || 10; 

		if(elem.type !== 'path'){
			console.log('Only path elemts are supported. This is ', elem.type);
			return;
		}

		var points = elem.approximateArray(0, elem.getTotalLength(), max_derivation);

		var gc = 'G0X'+points[0].x.toFixed(2)+'Y'+points[0].y.toFixed(2)+"\n";
		for (var i = 1; i < points.length; i++) {
			var p = points[i];
			gc += 'G1X'+p.x.toFixed(2)+'Y'+p.y.toFixed(2)+"\n";
		}
		elem.attr('gc', gc);
	};
	
	


		
	Element.prototype.approximateArray = function(start, end, max_derivation){
		console.log("approx", start, end);
		var elem = this;
		if(start === undefined) start = 0;
		if(end === undefined) end = elem.getTotalLength();
		if(max_derivation === undefined) max_derivation = 5;
		var length = end - start;
		var center = start + length/2;
		var start_point = elem.getPointAtLength(start);
		var end_point = elem.getPointAtLength(end);
		var angle_rad = start_point.alpha * Math.PI/180;
		var projection_point_x = start_point.x - length * Math.cos(angle_rad);
		var projection_point_y = start_point.y - length * Math.sin(angle_rad);
//		DEBUG visualization
//		elem.parent().append(elem.paper.circle(start_point.x,start_point.y, 0.3).attr({fill:'blue'}));
//		elem.parent().append(elem.paper.circle(end_point.x, end_point.y, 0.3).attr({fill:'cyan'}));
//		elem.parent().append(elem.paper.circle(projection_point_x, projection_point_y, 0.3).attr({fill:'red'}));
		
		var subdivide = false;
		if(Math.abs(projection_point_x - end_point.x) > max_derivation){
			subdivide = true;
		} else {
			if(Math.abs(projection_point_y - end_point.y) > max_derivation){
				subdivide = true;
			}
		}
		var points = [];
		if(subdivide){
			points = elem.approximateArray(start, center, max_derivation)
					.concat(elem.approximateArray(center, end, max_derivation));
		} else {
			points = [start_point, end_point];
		}
		
//		DEBUG visualization
//		for (var idx = 0; idx < points.length; idx++) {
//			var p = points[idx];
//			elem.parent().append(elem.paper.circle(p.x, p.y, 0.4).attr({fill:'green'}));
//		}
		return points;
	};
	

});

