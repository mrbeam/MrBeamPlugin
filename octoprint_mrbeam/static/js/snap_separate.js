//    Little snapsvg.io plugin to convenient splitting of groups.
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
	// just a helper
	var _p2s = /,?([achlmqrstvxz]),?/gi;
	var _convertToString = function (arr) {
		return arr.join(',').replace(_p2s, '$1');
	};


	/**
	 * Separates a group into n groups
	 * Supports rect, ellipse, circle, line, polyline, polygon and of course path
	 * 
	 * based on 
	 * https://github.com/duopixel/Method-Draw/blob/master/editor/src/svgcanvas.js
	 * Modifications: Timo (https://github.com/timo22345)
	 * 
	 * @returns {group} path element
	 */
	Element.prototype.separate = function (max_parts) {
		if(this.type !== 'g') return;
		var old_element = this;
		var parts = [];
		var children = this.children();
		var parent = old_element.parent();
		for (var i = 0; i < children.length; i++) {
			var child = children[i];
			var g = parent.group();
			g.attr(old_element.attr());
			g.append(child);
//			parent.append(g);
			parts.push(g);
		}

		return parts;
	};




});

