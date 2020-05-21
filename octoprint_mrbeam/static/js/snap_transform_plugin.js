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


(function() {
	Snap.plugin(function (Snap, Element, Paper, global) {

		var self = {};

		Paper.prototype.mbtransform_init = function(){
			var paper = this;
			self.paper = paper;
			self.transformHandleGroup = paper.select(self.config.transformHandleGroupId);
			self.translateHandle = paper.select(self.config.translateHandleId);
			self.scaleHandleNE = paper.select(self.config.scaleHandleNEId);
			self.scaleHandleNW = paper.select(self.config.scaleHandleNWId);
			self.scaleHandleSE = paper.select(self.config.scaleHandleSEId);
			self.scaleHandleSW = paper.select(self.config.scaleHandleSWId);
			self.rotHandle = paper.select(self.config.rotHandleId);
			self.initialized = true;
			paper.mbtransform = self;
		}

		self.initialized = false;
		self.config = {
			transformHandleGroupId: '#mbtransformHandleGroup',
			translateHandleId: '#translateHandle',
			scaleHandleNEId: '#scaleHandleNE',
			scaleHandleNWId: '#scaleHandleNW',
			scaleHandleSWId: '#scaleHandleSW',
			scaleHandleSEId: '#scaleHandleSE',
			rotHandleId: '#rotHandle',
			minTranslateHandleSize: 24
		}

		self.session = {};

		/**
		 * transform handler for translate, scale, rotate
		 */

		self.translateStart = function( target, x, y, event ){ // x, y, dx, dy pixel coordinates according to <svg width="..." height="..." >
			// hide scale & rotate handle
			self.transformHandleGroup.node.classList.add('translate');
		}	

		self.translateMove = function( target, dx, dy, x, y, event ){
			// calculate viewbox coordinates incl. zoom & pan (mm)
			const dxMM = self._convertToViewBoxUnits(dx);
			const dyMM = self._convertToViewBoxUnits(dy);

			// store session changes
			self.session.translate.dx = dxMM;
			self.session.translate.dy = dyMM;

			// move translateHandle
			self._sessionUpdate();

			// apply transform to target elements via callback

		}	

		self.translateEnd = function( target, dx, dy, x, y){
			// show scale & rotate handle
			self._alignHandlesToBB();
			self.transformHandleGroup.node.classList.remove('translate');
			self._sessionReset();
		}

		self.rotateStart = function( target, x, y, event ){ // x, y, dx, dy pixel coordinates according to <svg width="..." height="..." >
			const xMM = self._convertToViewBoxUnits(x);
			const yMM = self._convertToViewBoxUnits(y);
			// hide scale & rotate handle
			self.transformHandleGroup.node.classList.add('rotate');
			console.log(event);
			// rotation center
			self.session.rotate.ax = xMM;
			self.session.rotate.ay = yMM;
			self.session.rotate.cx = self.session.bbox.x + self.session.bbox.width / 2;
			self.session.rotate.cy = self.session.bbox.y + self.session.bbox.height / 2;
			self.paper.selectAll('#debugRotCenter').remove();
			self.paper.circle({cx: self.session.rotate.cx, cy: self.session.rotate.cy, r: 2, fill:'#ff0000', id:"debugRotCenter"});
			self.paper.selectAll('#debugAngle').remove();
			self.paper.path({d: 'M'+ self.session.rotate.cx+','+self.session.rotate.cy+'L'+xMM+','+yMM, stroke:'#f00000', id:"debugAngle"});
		}	

		self.rotateMove = function( target, dx, dy, x, y, event ){
			// calculate viewbox coordinates incl. zoom & pan (mm)
			const dxMM = self._convertToViewBoxUnits(dx);
			const dyMM = self._convertToViewBoxUnits(dy);
			const xMM = self._convertToViewBoxUnits(x);
			const yMM = self._convertToViewBoxUnits(y);

			//    b
			//   /
			//  /  \ r angle
			// c----------a

			var ax = self.session.rotate.ax;
			var ay = self.session.rotate.ay;
			var cx = self.session.rotate.cx;
			var cy = self.session.rotate.cy;
			var bx = ax + dxMM;
			var by = ay + dyMM;

			// store session changes
			self.session.rotate.r = Snap.angle(ax, ay, cx, cy, bx, by);
//			self.session.rotate.r = Snap.angle(cx, cy, ax, ay, bx, by);
//			self.session.rotate.r = Snap.angle(ax, ay, bx, by, cx, cy);
			console.log(self.session.rotate.r);

			// move translateHandle
			self._sessionUpdate();

			// apply transform to target elements via callback

		}	

		self.rotateEnd = function( target, dx, dy, x, y){
			// show scale & rotate handle
			self._alignHandlesToBB();
			self.transformHandleGroup.node.classList.remove('rotate');
			self._sessionReset();
		}
		
		self.scaleStart = function( target, x, y, event ){ // x, y, dx, dy pixel coordinates according to <svg width="..." height="..." >
			var usedHandle = this;
//			console.log(usedHandle.node.id);
			
			// hide scale & rotate handle
			const handleId = usedHandle.node.id;
			self.transformHandleGroup.node.classList.add('scale', handleId);
			
			// determine scale center
			var cx;
			var cy;
			switch (handleId.substr(-2)) {
				case 'SE':
					cx = self.session.bbox.x;
					cy = self.session.bbox.y; //self.session.bbox.y;
					self.session.signX = 1;
					self.session.signY = 1;
					break;
				case 'SW':
					cx = self.session.bbox.x + self.session.bbox.width;
					cy = self.session.bbox.y;
					self.session.signX = -1;
					self.session.signY = 1;
					break;
				case 'NW':
					cx = self.session.bbox.x + self.session.bbox.width;
					cy = self.session.bbox.y + self.session.bbox.height;
					self.session.signX = -1;
					self.session.signY = -1;
					break;
				case 'NE':
					cx = self.session.bbox.x;
					cy = self.session.bbox.y + self.session.bbox.height;
					self.session.signX = 1;
					self.session.signY = -1;
					break;
					
				default:
					console.error("Should never happen!");
					break;
			}
			
			self.session.centerX = cx;
			self.session.centerY = cy;
			self.session.scaleRefX = self.session.bbox.width * self.session.originMatrix.a;
			self.session.scaleRefY = self.session.bbox.height * self.session.originMatrix.d;
			
//			self.paper.selectAll('#debugCenter').remove();
//			self.paper.circle({cx: self.session.centerX, cy: self.session.centerY, r: 2, fill:'#ff0000', id:"debugCenter"});
//			self.paper.selectAll('#debugReference').remove();
//			self.paper.path({d: 'M'+ self.session.centerX+','+self.session.centerY+'h'+(self.session.bbox.width*self.session.signX), stroke:'#f00000', id:"debugReference"});
		}	

		self.scaleMove = function( target, dx, dy, x, y, event ){
			// convert to viewBox coordinates (mm)
			const dxMM = self._convertToViewBoxUnits(dx);
			const dyMM = self._convertToViewBoxUnits(dy);
			const scaleX = (self.session.signX * dxMM + self.session.scaleRefX) / self.session.scaleRefX;
			const scaleY = (self.session.signY * dyMM + self.session.scaleRefY) / self.session.scaleRefY;
//			console.log((scaleX*100).toFixed(1)+'%', dxMM*self.session.signX);

			// store session changes
			self.session.scale.sx = scaleX;
			self.session.scale.sy = scaleY;
			self.session.scale.cx = self.session.centerX;
			self.session.scale.cy = self.session.centerY;

			// move translateHandle
			self._sessionUpdate();

			// apply transform to target elements via callback

		}	

		self.scaleEnd = function( target, dx, dy, x, y){
			self._sessionReset();
			// show scale & rotate handle
			self._alignHandlesToBB();
			self.transformHandleGroup.node.classList.remove('scale', 'scaleHandleNE', 'scaleHandleNW', 'scaleHandleSW', 'scaleHandleSE');
			
		}	

		self._sessionUpdate = function(){
			const dx = self.session.translate.dx;
			const dy = self.session.translate.dy;
			const sx = self.session.scale.sx;
			const sy = self.session.scale.sy;
			const cx = self.session.scale.cx;
			const cy = self.session.scale.cy;
			const rot = self.session.rotate.r;
			const rcx = self.session.rotate.cx;
			const rcy = self.session.rotate.cy;
			
//			console.log("t", dx, dy, "s", sx, sy, "r", rot);
			
			var m = Snap.matrix();
			// SRT order, finally add former matrix
			m.scale(sx, sy, cx, cy).rotate(rot, rcx, rcy).translate(dx, dy).add(self.session.originMatrix);
			self.translateHandle.transform(m);
//			console.log("upd", m.toTransformString());
		}
		
		self._sessionReset = function(){
			self.session.translate = {dx: 0, dy:0};
			self.session.scale = {sx: 1, sy: 1, dx: 0, dy: 0};
			self.session.rotate = {r: 0, cx: 0, cy: 0};
			self.session.originMatrix = self.translateHandle.transform().localMatrix;
			self.session.bbox = self.translateHandle.getBBox();
			console.log("rst", self.session.originMatrix.split());
		};

		/**
		 * @param {Snap.Element, Snap.Set, CSS-Selector} elements_to_transform
		 * @param {function} transformMatrixCallback  
		 *
		 * @returns {undefined}
		 */
		self.activate = function (elements_to_transform, transformMatrixCallback) {
			if(!elements_to_transform){
				console.warn("Nothing to transform. Element was ", elements_to_transform);
				return;
			}

			if(typeof elements_to_transform === "string"){
				const selector = elements_to_transform;
				elements_to_transform = self.paper.selectAll(selector);
				if(elements_to_transform.length === 0){
					console.warn("No elements to transform. Selector was ", selector);
					return;
				}
			}

			// get bounding box of selector
			const bbox = self._getBBoxFromElementsWithMinSize(elements_to_transform);

			self._alignHandlesToBB(bbox);

			// set transform session origin
			self._sessionReset();
			self.session.bbox = bbox;

			// attach drag handlers for translation
			self.translateHandle.drag(
				self.translateMove.bind( self.translateHandle, elements_to_transform ),
				self.translateStart.bind( self.translateHandle, elements_to_transform ),
				self.translateEnd.bind( self.translateHandle, elements_to_transform )
			);
	
			self.rotHandle.drag(
				self.rotateMove.bind( self.rotHandle, elements_to_transform ),
				self.rotateStart.bind( self.rotHandle, elements_to_transform ),
				self.rotateEnd.bind( self.rotHandle, elements_to_transform )
			);
	
			const scaleHandles = [self.scaleHandleNE, self.scaleHandleNW, self.scaleHandleSW, self.scaleHandleSE];
			for (var i = 0; i < scaleHandles.length; i++) {
				var h = scaleHandles[i];
				h.drag(
					self.scaleMove.bind( h, elements_to_transform ),
					self.scaleStart.bind( h, elements_to_transform ),
					self.scaleEnd.bind( h, elements_to_transform )
				);
			}

			self.transformHandleGroup.node.classList.add('active');
		};

		self.deactivate = function(){
			self.transformHandleGroup.removeClass('active');

			// remove drag handlers
			self.translateHandle.undrag();

			// reset transform session origin
			self.session.originMatrix = null;
			self.session.bbox = null;

			// reset handles
			self.translateHandle.attr({x:0, y:0, width:0, height:0, transform: ''});
			self.scaleHandleNW.transform('');
			self.scaleHandleSW.transform('');
			self.scaleHandleNE.transform('');
			self.scaleHandleSE.transform('');
			self.rotHandle.transform('');
		};

		self._convertToViewBoxUnits = function(val){
			return val * MRBEAM_PX2MM_FACTOR_WITH_ZOOM;
		};

		self._alignHandlesToBB = function(bbox){
			if(bbox) {
				// resize translateHandle
				self.translateHandle.attr(bbox);
			} else {
				// just align every other handle
				bbox = self.translateHandle.getBBox();
			}

			// align scaleHandles
			self.scaleHandleNW.transform('t'+bbox.x+','+bbox.y);
			self.scaleHandleSW.transform('t'+bbox.x+','+(bbox.y+bbox.height));
			self.scaleHandleNE.transform('t'+(bbox.x+bbox.width)+','+bbox.y);
			self.scaleHandleSE.transform('t'+(bbox.x+bbox.width)+','+(bbox.y+bbox.height));
			self.rotHandle.transform('t'+(bbox.x+bbox.width+self.config.minTranslateHandleSize)+','+(bbox.y+bbox.height/2));
		};

		self._getBBoxFromElementsWithMinSize = function(elements){
			let bb = elements.getBBox();
			let dw = bb.width - self.config.minTranslateHandleSize;
			if(dw < 0){
				bb.width += -dw;
				bb.w += -dw;
				bb.x += dw/2; // dw is negative
				bb.x2 += -dw/2; // dw is negative
			}
			let dh = bb.height - self.config.minTranslateHandleSize;
			if(dh < 0){
				bb.height += -dh;
				bb.h += -dh;
				bb.y += dh/2; // dh is negative
				bb.y2 += -dh/2; // dh is negative
			}
			let x = bb.x;
			let y = bb.y;
			let w = bb.width;
			let h = bb.height;
			return { x: x, y: y, width: w, height: h };
	//		return bb;
		}

	});

})();