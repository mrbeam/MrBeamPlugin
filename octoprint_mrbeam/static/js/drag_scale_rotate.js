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

	/**
	 *
	 *
	 * @returns {undefined}
	 */
	Element.prototype.___transformable = function () {
		var elem = this;
		if (!elem || !elem.paper) // don't handle unplaced elements. this causes double handling.
			return;

		// add invisible fill for better dragging.
		elem.add_fill();
//		elem.click(function(){ elem.ftCreateHandles(); });
		elem.click(function(){ elem.paper.mbtransform.activate(elem); });
		return elem;


	};

/**
	 * Adds transparent fill if not present.
	 * This is useful for dragging the element around.
	 *
	 * @returns {path}
	 */
	//TODO add fill for Text (like bounding box or similar)
	Element.prototype.___add_fill = function(){
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


/**
 * Free transform plugin heavily inspired by http://svg.dabbles.info
 *
 */
(function() {

	Snap.plugin( function( Snap, Element, Paper, global ) {

		var ftOption = {
			handleFill: "red",
			handleStrokeDashPreset: [5,5],
			handleStrokeWidth: 2,
			handleLength: 22, // TODO combine with handleRadius
			handleRadius: 10, // TODO replace with minimumDraggingSize
			handleSize: 1.25,
			unscale: 1,
			handleStrokeDash: "5,5"
		};

		Element.prototype.ftToggleHandles = function(){
			if(this.data('handlesGroup')){
				this.ftRemoveHandles();
			} else {
				this.ftCreateHandles();
			}
		};

		Element.prototype.ftCreateHandles = function() {
			var ftEl = this;
			ftEl.ftInit();
			ftEl.ftBeforeTransform();
			var id = ftEl.id;
			var bb = ftEl.getBBox();
			ftEl.ftStoreInitialTransformMatrix();

			const bbT = ftEl.getBBox(1);
			var rad = ftOption.handleRadius * ftOption.unscale;

			var userContent = this.paper.select('#userContent');
			var translateHull = userContent
				.rect(rectObjFromBB(bbT, rad, rad))
				.attr({fill:'grey',opacity:0.3,id:'translateHull',cursor:'move'});

			//check if it needs to be on another side if design is exceeding workArea
			var wa = ftEl.data('wa');
			var rotX = bbT.cx - bbT.width/2 - ftOption.handleLength * ftOption.unscale;
			if( ftEl.matrix.x(rotX,bbT.cy) <= wa.x || ftEl.matrix.x(rotX,bbT.cy) >= wa.x2 ||
				ftEl.matrix.y(rotX,bbT.cy) <= wa.y || ftEl.matrix.y(rotX,bbT.cy)  >= wa.y2)
			{rotX += bbT.width + 2*ftOption.handleLength* ftOption.unscale;}
			var handlesGroup = userContent
				.g(translateHull)
				.attr({id:'handlesGroup'});

			var rotateDragger = handlesGroup
				.path(_getTransformHandlePath('rot')).transform('s'+ftOption.handleSize)
				.attr({id: 'rotateDragger',cursor:'pointer', class:'freeTransformHandle' })
				.data({cx: rotX, cy:bbT.cy});
			handlesGroup.g(rotateDragger).transform(['t', rotX, ',', bbT.cy].join(''));

			//todo make code more generic
			var resizeDragger1 = handlesGroup
				.path(_getTransformHandlePath('se')).transform('s'+ftOption.handleSize)
				.attr({id: 'resizeDragger_'+id, cursor:'se-resize', class:'freeTransformHandle' })
				.data({cx: bbT.x2, cy: bbT.y2});
			handlesGroup.g(resizeDragger1).transform(['t', bbT.x2, ',', bbT.y2].join(''));

			var resizeDragger2 = handlesGroup
				.path(_getTransformHandlePath('ne')).transform('s'+ftOption.handleSize)
				.attr({id: 'resizeDragger_'+id, cursor:'ne-resize', class:'freeTransformHandle' })
				.data({cx: bbT.x2, cy: bbT.y});
			handlesGroup.g(resizeDragger2).transform(['t', bbT.x2, ',', bbT.y].join(''));

			var resizeDragger3 = handlesGroup
				.path(_getTransformHandlePath('sw')).transform('s'+ftOption.handleSize)
				.attr({id: 'resizeDragger_'+id, cursor:'sw-resize', class:'freeTransformHandle' })
				.data({cx: bbT.x, cy: bbT.y2});
			handlesGroup.g(resizeDragger3).transform(['t', bbT.x, ',', bbT.y2].join(''));

			var resizeDragger4 = handlesGroup
				.path(_getTransformHandlePath('nw')).transform('s'+ftOption.handleSize)
				.attr({id: 'resizeDragger_'+id, cursor:'nw-resize', class:'freeTransformHandle' })
				.data({cx: bbT.x, cy: bbT.y});
			handlesGroup.g(resizeDragger4).transform(['t', bbT.x, ',', bbT.y].join(''));


			handlesGroup.data('parentId',ftEl.node.id);
			ftEl.data('handlesGroup', handlesGroup );

			ftEl.data('oHeight', bb.cy - bb.y);
			ftEl.ftUpdateHandlesGroup();

			ftEl.unclick();
			ftEl.data('click', ftEl.click( function() {  this.ftRemoveHandles(); } ) );

			ftEl.paper.selectAll('#resizeDragger_'+id).forEach(function(el){
				el.drag(
					resizeDraggerMove.bind( el, ftEl ),
					resizeDraggerStart.bind( el, ftEl  ),
					resizeDraggerEnd.bind( el, ftEl  )
				);
			});

			translateHull.drag(
				elementDragMove.bind( translateHull, ftEl ),
				elementDragStart.bind( translateHull, ftEl ),
				elementDragEnd.bind( translateHull, ftEl )
			);

			rotateDragger.drag(
				rotateDraggerMove.bind( rotateDragger, ftEl ),
				rotateDraggerStart.bind( rotateDragger, ftEl  ),
				rotateDraggerEnd.bind( rotateDragger, ftEl  )
			);

			ftEl.ftHighlightBB();
			ftEl.ftReportTransformation();
			return this;
		};

		Element.prototype.ftInit = function() {
			//check for existing handlesgroup and delete if necessary
			var handlesGroup = this.parent().select("#handlesGroup");
			if(handlesGroup !== null){
				this.parent().select("#"+handlesGroup.data('parentId')).ftRemoveHandles();
			}

			//init new element
			this.data('angle', 0);
			this.data('angleFactor', 1);
			this.data('scale', 1);
			this.data('tx', 0);
			this.data('ty', 0);
			this.data('wa', this.paper.select('#coordGrid').getBBox());
			this.data('ratio', 1);
			this.addClass('_freeTransformInProgress');

			//unscale from scaleGroup (outer Group)
			var sgUnscale = this.paper.select('#scaleGroup').transform().localMatrix.a;
			this.data('sgUnscale', 1 / sgUnscale);

			//local unscale
			this.ftUpdateUnscale();

			return this;
		};

		Element.prototype.ftUpdateUnscale = function() {
			var tm = this.transform();
			ftOption.unscale = 1 / Math.sqrt((tm.localMatrix.a * tm.localMatrix.a) + (tm.localMatrix.c * tm.localMatrix.c));
			this.data('unscale', ftOption.unscale);
		};


		Element.prototype.ftCleanUp = function() {
			var myClosureEl = this;
			myClosureEl.paper.selectAll('#debug').remove(); // DEBUG
			var myData = ['angle', 'scale','sgUnscale','unscale', 'tx', 'ty', 'otx', 'oty', 'bb', 'bbT', 'wa', 'initialTransformMatrix', 'handlesGroup' ]; // wa = workingArea
			myData.forEach( function( el ) { myClosureEl.removeData([el]); });
			return this;
		};

		Element.prototype.ftStoreInitialTransformMatrix = function() {
			this.data('initialTransformMatrix', this.transform().localMatrix );
			return this;
		};

		Element.prototype.ftGetInitialTransformMatrix = function() {
			return this.data('initialTransformMatrix');
		};

		Element.prototype.ftRemoveHandles = function() {
			this.unclick();
			this.removeClass('_freeTransformInProgress');
			if(this.data( 'handlesGroup')) this.data( 'handlesGroup').remove();
			if(this.data( 'bbT' )) this.data('bbT').remove();
			if(this.data( 'bb' )) this.data('bb').remove();
			this.click( function() { this.ftCreateHandles(); } ) ;
			this.ftCleanUp();
			this.ftAfterTransform();
			return this;
		};

		Element.prototype.ftUpdateTransform = function() {
			if(this.ftGetInitialTransformMatrix() === undefined){
//				console.log('no initial transform');
				return this;
			}
			var tx = this.data("tx") || 0;
			var ty = this.data("ty") || 0;
			var angle = this.data("angle") || 0;

			// console.log("translate: ", this.data('tx'), this.data('ty'), 'rotate: ', this.data('angle'), 'scale: ', this.data('scale'));
			var tstring = "t" + tx + "," + ty + this.ftGetInitialTransformMatrix().toTransformString() + "r" + angle + 'S' + this.data("scale" );
			if(this.data('mirror')){
				tstring = tstring + 'S-1,1';
			} 
			this.attr({ transform: tstring });
			if(this.data("bbT")) this.ftHighlightBB(this.paper.select('#userContent'));
			this.ftUpdateUnscale();
			this.ftReportTransformation();
			this.ftUpdateHandlesGroup(this.data());
			return this;
		};

		Element.prototype.ftManualTransform = function(params){
            var svg = this;
		    var bbox = svg.getBBox();

		    svg.ftBeforeTransform(); // issue #295

		    if(params.tx !== undefined && !isNaN(params.tx)){
                svg.data('tx', params.tx - bbox.x);
            }
            if(params.ty !== undefined && !isNaN(params.ty)){
                svg.data('ty', params.ty - bbox.y2);
            }
            // if the transformation comes from the keyboard arrows, it looks a bit different
            if(params.tx_rel !== undefined && !isNaN(params.tx_rel)){
                svg.data('tx', params.tx_rel);
                svg.data('scale', 1);
                svg.data('angle', 0);
            }
            if(params.ty_rel !== undefined && !isNaN(params.ty_rel)){
                svg.data('ty', params.ty_rel);
                svg.data('scale', 1);
                svg.data('angle', 0);
            }
            if(params.angle !== undefined && !isNaN(params.angle)){
				svg.data('angle', params.angle - svg.ftGetRotation());
			}
			if(params.scale !== undefined && !isNaN(params.scale)){
				svg.data('scale', params.scale / svg.ftGetScale());
			}
			if(params.mirror !== undefined){
				svg.data('mirror', params.mirror);
			}
			svg.ftStoreInitialTransformMatrix();
			svg.ftUpdateTransform();

			svg.ftAfterTransform(); // issue #295
        };

		Element.prototype.ftUpdateHandlesGroup = function(data) {
			if(data){
			var group = this;
			var t = group.transform().local.toString();
			var tx = data.tx || 0;
			var ty = data.ty || 0;
			var angle = data.angle || 0;
			var m = data.initialTransformMatrix ? data.initialTransformMatrix.toTransformString() : "";
			
			var tstring = "t" + tx + "," + ty + m + "r" + data.angle;
		
            group.parent().selectAll('#translateHull').forEach( function( el, i ) {
                el.transform(t);
            });
            if(group.parent().select("#handlesGroup") !== null){
			    group.parent().select("#handlesGroup").selectAll('.freeTransformHandle').forEach( function( el, i ) {
				    var s = group.data('unscale') * ftOption.handleSize;
				    el.transform(Snap.matrix(ftOption.handleSize,0,0,ftOption.handleSize,data.tx,data.ty));
			    });
            }
		}
//            group.parent().selectAll('#handlesGroup').forEach( function( el, i ) {
//                el.transform(group.transform().local.toString());
//            });

//            if(group.parent().select("#handlesGroup") !== null){
//			    group.parent().select("#handlesGroup").selectAll('.freeTransformHandle').forEach( function( el, i ) {
//				    var s = group.data('unscale') * ftOption.handleSize;
//				    el.transform(Snap.matrix(s,0,0,s,0,0));
//			    });
//            }
		};

		Element.prototype.ftHighlightBB = function() {
			var rad = ftOption.handleRadius * ftOption.unscale;

			// outer bbox
			if(this.data("bb")){
				this.data("bb").attr(rectObjFromBB(this.getBBox()));
			} else {
				this.data("bb", this.paper.rect( rectObjFromBB(this.getBBox()) )
					.attr({ id: 'bbox', fill: "none", stroke: 'gray', strokeWidth: ftOption.handleStrokeWidth, strokeDasharray: ftOption.handleStrokeDash })
					.prependTo(this.paper.select('#userContent')));
			}

			// transformed bbox
			if(this.data("bbT")){
				this.data("bbT").transform(this.transform().local.toString());
			} else {
				this.data("bbT", this.paper.rect( rectObjFromBB(this.getBBox(1)) )
							.attr({ fill: "none", 'vector-effect': "non-scaling-stroke", stroke: ftOption.handleFill, strokeWidth: ftOption.handleStrokeWidth, strokeDasharray: ftOption.handleStrokeDashPreset.join(',') })
							.transform( this.transform().local.toString() ) );
			}
			return this;
		};

		Element.prototype.ftReportTransformation = function(){
			if(this.data('ftOnTransformCallbacks') && this.data('ftOnTransformCallbacks').length > 0){
				for (var idx = 0; idx < this.data('ftOnTransformCallbacks').length; idx++) {
					var cb = this.data('ftOnTransformCallbacks')[idx];
					cb(this);
				}
			}
		};

		Element.prototype.ftRegisterOnTransformCallback = function(callback){
			if(typeof this.data('ftOnTransformCallbacks') === 'undefined'){
				this.data('ftOnTransformCallbacks', [callback]);
			} else {
				this.data('ftOnTransformCallbacks').push(callback);
			}

			this.ftReportTransformation();
		};

		Element.prototype.ftAfterTransform = function(){
			if(this.data('ftAfterTransformCallbacks') && this.data('ftAfterTransformCallbacks').length > 0){
				for (var idx = 0; idx < this.data('ftAfterTransformCallbacks').length; idx++) {
					var cb = this.data('ftAfterTransformCallbacks')[idx];
					cb(this);
				}
			}
		};

		Element.prototype.ftRegisterAfterTransformCallback = function(callback){
			if(typeof this.data('ftAfterTransformCallbacks') === 'undefined'){
				this.data('ftAfterTransformCallbacks', [callback]);
			} else {
				this.data('ftAfterTransformCallbacks').push(callback);
			}
		};

		Element.prototype.ftBeforeTransform = function(){
			if(this.data('ftBeforeTransformCallbacks') && this.data('ftBeforeTransformCallbacks').length > 0){
				for (var idx = 0; idx < this.data('ftBeforeTransformCallbacks').length; idx++) {
					var cb = this.data('ftBeforeTransformCallbacks')[idx];
					cb(this);
				}
			}
		};

		Element.prototype.ftRegisterBeforeTransformCallback = function(callback){
			if(typeof this.data('ftBeforeTransformCallbacks') === 'undefined'){
				this.data('ftBeforeTransformCallbacks', [callback]);
			} else {
				this.data('ftBeforeTransformCallbacks').push(callback);
			}
		};

		Element.prototype.ftGetRotation = function(){
			var transform = this.transform();
			var startIdx = transform.local.indexOf('r') + 1;
            var endIdx = transform.local.indexOf(',', startIdx);
            var rot = parseFloat(transform.local.substring(startIdx, endIdx)) || 0;
			return rot;
		};

		Element.prototype.ftGetScale = function(){
			var transform = this.transform();
			// get scale independent from rotation
			var scale = Math.sqrt((transform.localMatrix.a * transform.localMatrix.a) + (transform.localMatrix.c * transform.localMatrix.c));
			return scale;
		};

	});

	function rectObjFromBB ( bb, minWidth, minHeight ) {
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

	function elementDragStart( mainEl, x, y, ev ) {
		mainEl.data('otx', mainEl.data("tx") || 0);
		mainEl.data('oty', mainEl.data("ty") || 0);

	};

	function elementDragMove( mainEl, dx, dy, x, y, event ) {
		var sgUnscale = mainEl.data('sgUnscale');

		var udx = sgUnscale * dx * MRBEAM_PX2MM_FACTOR_WITH_ZOOM;
		var udy = sgUnscale * dy * MRBEAM_PX2MM_FACTOR_WITH_ZOOM;
		var tx = mainEl.data("otx") + +udx;
		var ty = mainEl.data("oty") + +udy;
		mainEl.data("tx", tx);
		mainEl.data("ty", ty);
		mainEl.ftUpdateTransform();

	}

	function elementDragEnd( mainEl, dx, dy, x, y ) {
	};

	function rotateDraggerStart( mainEl ) {
		var rotateDragger = this.parent().select('#rotateDragger');
		var cx = +rotateDragger.data('cx');
		var cy = +rotateDragger.data('cy');
		rotateDragger.data('ocx', mainEl.matrix.x(cx,cy));
		rotateDragger.data('ocy', mainEl.matrix.y(cx,cy));

		rotateDragger.data('savedAngle',mainEl.data('angle'));
	};

	function rotateDraggerEnd( mainEl ) {
		this.data('withSaved',true);
		var bb = mainEl.getBBox();

		//adjust height and calculate angleFactor for resize
		var oldHeight = +mainEl.data('oHeight');
		mainEl.data('angleFactor', ((bb.cy - bb.y) / oldHeight)/mainEl.data('scale'));

	};


	function rotateDraggerMove( mainEl, dx, dy, x, y, event ) {
		var rotateDragger = this;
		var mainBB = mainEl.getBBox();
		var sgUnscale = mainEl.data('sgUnscale');

		var rCenter = {x: mainBB.cx,y: mainBB.cy};
		var rStart = {x: +rotateDragger.data('ocx') , y: +rotateDragger.data('ocy')};
		var rEnd = {x: rStart.x + dx * sgUnscale, y: rStart.y + dy * sgUnscale};


		if(!mainEl.data('block_rotation')){

			var angleStart = Snap.angle(rCenter.x,rCenter.y,rStart.x,rStart.y);
			var angleEnd = Snap.angle(rCenter.x, rCenter.y, rEnd.x, rEnd.y);

			if(rotateDragger.data('withSaved')){
				var savedAngle = +rotateDragger.data('savedAngle');
			}else{
				var savedAngle = 0;
			};

			var nAngle = savedAngle+angleEnd-angleStart;

			if(event.shiftKey){
				nAngle = Math.round(nAngle/15) * 15;
			}
			//TODO check why there are still negative angles and fix
			mainEl.data('angle', (nAngle+360)%360);
		}

		mainEl.ftUpdateTransform();

	};


	function resizeDraggerStart( mainEl ) {
		var resizeDragger = this;
		var bb = mainEl.getBBox();

		//store height at start of dragging
		var sHeight = bb.cy - bb.y;
		resizeDragger.data('sHeight', sHeight);
		mainEl.data('ratio', (bb.cx - bb.x) / sHeight);

		//check where dragger is to adjust scaling-translation
		elementDragStart(mainEl);
		var vx = mainEl.matrix.x(resizeDragger.data('cx'),resizeDragger.data('cy'));
		var vy = mainEl.matrix.y(resizeDragger.data('cx'),resizeDragger.data('cy'));
		resizeDragger.data('signX',Math.sign(bb.cx - vx));
		resizeDragger.data('signY',Math.sign(-bb.cy + vy));
//		 console.log("Sig X/Y", resizeDragger.data('signX'), resizeDragger.data('signY'));

	};

	function resizeDraggerEnd( mainEl ) {
		mainEl.ftRemoveHandles();
		mainEl.ftCreateHandles();
	};


	function resizeDraggerMove( mainEl, dx, dy, x, y, event ) {
		var resizeDragger = this;
		var origHeight = +mainEl.data('oHeight') * +mainEl.data('angleFactor');
		var d = -dy;
		// TODO use dx and dy, scale properly to movement.
//		if(Math.abs(dx) > Math.abs(dy) - origHeight){
//			d = dx;
//		}

		//apply smoothing factor of 2
		var	delta = d/2 * MRBEAM_PX2MM_FACTOR_WITH_ZOOM;

		var newHeight = +resizeDragger.data('sHeight') - delta * mainEl.data('sgUnscale') * resizeDragger.data('signY');
		var newScale =  Math.abs(newHeight / origHeight);

		//todo implement shiftkey for resize
		// if(event.shiftKey){
		// 	newScale = Math.round(newScale*4) / 4;
		// }

		//TODO check for negative scale, what should happen?
		mainEl.data('scale', newScale);

		// drag element, nobody wants to have centered scaling
		var tx = d/2 * +mainEl.data('ratio') * resizeDragger.data('signX')   * resizeDragger.data('signY');
		var ty = -d/2;
		//TODO angle, for translation of innerBB(redBB)
		elementDragMove(mainEl, tx, ty);

		mainEl.ftUpdateTransform();
	};

	function _getTransformHandlePath(type){
		switch(type){
			case 'nw':
				return "M0,0v-8l-2,2 -6,-6 2,-2h-8v8l2,-2 6,6 -2,2z";
			case 'ne':
				return "M0,0v-8l2,2 6,-6 -2,-2h8v8l-2,-2 -6,6 2,2z";
			case 'se':
				return "M0,0v8l2,-2 6,6-2,2h8v-8l-2,2-6,-6 2,-2z";
			case 'sw':
				return "M0,0v8l-2,-2 -6,6 2,2h-8v-8l2,2 6,-6 -2,-2z";
			case 'rot':
				return "M 0,8 C 4.5,8 8,4.5 8,0 H 3 C 3,1.7 1.6,3 0,3 0,3 0,3 0,3 0,3 0,3 -0.3,3 -1.9,2.8 -3,1.5 -3,-0.1 c 0,-1.6 1.4,-3 3,-3 v 1.7 L 4,-5.5 0,-9.6 V -8 c -4.5,0 -8,3.6 -8,8 0,4.5 3.6,8 8,8 z";
		}
	}

})();





