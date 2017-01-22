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
	Element.prototype.transformable = function () {
		var elem = this;
		if (!elem || !elem.paper) // don't handle unplaced elements. this causes double handling.
			return;

		// add invisible fill for better dragging.
		elem.add_fill();
		elem.click(function(){ elem.ftCreateHandles(); });
		return elem;


	};

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
			handleLength: 22,
			handleRadius: 16,
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
			var id = ftEl.id;
			var bb = ftEl.getBBox();
			ftEl.ftStoreInitialTransformMatrix();

			var bbT = ftEl.getBBox(1);
			var unscale = ftEl.data('unscale');

			var translateHull = this.paper.select('#userContent')
				.rect(rectObjFromBB(bbT))
				.attr({ id:'translateHull',cursor:'move', class:'ft_bbox_transformed' });

			//check if it needs to be on another side if design is exceeding workArea
			var wa = ftEl.data('wa');
			var rotX = bbT.cx - bbT.width/2 - ftOption.handleLength * ftOption.unscale;
			if( ftEl.matrix.x(rotX,bbT.cy) <= wa.x || ftEl.matrix.x(rotX,bbT.cy) >= wa.x2 ||
				ftEl.matrix.y(rotX,bbT.cy) <= wa.y || ftEl.matrix.y(rotX,bbT.cy)  >= wa.y2)
			{rotX += bbT.width + 2*ftOption.handleLength* ftOption.unscale;}

			var rotateDragger = this.paper.select('#userContent')
				.circle(rotX, bbT.cy, ftOption.handleRadius * ftOption.unscale )
				.attr({ fill: ftOption.handleFill, id: 'rotateDragger', cursor:'pointer', class: 'ft_handle'  });

			//todo make code more generic
			var resizeDragger1 = this.paper.select('#userContent')
				.circle(bbT.x2, bbT.y2, ftOption.handleRadius * ftOption.unscale)
				.attr({ fill: ftOption.handleFill, id: 'resizeDragger_'+id, cursor:'se-resize', class: 'ft_handle' });

			var resizeDragger2 = this.paper.select('#userContent')
				.circle(bbT.x2, bbT.y, ftOption.handleRadius * ftOption.unscale)
				.attr({ fill: ftOption.handleFill, id: 'resizeDragger_'+id, 'vector-effect': 'non-scaling',cursor:'ne-resize', class: 'ft_handle'  });

			var resizeDragger3 = this.paper.select('#userContent')
				.circle(bbT.x, bbT.y2, ftOption.handleRadius * ftOption.unscale)
				.attr({ fill: ftOption.handleFill, id: 'resizeDragger_'+id, 'vector-effect': 'non-scaling',cursor:'sw-resize', class: 'ft_handle'  });

			var resizeDragger4 = this.paper.select('#userContent')
				.circle(bbT.x, bbT.y, ftOption.handleRadius * ftOption.unscale)
				.attr({ fill: ftOption.handleFill, id: 'resizeDragger_'+id, 'vector-effect': 'non-scaling',cursor:'nw-resize', class: 'ft_handle'  });

			var handlesGroup = this.paper.select('#userContent')
				.g(translateHull,rotateDragger,resizeDragger1,resizeDragger2,resizeDragger3,resizeDragger4)
				.attr({id:'handlesGroup'});

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
			this.attr({class:'_freeTransformInProgress'});

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
			this.data( 'handlesGroup').remove();
			if(this.data( 'bbT' )) this.data('bbT').remove();
			if(this.data( 'bb' )) this.data('bb').remove();
			this.click( function() { this.ftCreateHandles(); } ) ;
			this.ftCleanUp();
			return this;
		};

		Element.prototype.ftUpdateTransform = function() {
			if(this.ftGetInitialTransformMatrix() === undefined){
				return this;
			}

			//console.log("translate: ", this.data('tx'), this.data('ty'), 'rotate: ', this.data('angle'), 'scale: ', this.data('scale'));
			var tstring = "t" + this.data("tx") + "," + this.data("ty") + this.ftGetInitialTransformMatrix().toTransformString() + "r" + this.data("angle") + 'S' + this.data("scale" );
			this.attr({ transform: tstring });
			if(this.data("bbT")) this.ftHighlightBB(this.paper.select('#userContent'));
			this.ftUpdateUnscale();
			this.ftReportTransformation();
			this.ftUpdateHandlesGroup();
			return this;
		};

		Element.prototype.ftUpdateHandlesGroup = function() {
			var group = this;
			group.parent().selectAll('#handlesGroup').forEach( function( el, i ) {
				el.transform(group.transform().local.toString());
			});
			group.parent().select("#handlesGroup").selectAll('circle').forEach( function( el, i ) {
				el.attr({'r': ftOption.handleRadius * group.data('unscale')});
			});
		};

		Element.prototype.ftHighlightBB = function() {
			if(this.data("bbT")) this.data("bbT").remove();
			if(this.data("bb")) this.data("bb").remove();

			// outer bbox
//			this.data("bb", this.paper.rect( rectObjFromBB( this.getBBox() ) )
//				.attr({ id: 'bbox', fill: "none", stroke: 'gray', strokeWidth: ftOption.handleStrokeWidth, strokeDasharray: ftOption.handleStrokeDash })
//				.prependTo(this.paper.select('#userContent')));
			//TODO make more efficiently
			// this.data('bb');
			// transformed bbox
//			this.data("bbT", this.paper.rect( rectObjFromBB( this.getBBox(1) ) )
//							.attr({ fill: "none", 'vector-effect': "non-scaling-stroke", stroke: ftOption.handleFill, strokeWidth: ftOption.handleStrokeWidth, strokeDasharray: ftOption.handleStrokeDashPreset.join(',') })
//							.transform( this.transform().toString() ) );
			return this;
		};

		Element.prototype.ftReportTransformation = function(){
			if(this.data('ftCallbacks') && this.data('ftCallbacks').length > 0){
				for (var idx = 0; idx < this.data('ftCallbacks').length; idx++) {
					var cb = this.data('ftCallbacks')[idx];
					cb(this);
				}
			}
		};

		Element.prototype.ftRegisterCallback = function(callback){
			if(typeof this.data('ftCallbacks') === 'undefined'){
				this.data('ftCallbacks', [callback]);
			} else {
				this.data('ftCallbacks').push(callback);
			}

			this.ftReportTransformation();
		};

	});

	function rectObjFromBB ( bb ) {
		return { x: bb.x, y: bb.y, width: bb.width, height: bb.height };
	}

	function elementDragStart( mainEl, x, y, ev ) {
		mainEl.data('otx', mainEl.data("tx") || 0);
		mainEl.data('oty', mainEl.data("ty") || 0);

	};

	function elementDragMove( mainEl, dx, dy, x, y ) {
		var sgUnscale = mainEl.data('sgUnscale');

		var udx = sgUnscale * dx;
		var udy = sgUnscale * dy * -1;

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
		var cx = +rotateDragger.attr('cx');
		var cy = +rotateDragger.attr('cy');
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
		var rEnd = {x: rStart.x + dx * sgUnscale, y: rStart.y + dy * sgUnscale * -1};


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
		var vx = mainEl.matrix.x(resizeDragger.attr('cx'),resizeDragger.attr('cy'));
		var vy = mainEl.matrix.y(resizeDragger.attr('cx'),resizeDragger.attr('cy'));
		resizeDragger.data('signX',Math.sign(bb.cx - vx));
		resizeDragger.data('signY',Math.sign(bb.cy - vy));
		// console.log("Sig X/Y", resizeDragger.data('signX'), resizeDragger.data('signY'));

	};

	function resizeDraggerEnd( mainEl ) {};


	function resizeDraggerMove( mainEl, dx, dy, x, y, event ) {
		var resizeDragger = this;
		// TODO use dx and dy, scale properly to movement.
		var	delta = -dy/2; //apply smoothing factor of 2

		var origHeight = +mainEl.data('oHeight') * +mainEl.data('angleFactor');
		var newHeight = +resizeDragger.data('sHeight') - delta * mainEl.data('sgUnscale') * resizeDragger.data('signY');
		var newScale =  Math.abs(newHeight / origHeight);

		//todo implement shiftkey for resize
		// if(event.shiftKey){
		// 	newScale = Math.round(newScale*4) / 4;
		// }

		//TODO check for negative scale, what should happen?
		mainEl.data('scale', newScale);

		//TODO angle, for translation of innerBB(redBB)
		elementDragMove(mainEl, delta * +mainEl.data('ratio') * resizeDragger.data('signX')   * resizeDragger.data('signY'), -delta);

		mainEl.ftUpdateTransform();
	};

})();





