/* global Snap */

//    Drag, Scale & Rotate - a snapsvg.io plugin to free transform objects in an svg.
//    Copyright (C) 2020  Teja Philipp <osd@tejaphilipp.de>
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

(function () {
    Snap.plugin(function (Snap, Element, Paper, global) {
        var self = {};
        self.ORIGINAL_MATRIX = "mbtransform_original_matrix";
        self.INITIAL_MATRIX = "mbtransform_initial_matrix";
        self.BEFORE_TRANSFORM_CALLBACKS = "mbt_before_callbacks";
        self.ON_TRANSFORM_CALLBACKS = "mbt_on_callbacks";
        self.AFTER_TRANSFORM_CALLBACKS = "mbt_after_callbacks";

        /**
         *
         *
         * @returns {undefined}
         */
        Element.prototype.transformable = function (onclickCallback) {
            var elem = this;
            if (!elem || !elem.paper)
                // don't handle unplaced elements. this causes double handling.
                return;

            // add invisible fill for better dragging.
            elem.add_fill();
            elem.unclick(); // avoid multiple click actions
            elem.click(function (event, i) {
                // ctrlKey for PC, metaKey for Mac command key
                if (event.ctrlKey || event.metaKey) {
                    elem.paper.mbtransform.toggleElement(elem);
                } else {
                    elem.paper.mbtransform.activate(elem);
                }
                if (onclickCallback && typeof onclickCallback === "function") {
                    onclickCallback(event, i);
                }
            });
            return elem;
        };

        /**
         * Adds transparent fill if not present.
         * This is useful for dragging the element around.
         *
         * @returns {path}
         */
        //TODO add fill for Text (like bounding box or similar)
        Element.prototype.add_fill = function () {
            var elem = this;
            var children = elem.selectAll("*");
            if (children.length > 0) {
                for (var i = 0; i < children.length; i++) {
                    var child = children[i];
                    child.add_fill();
                }
            } else {
                var fill = elem.attr("fill");
                var type = elem.type;
                if (type === "path" && (fill === "none" || fill === "")) {
                    elem.attr({ fill: "#ffffff", "fill-opacity": 0 });
                }
            }
            return elem;
        };

        Element.prototype.mbtGetTransform = function () {
            return this.transform().localMatrix.split();
        };

        ///////////// CALLBACKS ////////////////////

        /**
         * The callback functions for each phase in the transform process are stored in the data layer of each element.
         * The phases are before, on & after transform.
         * */

        Element.prototype.mbtOnTransform = function () {
            if (
                this.data(self.ON_TRANSFORM_CALLBACKS) &&
                this.data(self.ON_TRANSFORM_CALLBACKS).length > 0
            ) {
                for (
                    var idx = 0;
                    idx < this.data(self.ON_TRANSFORM_CALLBACKS).length;
                    idx++
                ) {
                    var cb = this.data(self.ON_TRANSFORM_CALLBACKS)[idx];
                    cb(this);
                }
            }
        };

        Element.prototype.mbtRegisterOnTransformCallback = function (callback) {
            if (typeof this.data(self.ON_TRANSFORM_CALLBACKS) === "undefined") {
                this.data(self.ON_TRANSFORM_CALLBACKS, [callback]);
            } else {
                this.data(self.ON_TRANSFORM_CALLBACKS).push(callback);
            }

            this.mbtOnTransform();
        };

        Element.prototype.mbtAfterTransform = function () {
            if (
                this.data(self.AFTER_TRANSFORM_CALLBACKS) &&
                this.data(self.AFTER_TRANSFORM_CALLBACKS).length > 0
            ) {
                for (
                    var idx = 0;
                    idx < this.data(self.AFTER_TRANSFORM_CALLBACKS).length;
                    idx++
                ) {
                    var cb = this.data(self.AFTER_TRANSFORM_CALLBACKS)[idx];
                    cb(this);
                }
            }
        };

        Element.prototype.mbtRegisterAfterTransformCallback = function (
            callback
        ) {
            if (
                typeof this.data(self.AFTER_TRANSFORM_CALLBACKS) === "undefined"
            ) {
                this.data(self.AFTER_TRANSFORM_CALLBACKS, [callback]);
            } else {
                this.data(self.AFTER_TRANSFORM_CALLBACKS).push(callback);
            }
        };

        Element.prototype.mbtBeforeTransform = function () {
            if (
                this.data(self.BEFORE_TRANSFORM_CALLBACKS) &&
                this.data(self.BEFORE_TRANSFORM_CALLBACKS).length > 0
            ) {
                for (
                    var idx = 0;
                    idx < this.data(self.BEFORE_TRANSFORM_CALLBACKS).length;
                    idx++
                ) {
                    var cb = this.data(self.BEFORE_TRANSFORM_CALLBACKS)[idx];
                    cb(this);
                }
            }
        };

        Element.prototype.mbtRegisterBeforeTransformCallback = function (
            callback
        ) {
            if (
                typeof this.data(self.BEFORE_TRANSFORM_CALLBACKS) ===
                "undefined"
            ) {
                this.data(self.BEFORE_TRANSFORM_CALLBACKS, [callback]);
            } else {
                this.data(self.BEFORE_TRANSFORM_CALLBACKS).push(callback);
            }
        };

        Paper.prototype.mbtransform_init = function () {
            var paper = this;
            self.paper = paper;
            self.transformHandleGroup = paper.select("#mbtransformHandleGroup");
            self.scaleGroup = paper.select("#mbtransformScaleGroup");
            self.rotateGroup = paper.select("#mbtransformRotateGroup");
            self.translateGroup = paper.select("#mbtransformTranslateGroup");
            self.translateHandle = paper.select("#translateHandle");
            self.scaleHandleNE = paper.select("#scaleHandleNE");
            self.scaleHandleNW = paper.select("#scaleHandleNW");
            self.scaleHandleSE = paper.select("#scaleHandleSE");
            self.scaleHandleSW = paper.select("#scaleHandleSW");
            self.scaleHandleN = paper.select("#scaleHandleNN");
            self.scaleHandleE = paper.select("#scaleHandleEE");
            self.scaleHandleS = paper.select("#scaleHandleSS");
            self.scaleHandleW = paper.select("#scaleHandleWW");
            self.rotHandle = paper.select("#rotHandle");

            self.translateXVis = paper.select("#translateXVis");
            self.translateYVis = paper.select("#translateYVis");
            self.scaleVis = paper.select("#scaleVis");
            self.scaleXVis = paper.select("#scaleXVis");
            self.scaleYVis = paper.select("#scaleYVis");
            self.rotateVis = paper.select("#rotateVis");
            self.rotateVisAngle = paper.select("#rotateVisAngle");
            self.translateXText = paper.select("#translateXText");
            self.translateYText = paper.select("#translateYText");
            self.scaleXText = paper.select("#scaleXText");
            self.scaleYText = paper.select("#scaleYText");
            self.rotateText = paper.select("#rotateText");

            paper.mbtransform = self;
            self.elements_to_transform = Snap.set();

            self.initialized = true;
        };

        self.initialized = false;
        self.config = {
            minTranslateHandleSize: 24,
            visualization: true, // enables visual debugging: click points, angle, scale center, etc...
        };

        self.session = { lastUpdate: 0 };

        /**
         * transform handler for translate, scale, rotate
         */

        self.translateStart = function (target, x, y, event) {
            // x, y, dx, dy pixel coordinates according to <svg width="..." height="..." >
            // ctrlKey for PC, metaKey for Mac command key
            if (event.ctrlKey || event.metaKey) {
                console.info(
                    "translateStart with ShiftKey down: Should bubble event to target inside. Not supported right now."
                );
                //				$('#userContent').trigger('click', event);
            }
            // store former transformation
            self._sessionInit("translate");

            // hide scale & rotate handle
            self.transformHandleGroup.node.classList.add("translate");

            self.session.translate.cx = self.session.bb.cx;
            self.session.translate.cy = self.session.bb.cy;
        };

        self.translateMove = function (target, dx, dy, x, y, event) {
            // calculate viewbox coordinates incl. zoom & pan (mm)
            const dxMM = self._convertToViewBoxUnits(dx);
            const dyMM = self._convertToViewBoxUnits(dy);

            // store session delta
            self.session.translate.dx = dxMM;
            self.session.translate.dy = dyMM;

            self._sessionUpdate();
        };

        self.translateEnd = function (target, dx, dy, x, y) {
            console.log("translateEnd");
            // show scale & rotate handle
            self._alignHandlesToBB();
            self.transformHandleGroup.node.classList.remove("translate");
            self._sessionEnd();
        };

        self.rotateStart = function (target, x, y, event) {
            // x, y, dx, dy pixel coordinates according to <svg width="..." height="..." >
            // store former transformation
            self._sessionInit("rotate");

            // hide scale & rotate handle
            self.transformHandleGroup.node.classList.add("rotate");

            // rotation center
            const handleMatrix = this.transform().localMatrix; // handle origin as first point
            self.session.rotate.ax = handleMatrix.e;
            self.session.rotate.ay = handleMatrix.f;
            self.session.rotate.ocx = self.session.bb.cx;
            self.session.rotate.ocy = self.session.bb.cy;

            const rotateCenter = self._getSessionRotateCenter();
            self.session.rotate.cx = rotateCenter[0];
            self.session.rotate.cy = rotateCenter[1];

            // Matrix to unrotate the mouse movement dxMM,dyMM
            self.session.rotate._unrotateM = Snap.matrix().rotate(
                -Math.sign(self.session.originMatrix.a) *
                    Math.sign(self.session.originMatrix.d) *
                    self.session.rotate._alpha
            );
            self.session.rotate.mirroredY = Math.sign(self.session.scale._m.d); // TODO somehow this must be mergable with the matrix above.

            self.session.rotate.vcx = self.session.bboxWithoutTransform.cx;
            self.session.rotate.vcy = self.session.bboxWithoutTransform.cy;
        };

        self.rotateMove = function (target, dx, dy, x, y, event) {
            // calculate viewbox coordinates incl. zoom & pan (mm)
            const dxMM = self._convertToViewBoxUnits(dx);
            const dyMM = self._convertToViewBoxUnits(dy);

            // transform mouse movement into virgin (=unrotated) coord space // TODO merge the mirroredY multiplication into the matrix in
            const rdx =
                self.session.rotate.mirroredY *
                self.session.rotate._unrotateM.x(dxMM, dyMM);
            const rdy =
                self.session.rotate.mirroredY *
                self.session.rotate._unrotateM.y(dxMM, dyMM);

            const ax = self.session.rotate.ax;
            const ay = self.session.rotate.ay;
            const cx = self.session.rotate.cx;
            const cy = self.session.rotate.cy;

            // calculate viewbox coordinates incl. zoom & pan (mm)
            // TODO: take offset of click and rotate icon origin into account to avoid bogus rotation center.
            const bx = (self.session.rotate.bx = ax + rdx);
            const by = (self.session.rotate.by = ay + rdy);

            // store session delta angle
            //    b
            //   /
            //  /  \ r angle
            // c----------a
            self.session.rotate.alpha = Snap.angle(bx, by, ax, ay, cx, cy);

            self.paper.debug.point("A", ax, ay, "#009900");
            self.paper.debug.point("B", bx, by, "#009900");
            self.paper.debug.point("C", cx, cy, "#009900");

            self._sessionUpdate();
        };

        self.rotateEnd = function (target, dx, dy, x, y) {
            // show scale & rotate handle
            self._alignHandlesToBB();
            self.transformHandleGroup.node.classList.remove("rotate");
            self._sessionEnd();
        };

        self.scaleStart = function (target, x, y, event) {
            // x, y, dx, dy pixel coordinates according to <svg width="..." height="..." >

            // store former transformation
            self._sessionInit("scale");

            // hide scale & rotate handle
            const usedHandle = this;
            const handleId = usedHandle.node.id;
            self.transformHandleGroup.node.classList.add("scale", handleId);

            let scaleCenterHandle;
            switch (handleId.substr(-2)) {
                case "SE":
                    scaleCenterHandle = self.scaleHandleNW;
                    self.session.scale.signX = 1;
                    self.session.scale.signY = 1;
                    self.session.scale.prop = true;
                    break;
                case "SW":
                    scaleCenterHandle = self.scaleHandleNE;
                    self.session.scale.signX = 1;
                    self.session.scale.signY = 1;
                    self.session.scale.prop = true;
                    break;
                case "NW":
                    scaleCenterHandle = self.scaleHandleSE;
                    self.session.scale.signX = 1;
                    self.session.scale.signY = 1;
                    self.session.scale.prop = true;
                    break;
                case "NE":
                    scaleCenterHandle = self.scaleHandleSW;
                    self.session.scale.signX = 1;
                    self.session.scale.signY = 1;
                    self.session.scale.prop = true;
                    break;
                case "NN":
                    scaleCenterHandle = self.scaleHandleS;
                    self.session.scale.signX = 0;
                    self.session.scale.signY = 1;
                    self.session.scale.prop = false;
                    break;
                case "EE":
                    scaleCenterHandle = self.scaleHandleW;
                    self.session.scale.signX = 1;
                    self.session.scale.signY = 0;
                    self.session.scale.prop = false;
                    break;
                case "SS":
                    scaleCenterHandle = self.scaleHandleN;
                    self.session.scale.signX = 0;
                    self.session.scale.signY = 1;
                    self.session.scale.prop = false;
                    break;
                case "WW":
                    scaleCenterHandle = self.scaleHandleE;
                    self.session.scale.signX = 1;
                    self.session.scale.signY = 0;
                    self.session.scale.prop = false;
                    break;

                default:
                    console.error("Should never happen!");
                    break;
            }

            // get "click position" (position of the clicked scale handle, virgin coord space)
            const handleMatrix = usedHandle.transform().localMatrix;
            self.session.scale.usedHandle = usedHandle;
            self.session.scale.mx = handleMatrix.e;
            self.session.scale.my = handleMatrix.f;

            // scaling center (position of the opposite handle, virgin coord space)
            const scm = scaleCenterHandle.transform();
            self.session.scale.cx = scm.localMatrix.e;
            self.session.scale.cy = scm.localMatrix.f;

            // additionally get scaling center in absolute coord space
            self.session.scale.vcx = self.session.originInvert.x(
                scm.totalMatrix.e,
                scm.totalMatrix.f
            );
            self.session.scale.vcy = self.session.originInvert.y(
                scm.totalMatrix.e,
                scm.totalMatrix.f
            );

            // reference width & height for current session needs former transformation to be applied
            self.session.scale.refX =
                self.session.scale.mx - self.session.scale.cx;
            self.session.scale.refY =
                self.session.scale.my - self.session.scale.cy;

            // matrix for transforming mouse moves into rotated coord space
            self.session.scale.mouseMatrix = Snap.matrix()
                .scale(
                    Math.sign(self.session.originTransform.scalex),
                    Math.sign(self.session.originTransform.scaley)
                )
                .rotate(
                    Math.sign(self.session.originTransform.scalex) *
                        -self.session.originTransform.rotate
                );

            self.paper.debug.point(
                "c",
                self.session.scale.cx,
                self.session.scale.cy,
                "#e25303"
            );
            self.paper.debug.point(
                "A",
                self.session.scale.mx,
                self.session.scale.my,
                "#00aaff"
            );
        };

        self.scaleMove = function (target, dx, dy, x, y, event) {
            // convert to viewBox coordinates (mm)
            let dxMM = self._convertToViewBoxUnits(dx);
            let dyMM = self._convertToViewBoxUnits(dy);

            const sss = self.session.scale;
            sss.dxMM = dxMM;
            sss.dyMM = dyMM;

            // mouse position transformed the same way like the handles to calculate scaling distances within rotated coordinate system
            const rotatedMouseX =
                self.session.scale.mouseMatrix.x(dxMM, dyMM) *
                    Math.sign(sss._m.a) +
                sss.mx;
            const rotatedMouseY =
                self.session.scale.mouseMatrix.y(dxMM, dyMM) *
                    Math.sign(sss._m.d) +
                sss.my;

            self.paper.debug.point(
                "rotMouse",
                rotatedMouseX,
                rotatedMouseY,
                "#e25303"
            );

            const distX = rotatedMouseX - sss.cx;
            const distY = rotatedMouseY - sss.cy;

            let scaleX = (sss.signX * distX) / sss.refX;
            let scaleY = (sss.signY * distY) / sss.refY;

            if (sss.prop) {
                // link the factors (min abs value), keep the sign

                let newSx = scaleX * self.session.originTransform.scalex; // careful with originTransform - y-scaleing = -1 results in:  x-scaleing =-1 & rotation 180°
                let newSy = scaleY * self.session.originTransform.scaley;
                const signX = Math.sign(scaleX);
                const signY = Math.sign(scaleY);
                const formerSignX = Math.sign(
                    self.session.originTransform.scalex
                );
                const formerSignY = Math.sign(
                    self.session.originTransform.scaley
                );
                let formerScale;
                if (Math.abs(newSx) < Math.abs(newSy)) {
                    scaleY = signY * Math.abs(scaleX);
                    formerScale = Math.abs(self.session.originTransform.scalex);
                    sss.dominantAxis = "x";
                } else {
                    scaleX = signX * Math.abs(scaleY);
                    formerScale = Math.abs(self.session.originTransform.scaley);
                    sss.dominantAxis = "y";
                }

                sss.sx = scaleX;
                sss.sy = scaleY;
            } else {
                sss.sx = sss.signX !== 0 ? scaleX : 1;
                sss.sy = sss.signY !== 0 ? scaleY : 1;
            }

            self._sessionUpdate(this);
        };

        self.scaleEnd = function (target, dx, dy, x, y) {
            // show scale & rotate handles
            self._alignHandlesToBB();
            self._sessionEnd();
            self.transformHandleGroup.node.classList.remove(
                "scale",
                "scaleHandleNE",
                "scaleHandleNW",
                "scaleHandleSW",
                "scaleHandleSE",
                "scaleHandleNN",
                "scaleHandleEE",
                "scaleHandleSS",
                "scaleHandleWW"
            );
        };

        /**
         * *** Transformations without mouse. ***
         * params are _always_ relative values except width and height
         * **/
        self.manualTransform = function (elementset_or_selector, params) {
            self.elements_to_transform = self._getElementSet(
                elementset_or_selector
            );
            self._remember_original_transform();

            // init session
            self._sessionInit("manualTransform");

            let tx = 0;
            let ty = 0;
            let scalex = 1;
            let scaley = 1;
            let alpha = 0;
            let keyboardMovement = false;

            const bbox = self.elements_to_transform.getBBox();
            //			calc relative values
            if (params.tx !== undefined && !isNaN(params.tx))
                tx = params.tx - bbox.x;
            if (params.ty !== undefined && !isNaN(params.ty))
                ty = params.ty - bbox.y2;

            // if the transformation comes from the keyboard arrows, it looks a bit different
            if (params.tx_rel !== undefined && !isNaN(params.tx_rel)) {
                tx = self.toTwoDigitFloat(params.tx_rel);
                scalex = 1;
                alpha = 0;
                keyboardMovement = true;
            }
            if (params.ty_rel !== undefined && !isNaN(params.ty_rel)) {
                ty = self.toTwoDigitFloat(params.ty_rel);
                scaley = 1;
                alpha = 0;
                keyboardMovement = true;
            }
            if (params.angle !== undefined && !isNaN(params.angle)) {
                alpha = self.toTwoDigitFloat(params.angle);
            }

            if (params.width !== undefined && !isNaN(params.width)) {
                scalex = params.width / bbox.width; // relative!
                if (params.proportional) {
                    scaley = Math.sign(scaley) * Math.abs(scalex);
                }
            }
            if (params.height !== undefined && !isNaN(params.height)) {
                scaley = params.height / bbox.height; // relative!
                if (params.proportional) {
                    scalex = Math.sign(scalex) * Math.abs(scaley);
                }
            }
            if (params.scalex !== undefined && !isNaN(params.scalex)) {
                scalex = params.scalex; // relative!
                if (params.proportional) {
                    scaley = Math.sign(scaley) * Math.abs(scalex);
                }
            }
            if (params.scaley !== undefined && !isNaN(params.scaley)) {
                scaley = params.scaley; // relative!
                if (params.proportional) {
                    scalex = Math.sign(scalex) * Math.abs(scaley);
                }
            }

            // set values on transform groups
            // Scale
            const scx = bbox.cx;
            const scy = bbox.cy;
            const matScale = Snap.matrix().scale(scalex, scaley, scx, scy);
            self.scaleGroup.transform(matScale);

            // Rotate
            const matRotate = Snap.matrix().rotate(alpha, scx, scy);
            self.rotateGroup.transform(matRotate);

            // Translate
            const matTranslate = Snap.matrix().translate(tx, ty);
            self.translateGroup.transform(matTranslate);

            const m = self.translateHandle.transform().totalMatrix; // a relative matrix applied to existing transformation of the element.

            // apply transform to target elements via callback
            self._apply_on_transform(m);

            // avoid misalignment of translate handle and elements when using arrow keys to move designs
            if (keyboardMovement) {
                const bb = self.elements_to_transform.getBBox();
                self._alignHandlesToBB(bb);
                self.translateGroup.transform("");
            }

            // end session
            self._sessionEnd();
        };

        self._sessionInit = function (calledBy) {
            //			self.paper.debug.enable();
            self.paper.debug.cleanup();

            // change mouse cursor
            document.body.classList.toggle("mbtransform", true);

            // remember current scale factors, rotation and translation
            const tmp = self.translateHandle.transform().totalMatrix.split();
            const tmpSM = self.scaleGroup.transform().localMatrix;
            const tmpRM = self.rotateGroup.transform().localMatrix;
            const tmpTM = self.translateGroup.transform().localMatrix;

            self.session.scale = {
                sx: 1,
                sy: 1,
                _m: tmpSM,
                _mInv: tmpSM.invert(),
            };
            self.session.rotate = {
                alpha: 0,
                cx: 0,
                cy: 0,
                _m: tmpRM,
                _mInv: tmpRM.invert(),
                _alpha: tmp.rotate,
            };
            self.session.translate = {
                dx: 0,
                dy: 0,
                _m: tmpTM,
                _mInv: tmpTM.invert(),
            };

            self.session.type = calledBy;
            self.session.originMatrix = self.translateHandle.transform().totalMatrix;
            self.session.originTransform = self.session.originMatrix.split();
            self.session.originInvert = self.session.originMatrix.invert();

            self.session.bboxWithoutTransform = self.translateHandle.getBBox(
                true
            );
            self.session.initialMatrix = self.translateHandle.transform().totalMatrix; // stack of scale, rotate, translate matrices

            self.session.bb = self._transformBBox(
                self.session.bboxWithoutTransform,
                self.session.initialMatrix
            );

            self._apply_before_transform();

            //			self.paper.debug.coords('scale', '#ffaaaa', self.scaleGroup);
            //			self.paper.debug.coords('rotate', '#aaffaa', self.rotateGroup);
            //			self.paper.debug.coords('translate', '#aaaaff', self.translateGroup);
        };

        self._sessionUpdate = function () {
            if (Date.now() - self.session.lastUpdate > 40) {
                // 40ms -> reduces updates to 25 fps maximum

                // Scale
                if (self.session.type === "scale") {
                    const scx = self.session.scale.vcx;
                    const scy = self.session.scale.vcy;
                    const matScale = self.session.scale._m
                        .clone()
                        .scale(
                            self.session.scale.sx,
                            self.session.scale.sy,
                            scx,
                            scy
                        );
                    self.scaleGroup.transform(matScale);
                }

                // Rotate
                if (self.session.type === "rotate") {
                    const alpha =
                        self.session.rotate.alpha + self.session.rotate._alpha;

                    const rcx = self.session.rotate.cx;
                    const rcy = self.session.rotate.cy;

                    const matRotate = self.session.rotate._m
                        .clone()
                        .rotate(self.session.rotate.alpha, rcx, rcy);
                    self.rotateGroup.transform(matRotate);
                }

                // Translate
                if (self.session.type === "translate") {
                    const tx =
                        self.session.translate.dx + self.session.translate._dx;
                    const ty =
                        self.session.translate.dy + self.session.translate._dy;
                    const matTranslate = self.session.translate._m
                        .clone()
                        .translate(
                            self.session.translate.dx,
                            self.session.translate.dy
                        );
                    self.translateGroup.transform(matTranslate);
                }

                self._visualizeTransform();

                self.updateCounter++;
                self.session.lastUpdate = Date.now();

                // apply transform to target elements via callback
                const m = self.translateHandle.transform().totalMatrix;
                self._apply_on_transform(m);
            }
        };

        self._sessionEnd = function () {
            self.paper.debug.cleanup();
            self._visualizeTransformCleanup();
            self._apply_after_transform();
            // change mouse cursor
            document.body.classList.toggle("mbtransform", false);
        };

        self._apply_before_transform = function () {
            for (var i = 0; i < self.elements_to_transform.length; i++) {
                var el = self.elements_to_transform[i];
                el.mbtBeforeTransform();
            }
        };
        self._apply_on_transform = function (m) {
            for (var i = 0; i < self.elements_to_transform.length; i++) {
                var el = self.elements_to_transform[i];
                const newM = el.data(self.ORIGINAL_MATRIX).clone().multLeft(m);
                el.transform(newM);
                el.mbtOnTransform();
            }
        };
        self._apply_after_transform = function () {
            for (var i = 0; i < self.elements_to_transform.length; i++) {
                var el = self.elements_to_transform[i];
                el.mbtAfterTransform();
            }
        };

        self._remember_original_transform = function () {
            for (var i = 0; i < self.elements_to_transform.length; i++) {
                var el = self.elements_to_transform[i];
                const m = el.transform().localMatrix;
                el.data(self.ORIGINAL_MATRIX, m);
                if (!el.data(self.INITIAL_MATRIX)) {
                    el.data(self.INITIAL_MATRIX, m); // store initial matrix for reverting transforms.
                }
            }
        };

        self.reset_transform = function (elementset_or_selector) {
            let elements_to_reset = self._getElementSet(elementset_or_selector);

            for (var i = 0; i < elements_to_reset.length; i++) {
                var el = elements_to_reset[i];
                if (el.data(self.INITIAL_MATRIX)) {
                    const m = el.data(self.INITIAL_MATRIX);
                    el.transform(m);
                    el.data(self.ORIGINAL_MATRIX, m);
                } else {
                    console.warn(
                        "No initial matrix found. Setting transform=''."
                    );
                    el.transform("");
                }
            }
        };

        /**
         * @param {Snap.Element, Snap.Set, CSS-Selector} elements_to_transform
         *
         * @returns {undefined}
         */
        self.activate = function (elementset_or_selector) {
            if (self.transformHandleGroup.node.classList.contains("active")) {
                self.deactivate();
            }

            // ensure that these classes are removed. Otherwise when activating the transform handles, some handles are hidden.
            self.transformHandleGroup.node.classList.remove(
                "translate",
                "rotate",
                "scale",
                "scaleHandleNE",
                "scaleHandleNW",
                "scaleHandleSW",
                "scaleHandleSE",
                "scaleHandleNN",
                "scaleHandleEE",
                "scaleHandleSS",
                "scaleHandleWW"
            );

            let elements_to_transform = self._getElementSet(
                elementset_or_selector
            );
            if (elements_to_transform.length === 0) {
                console.log("No elements to transfrom. Aborting.");
                return;
            }
            // get bounding box of selector
            const selection_bbox = self._getBBoxFromElementsWithMinSize(
                elements_to_transform
            );

            // store working area size in MM
            self.session.paperBBox = self.paper.select("#coordGrid").getBBox();

            // set transform session origin
            self.session.bb = selection_bbox;

            self.elements_to_transform = elements_to_transform;
            self._remember_original_transform();

            self.scaleGroup.transform("");
            self.rotateGroup.transform("");
            self.translateGroup.transform("");

            self._alignHandlesToBB(selection_bbox);

            // attach drag handlers for translation
            self.translateHandle.drag(
                self.translateMove.bind(
                    self.translateHandle,
                    elements_to_transform
                ),
                self.translateStart.bind(
                    self.translateHandle,
                    elements_to_transform
                ),
                self.translateEnd.bind(
                    self.translateHandle,
                    elements_to_transform
                )
            );

            self.rotHandle.drag(
                self.rotateMove.bind(self.rotHandle, elements_to_transform),
                self.rotateStart.bind(self.rotHandle, elements_to_transform),
                self.rotateEnd.bind(self.rotHandle, elements_to_transform)
            );

            const scaleHandles = [
                self.scaleHandleNE,
                self.scaleHandleNW,
                self.scaleHandleSW,
                self.scaleHandleSE,
                self.scaleHandleN,
                self.scaleHandleE,
                self.scaleHandleS,
                self.scaleHandleW,
            ];
            for (var i = 0; i < scaleHandles.length; i++) {
                var h = scaleHandles[i];
                h.drag(
                    self.scaleMove.bind(h, elements_to_transform),
                    self.scaleStart.bind(h, elements_to_transform),
                    self.scaleEnd.bind(h, elements_to_transform)
                );
            }

            self.transformHandleGroup.node.classList.add("active");

            self.updateCounter = 0;
            self.updateFPS = setInterval(function () {
                self.updateCounter = 0;
            }, 1000);
        };

        self.deactivate = function () {
            self.updateFPS = null;
            self.transformHandleGroup.node.classList.remove("active");

            // remove drag handlers
            self.translateHandle.undrag();
            self.rotHandle.undrag();

            const scaleHandles = [
                self.scaleHandleNE,
                self.scaleHandleNW,
                self.scaleHandleSW,
                self.scaleHandleSE,
                self.scaleHandleN,
                self.scaleHandleE,
                self.scaleHandleS,
                self.scaleHandleW,
            ];
            for (var i = 0; i < scaleHandles.length; i++) {
                scaleHandles[i].undrag();
            }

            // reset transform session origin
            self.session.originMatrix = null;
            self.session.bb = null;
            self.elements_to_transform = Snap.set();
        };

        self.getSelection = function () {
            return self.elements_to_transform;
        };

        self.toggle = function (elements_to_transform) {
            if (self.transformHandleGroup.node.classList.contains("active")) {
                self.deactivate();
            } else {
                self.activate(elements_to_transform);
            }
        };

        self.toggleElement = function (element_to_toggle) {
            let elements = self._getElementSet(element_to_toggle);
            if (elements.length > 0) {
                let toggleEl = elements[0];
                if (self._setContains(self.elements_to_transform, toggleEl)) {
                    self.elements_to_transform.exclude(toggleEl);
                } else {
                    self.elements_to_transform.push(toggleEl);
                }
            }

            if (self.elements_to_transform.length === 0) {
                self.deactivate();
            } else {
                self.activate(self.elements_to_transform);
            }
        };

        self._setContains = function (set, element) {
            for (var i = 0; i < set.length; i++) {
                if (element === set[i]) return true;
            }
            return false;
        };

        self._getElementSet = function (elementset_or_selector) {
            if (!elementset_or_selector) {
                console.warn(
                    `${elementset_or_selector} is neither a selector nor a Snap set of elements.`
                );
                return Snap.set();
            }

            if (typeof elementset_or_selector === "string") {
                let elementSet = self.paper.selectAll(elementset_or_selector);
                if (elementSet.length === 0) {
                    console.warn(
                        `Selector '${elementset_or_selector}' got no results.`
                    );
                    return Snap.set();
                } else {
                    return elementSet;
                }
            } else {
                if (elementset_or_selector.type === "set") {
                    return elementset_or_selector;
                } else if (
                    typeof elementset_or_selector === "object" &&
                    typeof elementset_or_selector.transform === "function"
                ) {
                    // check if snap element
                    return Snap.set(elementset_or_selector);
                } else {
                    console.warn(
                        `'${elementset_or_selector}' is neither a Snap Element nor a Snap Set.`
                    );
                    return Snap.set();
                }
            }
        };

        self._getSessionRotateCenter = function () {
            // invert Translate Matrix
            const _cx = self.session.translate._mInv.x(
                self.session.bb.cx,
                self.session.bb.cy
            );
            const _cy = self.session.translate._mInv.y(
                self.session.bb.cx,
                self.session.bb.cy
            );
            // invert Rotate Matrix
            const rcx = self.session.rotate._mInv.x(_cx, _cy);
            const rcy = self.session.rotate._mInv.y(_cx, _cy);
            return [rcx, rcy];
        };

        self._transformBBox = function (bbox, matrix) {
            const x = matrix.x(bbox.x, bbox.y);
            const y = matrix.y(bbox.x, bbox.y);
            const x2 = matrix.x(bbox.x2, bbox.y2);
            const y2 = matrix.y(bbox.x2, bbox.y2);
            const w = x2 - x;
            const h = y2 - y;
            const cx = (x + x2) / 2;
            const cy = (y + y2) / 2;
            var path = [
                ["M", x, y],
                ["l", w, 0],
                ["l", 0, h],
                ["l", -w, 0],
                ["z"],
            ];
            path.toString = Snap.path.toString; // attach original toString function
            // TODO support
            // r0: 55.90169943749474
            // r1: 25
            // r2: 50
            return {
                x: x,
                y: y,
                x2: x2,
                y2: y2,
                w: w,
                h: h,
                width: w,
                height: h,
                cx: cx,
                cy: cy,
                vb: `${x} ${y} ${w} ${h}`,
                path: path,
            };
        };

        self._convertToViewBoxUnits = function (val) {
            return val * MRBEAM_PX2MM_FACTOR_WITH_ZOOM;
        };

        self._convertToViewBoxUnitsWithTransform = function (dx, dy) {
            const rotation = self.session.originMatrix.split().rotate;

            const mat = Snap.matrix().rotate(rotation);
            const dxMM = dx * MRBEAM_PX2MM_FACTOR_WITH_ZOOM;
            const dyMM = dy * MRBEAM_PX2MM_FACTOR_WITH_ZOOM;
            const transformedX = mat.x(dx, dy);
            const transformedY = mat.y(dx, dy);
            return [transformedX, transformedY];
        };

        self._alignHandlesToBB = function (bbox_to_wrap) {
            if (bbox_to_wrap) {
                // resize translateHandle (rectangle)
                self.translateHandle.transform("");
                self.translateHandle.attr(bbox_to_wrap);
            } else {
                // just align scale and rotation arrows
                bbox_to_wrap = self.translateHandle.getBBox(true);
            }

            const lm = self.scaleGroup.transform().localMatrix;
            const verbose = lm.split();
            const unscaleMat = Snap.matrix().scale(
                1 / Math.abs(verbose.scalex),
                1 / Math.abs(verbose.scaley)
            );

            self.scaleHandleNW.transform(
                lm
                    .clone()
                    .translate(bbox_to_wrap.x, bbox_to_wrap.y)
                    .add(unscaleMat)
            );
            self.scaleHandleSW.transform(
                lm
                    .clone()
                    .translate(bbox_to_wrap.x, bbox_to_wrap.y2)
                    .add(unscaleMat)
            );
            self.scaleHandleNE.transform(
                lm
                    .clone()
                    .translate(bbox_to_wrap.x2, bbox_to_wrap.y)
                    .add(unscaleMat)
            );
            self.scaleHandleSE.transform(
                lm
                    .clone()
                    .translate(bbox_to_wrap.x2, bbox_to_wrap.y2)
                    .add(unscaleMat)
            );

            self.scaleHandleN.transform(
                lm
                    .clone()
                    .translate(bbox_to_wrap.cx, bbox_to_wrap.y)
                    .add(unscaleMat)
            );
            self.scaleHandleE.transform(
                lm
                    .clone()
                    .translate(bbox_to_wrap.x2, bbox_to_wrap.cy)
                    .add(unscaleMat)
            );
            self.scaleHandleS.transform(
                lm
                    .clone()
                    .translate(bbox_to_wrap.cx, bbox_to_wrap.y2)
                    .add(unscaleMat)
            );
            self.scaleHandleW.transform(
                lm
                    .clone()
                    .translate(bbox_to_wrap.x, bbox_to_wrap.cy)
                    .add(unscaleMat)
            );
            self.rotHandle.transform(
                lm
                    .clone()
                    .translate(bbox_to_wrap.x2, bbox_to_wrap.cy)
                    .add(unscaleMat)
            );
            self._highlightSelectedItems();
        };

        self._highlightSelectedItems = function () {
            snap.selectAll(".isSelectedBBox").remove();
            for (var i = 0; i < self.elements_to_transform.length; i++) {
                const bb = self.elements_to_transform[i].getBBox();
                const dAttr = `M${bb.x},${bb.y2}m0,-15v15h15M${bb.x2},${bb.y2}m-15,0h15v-15M${bb.x2},${bb.y}m0,15v-15h-15M${bb.x},${bb.y}m15,0h-15v15`;
                self.transformHandleGroup.path(dAttr).attr({
                    class: "isSelectedBBox",
                });
            }
        };

        self._getBBoxFromElementsWithMinSize = function (elements) {
            let bb = elements.getBBox();
            let dw = bb.width - self.config.minTranslateHandleSize;
            if (dw < 0) {
                bb.width += -dw;
                bb.w += -dw;
                bb.x += dw / 2; // dw is negative
                bb.x2 += -dw / 2; // dw is negative
            }
            let dh = bb.height - self.config.minTranslateHandleSize;
            if (dh < 0) {
                bb.height += -dh;
                bb.h += -dh;
                bb.y += dh / 2; // dh is negative
                bb.y2 += -dh / 2; // dh is negative
            }
            let x = bb.x;
            let y = bb.y;
            let x2 = bb.x + bb.width;
            let y2 = bb.y + bb.height;
            let cx = bb.x + bb.width / 2;
            let cy = bb.y + bb.height / 2;
            let w = bb.width;
            let h = bb.height;
            return {
                x: x,
                y: y,
                cx: cx,
                cy: cy,
                x2: x2,
                y2: y2,
                width: w,
                height: h,
            };
        };

        self.toTwoDigitFloat = function (num) {
            return Math.round((num + Number.EPSILON) * 100) / 100;
        };

        ///////////// VISUALIZATIONS ////////////////////

        self._visualizeTransform = function () {
            if (self.config.visualization) {
                // translate
                if (self.session.type === "translate") {
                    self._visualizeTranslate();
                }
                if (self.session.type === "rotate") {
                    self._visualizeRotate();
                }
                if (self.session.type === "scale") {
                    self._visualizeScale();
                }

                self.transformHandleGroup.node.classList.toggle(
                    "visualize",
                    true
                );
            }
        };

        self._visualizeTransformCleanup = function () {
            self.transformHandleGroup.node.classList.toggle("visualize", false);
        };

        self._visualizeTranslate = function () {
            const startXh = self.session.translate.cx;
            const startYh = 10;
            const startXv = 10;
            const startYv = self.session.translate.cy;
            const mdx = Snap.matrix()
                .translate(startXh, startYh)
                .scale(self.session.translate.dx, 1);
            self.translateXVis.transform(mdx);
            const mdy = Snap.matrix()
                .translate(startXv, startYv)
                .scale(1, self.session.translate.dy);
            self.translateYVis.transform(mdy);

            self.translateXText.node.textContent =
                self.session.translate.dx.toFixed(1) + "mm";
            self.translateXText.transform(
                Snap.matrix(
                    1,
                    0,
                    0,
                    1,
                    startXh + self.session.translate.dx / 2,
                    startYh + 7
                )
            );
            self.translateYText.node.textContent =
                self.session.translate.dy.toFixed(1) + "mm";
            self.translateYText.transform(
                Snap.matrix(
                    0,
                    -1,
                    1,
                    0,
                    startXv + 8,
                    startYv + self.session.translate.dy / 2
                )
            );

            // TODO distances from working area edges
        };

        self._visualizeRotate = function () {
            const cx = self.session.rotate.ocx;
            const cy = self.session.rotate.ocy;
            const a = self.session.rotate.alpha;

            const visM = Snap.matrix(1, 0, 0, 1, cx, cy).rotate(
                self.session.rotate._alpha
            );
            self.rotateVis.transform(visM);
            self.rotateVisAngle.transform(
                Snap.matrix().rotate(self.session.rotate.alpha)
            );
            const angleText = ((a + 180 + 720) % 360) - 180; // ensures -180° to 180°
            self.rotateText.node.textContent = `${
                angleText > 0 ? "+" : ""
            }${angleText.toFixed(1)} °`;
        };

        self._visualizeScale = function () {
            const gap = 15;
            const sss = self.session.scale;
            const handleX = sss.mx + sss.dxMM;
            const handleY = sss.my + sss.dyMM;
            const totalSx = sss._m.a * sss.sx;
            const totalSy = sss._m.d * sss.sy;
            const width = self.session.bboxWithoutTransform.width * totalSx;
            const height = self.session.bboxWithoutTransform.height * totalSy;
            const cx = sss.cx;
            const cy = sss.cy;

            // where to show visualizations
            let handleIsLeft = Math.sign(sss.cx - sss.mx);
            let handleIsTop = Math.sign(sss.cy - sss.my);
            const sxPositive = Math.sign(totalSx);
            const syPositive = Math.sign(totalSy);
            const rulerCx =
                cx - (handleIsLeft * Math.sign(sss._m.a) * width) / 2;
            const rulerCy =
                cy - (handleIsTop * Math.sign(sss._m.d) * height) / 2;
            if (!sss.prop) {
                if (sss.signX === 0) handleIsLeft = 1;
                if (sss.signY === 0) handleIsTop = 1;
            }

            self.scaleVis.node.classList.toggle("showX", sss.signX !== 0);
            self.scaleVis.node.classList.toggle("showY", sss.signY !== 0);

            // move ruler center to the center of the translatehandle bbox
            const visM = Snap.matrix(1, 0, 0, 1, rulerCx, rulerCy);
            self.scaleVis.transform(visM);

            const horizontalEdgeY = (handleIsTop * height) / 2; // transform handle bbox above edge or below edge
            const horizontalRulerOffset = handleIsTop * syPositive * gap; // gap to add to horizontalEdgeY
            const horizontalTextOffset = horizontalRulerOffset;
            const transformX = Snap.matrix(
                width,
                0,
                0,
                1,
                0,
                horizontalEdgeY + horizontalRulerOffset
            );
            self.scaleXVis.transform(transformX);
            const labelX = `${width.toFixed(1)}mm / ${(sss.sx * 100).toFixed(
                1
            )}%`;
            self.scaleXText.node.textContent = labelX;
            self.scaleXText.transform(
                Snap.matrix(
                    1,
                    0,
                    0,
                    1,
                    0,
                    horizontalEdgeY +
                        horizontalRulerOffset +
                        horizontalTextOffset
                )
            );
            self.paper.debug.point(
                "hEdge",
                0,
                horizontalEdgeY,
                "#005303",
                "#scaleVis"
            );

            const verticalEdgeX = (handleIsLeft * width) / 2;
            const verticalRulerOffset = handleIsLeft * sxPositive * gap;
            const verticalTextOffset = verticalRulerOffset;
            const transformY = Snap.matrix(
                1,
                0,
                0,
                height,
                verticalEdgeX + verticalRulerOffset,
                0
            );
            self.scaleYVis.transform(transformY);
            const labelY = `${height.toFixed(1)}mm / ${(sss.sy * 100).toFixed(
                1
            )}%`;
            self.scaleYText.node.textContent = labelY;
            self.scaleYText.transform(
                Snap.matrix(
                    0,
                    -1,
                    1,
                    0,
                    verticalEdgeX + verticalRulerOffset + verticalTextOffset,
                    0
                )
            );
            self.paper.debug.point(
                "vEdge",
                verticalEdgeX,
                0,
                "#005303",
                "#scaleVis"
            );
        };
    });
})();

