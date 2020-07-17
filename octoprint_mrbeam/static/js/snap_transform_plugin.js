/* global Snap */

//    Drag, Scale & Rotate - a snapsvg.io plugin to free transform objects in an svg.
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
			self.scaleHandleN = paper.select(self.config.scaleHandleNId);
			self.scaleHandleE = paper.select(self.config.scaleHandleEId);
			self.scaleHandleS = paper.select(self.config.scaleHandleSId);
			self.scaleHandleW = paper.select(self.config.scaleHandleWId);
			self.rotHandle = paper.select(self.config.rotHandleId);
			self.initialized = true;
			self.translateXVis = paper.select('#translateXVis');
			self.translateYVis = paper.select('#translateYVis');
			self.scaleXVis = paper.select('#scaleXVis');
			self.scaleYVis = paper.select('#scaleYVis');
			self.rotateVis = paper.select('#rotateVis');
			self.translateXText = paper.select('#translateXText');
			self.translateYText = paper.select('#translateYText');
			self.scaleXText = paper.select('#scaleXText');
			self.scaleYText = paper.select('#scaleYText');
			self.rotateText = paper.select('#rotateText');
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
			scaleHandleNId: '#scaleHandleNN',
			scaleHandleEId: '#scaleHandleEE',
			scaleHandleSId: '#scaleHandleSS',
			scaleHandleWId: '#scaleHandleWW',
			rotHandleId: '#rotHandle',
			minTranslateHandleSize: 24,
			
			visualization: false // enables visual debugging: click points, angle, scale center, etc...
		}

		self.session = {lastUpdate: 0};

		/**
		 * transform handler for translate, scale, rotate
		 */

		self.translateStart = function( target, x, y, event ){ // x, y, dx, dy pixel coordinates according to <svg width="..." height="..." >
			// hide scale & rotate handle
			self.transformHandleGroup.node.classList.add('translate');
			
			self.session.translate.cx = self.session.bb.cx;
			self.session.translate.cy = self.session.bb.cy;
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

		}	

		self.translateEnd = function( target, dx, dy, x, y){
			
			// show scale & rotate handle
			self._alignHandlesToBB();
			self.transformHandleGroup.node.classList.remove('translate');
			self._sessionReset();
			
		}

		self.rotateStart = function( target, x, y, event ){ // x, y, dx, dy pixel coordinates according to <svg width="..." height="..." >
			
			// hide scale & rotate handle
			self.transformHandleGroup.node.classList.add('rotate');

			// rotation center
			const handleMatrix = this.transform().localMatrix; // handle origin as first point
			self.session.rotate.ax = handleMatrix.e;
			self.session.rotate.ay = handleMatrix.f;
			self.session.rotate.cx = self.session.bb.cx;
			self.session.rotate.cy = self.session.bb.cy;
			self.session.rotate.ocx = self.session.bboxWithoutTransform.cx;
			self.session.rotate.ocy = self.session.bboxWithoutTransform.cy;
			self.session.originInvert = self.session.originMatrix.invert(); // TODO move to session Start instead of scale/rotate start

		}	

		self.rotateMove = function( target, dx, dy, x, y, event ){
			const dxMM = self._convertToViewBoxUnits(dx);
			const dyMM = self._convertToViewBoxUnits(dy);
			const ax = self.session.rotate.ax;
			const ay = self.session.rotate.ay;
			const cx = self.session.rotate.cx;
			const cy = self.session.rotate.cy;
			
			snap.select('#scaleCenter').attr({cx: cx, cy: cy});

			
			// calculate viewbox coordinates incl. zoom & pan (mm)
			const bx = self.session.rotate.bx = ax + dxMM;
			const by = self.session.rotate.by = ay + dyMM;

			// store session changes
			//    b
			//   /
			//  /  \ r angle
			// c----------a
			self.session.rotate.r = Snap.angle(bx, by, ax, ay, cx, cy);

			// move translateHandle
//			this.transform(`translate(${dxMM}, ${dyMM})`)
			self._sessionUpdate();

		}	

		self.rotateEnd = function( target, dx, dy, x, y){
			
			// show scale & rotate handle
			self._alignHandlesToBB();
			self.transformHandleGroup.node.classList.remove('rotate');
			self._sessionReset();
			
		}
		
		self.scaleStart = function( target, x, y, event ){ // x, y, dx, dy pixel coordinates according to <svg width="..." height="..." >
			
			// hide scale & rotate handle
			const usedHandle = this;
			const handleId = usedHandle.node.id;
			self.transformHandleGroup.node.classList.add('scale', handleId);
			
			let scaleCenterHandle;
			switch (handleId.substr(-2)) {
				case 'SE':
					scaleCenterHandle = self.scaleHandleNW;
					self.session.scale.signX = 1;
					self.session.scale.signY = 1;
					self.session.scale.prop = true;
					break;
				case 'SW':
					scaleCenterHandle = self.scaleHandleNE;
					self.session.scale.signX = -1;
					self.session.scale.signY = 1;
					self.session.scale.prop = true;
					break;
				case 'NW':
					scaleCenterHandle = self.scaleHandleSE;
					self.session.scale.signX = -1;
					self.session.scale.signY = -1;
					self.session.scale.prop = true;
					break;
				case 'NE':
					scaleCenterHandle = self.scaleHandleSW;
					self.session.scale.signX = 1;
					self.session.scale.signY = -1;
					self.session.scale.prop = true;
					break;
				case 'NN':
					scaleCenterHandle = self.scaleHandleS;
					self.session.scale.signX = 0;
					self.session.scale.signY = -1;
					self.session.scale.prop = false;
					break;
				case 'EE':
					scaleCenterHandle = self.scaleHandleW;
					self.session.scale.signX = 1;
					self.session.scale.signY = 0;
					self.session.scale.prop = false;
					break;
				case 'SS':
					scaleCenterHandle = self.scaleHandleN;
					self.session.scale.signX = 0;
					self.session.scale.signY = 1;
					self.session.scale.prop = false;
					break;
				case 'WW':
					scaleCenterHandle = self.scaleHandleE;
					self.session.scale.signX = -1;
					self.session.scale.signY = 0;
					self.session.scale.prop = false;
					break;
					
				default:
					console.error("Should never happen!");
					break;
			}
			
			
			const handleMatrix = this.transform().localMatrix;
			// translation of the scaling handle
			self.session.scale.mx = handleMatrix.e;
			self.session.scale.my = handleMatrix.f;
			
			self.session.originInvert = self.session.originMatrix.invert();
			
			// scaling center
			const scm = scaleCenterHandle.transform().localMatrix
			self.session.scale.tcx = scm.e;
			self.session.scale.tcy = scm.f;
			self.session.scale.cx = self.session.originInvert.x(scm.e, scm.f);
			self.session.scale.cy = self.session.originInvert.y(scm.e, scm.f);
//			self.session.scale.cx = cx; //self.session.originMatrix.x(cx, cy);
//			self.session.scale.cy = cy; //self.session.originMatrix.y(cx, cy);
			
			// reference width & height for current session needs former transformation to be applied
			const bbNT = self.session.bboxWithoutTransform;
			self.session.scale.refX = bbNT.width; // * self.session.originTransform.scalex;
			self.session.scale.refY = bbNT.height; // * self.session.originTransform.scaley;
			

			
		}	

		self.scaleMove = function( target, dx, dy, x, y, event ){
			// convert to viewBox coordinates (mm)
//			const [dxMM, dyMM] = self._convertToViewBoxUnitsWithTransform(dx, dy);
//			const currentRotation = self.session.originTransform.rotate;
//			const radians = currentRotation * Math.PI / 180;
			
			const dxMM = self._convertToViewBoxUnits(dx);
			const dyMM = self._convertToViewBoxUnits(dy);

			const sss = self.session.scale;
			sss.dxMM = dxMM;
			sss.dyMM = dyMM;
			
			
			// mouse position transformed the same way like the handles to calculate scaling distances within rotated coordinate system
			const rotatedMouseX = self.session.originInvert.x(dxMM + sss.mx, dyMM + sss.my);
			const rotatedMouseY = self.session.originInvert.y(dxMM + sss.mx, dyMM + sss.my);
			
			snap.select('#rotatedMouse').attr({cx: rotatedMouseX, cy:rotatedMouseY});
			snap.select('#scaleCenter').attr({cx: sss.cx, cy:sss.cy});
			
			const distX = (rotatedMouseX - sss.cx);
			const distY = (rotatedMouseY - sss.cy);
			
			let scaleX = sss.signX * distX / sss.refX
			let scaleY = sss.signY * distY / sss.refY;
			
			if(sss.prop){ // link the factors (min abs value), keep the sign

				let newSx = scaleX * self.session.originTransform.scalex;
				let newSy = scaleY * self.session.originTransform.scaley;
				const signX = Math.sign(scaleX);
				const signY = Math.sign(scaleY);
				const formerSignX = Math.sign(self.session.originTransform.scalex);
				const formerSignY = Math.sign(self.session.originTransform.scaley);
				let formerScale;
				if(Math.abs(newSx) <  Math.abs(newSy)){
					scaleY = signY * Math.abs(scaleX);
					formerScale = Math.abs(self.session.originTransform.scalex);
					sss.dominantAxis = 'x';
				} else {
					scaleX = signX * Math.abs(scaleY);
					formerScale = Math.abs(self.session.originTransform.scaley);
					sss.dominantAxis = 'y';
				}
				sss.sx = scaleX * formerScale * formerSignX;
				sss.sy = scaleY * formerScale * formerSignY; 
				
			} else {
				
				sss.sx = (sss.signX !== 0) ?  scaleX * self.session.originTransform.scalex : 1;
				sss.sy = (sss.signY !== 0) ?  scaleY * self.session.originTransform.scaley : 1;
				
			}
			

			// move scaleHandle
			self._sessionUpdate(this);

		}	

		self.scaleEnd = function( target, dx, dy, x, y){
			// show scale & rotate handles
			self._alignHandlesToBB();
			self._sessionReset();
			self.transformHandleGroup.node.classList.remove('scale', 'scaleHandleNE', 'scaleHandleNW', 'scaleHandleSW', 'scaleHandleSE', 'scaleHandleNN', 'scaleHandleEE', 'scaleHandleSS', 'scaleHandleWW');
			
		}	

		self._sessionUpdate = function(){
			if(Date.now() - self.session.lastUpdate > 25){ // reduce updates to 40 fps maximum
				
				const dx = self.session.translate.dx;
				const dy = self.session.translate.dy;
				const sx = self.session.scale.sx;
				const sy = self.session.scale.sy;
				const cx = self.session.scale.cx;
				const cy = self.session.scale.cy;
				const degree = self.session.rotate.r;
				
				
				// false. does not respect rotated translations
//				const rcx = self.session.rotate.cx - self.session.originMatrix.e;
//				const rcy = self.session.rotate.cy - self.session.originMatrix.f;
//				console.log("rcx", rcx, '=', self.session.rotate.cx, '-', self.session.originMatrix.e);

				const rcx = self.session.rotate.ocx;
				const rcy = self.session.rotate.ocy;
				console.log("rcx", rcx, '=', self.session.rotate.ocx);
				

				console.info("S", sx.toFixed(2), sy.toFixed(2), "R", degree.toFixed(2)+'°', "T", dx, dy );

				let m = Snap.matrix();
				// SRT order, alipplied on former matrix
				m.add(self.session.originMatrix);
			
				m.scale(sx, sy, cx, cy).rotate(degree, rcx, rcy);
				m.e += dx; // apply transformation manually as Matrix.transform() applys rotation and scaling (https://github.com/adobe-webplatform/Snap.svg/blob/master/src/matrix.js#L136)
				m.f += dy;
				self.translateHandle.transform(m);

				if(self.config.visualization){
					self._visualizeTransform();
				}

				self.updateCounter++;
				self.session.lastUpdate = Date.now()

	//			debug stuff
//				const dm = Snap.matrix().translate(self.session.scale.tcx, self.session.scale.tcy).rotate(self.session.originTransform.rotate);
//				snap.select('#scaleAxes').transform(dm);
			}
			
			// apply transform to target elements via callback
			// TODO
		}
		
		self._sessionReset = function(){
			//self.paper.selectAll('.transformVis').attr({d:''});
			self.session.translate = {dx: 0, dy:0};
			self.session.scale = {sx: 1, sy: 1, dx: 0, dy: 0};
			self.session.rotate = {r: 0, cx: 0, cy: 0};
			self.session.originMatrix = self.translateHandle.transform().localMatrix;
			self.session.originTransform = self.session.originMatrix.split();
			self.session.bb = self.translateHandle.getBBox();
			self.session.bboxWithoutTransform = self.translateHandle.getBBox(true);


			console.info("Apply Transform: ", self.session.originMatrix.split());
			
		};
		
		self._visualizeTransform = function(){
			
			// translate
			if(self.session.translate.dx !== 0 || self.session.translate.dy !== 0) {
				self._visualizeTranslate();
			}
			if(self.session.rotate.r !== 0) {
				self._visualizeRotate();
			}
			if(self.session.scale.sx !== 1 || self.session.scale.sy !== 1) {
				self._visualizeScale();
			}

		};

		self._visualizeTranslate = function(){
			const startXh = self.session.translate.cx;
			const startYh = 10;
			const startXv = 10;
			const startYv = self.session.translate.cy;
			const dX = 'M'+ startXh+','+startYh+'v-5h'+self.session.translate.dx+'v5';
			self.translateXVis.attr('d', dX);
			const dY = 'M'+ startXv+','+startYv+'h-5v'+self.session.translate.dy+'h5';
			self.translateYVis.attr('d', dY);
			
			self.translateXText.node.textContent = self.session.translate.dx.toFixed(2);
			self.translateXText.attr({x: startXh, y: startYh});
			self.translateYText.node.textContent = self.session.translate.dy.toFixed(2);
			self.translateYText.attr({x: startXv, y: startYv});
		};

		self._visualizeRotate = function(){
			const ax = self.session.rotate.ax;
			const ay = self.session.rotate.ay;
			const bx = self.session.rotate.bx;
			const by = self.session.rotate.by;
			const cx = self.session.rotate.cx;
			const cy = self.session.rotate.cy;
			self.rotateVis.attr('d', 'M'+ ax+','+ay+'L'+cx+','+cy+'L'+bx+','+by);
			
			self.rotateText.node.textContent = self.session.rotate.r.toFixed(1) + '°';
			self.rotateText.attr({x: ax , y: ay });
		};
		
		self._visualizeScale = function () {
			const gap = 15;
			const dist = 10;
			const sss = self.session.scale;
			const mouseX = sss.mx + sss.dxMM; 
			const mouseY = sss.my + sss.dyMM; 
			const cx = sss.cx;
			const cy = sss.cy;
			const mirrorX = mouseY < cy ? 1 : -1;
			const mirrorY = mouseX < cx ? 1 : -1;
			
			let attrDx = '';
			let labelX = '';
			if(sss.sx !== 1 && sss.signX !== 0 && sss.dominantAxis !== 'y'){ // show only if: axis is scaled && handle is scaling this axis && this axis is dominant in proportional scaling
				if(cy < mouseY){ // show above
					
				} else { // show below
					
				}
				attrDx = `M${cx},${cy}m0,${gap*mirrorX}v${dist*mirrorX}H${mouseX}v${-dist*mirrorX}`
				labelX = mouseX.toFixed(1) + 'mm';
				self.scaleXText.attr({x: (cx + mouseX)/2, y: cy + gap * mirrorX });
			} 
			self.scaleXVis.attr('d', attrDx);
			self.scaleXText.node.textContent = labelX;
			
			let attrDy = '';
			let labelY = '';
			if(sss.sy !== 1 && sss.signY !== 0 && sss.dominantAxis !== 'x'){
				attrDy = `M${cx},${cy}m${gap*mirrorY},0h${dist*mirrorY}V${mouseY}h${-dist*mirrorY}`
				labelY = mouseY.toFixed(1) + 'mm';
				self.scaleYText.attr({x: cx + gap * mirrorY, y:  (cy + mouseY)/2 });
			} 
			self.scaleYVis.attr('d', attrDy);
			self.scaleYText.node.textContent = labelY;
			
			
			
		}
		

		
	
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
			const selection_bbox = self._getBBoxFromElementsWithMinSize(elements_to_transform);

			// store working area size in MM
			self.session.paperBBox = self.paper.select('#coordGrid').getBBox();
			
			// set transform session origin
			self.session.bb = selection_bbox;

			self._alignHandlesToBB(selection_bbox);
			self._sessionReset();

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
	
			const scaleHandles = [
				self.scaleHandleNE, 
				self.scaleHandleNW, 
				self.scaleHandleSW, 
				self.scaleHandleSE, 
				self.scaleHandleN, 
				self.scaleHandleE, 
				self.scaleHandleS, 
				self.scaleHandleW
			];
			for (var i = 0; i < scaleHandles.length; i++) {
				var h = scaleHandles[i];
				h.drag(
					self.scaleMove.bind( h, elements_to_transform ),
					self.scaleStart.bind( h, elements_to_transform ),
					self.scaleEnd.bind( h, elements_to_transform )
				);
			}

			self.transformHandleGroup.node.classList.add('active');
			
			self.updateCounter = 0;
			self.updateFPS = setInterval(function(){
//				if(self.updateCounter > 0) console.log("updateFPS: ", self.updateCounter);
				self.updateCounter = 0;
			}, 1000)
		};

		self.deactivate = function(){
			self.updateFPS = null;
			self.transformHandleGroup.removeClass('active');

			// remove drag handlers
			self.translateHandle.undrag();

			// reset transform session origin
			self.session.originMatrix = null;
			self.session.bb = null;

			// reset handles
//			self.translateHandle.attr({x:0, y:0, width:0, height:0, transform: ''});
//			self.scaleHandleNW.transform('');
//			self.scaleHandleSW.transform('');
//			self.scaleHandleNE.transform('');
//			self.scaleHandleSE.transform('');
//			self.rotHandle.transform('');
		};

		self._convertToViewBoxUnits = function(val){
			return val * MRBEAM_PX2MM_FACTOR_WITH_ZOOM;
		};
		
		self._convertToViewBoxUnitsWithTransform = function(dx, dy){
			const rotation = self.session.originMatrix.split().rotate;
			
			console.log("rotation", rotation, self.session.rotate.r);
			const mat = Snap.matrix().rotate(rotation);
			const dxMM = dx * MRBEAM_PX2MM_FACTOR_WITH_ZOOM;
			const dyMM = dy * MRBEAM_PX2MM_FACTOR_WITH_ZOOM;
			const transformedX = mat.x(dx, dy);
			const transformedY = mat.y(dx, dy);
			return [transformedX, transformedY];
		};
		
