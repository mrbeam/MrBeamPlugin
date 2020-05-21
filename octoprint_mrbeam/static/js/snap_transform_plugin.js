/* global Snap */

//    Drag, Scale & Rotate - a snapsvg.io plugin to free transform objects in an svg.
//    Copyright (C) 2015  Teja Philipp <osd@tejaphilipp.de>
//
//    heavily inspired by http://svg.dabbles.info
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

	var stpOptions = {
		transformRect: {id:'mbTransform', strokeWidth: 2, strokeDasharray: '5 5', stroke: '#00aaff', fill: '#00000033'},
		handleFill: "red",
		handleStrokeDashPreset: [5,5],
		handleStrokeWidth: 2,
		handleLength: 22, // TODO combine with handleRadius
		handleRadius: 10, // TODO replace with minimumDraggingSize
		handleSize: 1.25,
		unscale: 1,
		handleStrokeDash: "5,5"
	};
	
	var STP = {}
	STP.translateStart = function( mainEl, x, y, event ){ // x, y, dx, dy pixel coordinates according to <svg width="..." height="..." >
		console.log(x,y);
		// store bbox as reference
		
		// hide scale & rotate handle
		//		
//		mainEl.data('otx', mainEl.data("tx") || 0);
//		mainEl.data('oty', mainEl.data("ty") || 0);



	}	
	STP.translateMove = function( mainEl, dx, dy, x, y, event ){
		console.log(dx,dy,x,y);
		// calculate viewbox coordinates incl. zoom & pan
		
		// move #mbTransform
		
		// move #scaleHandles
		
		// move rotateHandle
		
		// move elements_to_transform
		
//		var udx = sgUnscale * dx * MRBEAM_PX2MM_FACTOR_WITH_ZOOM;
//		var udy = sgUnscale * dy * MRBEAM_PX2MM_FACTOR_WITH_ZOOM;
//		var tx = mainEl.data("otx") + +udx;
//		var ty = mainEl.data("oty") + +udy;
//		mainEl.data("tx", tx);
//		mainEl.data("ty", ty);
//		mainEl.ftUpdateTransform();

	}	
	STP.translateEnd = function( mainEl, dx, dy, x, y){
		// show scale & rotate handle

	}	
	

	/**
	 *
	 *
	 * @returns {undefined}
	 */
	Paper.prototype.mbTransform = function (elements_to_transform, handle_target) {
		// get bounding box of selector
		let bbox = elements_to_transform.getBBox();
		
		// draw translate rect
		if(!handle_target){
			handle_target = this;
		}
		let mbTransform = this.rect(_rectObjFromBB(bbox)).attr(stpOptions.transformRect);
		mbTransform.drag(
			STP.translateMove.bind( mbTransform, elements_to_transform ),
			STP.translateStart.bind( mbTransform, elements_to_transform ),
			STP.translateEnd.bind( mbTransform, elements_to_transform )
		);
		handle_target.append(mbTransform);
	};
	
	function _rectObjFromBB ( bb, minWidth, minHeight ) {
		minWidth = minWidth || 0;
		minHeight = minHeight || 0;
		var x = bb.x;
		var y = bb.y;
		var w = bb.width;
		var h = bb.height;
		if(bb.width < minWidth){
			let d = minWidth - bb.width;
			w = minWidth;
			x = x - d / 2;
		}
		if(bb.height < minHeight){
			let d = minHeight - bb.height;
			h = minHeight;
			y = y - d / 2;
		}
		return { x: x, y: y, width: w, height: h };
	}

	/**
	 * Adds transparent fill if not present.
	 * This is useful for dragging the element around.
	 *
	 * @returns {path}
	 */
	//TODO add fill for Text (like bounding box or similar)
	Element.prototype.add_fill = function(){
		var elem = this;
		var children = elem.selectAll('*');
		if (children.length > 0) {
			for (var i = 0; i < children.length; i++) {
				var child = children[i];
				child.add_fill();
			}
		} else {
			var fill = elem.attr('fill');
			var type = elem.type;
			if(type === 'path' && (fill === 'none' || fill === '')){

				elem.attr({fill: '#ffffff', "fill-opacity": 0});
			}
		}
		return elem;
	};
});