/******
 * Visual Debug plugin
 *****/
(function () {
    Snap.plugin(function (Snap, Element, Paper, global) {
        var self = {};

        Paper.prototype.debug_init = function () {
            var paper = this;
            self.paper = paper;
            self.isEnabled = false;
            self.positions = 0;
            self.persist = false;
            self.reminderSent = false;

            paper.debug = self;
            self.initialized = true;
        };

        self.enable = function () {
            self.isEnabled = true;
        };
        self.disable = function () {
            self.isEnabled = false;
        };
        self._isNotEnabled = function () {
            if (!self.isEnabled && !self.reminderSent) {
                console.info(
                    "Snap.debug disabled. Call <paper>.enable() first."
                );
                self.reminderSent = true;
            }
            return !self.isEnabled;
        };

        self.point = function (label, x, y, color = "#ff00ff", parent = null) {
            if (self._isNotEnabled()) return;

            if (!label) {
                console.error("debug.point needs a label!");
                return;
            }

            const id = `_dbg_${label}`;

            if (isNaN(x) || isNaN(y)) {
                console.error(
                    "Unable to draw debug point '${label}' at (${x},${y})"
                );
                self.paper.selectAll("#" + id).remove();
            }

            // check if exists
            let pointEl = self.paper.select("#" + id);
            if (!pointEl) {
                const pointMarker = self.paper.path({
                    d: "M0,0m-2,0h4m-2,-2v4",
                    stroke: color,
                    strokeWidth: 1,
                    fill: "none",
                });
                const pointLabel = self.paper.text({
                    x: 0,
                    y: 0,
                    text: label,
                    fill: color,
                    style:
                        "font-size:8px; font-family:monospace; transform:translate(2px,-2px);",
                });
                pointEl = self.paper.group(pointMarker, pointLabel);
                pointEl.attr({ id: id, class: "_dbg_" });
            }
            pointEl.transform(`translate(${x},${y})`);
            if (parent !== null) {
                self.add_to_parent(pointEl, parent);
            }

            return pointEl;
        };

        self.line = function (
            label,
            x1,
            y1,
            x2,
            y2,
            color = "#ff00ff",
            parent = null
        ) {
            if (self._isNotEnabled()) return;

            if (!label || typeof label !== "string") {
                console.error("debug.line needs a label!");
                return;
            }

            const id = `_dbg_${label}`;

            if (isNaN(x1) || isNaN(y1) || isNaN(x2) || isNaN(y2)) {
                console.error(
                    "Unable to draw debug line '${label}' at (${x1},${y1} -> ${x2},${y2})"
                );
                self.paper.selectAll("#" + id).remove();
            }

            // check if exists
            let lineEl = self.paper.select("#" + id);
            const sx = x2 === x1 ? 1 : x2 - x1;
            const sy = y2 === y1 ? 1 : y2 - y1;
            if (!lineEl) {
                const line = self.paper.path({
                    d: "M0,0l1,1",
                    stroke: color,
                    strokeWidth: 1,
                    fill: "none",
                });
                const pointLabel = self.paper.text({
                    x: 0,
                    y: 0,
                    text: label,
                    fill: color,
                    style:
                        "vector-effect: non-scaling-stroke; font-size:8px; font-family:monospace; transform:translate(2px,-2px); vector-effect:non-scaling-stroke;",
                });
                lineEl = self.paper.group(line, pointLabel);
                lineEl.attr({ id: id, class: "_dbg_" });
            }
            lineEl.select("path").transform(`scale(${sx},${sy})`);
            lineEl.transform(`translate(${x1},${y1})`);

            if (parent !== null) {
                self.add_to_parent(lineEl, parent);
            }
        };

        self.coords = function (label, color = "#ff00ff", parent = null) {
            if (self._isNotEnabled()) return;

            if (!label) {
                console.error("debug.coords needs a label!");
                return;
            }

            const id = `_dbg_${label}`;

            // check if exists
            let axesEl = self.paper.select("#" + id);
            if (!axesEl) {
                const axesPath = self.paper.path({
                    d:
                        "M-100,0h200l-5,-5v10l5,-5 m-100,-100v200l-5,-5h10l-5,5 M0,10v5 M0,20v5 M0,30v5 M0,40v5 M0,50v10 M10,0h5 M20,0h5 M30,0h5 M40,0h5 M50,0h10",
                    stroke: color,
                    strokeWidth: 1,
                    fill: "none",
                });
                const coordLabel = self.paper.text({
                    class: "label",
                    x: 0,
                    y: 0,
                    fill: color,
                    style:
                        "font-size:8px; font-family:monospace; transform:translate(2px,-2px);",
                });
                const xLabel = self.paper.text({
                    x: 100,
                    y: 0,
                    text: "x",
                    fill: color,
                    style:
                        "font-size:8px; font-family:monospace; transform:translate(2px,-2px);",
                });
                const yLabel = self.paper.text({
                    x: 0,
                    y: 100,
                    text: "y",
                    fill: color,
                    style:
                        "font-size:8px; font-family:monospace; transform:translate(2px,-2px);",
                });
                axesEl = self.paper.group(axesPath, coordLabel, xLabel, yLabel);
                axesEl.attr({ id: id, class: "_dbg_" });
            }
            if (parent !== null) {
                self.add_to_parent(axesEl, parent);
            }
            const matrixStr = axesEl
                .transform()
                .totalMatrix.toTransformString();
            axesEl.select(".label").attr({ text: `${label}: ${matrixStr}` });
            return axesEl;
        };

        self.position = function (label, el, color = "#ff00ff") {
            if (self._isNotEnabled()) return;

            if (!label) {
                console.error("debug.position needs a label!");
                return;
            }

            const id = `_dbg_${label}`;

            // check if exists
            let posEl = self.paper.select("#" + id);
            if (!posEl) {
                const y = self.positions * 8;
                posEl = self.paper.text({
                    x: 0,
                    y: y,
                    dy: 8,
                    fill: color,
                    style:
                        "font-size:8px; font-family:monospace; vector-effect:non-scaling-stroke;",
                });
                self.positions += 1;
            }

            if (typeof el === "string") {
                const selector = el;
                el = self.paper.select(selector);
            }

            if (!el) {
                console.error(
                    "debug.position needs an element or selector to work on!"
                );
                return;
            }

            self.paper.mousemove(function (e) {
                let parentMat = Snap.matrix();
                if (el !== null) {
                    parentMat = el.transform().totalMatrix.invert();
                }
                const mmPos = self._get_pointer_event_position_MM(e);
                const x = parentMat.x(mmPos.xMM, mmPos.yMM);
                const y = parentMat.y(mmPos.xMM, mmPos.yMM);
                const text = `${label}: ${x.toFixed(1)},${y.toFixed(1)}`;
                posEl.attr({ text: text });
            });
        };

        self._get_pointer_event_position_MM = function (event) {
            var targetBBox = self.paper.node.getBoundingClientRect();
            const xPx = event.clientX - targetBBox.left;
            const yPx = event.clientY - targetBBox.top;
            const xPerc = xPx / targetBBox.width;
            const yPerc = yPx / targetBBox.height;
            const xMM =
                xPx * MRBEAM_PX2MM_FACTOR_WITH_ZOOM +
                MRBEAM_WORKINGAREA_PAN_MM[0];
            const yMM =
                yPx * MRBEAM_PX2MM_FACTOR_WITH_ZOOM +
                MRBEAM_WORKINGAREA_PAN_MM[1];
            return {
                xPx: xPx,
                yPx: yPx,
                xPerc: xPerc,
                yPerc: yPerc,
                xMM: xMM,
                yMM: yMM,
            };
        };

        self.add_to_parent = function (element, parent) {
            if (!parent) {
                console.warn("No parent specified. Skip.", parent);
                return;
            }

            if (typeof parent === "string") {
                const selector = parent;
                parent = self.paper.select(selector);
                if (parent.length === 0) {
                    console.warn("No parent found. Selector was ", selector);
                    return;
                }
            }

            parent.append(element);
        };

        // TODO: coord grid, path, circle

        self.cleanup = function () {
            if (!self.persist) {
                self.paper.selectAll("._dbg_").remove();
            }
        };
    });
})();