//		self._get_pointer_event_position_MM = function(event){
//			var targetBBox = self.paper.node.getBoundingClientRect();
//			const xPx = (event.clientX - targetBBox.left);
//			const yPx = (event.clientY - targetBBox.top);
//			const xPerc = xPx / targetBBox.width;
//			const yPerc = yPx / targetBBox.height;
//			const xMM = xPx * MRBEAM_PX2MM_FACTOR_WITH_ZOOM + MRBEAM_WORKINGAREA_PAN_MM[0];
//			const yMM = yPx * MRBEAM_PX2MM_FACTOR_WITH_ZOOM + MRBEAM_WORKINGAREA_PAN_MM[1];
//			return {xPx: xPx, yPx: yPx, xPerc: xPerc, yPerc: yPerc, xMM: xMM, yMM: yMM};
//		};

		self._alignHandlesToBB = function(bbox_to_wrap){
			const gap = 1;
			if(bbox_to_wrap) {
				// resize translateHandle
				self.translateHandle.transform('');
				self.translateHandle.attr(bbox_to_wrap);
			} else {
				// just align every other handle
				bbox_to_wrap = self.translateHandle.getBBox(true);
			}
			const lm = self.translateHandle.transform().localMatrix;
			const verbose = lm.split();
			const unscaleMat = Snap.matrix().scale(1/verbose.scalex, 1/verbose.scaley)

			// align scaleHandles to rotated BBox
			self.scaleHandleNW.transform(lm.clone().translate(bbox_to_wrap.x, bbox_to_wrap.y).add(unscaleMat));
			self.scaleHandleSW.transform(lm.clone().translate(bbox_to_wrap.x, bbox_to_wrap.y2).add(unscaleMat));
			self.scaleHandleNE.transform(lm.clone().translate(bbox_to_wrap.x2, bbox_to_wrap.y).add(unscaleMat));
			self.scaleHandleSE.transform(lm.clone().translate(bbox_to_wrap.x2, bbox_to_wrap.y2).add(unscaleMat));
			
			self.scaleHandleN.transform(lm.clone().translate(bbox_to_wrap.cx, (bbox_to_wrap.y - gap)).add(unscaleMat));
			self.scaleHandleE.transform(lm.clone().translate((bbox_to_wrap.x2 + gap), bbox_to_wrap.cy).add(unscaleMat));
			self.scaleHandleS.transform(lm.clone().translate(bbox_to_wrap.cx, (bbox_to_wrap.y2 + gap)).add(unscaleMat));
			self.scaleHandleW.transform(lm.clone().translate((bbox_to_wrap.x - gap), bbox_to_wrap.cy).add(unscaleMat));
			self.rotHandle.transform(lm.clone().translate((bbox_to_wrap.x2+self.config.minTranslateHandleSize), bbox_to_wrap.cy).add(unscaleMat));
			
			// align scaleHandles to outerBBox
//			self.scaleHandleNW.transform('t'+bbox_to_wrap.x+','+bbox_to_wrap.y);
//			self.scaleHandleSW.transform('t'+bbox_to_wrap.x+','+bbox_to_wrap.y2);
//			self.scaleHandleNE.transform('t'+bbox_to_wrap.x2+','+bbox_to_wrap.y);
//			self.scaleHandleSE.transform('t'+bbox_to_wrap.x2+','+bbox_to_wrap.y2);
//			
//			self.scaleHandleN.transform('t'+bbox_to_wrap.cx +','+(bbox_to_wrap.y - gap));
//			self.scaleHandleE.transform('t'+(bbox_to_wrap.x2 + gap) +','+bbox_to_wrap.cy);
//			self.scaleHandleS.transform('t'+bbox_to_wrap.cx +','+(bbox_to_wrap.y2 + gap));
//			self.scaleHandleW.transform('t'+(bbox_to_wrap.x - gap) +','+bbox_to_wrap.cy);
//			self.rotHandle.transform('t'+(bbox_to_wrap.x2+self.config.minTranslateHandleSize)+','+bbox_to_wrap.cy);
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
			let x2 = bb.x + bb.width;
			let y2 = bb.y + bb.height;
			let cx = bb.x + bb.width/2;
			let cy = bb.y + bb.height/2;
			let w = bb.width;
			let h = bb.height;
			return { x: x, y: y, cx: cx, cy: cy, x2: x2, y2: y2, width: w, height: h };
		}

	});

})();