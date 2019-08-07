/* global Snap */

//    Unref - a snapsvg.io plugin to dereference <use> elements from svg files.
//    Copyright (C) 2018  Teja Philipp <osd@tejaphilipp.de>
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
	 * bakes transformations of the element and all sub-elements into coordinates
	 *
	 * @param {boolean/function} remove_sources : remove source elements after dereferencing
	 * @returns {undefined}
	 */
	Element.prototype.unref = function (remove_sources = false) {
		var elem = this;
		var elements_to_replace = [];
		var used_source_elements = [];

		// 1. find all <use> elements in subtree
		if(elem.type === 'use'){
			elements_to_replace.push(elem);
		} else {
			elements_to_replace = elem.selectAll('use');
		}

		// 2. replace them and remember the referenced source elements
		for (var i = 0; i < elements_to_replace.length; i++) {
			var e = elements_to_replace[i];
			var src = e._replace_with_src();
			if (src) {
                used_source_elements.push(src);
            }
		}

		// 3. remove the source elements
		var evaluate_remove = typeof(remove_sources) === "function";
		if(remove_sources === true || evaluate_remove){
			for (var i = 0; i < used_source_elements.length; i++) {
				var s = used_source_elements[i];
				if(evaluate_remove){
					var do_remove = remove_sources(s);
					if(do_remove)
						s.remove();
				} else {
					s.remove();
				}
			}
		}
	};

	/**
	 * Replaces an use element with a copy of the src.
	 * The element will be replaced by the path with same id.
	 *
	 * @returns {url} : url of the used src element
	 */
	Element.prototype._replace_with_src = function(){
		var elem = this;
		if (elem.type !== "use"){
			return;
		}

		// check reference and fetch node
		var src_elem_url = elem.attr('xlink:href'); // SVG 1.1
		if(src_elem_url == null) {
			src_elem_url = elem.attr('href'); // SVG 2.0+
		}
		if(src_elem_url == null || src_elem_url === ""){
			console.log("Unable to find referenced element of ", elem);
			return;
		}
		var src_elem = elem.paper.select(src_elem_url);


		if(src_elem){
			// copy attributes
			var attr = elem.attr();
			var new_attrs = src_elem.attr();

			// combine transformations / important placement attributes
			var x_off = attr.x || 0;
			var y_off = attr.y || 0;
			var use_tag_translate_M = Snap.matrix(1,0,0,1,x_off,y_off);
			var transform_M = elem.transform().localMatrix;
			var src_transform_M = src_elem.transform().localMatrix;
			var combined_M = transform_M.multLeft(src_transform_M.multLeft(use_tag_translate_M));
			var new_transform = combined_M.toTransformString();

			// all other attributes
			var attribute_keys = [
				'id', // core attrs
				'style', // styling attrs
				'class',
				'fill', 'fill-opacity', 'fill-rule', // presentation attrs
				'stroke', 'stroke-dasharray', 'stroke-dashoffset', 'stroke-linecap', 'stroke-linejoin', 'stroke-miterlimit', 'stroke-opacity', 'stroke-width',
				'clip-path', 'clip-rule',
				'color', 'color-interpolation', 'color-rendering',
				'filter', 'mask', 'opacity',
				'cursor', 'pointer-events',
				'vector-effect', 'shape-rendering',
				'display',
				'visibility'
			];
			for (var i = 0; i < attribute_keys.length; i++) {
				var key = attribute_keys[i];
				if(attr[key]) new_attrs[key] = attr[key];
			}

			var duplicate = src_elem.clone();
			duplicate.attr(new_attrs);
			duplicate.attr('transform', new_transform);
			elem.before(duplicate);
			elem.remove();
			return src_elem;
		}
	};
});

