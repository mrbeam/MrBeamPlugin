//    SVG cleaner - a snapsvg.io plugin to normalize and clean SVGs.
//    Copyright (C) 2016  Florian Becker <florian@mr-beam.org>
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
	 * @param {boolean} toCubics : use only cubic path segments
	 * @param {integer} dec : number of digits after decimal separator. defaults to 5
	 * @returns {undefined}
	 */
	Element.prototype.clean = function () {
		var elem = this;
		if (!elem || !elem.paper){
  			return;
        } // don't handle unplaced elements. this causes double handling.

		var children = elem.children();
		if (children.length > 0) {
			for (var i = 0; i < children.length; i++) {
				var child = children[i];
				child.clean();
			}
			return;
		}

        console.log(elem)

	};
});
