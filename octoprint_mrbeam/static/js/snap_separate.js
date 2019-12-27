//    Little snapsvg.io plugin to convenient splitting of groups.
//    Copyright (C) 2019  Teja Philipp <osd@tejaphilipp.de>
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
	 * Supports rect, ellipse, circle, line, polyline, polygon, text, tspan and of course path
	 * Doesn't support use, symbol (use unref.js to avoid problems)
	 * 
	 * 
	 * @returns {array} svg snippets (empty means not separatable)
	 */
	Element.prototype.separate_children = function (max_parts=0) {
		if(this.type !== 'g'){
			console.warn("Can't separate " + this.type);
			return [];
		}
		let old_element = this;

		let elem_ids = []
		let native_elements = old_element.selectAll('path, circle, ellipse, rect, line, polyline, polygon, image, text, tspan');
		for (var i = 0; i < native_elements.length; i++) {
			var ne = native_elements[i];
			ne.attr("mb:id", ne.node.id);
			elem_ids.push(ne.node.id);
		}

		let buckets = max_parts > 0 ? Math.min(elem_ids.length, max_parts) : elem_ids.length;
		if(buckets <= 1) {
			console.info("Not separatable.");
			return [];
		}
		let max_elem_per_bucket = Math.ceil(elem_ids.length / buckets);
		
		let parts = [];
		for (var i = 0; i < buckets; i++) {
			let n = old_element.clone();
			const idx_start = i * max_elem_per_bucket;
			const idx_end = idx_start + max_elem_per_bucket;
			const exclude_list = elem_ids.slice(idx_start, idx_end);
			if(exclude_list.length > 0){
				console.log("exclude_list", exclude_list);
				n.remove_native_elements(exclude_list);
				parts.push(n);
			}
		}

		return parts;
	};

	Element.prototype.separate_colors = function () {
		if(this.type !== 'g'){
			console.warn("Can't separate " + this.type);
			return;
		}
		let old_element = this;
		let elem_colors = old_element.get_stroke_colors();
		
		let parts = [];
		for (var i = 0; i < elem_colors.length; i++) {
			let n = old_element.clone();
			const col = elem_colors[i];
			const selector = '[stroke]:not([stroke="'+col+'"])'
			n.selectAll(selector).remove();
			if(n.children().length > 0){
				parts.push(n);
			}
			
		}
		
		// one part for non-stroked elements
		let n = old_element.clone();
		n.selectAll(":not([stroke])").remove();
		if(n.children().length > 0){
			parts.push(n);
		}
		return parts;
	};
	
	// TODO move to snap_helpser.js (to be created) ??
	Element.prototype.get_stroke_colors = function() {
		let elem = this;
		let colored_children = elem.selectAll('[stroke]');

		let elem_colors = []
		for (var i = 0; i < colored_children.length; i++) {
			let stroke = colored_children[i].attr()['stroke'];
			if(stroke !== null && stroke !== ''){
				elem_colors.push(stroke);
			}
		}
		elem_colors = [...new Set(elem_colors)];
		return elem_colors;
	};

	Element.prototype.remove_native_elements = function(exclude_mbids){
		let items = this.selectAll("path, circle, rect, image, ellipse, line, polyline, polygon, text, tspan");
		for (let i = 0; i < items.length; i++) {
			let e = items[i];
			if(exclude_mbids.indexOf(e.attr('mb:id')) < 0){
				e.remove();
			}
		}
	};


});

