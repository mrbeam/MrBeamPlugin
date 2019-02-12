/* global snap, ko, $, Snap, API_BASEURL, _, CONFIG_WEBCAM_STREAM, ADDITIONAL_VIEWMODELS, mina, BEAMOS_DISPLAY_VERSION */

MRBEAM_PX2MM_FACTOR_WITH_ZOOM = 1; // global available in this viewmodel and in snap plugins at the same time.
MRBEAM_DEBUG_RENDERING = false;
if(MRBEAM_DEBUG_RENDERING){
	function debugBase64(base64URL, target=""){
		var dbg_link = "<a target='_blank' href='"+base64URL+"'>Right click -> Open in new tab</a>";
			new PNotify({
				title: "render debug output " + target,
				text: dbg_link,
				type: "warn",
				hide: false
			});
		}
}


$(function(){

	function versionCompare(v1, v2, options) {
		var lexicographical = options && options.lexicographical,
			zeroExtend = options && options.zeroExtend,
			v1parts = v1.split('.'),
			v2parts = v2.split('.');

		function isValidPart(x) {
			return (lexicographical ? /^\d+[A-Za-z]*$/ : /^\d+$/).test(x);
		}

		if (!v1parts.every(isValidPart) || !v2parts.every(isValidPart)) {
			return NaN;
		}

		if (zeroExtend) {
			while (v1parts.length < v2parts.length) v1parts.push("0");
			while (v2parts.length < v1parts.length) v2parts.push("0");
		}

		if (!lexicographical) {
			v1parts = v1parts.map(Number);
			v2parts = v2parts.map(Number);
		}

		for (var i = 0; i < v1parts.length; ++i) {
			if (v2parts.length === i) {
				return 1;
			}

			if (v1parts[i] === v2parts[i]) {
				continue;
			}
			else if (v1parts[i] > v2parts[i]) {
				return 1;
			}
			else {
				return -1;
			}
		}

		if (v1parts.length !== v2parts.length) {
			return -1;
		}

		return 0;
	}

	// constants
    var HUMAN_READABLE_IDS_CONSTANTS = 'bcdfghjklmnpqrstvwxz';
    var HUMAN_READABLE_IDS_VOCALS    = 'aeiouy';

	function getHumanReadableId(length){
		length = length || 4;
		var out = [];
		for (var i = 0; i < length/2; i++) {
			var cIdx = Math.floor(Math.random()*HUMAN_READABLE_IDS_CONSTANTS.length);
			var vIdx = Math.floor(Math.random()*HUMAN_READABLE_IDS_VOCALS.length);
			out.push(HUMAN_READABLE_IDS_CONSTANTS.charAt(cIdx));
			out.push(HUMAN_READABLE_IDS_VOCALS.charAt(vIdx));
		}
		return  out.join('');
	}

	function WorkingAreaViewModel(params) {
		var self = this;

		self.parser = new gcParser();

		self.loginState = params[0];
		self.settings = params[1];
		self.state = params[2];
		self.files = params[3];
		self.profile = params[4];
		self.camera = params[5];

		self.log = [];

		self.command = ko.observable(undefined);
		self.id_counter = 1000;

		self.availableHeight = ko.observable(undefined);
		self.availableWidth = ko.observable(undefined);
		self.px2mm_factor = 1; // initial value
		self.svgDPI = function(){return 90}; // initial value, gets overwritten by settings in onAllBound()
        self.dxfScale =  function(){return 1}; // initial value, gets overwritten by settings in onAllBound()

		self.workingAreaWidthMM = ko.computed(function(){
			return self.profile.currentProfileData().volume.width();
		}, self);
		self.workingAreaHeightMM = ko.computed(function(){
			return self.profile.currentProfileData().volume.depth();
		}, self);
		self.flipYMatrix = ko.computed(function(){
			var h = self.workingAreaHeightMM();
			return Snap.matrix(1,0,0,-1,0,h);
		}, self);

        // get overwritten by settings in onAllBound()
		self.gc_options = ko.computed(function(){
			return {enabled: false};
		});

        // QuickText fields
        self.fontMap = ["Allerta Stencil","Amatic SC","Comfortaa","Fredericka the Great","Kavivanar","Lobster","Merriweather","Mr Bedfort","Quattrocento","Roboto"];
        self.currentQuickTextFile = undefined;
        self.currentQuickText = ko.observable();
        self.currentQuickShapeFile = undefined;
        self.currentQuickShape = ko.observable();
        self.lastQuickTextFontIndex = 0;
        self.lastQuickTextIntensity = 0; // rgb values: 0=black, 155=white

		self.zoom = ko.observable(1.0);
		self.zoomPercX = ko.observable(0);
		self.zoomPercY = ko.observable(0);
		self.zoomOffX = ko.observable(0);
		self.zoomOffY = ko.observable(0);
		self.zoomViewBox = ko.computed(function(){
			var z = self.zoom();
			var w = self.workingAreaWidthMM() * z;
			var h = self.workingAreaHeightMM() * z;
			var x = self.zoomOffX();
			var y = self.zoomOffY();
			return [x, y, w, h].join(' ');
		});

		self.set_zoom_factor = function(delta, centerX, centerY){
			var oldZ = self.zoom();
			var newZ = oldZ + delta;
			newZ = Math.min(Math.max(newZ, 0.25), 1);
			if(newZ !== self.zoom()){
				if(newZ == 1){
				    self.set_zoom_offX(0);
				    self.set_zoom_offY(0);
                }else{
				    var deltaWidth = self.workingAreaWidthMM() * delta;
				    var deltaHeight = self.workingAreaHeightMM() * delta;
				    var oldOffX = self.zoomOffX();
				    var oldOffY = self.zoomOffY();
				    self.set_zoom_offX(oldOffX - deltaWidth*centerX);
				    self.set_zoom_offY(oldOffY - deltaHeight*centerY);
                }
				self.zoom(newZ);
			}
		};
		self.set_zoom_offX = function(offset){
			var max = (1 - self.zoom()) * self.workingAreaWidthMM();
			var min = 0;
			offset = Math.min(Math.max(offset, min), max);
			self.zoomOffX(offset);
		};
		self.set_zoom_offY = function(offset){
			var max = (1 - self.zoom()) * self.workingAreaHeightMM();
			var min = 0;
			offset = Math.min(Math.max(offset, min), max);
			self.zoomOffY(offset);
		};
		self.zoom_factor_text = ko.computed(function(){
			if(self.zoom() !== 1){
				return (1/self.zoom() * 100).toFixed(0) + '%';
			} else {
				return "";
			}
		});

		self.hwRatio = ko.computed(function(){
			// y/x = 297/216 junior, respectively 594/432 senior
			var w = self.workingAreaWidthMM();
			var h = self.workingAreaHeightMM();
			var ratio = h / w;
			return ratio;
		}, self);

		// TODO CLEM check comma expression for functionality!
		self.workingAreaDim = ko.computed(function(){
			var maxH = self.availableHeight();
			var maxW = self.availableWidth();
			var hwRatio = self.hwRatio();
			if( hwRatio > 0, maxH > 0, maxW > 0){
				var w = 0;
				var h = 0;
				if( maxH/maxW > hwRatio) {
					w = maxW;
					h = maxW * hwRatio;
				} else {
					w = maxH / hwRatio;
					h = maxH;
				}
				var dim = [w,h];
				return dim;
			}
		});

		self.workingAreaWidthPx = ko.computed(function(){
			var dim = self.workingAreaDim();
			return dim ? dim[0] : 1;
		}, self);

		self.workingAreaHeightPx = ko.computed(function(){
			var dim = self.workingAreaDim();
			return dim ? dim[1] : 1;
		}, self);

		self.px2mm_factor = ko.computed(function(){
			return self.zoom() * self.workingAreaWidthMM() / self.workingAreaWidthPx();
		});

		// matrix scales svg units to display_pixels
		self.scaleMatrix = ko.computed(function(){
			var m = new Snap.Matrix();
			return m;
		});


//		self.matrixMMflipY = ko.computed(function(){
//			var m = new Snap.Matrix();
//			var yShift = self.workingAreaHeightMM(); // 0,0 origin of the gcode is bottom left. (top left in the svg)
//			m.scale(1, -1).translate(0, -yShift);
//			return m;
//		});

		self.scaleMatrixCrosshair = function(){
		    var x = self.crosshairX !== undefined ? self.crosshairX() : 0;
		    var y = self.crosshairY !== undefined ? self.crosshairY() : 0;
			var y = self.workingAreaHeightMM() - y;
		    var m = "matrix(1, 0, 0, 1, " + x + ", " + y + ")";
		    return m;
        };

		self.placedDesigns = ko.observableArray([]);
		self.working_area_empty = ko.computed(function(){
			return self.placedDesigns().length === 0;
		});

		self.clear = function(){
			self.abortFreeTransforms();
			snap.selectAll('#userContent>*:not(defs)').remove();
			snap.selectAll('#placedGcodes>*').remove();
            snap.selectAll('rect:not(#coordGrid):not(#highlightMarker)').remove();
			self.placedDesigns([]);
		};

		self.colorNamer = new ColorClassifier();
		self.getUsedColors = function () {
			var colHash = {};
			var colFound = [];
			snap.selectAll('#userContent *[stroke]:not(#bbox)').forEach(function (el) {
				var colHex = el.attr().stroke;
				if (typeof(colHex) !== 'undefined' && colHex !== 'none' && typeof(colHash[colHex]) === 'undefined') {
//					var colName = self.colorNamer.classify(colHex);
					var colName = colHex;
					colFound.push({hex: colHex, name: colName});
					colHash[colHex] = 1;
				}
			});
			return colFound;
		};

		self._getHexColorStr = function(inputColor){
			var c = new Color(inputColor);
			return c.getHex();
		};

		self.trigger_resize = function(){
			if(typeof(snap) !== 'undefined') self.abortFreeTransforms();
			var tabContentPadding = 18;
			self.availableHeight(document.documentElement.clientHeight - $('#mrbeam-main-tabs').height() - tabContentPadding); // TODO remove magic number
			self.availableWidth($('#workingarea div.span8').innerWidth());
//			console.log("availableHeight ", self.availableHeight());
//			console.log("availableWidth ", self.availableWidth());
		};

		self.move_laser = function(data, evt){
			self.abortFreeTransforms();
			if(self.state.isOperational() && !self.state.isPrinting() && !self.state.isLocked()){
				var coord = self.getXYCoord(evt);
				$.ajax({
					url: API_BASEURL + "plugin/mrbeam",
					type: "POST",
					dataType: "json",
					contentType: "application/json; charset=UTF8",
					data: JSON.stringify({"command": "position", x:parseFloat(coord.x.toFixed(2)), y:parseFloat(coord.y.toFixed(2))})
				});
			}
		};

		self.getXYCoord = function(evt){
            var elemPos = evt.currentTarget.getBoundingClientRect();
            var x = self.px2mm(evt.clientX - elemPos.left);
            var y = self.px2mm(elemPos.bottom - evt.clientY);
            x = Math.min(x, self.workingAreaWidthMM());
            y = Math.min(y, self.workingAreaHeightMM());
            return {x:x, y:y};
		};

		self.crosshairX = function(){
			var pos = self.state.currentPos();
			if(pos !== undefined){
				return pos.x; //  - 15; // subtract width/2;
			} else {
				return -100;
			}

		};
		self.crosshairY = function(){
			var h = self.workingAreaDim !== undefined ? self.workingAreaDim()[1] : 0;
			var pos = self.state.currentPos();
			return pos !== undefined ? pos.y : -100; //  - 15) : -100; // subtract height/2;
		};

		self.px2mm = function(val){
			return val * self.px2mm_factor();
		};

		self.mm2px = function(val){
			return val / self.px2mm_factor();
		};

		self.mm2svgUnits = function(val){
			return val * self.svgDPI()/25.4;
		};

		self.isPlaced = function(file){
			if(file === undefined) return false;

			var filePlaced = ko.utils.arrayFirst(this.placedDesigns(), function(d) {
				return d.name === file.name;
			});
			return filePlaced;
		};

		self.countPlacements = function(file){
		    // quicktexts can't get duplicated and don't have ["refs"]["download"]
            if (file['type'] === 'quicktext' || file['type'] === 'quickshape') {
                return 1;
            }
			var label = file["refs"]["download"];
			var p = snap.selectAll("g[mb\\:origin='"+label+"']");
			return p.length;
		};

		self.placeGcode = function(file){
			var previewId = self.getEntryId();

			// TODO think about if double placing a gcode file is a problem.
//			if(snap.select('#'+previewId)){
//				console.error("working_area placeGcode: file already placed.");
//				return;
//			} else {
				var g = snap.group();
				g.attr({id: previewId, 'mb:id': self._normalize_mb_id(previewId)});
				snap.select('#placedGcodes').append(g);
				file.previewId = previewId;
				self.placedDesigns.push(file);
//			}

			self.loadGcode(file, function(gcode){
				var pathCallback = function(path){
					var points = [];
					var intensity = -1;
					for (var idx = 0; idx < path.length; idx++) {
						var item = path[idx];
						points.push( [ item.x, item.y ] );
						intensity = item.laser;
					}
					if(points.length > 0)
					self.draw_gcode(points, intensity, '#'+previewId);

				};
				var imgCallback = function(x,y,w,h, url){
					self.draw_gcode_img_placeholder(x,y,w,h,url, '#'+previewId);
				};
				self.parser.parse(gcode, /(m0?3)|(m0?5)/i, pathCallback, imgCallback);
			});
		};

		self.loadGcode = function(file, callback){
			var url = file.refs.download;
			var date = file.date;
			$.ajax({
                url: url,
                data: { "ctime": date },
                type: "GET",
                success: function(response, rstatus) {
                    if(rstatus === 'success'){
						if(typeof(callback) === 'function'){
							callback(response);
						}
                    }
                },
                error: function() {
					console.error("working_area.js placeGcode: unable to load ", url);
                }
            });

		};

		self.removeGcode = function(file){
			var previewId = file.previewId;
			snap.selectAll('#' + previewId).remove();
			self.placedDesigns.remove(file);
		};

        /**
         * Call to place (add) a SVG file to working area
         * @param file
         * @param callback
         */
		self.placeSVG = function(file, callback) {
			var url = self._getSVGserveUrl(file);
			cb = function (fragment) {
				if(self._isBinaryData(fragment.node.textContent)) { // workaround: only catching one loading error
					self.file_not_readable();
					return;
				}
				var id = self.getEntryId();
				var previewId = self.generateUniqueId(id, file); // appends -# if multiple times the same design is placed.
				var origin = file["refs"]["download"];
				file.id = id; // list entry id
				file.previewId = previewId;
				file.url = url;
				file.misfit = false;
				self.placedDesigns.push(file);

				// get scale matrix
                fragment = self._removeUnsupportedSvgElements(fragment); // TODO check if this is necessary. Is done in prepareAndInsertSVG()
				var generator_info = self._get_generator_info(fragment);
				var doc_dimensions = self._getDocumentDimensionAttributes(fragment);
				var unitScaleX = self._getDocumentScaleToMM(doc_dimensions.units_x, generator_info);
				var unitScaleY = self._getDocumentScaleToMM(doc_dimensions.units_y, generator_info);
				var mat = self.getDocumentViewBoxMatrix(doc_dimensions, doc_dimensions.viewbox);
                var scaleMatrixStr = new Snap.Matrix(mat[0][0],mat[0][1],mat[1][0],mat[1][1],mat[0][2],mat[1][2]).scale(unitScaleX, unitScaleY).toTransformString();

				var insertedId = self._prepareAndInsertSVG(fragment, previewId, origin, scaleMatrixStr);
				if(typeof callback === 'function') callback(insertedId);
			};
			try { // TODO Figure out why the loading exception is not caught.
				self.loadSVG(url, cb);
			} catch (e) {
				console.error(e);
				self.file_not_readable();
			}
		};

        /**
         * Call to place (add) a DXF file to working area
         * @param file
         * @param callback (otional)
         */
		self.placeDXF = function(file, callback) {
			var url = self._getSVGserveUrl(file);

			cb = function (fragment) {
				// does not work. false positives. 
//				if(fragment.node.textContent.trim() === ""){ // workaround. try catch does somehow not work.
//					self.file_not_readable();
//					return;
//				}

				var origin = file["refs"]["download"];

				var tx = 0;
				var ty = 0;
				var doc_dimensions = self._getDocumentDimensionAttributes(fragment);
				var viewbox = doc_dimensions.viewbox.split(' ');
				var origin_left = parseFloat(viewbox[0]);
				var origin_top = parseFloat(viewbox[1]);
				if(!isNaN(origin_left) && origin_left < 0) tx = -origin_left * self.dxfScale();
				if(!isNaN(origin_top) && origin_top < 0) ty = -origin_top * self.dxfScale();
				// scale matrix
                var scaleMatrixStr = new Snap.Matrix(1,0,0,1,tx,ty).scale(self.dxfScale()).toTransformString();

				var id = self.getEntryId();
				var previewId = self.generateUniqueId(id, file); // appends -# if multiple times the same design is placed.

				file.id = id; // list entry id
				file.previewId = previewId;
				file.url = url;
				file.misfit = false;

				self.placedDesigns.push(file);

				var insertedId = self._prepareAndInsertSVG(fragment, previewId, origin, scaleMatrixStr);
				if(typeof callback === 'function') callback(insertedId);
			};
			try { // TODO this would be the much better way. Figure out why the loading exception is not caught.
				Snap.loadDXF(url, cb);
			} catch (e) {
				console.error(e);
				self.file_not_readable();
			}

		};

        /**
         * This should be the common handler for everything added to the working area that is converted to SVG
         * @param fragment svg snippet
         * @param id generated by placeSVG, placeDXF, placeImage, quick text, quick shape, ... 
         * @param origin file url or uniq element source id
         * @param scaleMatrixStr (optional)
		 * @param flags object with self-explaining keys (true per default): showTransformHandles, embedGCode, bakeTransforms
         * @returns {*}
         * @private
         */
		self._prepareAndInsertSVG = function(fragment, id, origin, scaleMatrixStr, flags = {}){

			var switches = $.extend({showTransformHandles: true, embedGCode: true, bakeTransforms: true}, flags);
			fragment = self._removeUnsupportedSvgElements(fragment);

			// get original svg attributes
			var newSvgAttrs = self._getDocumentNamespaceAttributes(fragment);
			if (scaleMatrixStr) {
				newSvgAttrs['transform'] = scaleMatrixStr;
			}

			var newSvg = snap.group(fragment.selectAll("svg>*"));
			newSvg.unref(true);

			// handle texts
			var hasText = newSvg.selectAll('text,tspan');
			if(hasText && hasText.length > 0){
				self.svg_contains_text_warning(newSvg);
			}

			// remove style elements with online references
			var hasStyle = newSvg.selectAll('style');
			if (hasStyle && hasStyle.length > 0) {
				for(var y=0; y<hasStyle.length; y++) {
					if (hasStyle[y].node.innerHTML && hasStyle[y].node.innerHTML.search("@import ") >= 0) {
						self.svg_contains_online_style_warning();
						console.warn("Removing style element: web references not supported: ", hasStyle[y].node.innerHTML);
						hasStyle[y].node.remove();
					}
				}
			}

			newSvg.attr(newSvgAttrs);
			if(switches.bakeTransforms){
				newSvg.bake(); // remove transforms
			}
			newSvg.selectAll('path').attr({strokeWidth: '0.8', class:'vector_outline'});
			// replace all fancy color definitions (rgba(...), hsl(...), 'pink', ...) with hex values
			newSvg.selectAll('*[stroke]:not(#bbox)').forEach(function (el) {
				var colStr = el.attr().stroke;
				// handle stroke="" default value (#000000)
				if (typeof(colStr) !== 'undefined' && colStr !== 'none') {
					var colHex = self._getHexColorStr(colStr);
					el.attr('stroke', colHex);
				}
			});
			newSvg.selectAll('*[fill]:not(#bbox)').forEach(function (el) {
				var colStr = el.attr().fill;
				// handle fill="" default value (#000000)
				if (typeof(colStr) !== 'undefined' && colStr !== 'none') {
					var colHex = self._getHexColorStr(colStr);
					el.attr('fill', colHex);
				}
			});

			newSvg.attr({
				id: id,
				'mb:id': self._normalize_mb_id(id),
				class: 'userSVG',
				'mb:origin': origin
			});
			snap.select("#userContent").append(newSvg);
			newSvg.transformable();
			newSvg.ftRegisterBeforeTransformCallback(function(){
				newSvg.clean_gc();
			});
			newSvg.ftRegisterAfterTransformCallback(function(){
				var mb_meta = self._set_mb_attributes(newSvg);
				newSvg.embed_gc(self.flipYMatrix(), self.gc_options(), mb_meta);
			});

			// activate handles on all things we add to the working_area
			if(switches.showTransformHandles){
				self.showTransformHandles(id, true);
			}

			var mb_meta = self._set_mb_attributes(newSvg);
			if(switches.embedGCode){
				newSvg.embed_gc(self.flipYMatrix(), self.gc_options(), mb_meta);
			}

			setTimeout(function(){
				newSvg.ftRegisterOnTransformCallback(self.svgTransformUpdate);
			}, 200);

			return id;
		};

        /**
         * Removes unsupported elements from fragment.
         * List of elements to remove is defined within this function in var unsupportedElems
         * @param fragment
         * @returns fragment
         * @private
         */
		self._removeUnsupportedSvgElements = function(fragment){

            // add more elements that need to be removed here
            var unsupportedElems = ['clipPath', 'flowRoot', 'switch', '#adobe_illustrator_pgf'];
            //
            for (var i = 0; i < unsupportedElems.length; i++) {
                var myElem = fragment.selectAll(unsupportedElems[i]);
                if (myElem.length !== 0) {
                    console.warn("Warning: removed unsupported '"+unsupportedElems[i]+"' element in SVG");
                    self.svg_contains_unsupported_element_warning(unsupportedElems[i]);
                    myElem.remove();
                }
            }

            // find all elements with "display=none" and remove them
            fragment.selectAll("[display=none]").remove(); // TODO check if this really works. I (tp) doubt it.
            fragment.selectAll("script").remove();
            return fragment;
		};

		self.loadSVG = function(url, callback){
			Snap.load(url, callback);
		};

		self.removeSVG = function(file){
			self.abortFreeTransforms();
			snap.selectAll('#'+file.previewId).remove();
			self.placedDesigns.remove(file);
		};
		self.fitSVG = function(file){
			self.abortFreeTransforms();
			var svg = snap.select('#'+file.previewId);
			var fitMatrix = new Snap.Matrix();
			fitMatrix.scale(svg.data('fitMatrix').scale);
			fitMatrix.translate(svg.data('fitMatrix').dx, svg.data('fitMatrix').dy);
			fitMatrix.add(svg.transform().localMatrix);
			svg.transform(fitMatrix);
			self._mark_as_misfit(file, false, svg);
			self.svgTransformUpdate(svg);

			self.showTransformHandles(file.previewId, true);

			var mb_meta = self._set_mb_attributes(svg);
			svg.embed_gc(self.flipYMatrix(), self.gc_options(), mb_meta);
		};


        /**
         * Returns with what program and version the given svg file was created. E.g. 'coreldraw'
         * @param fragment
         * @returns {*}
         * @private
         */
		self._get_generator_info = function(f){
			var gen = null;
			var version = null;
			var root_attrs;
			if(f.select('svg') === null){
				root_attrs = f.node.attributes;
			} else {
				root_attrs = f.select('svg').node.attributes;
			}

			// detect Inkscape by attribute
			var inkscape_version = root_attrs['inkscape:version'];
			if(inkscape_version !== undefined){
				gen = 'inkscape';
				version = inkscape_version.value;
//				console.log("Generator:", gen, version);
				return {generator: gen, version: version};
			}

			// detect Illustrator by comment (works with 'save as svg')
			// <!-- Generator: Adobe Illustrator 16.0.0, SVG Export Plug-In . SVG Version: 6.00 Build 0)  -->
			var children = f.node.childNodes;
			for (var i = 0; i < children.length; i++) {
				var node = children[i];
				if(node.nodeType === 8){ // check for comment
					if (node.textContent.indexOf('Illustrator') > -1) {
						gen = 'illustrator';
						var matches = node.textContent.match(/\d+\.\d+(\.\d+)*/g);
						version = matches.join('_');
//						console.log("Generator:", gen, version);
						return { generator: gen, version: version };
					}
				}
			}

			// detect Illustrator by data-name (for 'export as svg')
			if(root_attrs && root_attrs['data-name']){
				gen = 'illustrator';
				version = '?';
//				console.log("Generator:", gen, version);
				return { generator: gen, version: version };
			}

			// detect Corel Draw by comment
			// <!-- Creator: CorelDRAW X5 -->
			var children = f.node.childNodes;
			for (var i = 0; i < children.length; i++) {
				var node = children[i];
				if(node.nodeType === 8){ // check for comment
					if (node.textContent.indexOf('CorelDRAW') > -1) {
						gen = 'coreldraw';
						var version = node.textContent.match(/(Creator: CorelDRAW) (\S+)/)[2];
//						console.log("Generator:", gen, version);
						return { generator: gen, version: version };
					}
				}
			}

			// detect Method Draw by comment
			// <!-- Created with Method Draw - http://github.com/duopixel/Method-Draw/ -->
			for (var i = 0; i < children.length; i++) {
				var node = children[i];
				if(node.nodeType === 8){ // check for comment
					if (node.textContent.indexOf('Method Draw') > -1) {
						gen = 'method draw';
//						console.log("Generator:", gen, version);
						return { generator: gen, version: version };
					}
				}
			}


			// detect dxf.js generated svg
			// <!-- Created with dxf.js -->
			for (var i = 0; i < children.length; i++) {
				var node = children[i];
				if(node.nodeType === 8){ // check for comment
					if (node.textContent.indexOf('Created with dxf.js') > -1) {
						gen = 'dxf.js';
						console.log("Generator:", gen, version);
						return { generator: gen, version: version };
					}
				}
			}
//			console.log("Generator:", gen, version);
			return { generator: 'unknown', version: 'unknown' };
		};

		self._isBinaryData = function(str){
			return /[\x00-\x08\x0E-\x1F]/.test(str);
		};

        /**
         * Finds dimensions (wifth, hight, etc..) of an SVG
         * @param fragment
         * @returns {{width: *, height: *, viewbox: *, units_x: *, units_y: *}}
         * @private
         */
		self._getDocumentDimensionAttributes = function(fragment){
			if(fragment.select('svg') === null){
				root_attrs = fragment.node.attributes;
			} else {
				var root_attrs = fragment.select('svg').node.attributes;
			}
			var doc_width = null;
			var doc_height = null;
			var doc_viewbox = null;
			var units_x = null;
			var units_y = null;

			// iterate svg tag attributes
			for(var i = 0; i < root_attrs.length; i++){
				var attr = root_attrs[i];

				// get dimensions
				if(attr.name === "width"){
					doc_width = attr.value;
					units_x = doc_width.replace(/[\d.]+/,'');
				}
				if(attr.name === "height"){
					doc_height = attr.value;
					units_y = doc_height.replace(/[\d.]+/,'');
				}
				if(attr.name === "viewBox") doc_viewbox = attr.value;
			}
			return {
				width: doc_width,
				height: doc_height,
				viewbox: doc_viewbox,
				units_x: units_x,
				units_y: units_y
			};
		};

		self._getDocumentScaleToMM = function(declaredUnit, generator){
			if(declaredUnit === null || declaredUnit === ''){
//				console.log("unit '" + declaredUnit + "' not found. Assuming 'px'");
				declaredUnit = 'px';
			}
			if(declaredUnit === 'px' || declaredUnit === ''){
				if(generator.generator === 'inkscape'){
					if(versionCompare(generator.version, '0.91') <= 0){
//						console.log("old inkscape, px @ 90dpi");
						declaredUnit = 'px_inkscape_old';
					} else {
//						console.log("new inkscape, px @ 96dpi");
						declaredUnit = 'px_inkscape_new';
					}
				} else if (generator.generator === 'corel draw'){
//					console.log("corel draw, px @ 90dpi");

				} else if (generator.generator === 'illustrator') {
//					console.log("illustrator, px @ 72dpi");
					declaredUnit = 'px_illustrator';
				} else if (generator.generator === 'unknown'){
//					console.log('unable to detect generator, using settings->svgDPI:', self.svgDPI());
					declaredUnit = 'px_settings';
					self.uuconv.px_settings = self.svgDPI() / 90; // scale to our internal 90
				}
			}
			var declaredUnitValue = self.uuconv[declaredUnit];
			var scale = declaredUnitValue / self.uuconv.mm;
//			console.log("Units: " + declaredUnit, " => scale factor to mm: " + scale);
			return scale;
		};

		self._getDocumentNamespaceAttributes = function(file){
			if(file.select('svg') === null){
				root_attrs = file.node.attributes;
			} else {
				var root_attrs = file.select('svg').node.attributes;
			}
			var namespaces = {};

			// iterate svg tag attributes
			for(var i = 0; i < root_attrs.length; i++){
				var attr = root_attrs[i];

				// copy namespaces into group
				if(attr.name.indexOf("xmlns") === 0){
					namespaces[attr.name] = attr.value;
				}
			}
			return namespaces;
		};

		self.highlightDesign = function(data){
			$('#userContent').addClass('dimDesigns');
			var svgEl = $('#'+data.previewId);
			svgEl.addClass('designHighlight');
			self.showHighlightMarkers(data.previewId);
		};
		self.removeHighlight = function(data){
			$('#userContent').removeClass('dimDesigns');
			var svgEl = $('#'+data.previewId);
			svgEl.removeClass('designHighlight');
			self.showHighlightMarkers(null);
		};
		self.showHighlightMarkers = function(svgId) {
//			if(svgId === null){
//				var w = self.mm2svgUnits(self.workingAreaWidthMM());
//				var h = self.mm2svgUnits(self.workingAreaHeightMM());
//				snap.select('#highlightMarker').attr({x: -1, y:-1, width:0, height:0});
//			} else {
//				var svgEl = snap.select('#'+svgId);
//				var bbox = svgEl.getBBox();
//				var x = bbox.x - 20;
//				var y = bbox.y - 20;
//				var w = bbox.w + 40;
//				var h = bbox.h + 40;
//				snap.select('#highlightMarker').attr({x: x, y:y, width:w, height:h});
//			}
		};

		self.duplicateSVG = function(src) {
			self.abortFreeTransforms();
			var srcElem = snap.select('#'+src.previewId);
			var clone_id = srcElem.attr('mb:clone_of') || self._normalize_mb_id(src.previewId);
			var newSvg = srcElem.clone();
			newSvg.clean_gc();
			var file = {url: src.url, origin: src.origin, name: src.name, type: src.type, refs:{download: src.url}};
			var id = self.getEntryId();
			var previewId = self.generateUniqueId(id, file);
			newSvg.attr({id: previewId,
                'mb:id': self._normalize_mb_id(previewId),
                'mb:clone_of':clone_id,
                class: 'userSVG'});
			snap.select("#userContent").append(newSvg);

			file.id = id; // list entry id
			file.previewId = previewId;
			file.misfit = false;

			self.placedDesigns.push(file);
			self.placeSmart(newSvg);
			newSvg.transformable();
			newSvg.ftRegisterOnTransformCallback(self.svgTransformUpdate);
			newSvg.ftRegisterBeforeTransformCallback(function(){
				newSvg.clean_gc();
			});
			newSvg.ftRegisterAfterTransformCallback(function(){
			    var mb_meta = self._set_mb_attributes(newSvg);
				newSvg.embed_gc(self.flipYMatrix(), self.gc_options(), mb_meta);
			});
			setTimeout(function(){
				newSvg.ftReportTransformation();
			}, 200);

			// activate handles on all things we add to the working_area
            self.showTransformHandles(previewId, true);

            var mb_meta = self._set_mb_attributes(newSvg);
			newSvg.embed_gc(self.flipYMatrix(), self.gc_options(), mb_meta);
			// self.check_sizes_and_placements(); // TODO?
		};

		self.placeSmart = function(elem){
			var spacer = 2;
			var label = elem.attr('mb:origin');
			var placed = snap.selectAll("g[mb\\:origin='"+label+"']");
			var maxY = -9999;
			var minX = self.workingAreaWidthMM();
			var lowestRow = [];
			var leftest = null;
			for (var i = 0; i < placed.length; i++) {
				var item = placed[i];
				if(item.id !== elem.id){
					var bbox = item.getBBox();
					if(bbox.y === maxY){
						lowestRow.push(item);
					} else if(bbox.y > maxY){
						lowestRow = [item];
						maxY = bbox.y;
					}
					if(bbox.x < minX){
						minX = bbox.x;
						leftest = item;
					}
				}
			}
			var lowestRightest = null;
			var maxX = 0;
			for (var i = 0; i < lowestRow.length; i++) {
				var item = lowestRow[i];
				var bbox = item.getBBox();
				if(bbox.x2 > maxX){
					maxX = bbox.x2;
					lowestRightest = item;
				}
			}
			var lowestBBox = lowestRightest.getBBox();
			var elemBBox = elem.getBBox();
			var newX = maxX + spacer;
			var newY = lowestBBox.y;

			if(newX + elemBBox.w > self.workingAreaWidthMM()){
				newX = leftest.getBBox().x;
				newY = lowestBBox.y2 + spacer;
			}
			var dx = newX - elemBBox.x;
			var dy = newY - elemBBox.y;
			var elemCTM = elem.transform().localMatrix;
			elemCTM.e += dx;
			elemCTM.f += dy;
			elem.transform(elemCTM);
		};

        /**
         * toggle transformation handles
         * @param previewId or file
         */
		self.toggleTransformHandles = function(previewId){
		    if (typeof previewId === "object" && previewId.previewId) {
		        previewId = previewId.previewId;
            }
			var el = snap.select('#'+previewId);
			if(el){
				el.ftToggleHandles();
			}
		};

        /**
         * Show or hide transformation handles
         * @param previewId or file
         * @param show true or false
         */
		self.showTransformHandles = function(previewId, show){
		    if (typeof previewId === "object" && previewId.previewId) {
		        previewId = previewId.previewId;
            }
			var el = snap.select('#'+previewId);
			if(el){
			    if (show) {
                    el.ftCreateHandles();
                } else {
			        el.ftRemoveHandles();
                }
			}
		};

		self.svgTransformUpdate = function(svg) {
            var globalScale = self.scaleMatrix().a;
//            var transform = svg.transform();
            var bbox = svg.getBBox();
            var tx = bbox.x * globalScale;
            var ty = self.workingAreaHeightMM() - bbox.y2 * globalScale;
            var horizontal = (bbox.x2 - bbox.x) * globalScale;
            var vertical = (bbox.y2 - bbox.y) * globalScale;
			var rot = svg.ftGetRotation();
            var id = svg.attr('id');
            var label_id = id.substr(0, id.indexOf('-'));
			$('#'+label_id+' .translation').val(tx.toFixed(1) + ',' + ty.toFixed(1));
			$('#'+label_id+' .horizontal').val(horizontal.toFixed() + 'mm');
			$('#'+label_id+' .vertical').val(vertical.toFixed() + 'mm');
			$('#'+label_id+' .rotation').val(rot.toFixed(1) + '°');
			var scale = svg.ftGetScale();
			// var dpiscale = 90 / self.settings.settings.plugins.mrbeam.svgDPI();
			// $('#'+label_id+' .scale').val((scale/dpiscale*100).toFixed(1) + '%');
			$('#'+label_id+' .scale').val((scale*100).toFixed(1) + '%');
			self.check_sizes_and_placements();
		};

		self.svgManualTranslate = function(data, event) {
			if (event.keyCode === 13 || event.type === 'blur') {
				self.abortFreeTransforms();
				var svg = snap.select('#'+data.previewId);
				var globalScale = self.scaleMatrix().a;
				var newTranslateStr = event.target.value;
				var nt = newTranslateStr.split(/[^0-9.-]/); // TODO improve
				var ntx = nt[0] / globalScale;
				var nty = (self.workingAreaHeightMM() - nt[1]) / globalScale;

				svg.ftManualTransform({tx: ntx, ty: nty, diffType:'absolute'});
				self.check_sizes_and_placements();
			}
		};


		self.svgManualRotate = function(data, event) {
			if (event.keyCode === 13 || event.type === 'blur') {
				self.abortFreeTransforms();
				var svg = snap.select('#'+data.previewId);
				var newRotate = parseFloat(event.target.value);
				svg.ftManualTransform({angle: newRotate});
				self.check_sizes_and_placements();
			}
		};
		self.svgManualScale = function(data, event) {
			if (event.keyCode === 13 || event.type === 'blur') {
				self.abortFreeTransforms();
				var svg = snap.select('#'+data.previewId);
				var newScale = parseFloat(event.target.value) / 100.0;
				svg.ftManualTransform({scale: newScale});
				self.check_sizes_and_placements();
			}
		};
		self.svgManualWidth = function(data, event) {
			if (event.keyCode === 13 || event.type === 'blur') {
				self.abortFreeTransforms();
				var svg = snap.select('#'+data.previewId);
				var desiredW = parseFloat(event.target.value);
				var currentW = svg.getBBox().w;
				var globalScale = self.scaleMatrix().a;
				var newRelativeScale = (desiredW / globalScale) / currentW;
				var newScale = newRelativeScale * svg.ftGetScale();
				svg.ftManualTransform({scale: newScale});
				self.check_sizes_and_placements();
			}
		};
		self.svgManualHeight = function(data, event) {
			if (event.keyCode === 13 || event.type === 'blur') {
				self.abortFreeTransforms();
				var svg = snap.select('#'+data.previewId);
				var desiredH = parseFloat(event.target.value);
				var currentH = svg.getBBox().h;
				var globalScale = self.scaleMatrix().a;
				var newRelativeScale = (desiredH / globalScale) / currentH;
				var newScale = newRelativeScale * svg.ftGetScale();
				svg.ftManualTransform({scale: newScale});
				self.check_sizes_and_placements();
			}
		};
		self.svgManualMultiply = function(data, event) {
			if (event.keyCode === 13 || event.type === 'blur') {
				self.abortFreeTransforms();
				var svg = snap.select('#'+data.previewId);
				var gridsize = event.target.value.split(/\D+/);
				var cols = gridsize[0] || 1;
				var rows = gridsize[1] || 1;
				var dist = 2;
				svg.grid(cols, rows, dist);
				var mb_meta = self._set_mb_attributes(svg);
				svg.embed_gc(self.flipYMatrix(), self.gc_options(), mb_meta);
				event.target.value = cols+"×"+rows;
				svg.ftStoreInitialTransformMatrix();
			    svg.ftUpdateTransform();
			    self.check_sizes_and_placements();
			}
		};



		self.outsideWorkingArea = function(svg){
			var waBB = snap.select('#coordGrid').getBBox();
			var svgBB = svg.getBBox();

			var tooWide = svgBB.w > waBB.w;
			var tooHigh = svgBB.h > waBB.h;
			var scale = 1;
			if(tooWide || tooHigh){
				scale = Math.min(waBB.w / svgBB.w, waBB.h / svgBB.h) - 0.0001; // scale minimal smaller to avoid rounding errors
			}

			var dx = 0;
			var dy = 0;
			var outside = false;
			if(svgBB.x < waBB.x){
				dx = -svgBB.x + 0.01;
				outside = true;
			} else if(svgBB.x2 > waBB.x2){
				dx = -svgBB.x + 0.01;
				outside = true;
			}
			if(svgBB.y < waBB.y){
				dy = -svgBB.y + 0.01;
				outside = true;
			} else 	if(svgBB.y2 > waBB.y2){
				dy = -svgBB.y2 + waBB.y2 - 0.01;
				outside = true;
			}

			return {
				oversized: tooWide || tooHigh,
				outside: outside,
				scale: scale,
				dx: dx,
				dy: dy
			};
		};

		self.svg_contains_unsupported_element_warning = function(elemName){
            elemName = elemName.replace('\\:', ':');
			var error = "<p>" + gettext("The SVG file contains unsupported elements: '"+elemName+"' These elements got removed.") + "</p>";
			new PNotify({
				title: "Unsupported elements in SVG: '"+elemName+"'",
				text: error,
				type: "warn",
				hide: false
			});
		};

		self.svg_contains_text_warning = function(svg){
            var error = "<p>" + gettext("The SVG file contains text elements.<br/>If you want to laser just their outlines,<br/>please convert them to paths.<br/>Otherwise they will be engraved with infill.") + "</p>";
            new PNotify({
                title: "Text elements found",
                text: error,
                type: "warn",
                hide: false,
				buttons: {
        			sticker: false
    			}
            });
		};

        self.svg_contains_online_style_warning = function(svg){
            var error = "<p>" + gettext("The SVG file contained style elements with online references. Since online references are not supported, we removed them. The image might look a bit different now.") + "</p>";
            new PNotify({
                title: "Style elements removed",
                text: error,
                type: "warn",
                hide: false,
				buttons: {
        			sticker: false
    			}
            });
		};

        self.file_not_readable = function(){
            var error = "<p>" + gettext("Something went wrong while reading this file. <br/><h3 style='text-align:center;'>Sorry!</h3><br/>Please check it with another application. If it works there, our support team would be happy to take a look.") + "</p>";
            new PNotify({
                title: "Oops.",
                text: error,
                type: "error",
                hide: false,
				buttons: {
        			sticker: false
    			}
            });
		};

		self.placeIMG = function (file) {
			var url = self._getIMGserveUrl(file);
			var img = new Image();
			img.onload = function () {

				var wpx = this.width;
				var hpx = this.height;

				var dimMM = self.getUsefulDimensions(wpx, hpx);
				var wMM = dimMM[0];
				var hMM = dimMM[1];

				var y = self.workingAreaHeightMM() - hMM;
				var imgWrapper = snap.group();
				var newImg = imgWrapper.image(url, 0, y, wMM, hMM); //.attr({transform: 'matrix(1,0,0,-1,0,'+hMM+')'});
				var id = self.getEntryId();
				newImg.attr({filter: 'url(#grayscale_filter)', 'data-serveurl': url});
				var previewId = self.generateUniqueId(id, file); // appends # if multiple times the same design is placed.
				var imgWrapper = snap.group().attr({id: previewId, 'mb:id':self._normalize_mb_id(previewId), class: 'userIMG'});
				imgWrapper.append(newImg);
				snap.select("#userContent").append(imgWrapper);
				imgWrapper.transformable();
				imgWrapper.ftRegisterOnTransformCallback(self.svgTransformUpdate);
				setTimeout(function(){
					imgWrapper.ftReportTransformation();
				}, 200);
				file.id = id;
				file.previewId = previewId;
				file.url = url;
				file.subtype = "bitmap";
				self.placedDesigns.push(file);
			};
			img.src = url;
		};

		self.removeIMG = function(file){
			self.removeSVG(file);
		};

		self.moveSelectedDesign = function(ifX,ifY){
		    var diff = 2;
		    var transformHandles = snap.select('#handlesGroup');

		    if(transformHandles){
				var selectedId = transformHandles.data('parentId');
			    var svg = snap.select('#'+selectedId);
                var globalScale = self.scaleMatrix().a;

                // var bbox = svg.getBBox();
                // var nx = bbox.x + diff * ifX;
                // var ny = bbox.y + diff * ifY;

                var nx = diff * ifX;
                var ny = diff * ifY;

                var ntx = nx/globalScale;
                var nty = ny/globalScale;

                svg.ftStoreInitialTransformMatrix();
                svg.data('tx', ntx);
                svg.data('ty', nty);
                svg.ftUpdateTransform();

			}
        };

		self.removeSelectedDesign = function(){
			var transformHandles = snap.select('#handlesGroup');
			if(transformHandles){
				var selectedId = transformHandles.data('parentId');
				for (var i = 0; i < self.placedDesigns().length; i++) {
					var file = self.placedDesigns()[i];
					if(file.previewId === selectedId){
						self.abortFreeTransforms();
						self.removeSVG(file);
						return;
					}
				}
			}
		};

		self.getUsefulDimensions = function(wpx, hpx){
			var maxWidthMM   = wpx * 0.25; // TODO parametrize
			var maxHeightMM  = hpx * 0.25; // TODO parametrize
			var aspectRatio  = wpx / hpx;
			var destWidthMM  = Math.min(self.workingAreaWidthMM() - 2, maxWidthMM);
			var destHeightMM = Math.min(self.workingAreaHeightMM() - 2, maxHeightMM);
			if ((destWidthMM / aspectRatio) > destHeightMM) {
				destWidthMM = destHeightMM * aspectRatio;
			} else {
				destHeightMM = destWidthMM / aspectRatio;
			}
			return [destWidthMM, destHeightMM];
		};

		self.getDocumentDimensionsInPt = function(doc_width, doc_height, doc_viewbox){
			if(doc_width === null || doc_width === "100%"){
				// assume defaults if not set
				if(doc_viewbox !== null ){
					var parts = doc_viewbox.split(' ');
					if(parts.length === 4){
						doc_width = parts[2];
					}
				}
				if(doc_width === "100%"){
					doc_width = 744.09; // 210mm @ 90dpi
				}
				if(doc_width === null){
					doc_width = 744.09; // 210mm @ 90dpi
				}
			}
			if(doc_height === null || doc_height === "100%"){
				// assume defaults if not set
				if(doc_viewbox !== null ){
					var parts = doc_viewbox.split(' ');
					if(parts.length === 4){
						doc_height = parts[3];
					}
				}
				if(doc_height === "100%"){
					doc_height = 1052.3622047; // 297mm @ 90dpi
				}
				if(doc_height === null){
					doc_height = 1052.3622047; // 297mm @ 90dpi
				}
			}

			var widthPt = self.unittouu(doc_width);
			var heightPt = self.unittouu(doc_height);

			return [widthPt, heightPt];
		};

		self.getDocumentViewBoxMatrix = function(dim, vbox){
			if(dim.width === null || dim.height === null){
				return [[1,0,0],[0,1,0], [0,0,1]];
			}
			if(vbox !== null ){
				var width = parseFloat(dim.width);
				var height = parseFloat(dim.height);
				var parts = vbox.split(' ');
				if(parts.length === 4){
					var offsetVBoxX = parseFloat(parts[0]);
					var offsetVBoxY = parseFloat(parts[1]);
					var widthVBox = parseFloat(parts[2]);
					var heightVBox = parseFloat(parts[3]);

					var fx = width / widthVBox;
					var fy = height / heightVBox;
					var dx = offsetVBoxX * fx;
					var dy = offsetVBoxY * fy;
					return [[fx,0,0],[0,fy,0], [dx,dy,1]];

				}
			}
			return [[1,0,0],[0,1,0], [0,0,1]];
		};

		//a dictionary of unit to user unit conversion factors
		self.uuconv = {
			'px':1, // Reference @ 90 dpi
			'in':90.0,
			'pt':1.25,
			'px_inkscape_old':1, // 90 dpi // < Inkscape v0.91
			'px_inkscape_new':0.9375, // 96 dpi
			'px_illustrator':1.25, // 72 dpi
			'mm':3.5433070866,
			'cm':35.433070866,
			'm':3543.3070866,
			'km':3543307.0866,
			'pc':15.0,
			'yd':3240 ,
			'ft':1080
		};

		// Returns userunits given a string representation of units in another system'''
		self.unittouu = function(string){
			var unit_re = new RegExp('(' + Object.keys(self.uuconv).join('|') +')$');

			var unit_factor = 1;
			var u_match = string.match(unit_re);
			if(u_match !== null){
				var unit = string.substring(u_match.index);
				string = string.substring(0,u_match.index);
				if(self.uuconv[unit])
					unit_factor = self.uuconv[unit];
			}

			var p = parseFloat(string);
			if(p)
				return p * unit_factor;
			return 0;
		};

		self._getSVGserveUrl = function(file){
			if (file && file["refs"] && file["refs"]["download"]) {
				var url = file.refs.download +'?'+ Date.now(); // be sure to avoid caching.
				return url;
			}
		};

		self._getIMGserveUrl = function(file){
			return self._getSVGserveUrl(file);
		};

		self.templateFor = function(data) {
			if(data.type === "model" || data.type === "machinecode") {
                var extension = data.name.split('.').pop().toLowerCase();
                if (extension === "svg") {
                    return "wa_template_" + data.type + "_svg";
				} else if (extension === "dxf") {
                    return "wa_template_" + data.type + "_svg";
                } else if (_.contains(['jpg', 'jpeg', 'png', 'gif', 'bmp', 'pcx', 'webp'], extension)) {
                    return "wa_template_" + data.type + "_img";
                } else {
                    return "wa_template_" + data.type;
                }
            } else if (data.type === "quicktext") {
			    return "wa_template_quicktext";
            } else if (data.type === "quickshape") {
			    return "wa_template_quickshape";
			} else {
				return "wa_template_dummy";
			}
		};

		self.getEntryId = function(prefix, length) {
		    prefix = prefix || 'wa';
			return prefix + "_" + getHumanReadableId(length);
		};

		self.init = function(){
			// init snap.svg
            snap = Snap('#area_preview');
			self.px2mm_factor.subscribe(function(newVal){
				if(!isNaN(newVal)){
					MRBEAM_PX2MM_FACTOR_WITH_ZOOM = newVal;
					self.draw_coord_grid();
				}
			});
			self.workingAreaHeightMM.subscribe(function(newVal){
				if(!isNaN(newVal))
					self.draw_coord_grid();
			});
			self.workingAreaWidthMM.subscribe(function(newVal){
				if(!isNaN(newVal))
					self.draw_coord_grid();
			});

			$('#coordGrid').on('click', function (event) {
				self.abortFreeTransforms();
			});

			$('#coordGrid').on('dblclick', function (event) {
				self.move_laser({}, event);
			});
		};

		self.draw_coord_grid = function(){
			if(snap === null) return;
			var grid = snap.select('#coordGrid');
			var w = self.workingAreaWidthMM();
			var h = self.workingAreaHeightMM();

			if( grid.attr('width') !== w || grid.attr('height') !== h || grid.attr('fill') === 'none'){
				snap.selectAll('#coordPattern').remove();
				var max_lines = 20;

				var linedist = Math.floor(Math.max(self.workingAreaWidthMM(), self.workingAreaHeightMM()) / (max_lines * 10))*10;
				var yPatternOffset = self.workingAreaHeightMM() % linedist;
//				var yPatternOffset = 0;

				var marker = snap.circle(linedist/2, linedist/2, .5).attr({
					fill: "#000000",
					stroke: "none",
					strokeWidth: 1,
                    r: 0.75
				});

				// dot pattern
				var p = marker.pattern(0, 0, linedist, linedist);
				p.attr({
					id: 'coordPattern',
					x: linedist/2,
					y: linedist/2 + yPatternOffset
				});

				grid.attr({
					width: w,
					height: h,
					fill: p
				});
			}
		};

		self.generateUniqueId = function(idBase, file){
		    var suffix = "";
		    if (file) {
                var suffix = self.countPlacements(file);
            } else {
		        suffix = self.id_counter++;
            }

			var suffix = 0;
			var id = idBase + "-" + suffix;
			while(snap.select('#'+id) !== null){
				suffix += 1;
				id = idBase + "-" + suffix;
			}
			return id;
		};

		self.abortFreeTransforms = function(){
			var tip = snap.selectAll('._freeTransformInProgress');
			for (var i = 0; i < tip.length; i++) {
				var el = tip[i];
				el.ftRemoveHandles();
			}
			//self.check_sizes_and_placements();
		};

		self.getCompositionSVG = function(fillAreas, pxPerMM, cutOutlines, callback){
			self.abortFreeTransforms();
			var wMM = self.workingAreaWidthMM();
			var hMM = self.workingAreaHeightMM();
			var wPT = wMM * 90 / 25.4;  // TODO ... switch to 96dpi ?
			var hPT = hMM * 90 / 25.4;
			var compSvg = self.getNewSvg('compSvg', wPT, hPT);
			var attrs = {};
			var content = compSvg.g(attrs);
			var userContent = snap.select("#userContent").clone();
			content.append(userContent);

			// remove all items maked with deleteBeforeRendering class
			var dels = compSvg.selectAll('.deleteBeforeRendering');
            if (dels && dels.length > 0) {
                for(var i=0; i<dels.length; i++) {
                    dels[i].remove();
                }
            }

            // embed the fonts as dataUris
            $('#compSvg defs').append('<style id="quickTextFontPlaceholder" class="quickTextFontPlaceholder deleteAfterRendering"></style>');
            self._qt_copyFontsToSvg(compSvg.select(".quickTextFontPlaceholder").node);

			self.renderInfill(compSvg, fillAreas, cutOutlines, wMM, hMM, pxPerMM, function(svgWithRenderedInfill){
				callback( self._wrapInSvgAndScale(svgWithRenderedInfill));
				$('#compSvg').remove();
			});
		};

		self._wrapInSvgAndScale = function(content){
			var svgStr = content.innerSVG();
			if(svgStr !== ''){
				var wMM = self.workingAreaWidthMM();
				var hMM = self.workingAreaHeightMM();
				var dpiFactor = 90 / 25.4; // we create SVG always with 90 dpi.  // TODO ... switch to 96dpi ?
				var w = dpiFactor * wMM;
				var h = dpiFactor * hMM;
				var viewBox = "0 0 " + wMM + " " + hMM;

				svgStr = self._normalize_svg_string(svgStr);
				var gc_otions_str = self.gc_options_as_string().replace('"', "'");

				var svg = '<svg version="1.1" xmlns="http://www.w3.org/2000/svg" xmlns:mb="http://www.mr-beam.org/mbns"'
						+ ' width="'+ w +'" height="'+ h +'"  viewBox="'+ viewBox +'" mb:gc_options="'+gc_otions_str+'"><defs/>'+svgStr+'</svg>';
				return svg;
			} else {
				return;
			}
		};

		self._normalize_svg_string = function(svgStr){
		    // TODO: look for better solution to solve this Firefox bug problem
            svgStr = svgStr.replace("(\\\"","(");
            svgStr = svgStr.replace("\\\")",")");
            return svgStr;
        };

        self._normalize_mb_id = function(id) {
            return id ? id.replace(/\s/g, '_') : '';
        }

        self.gc_options_as_string = function() {
            var gc_options = self.gc_options();
            var res = [];
            for (var key in gc_options) {
                res.push(key + ":" + gc_options[key]);
            }
            return res.join(", ");
        };

        self._set_mb_attributes = function (snapSvg) {
            var mb_meta = {};
            snapSvg.selectAll("path").forEach(function (element) {
                var id = element.attr('id');

                // if there's no id, let's create one
                if (!id) {
                    id = self.generateUniqueId(self.getEntryId('wa',6));
                    element.attr('id', id);
                }

                var my_meta = {node: element.node.nodeName || ''};
                var attrs = element.node.attributes;
                for (var i = 0; i < attrs.length; i++) {
                    if (attrs[i].nodeName.startsWith('mb:') && attrs[i].nodeName != 'mb:gc') {
                        my_meta[attrs[i].nodeName] = attrs[i].nodeValue;
                    }
                }
                var normalized_id = self._normalize_mb_id(id);
                if (my_meta['mb:id'] && normalized_id != my_meta['mb:id'] && !my_meta['mb:clone_of']) {
                    element.attr('mb:clone_of', my_meta['mb:id']);
                    my_meta['mb:clone_of'] = my_meta['mb:id'];
                }

                element.attr("mb:id", normalized_id);

                my_meta['mb:id'] = normalized_id;
                mb_meta[id] = my_meta;
            });
            return mb_meta;
        };

		self.getPlacedSvgs = function() {
			var svgFiles = [];
			ko.utils.arrayForEach(self.placedDesigns(), function(design) {
				if(design.type === 'model'){
				var extension = design.name.split('.').pop().toLowerCase();
					if (extension === "svg" || extension === "dxf") {
						svgFiles.push(design);
					}
				}
			});
			return svgFiles;
		};

		self.getPlacedImages = function(){
			return snap.selectAll("#userContent image");
		};

		self.hasTextItems = function () {
			if(snap.selectAll("#userContent tspan").length > 0 ||
				snap.selectAll("#userContent text").length > 0 ||
				snap.selectAll("userContent #text").length > 0) {
				return true;
			}else{
				return false;
			}
		};

		self.getPlacedGcodes = ko.computed(function() {
			var gcodeFiles = [];
			ko.utils.arrayForEach(self.placedDesigns(), function(design) {
				if(design.type === 'machinecode') gcodeFiles.push(design);
			});
			return gcodeFiles;
		}, self);

		self.hasFilledVectors = function(){
			var el = snap.selectAll('#userContent *');
			for (var i = 0; i < el.length; i++) {
				var e = el[i];
				if (["path", "circle", "ellipse", "rect", "line", "polyline", "polygon", "path"].indexOf(e.type) >= 0){
					var fill = e.attr('fill');
					var op = e.attr('fill-opacity');
					if(fill !== 'none' && op > 0){
						return true;
					}
				}
			}
			return false;
		};
		self.hasStrokedVectors = function(){
			var el = snap.selectAll('#userContent *');
			for (var i = 0; i < el.length; i++) {
				var e = el[i];
				if (["path", "circle", "ellipse", "rect", "line", "polyline", "polygon", "path"].indexOf(e.type) >= 0){
					var stroke = e.attr('stroke');
					var sw = e.attr('stroke-width');
					if(stroke !== 'none' && parseFloat(sw) > 0){
						return true;
					}
				}
			}
			return false;
		};

		self.draw_gcode = function(points, intensity, target){
			var stroke_color = intensity === 0 ? '#BBBBBB' : '#FF0000';
			var d = 'M'+points.join(' ');
			var p = snap.path(d).attr({
				fill: "none",
				stroke: stroke_color,
				strokeWidth: 0.5,
				'vector-effect': "non-scaling-stroke"
			});
			snap.select(target).append(p);
		};

		self.draw_gcode_img_placeholder = function(x,y,w,h,url, target){
			if(url !== ""){
				var p = snap.image(url,x,y,w,h).attr({
					transform: 'matrix(1,0,0,-1,0,'+ String(h) +')',
					filter: 'url(#gcimage_preview)'
				});

			}
			snap.select(target).append(p);
		};

		self.clear_gcode = function(){
			snap.select('#gCodePreview').clear();
		};

		self.onStartup = function(){
			self.state.workingArea = self;
			self.files.workingArea = self;
			$(window).resize(function(){
				self.trigger_resize();
			});
			self.trigger_resize(); // initialize
			self.init();
		};

		self.onAllBound = function(allViewModels){
		    self.svgDPI = self.settings.settings.plugins.mrbeam.svgDPI; // we assign ko function
		    self.dxfScale = self.settings.settings.plugins.mrbeam.dxfScale;
            self.gc_options = ko.computed(function(){
                return {
                    beamOS: BEAMOS_DISPLAY_VERSION,
                    gc_nextgen: mrbeam.path.version,
                    enabled: self.settings.settings.plugins.mrbeam.gcode_nextgen.enabled(),
                    precision: self.settings.settings.plugins.mrbeam.gcode_nextgen.precision(),
                    optimize_travel: self.settings.settings.plugins.mrbeam.gcode_nextgen.optimize_travel(),
                    small_paths_first: self.settings.settings.plugins.mrbeam.gcode_nextgen.small_paths_first(),
                    clip_working_area: self.settings.settings.plugins.mrbeam.gcode_nextgen.clip_working_area(),
                    clipRect: [0,0,self.workingAreaWidthMM(), self.workingAreaHeightMM()]
                };
            });
			$('#quick_shape_dialog').on('hidden', function(){
				self._qs_removeInvalid();
			});
        };

		self.onTabChange = function(current, prev){
		    if(current == '#settings'){
		        // Since Settings is not a BS dialog anymore,
                // we need to trigger 'show' and 'hidden' events "manually"
                // for OctoPrint to trigger onSettingsShown() and onSettingsHidden()
                if (self.settings && self.settings.settingsDialog) {
                    self.settings.settingsDialog.trigger('show');
                }
		    }
		};

		self.onAfterTabChange = function(current, prev){
			if(current == '#workingarea'){
				self.trigger_resize();
			}
			if(prev == '#settings'){
			    // Since Settings is not a BS dialog anymore,
                // we need to trigger 'show' and 'hidden' events "manually"
                // for OctoPrint to trigger onSettingsShown() and onSettingsHidden()
			    if (self.settings && self.settings.settingsDialog) {
                    self.settings.settingsDialog.trigger('hidden');
                }
            }
		};
		
		self.onBeforeTabChange = function(current, prev){
			self.abortFreeTransforms(); // otherwise transformation is reported when design is not displayed. => has 0 size afterwards.
		};

		self.check_sizes_and_placements = function(){
			ko.utils.arrayForEach(self.placedDesigns(), function(design) {
				if(design.type == 'model' || design.type == 'quicktext' || design.type == 'quickshape'){
					var svg = snap.select('#' + design.previewId);
					var misfitting = self.outsideWorkingArea(svg);
					self._mark_as_misfit(design, misfitting, svg);
                }
			});
		};

		/**
		 * Takes one design (element from placedDesigns) and marks it as misfit or un-marks it
		 * @param design design element to mark or unmark (element from placedDesigns)
		 * @param fitMatrix (from self.outsideWorkingArea()) or null or flash-ish if mark should be removed
		 * @param svg (optional)  snap.select('#' + design.previewId);
		 */
		self._mark_as_misfit = function(design, fitMatrix, svg) {
		    if (!svg) {
		        svg = snap.select('#' + design.previewId);
		    }
		    if(fitMatrix && (fitMatrix.oversized || fitMatrix.outside)){
                design.misfit = true;
                $('#'+design.id).addClass('misfit');
                svg.addClass('misfit');
                svg.selectAll('*').forEach(function(e){e.addClass('misfit')})
                svg.data('fitMatrix', fitMatrix);
            } else {
                design.misfit = false;
                $('#'+design.id).removeClass('misfit');
                svg.removeClass('misfit');
                svg.selectAll('*').forEach(function(e){e.removeClass('misfit')})
                svg.data('fitMatrix', null);
            }
		}

		self._embedAllImages = function(svg, callback){

			var allImages = svg.selectAll('image');
			var linkedImages = allImages.items.filter(function(i){
				if(i.attr('xlink:href') !== null) {
					return !i.attr('xlink:href').startsWith('data:');
				} else if(i.attr('href') !== null) {
					return !i.attr('href').startsWith('data:');
				}});
			if(linkedImages.length > 0){
				var callbackCounter = linkedImages.length;
				for (var i = 0; i < linkedImages.length; i++) {
					var img = linkedImages[i];
					img.embedImage(function(){
						callbackCounter--;
						if(callbackCounter === 0 && typeof callback === 'function'){
							callback();
						}
					});
				}
			} else {
				// callback if nothing to embed
				if(typeof callback === 'function'){
					callback();
				}
			}
		};

		// render the infill and inject it as an image into the svg
		self.renderInfill = function (svg, fillAreas, cutOutlines, wMM, hMM, pxPerMM, callback) {
			//TODO cutOutlines use it and make it work
			var wPT = wMM * 90 / 25.4;
			var hPT = hMM * 90 / 25.4;
			var tmpSvg = self.getNewSvg('tmpSvg', wPT, hPT);
			var attrs = {viewBox: "0 0 " + wMM + " " + hMM};
			tmpSvg.attr(attrs);
			// get only filled items and embed the images
			var userContent = svg.clone();
			tmpSvg.append(userContent);
			self._embedAllImages(tmpSvg, function(){
				var fillings = userContent.removeUnfilled(fillAreas);
				for (var i = 0; i < fillings.length; i++) {
					var item = fillings[i];

					var style = item.attr('style');
					if (item.type === 'image' || item.type === "text" || item.type === "#text") {
						// remove filter effects on images for proper rendering
						if (style !== null) {
							var strippedFilters = style.replace(/filter.+?;/g, '');
							item.attr('style', strippedFilters);
						}
					} else {
						// remove stroke from other elements
						var styleNoStroke = 'stroke: none;';
						if (style !== null) {
							styleNoStroke += style.replace(/stroke.+?;/g, '');
						}
						item.attr('stroke', 'none');
						item.attr('style', styleNoStroke);
					}
				}

				var cb = function(result) {
					if (MRBEAM_DEBUG_RENDERING) {
						debugBase64(result, 'png_debug');
					}

					if(fillings.length > 0){

						// fill rendering replaces all
						svg.selectAll('image').remove();
						svg.selectAll('.deleteAfterRendering').remove();
						svg.selectAll('text,tspan').remove();

						var waBB = snap.select('#coordGrid').getBBox();
						var fillImage = snap.image(result, 0, 0, waBB.w, waBB.h);
						fillImage.attr('id', 'fillRendering');
						svg.append(fillImage);
					}
					if (typeof callback === 'function') {
						callback(svg);
					}
					self._cleanup_render_mess();
				};

				if(MRBEAM_DEBUG_RENDERING){
//					var base64String = btoa(tmpSvg.innerSVG());
					var raw = tmpSvg.innerSVG();
					var svgString = raw.substr(raw.indexOf('<svg'));
					var dataUrl = 'data:image/svg+xml;base64, ' + btoa(svgString);
					debugBase64(dataUrl, 'svg_debug');
				}
				console.log("Rendering " + fillings.length + " filled elements.");
				tmpSvg.renderPNG(wMM, hMM, pxPerMM, cb);
			});
		};

		self._cleanup_render_mess = function(){
			$('#tmpSvg').remove();
		};

		self.onBeforeBinding = function(){
			self.files.workingArea = self;
		};

		self.getNewSvg = function(id, w, h){
		    var svg = Snap(w, h);
            svg.attr('id', id);
            svg.attr('xmlns', 'http://www.w3.org/2000/svg');
            svg.attr('xmlns:mb', 'http://www.mr-beam.org/mbns');
            svg.attr('xmlns:xlink', 'http://www.w3.org/1999/xlink');
            return svg;
        };

		self._enableWorkingAreaOverModal = function(){ $('#area_preview').addClass('overModalBG'); }
		self._disableWorkingAreaOverModal = function(){ setTimeout(function(){$('#area_preview').removeClass('overModalBG');},300); }

        // ***********************************************************
		//  QUICKSHAPE start
        // ***********************************************************


        self.newQuickShape = function() {
            var file = self._qs_placeQuickShape();
            self.editQuickShape(file);

        };

       /**
         * Equivalent to self.placeSVG for QuickShape
         * @returns file object
         */
        self._qs_placeQuickShape = function(){

			var w = self.workingAreaWidthMM() / 5;
			var h = w * 0.5;
			var x = (self.workingAreaWidthMM() - w) / 2;
			var y = (self.workingAreaHeightMM() - h) / 3;
			var r = 0;

            var id = self.getEntryId('qs');
			var origin = id;
			var ts = Date.now();
			var file = {
				date: ts,
				name: '',
				id: id,
				previewId: null,
				url: null,
				misfit: false,
				origin: 'local',
				path: null,
				type: "quickshape",
				typePath: ["quickshape"],
				qs_params: {
					type: '#rect',
					color: '#e25303',
					rect_w: w, rect_h: h, rect_radius: r,
					circle_radius: w,
					star_radius: w/2, star_corners:5, star_sharpness: 0.5522,
					heart_w: w, heart_h:0.8*w, heart_lr: 0
				},
				invalid: false
			};
            var previewId = self.generateUniqueId(id, file); // appends -# if multiple times the same design is placed.
			file.previewId = previewId;
            self.placedDesigns.push(file);

			var d = self._qs_getRect(w,h,r);
			var shapeSvg = '<svg><g><path d="'+d+'" stroke-width="1" stroke="'+file.qs_params.color+'" fill="#ffffff" fill-opacity="0" /></g></svg>';
			var fragment = Snap.parse(shapeSvg);

			var scaleMatrixStr = new Snap.Matrix(1,0,0,1,x,y).toString();
			self._prepareAndInsertSVG(fragment, previewId, origin, '', {showTransformHandles: false, embedGCode: false});
			$('#'+previewId).attr('transform', scaleMatrixStr);
            return file;
        };

		/**
         * Opens QuickText window to edit an existing QuickText object
         * @param file Object representing the QuickText to edit
         */
        self.editQuickShape = function (file) {
			var params = file.qs_params;
			self.showTransformHandles(file.previewId, false);
			self.currentQuickShapeFile = null;
			
			$('#quick_shape_dialog').modal({keyboard: true});
			$('#quick_shape_dialog').one('hide', self._qs_currentQuickShapeShowTransformHandlesIfNotEmpty);
			// firing those change events is necessary to work around a bug in chrome|knockout|js. Otherwise entering numbers directly does not fire the change event if the number is accidentially equal to the field content it had before .val(..).
			$('#quick_shape_rect_w').val(params.rect_w).change();
			$('#quick_shape_rect_h').val(params.rect_h).change();
			$('#quick_shape_rect_radius').val(params.rect_radius).change();
			$('#quick_shape_circle_radius').val(params.circle_radius).change();
			$('#quick_shape_star_radius').val(params.star_radius).change();
			$('#quick_shape_star_corners').val(params.star_corners).change();
			$('#quick_shape_star_sharpness').val(params.star_sharpness).change();
			$('#quick_shape_heart_w').val(params.heart_w).change();
			$('#quick_shape_heart_h').val(params.heart_h).change();
			$('#quick_shape_heart_lr').val(params.heart_lr).change();
			$('#quick_shape_color').val(params.color).change();
			self.currentQuickShapeFile = file;

			$('#shape_tab_link_'+params.type.substr(1)).tab('show');
			$('#quick_shape_dialog div.tab-pane.active input:first').focus();
			self._qs_currentQuickShapeUpdate();
		};

		        /**
         * shows transformation handles on QT if it exists.
         * @private
         */
        self._qs_currentQuickShapeShowTransformHandlesIfNotEmpty = function() {
            if (self.currentQuickShapeFile && self.currentQuickShapeFile.previewId) {
                self.showTransformHandles(self.currentQuickShapeFile.previewId, true);
            }
        };

		self.switchQuickShape = function (newShapeType){
			if (self.currentQuickShapeFile) {
				self.currentQuickShapeFile.qs_params.type = newShapeType;
			}
			self._qs_currentQuickShapeUpdate();
		};

		/**
		 * updates the actual SVG object, the file list object and more
		 * Needs to be called after all changes to a QuickShape object
		 *
		 * Updates will be done for the QS object self.currentQuickShapeFile is pointing to
		 */
		self._qs_currentQuickShapeUpdate = function(){
			if (self.currentQuickShapeFile) {
				self.currentQuickShape(self.currentQuickShapeFile.name);
//				var type = $('#shape_tabs li.active a').attr('href');
				var type = self.currentQuickShapeFile.qs_params.type;
				var qs_params = {
					type: type,
					color: $('#quick_shape_color').val(),
					rect_w: parseFloat($('#quick_shape_rect_w').val()),
					rect_h: parseFloat($('#quick_shape_rect_h').val()),
					rect_radius: parseFloat($('#quick_shape_rect_radius').val()),
					circle_radius: parseFloat($('#quick_shape_circle_radius').val()),
					star_radius: parseFloat($('#quick_shape_star_radius').val()),
					star_corners: parseInt($('#quick_shape_star_corners').val(), 10),
					star_sharpness: parseFloat($('#quick_shape_star_sharpness').val()),
					heart_w: parseFloat($('#quick_shape_heart_w').val()),
					heart_h: parseFloat($('#quick_shape_heart_h').val()),
					heart_lr: parseFloat($('#quick_shape_heart_lr').val())
				};
				// update svg object
				var g = snap.select('#' + self.currentQuickShapeFile.previewId);
				setTimeout(function () {
					g.ftReportTransformation();
				}, 200);
				var shape = g.select('path');
				var d;
				switch(qs_params.type){
					case '#circle':
						d = self._qs_getCircle(qs_params.circle_radius);
						break;
					case '#star':
						d = self._qs_getStar(qs_params.star_radius,qs_params.star_corners,qs_params.star_sharpness);
						break;
					case '#heart':
						d = self._qs_getHeart(qs_params.heart_w,qs_params.heart_h,qs_params.heart_lr);
						break;
					default: // #rect
						d = self._qs_getRect(qs_params.rect_w,qs_params.rect_h,qs_params.rect_radius);
						break;
				}
				shape.attr({d: d, stroke: qs_params.color});
				self.currentQuickShapeFile.qs_params = qs_params;
				if(d === ""){
					self.currentQuickShapeFile.invalid = true;
				} else {
					self.currentQuickShapeFile.invalid = false;
				}

				// update fileslist
				var displayText = self._qs_displayText(qs_params);
				$('#'+self.currentQuickShapeFile.id+' .title').text(displayText);
			}
		};

		self._qs_getCircle = function(r){
			if(isFinite(r) && r > 0){
				return self._qs_getRect(r,r,100);
			} else {
				return "";
			}
				
		};
		self._qs_getRect = function(w,h,r){
			if(!isFinite(w) || 
				!isFinite(h) || 
				!isFinite(r) 
			) {
				return "";
			}
			
			if(r <= 0){
				var d = 'M0,0l'+w+',0 0,'+h+' '+(-w)+',0 z';
				return d;
			} else {
				//     a___________b
				//    /             \
				//   h               c
				//   |               |
				//   g               d
				//    \             /
				//     f___________e

				var rx;
				var ry;
				if(r <= 50){
					rx = r/50 * Math.min(w, h)/2;
					ry = rx;
				} else {
					var rBig = Math.max(w, h)/2;
					var rSmall = Math.min(w, h)/2;
					if(w > h) {
						rx = rSmall + (r-50)/50 * (rBig - rSmall);
						ry = rSmall;
					} else {
						ry = rSmall + (r-50)/50 * (rBig - rSmall);
						rx = rSmall;
					}
				}

				var q = 0.552284749831; // circle approximation with cubic beziers: (4/3)*tan(pi/8) = 0.552284749831

				var a = [rx,0];
				var b = [w-rx,0];
				var c = [w,ry];
				var c1 = [b[0] + q*rx, b[1]];
				var c2 = [c[0], c[1] - q*ry];
				var d = [w,h-ry];
				var e = [w-rx,h];
				var e1 = [d[0], d[1] + q*ry];
				var e2 = [e[0] + q*rx, e[1]];
				var f = [rx,h];
				var g = [0,h-ry];
				var g1 = [f[0] - q*rx, f[1]];
				var g2 = [g[0], g[1] + q*ry];
				var h = [0,ry];
				var a1 = [h[0], h[1] - q*ry];
				var a2 = [a[0] - q*rx, a[1]];

				var d = 'M'+a.join(',')
						+'L'+b.join(',')
						+'C'+c1.join(',')
						+' '+c2.join(',')
						+' '+c.join(',')
						+'L'+d.join(',')
						+'C'+e1.join(',')
						+' '+e2.join(',')
						+' '+e.join(',')
						+'L'+f.join(',')
						+'C'+g1.join(',')
						+' '+g2.join(',')
						+' '+g.join(',')
						+'L'+h.join(',')
						+'C'+a1.join(',')
						+' '+a2.join(',')
						+' '+a.join(',')
						+'z';
				return d;

			}
		};

		self._qs_getStar = function(r,c,sh){
			if(!isFinite(r) || 
				!isFinite(c) || 
				!isFinite(sh) || 
				r < 0 || 
				c < 3  
			) {
				return "";
			}
			var points = [];
			var step = 2*Math.PI / c;
			var ri = (1-sh)*r;
			for (var i = 0; i < c; i++) {
				var angle_outer = i * step;
				var angle_inner = angle_outer + step/2;
				var pox = Math.cos(angle_outer) * r;
				var poy = Math.sin(angle_outer) * r;
				var pix = Math.cos(angle_inner) * ri;
				var piy = Math.sin(angle_inner) * ri;
				points.push(pox, poy, pix, piy);
			}
			var d = 'M'+points[0]+','+points[1]+'L'+points.join(' ') +'z';
			return d;
		};

		self._qs_getHeart = function(w,h,lr){
			if(!isFinite(w) || !isFinite(h) || !isFinite(lr)){
				return "";
			}
			//         __   __
			//        e  \ /  c
			//       (    d    )
			//        f       b
			//         \     /
			//          \   /
			//            a
			var dx = w/5 * 0.78;
			var dy = h/5 * 0.96;
			var q = 0.552284749831; // circle approximation with cubic beziers: (4/3)*tan(pi/8) = 0.552284749831
			var rx = dx;
			var ry = dy;

			var bb = 1.5; // fatter ears
			var earx = 0.4; // longer ears
			var r_comp = Math.max(0,lr)*0.7;
			var l_comp = Math.min(0,lr)*0.7;

			var a = [3*dx, 5*dy];
			var b = [(5+r_comp)*dx, 3*dy];
			var b1 = [a[0] +dx +lr*dx, a[1] - dy];
			var b2 = [b[0] - dx/2, b[1] + dy/2];
			var c = [(5+earx)*dx, (1-earx)*dy];
			var c1 = [b[0] + q*rx, b[1] - q*ry];
			var c2 = [c[0] + q*rx*bb, c[1] + q*ry*bb];
			var d = [3*dx, 1*dy];
			var d1 = [c[0] - q*rx*bb, c[1] - q*ry*bb];
			var d2 = [d[0] + q*rx, d[1] - q*ry];
			var e = [(1-earx)*dx, (1-earx)*dy];
			var e1 = [d[0] - q*rx, d[1] - q*ry];
			var e2 = [e[0] + q*rx*bb, e[1] - q*ry*bb];
			var f = [(1+l_comp)*dx, 3*dy];
			var f1 = [e[0] - q*rx*bb, e[1] + q*ry*bb];
			var f2 = [f[0] - q*rx, f[1] - q*ry];
			var a1 = [f[0] + dx/2, f[1] + dy/2];
			var a2 = [a[0] -dx +lr*dx, a[1] - dy];

			var d = 'M'+a.join(',')
						+'C'+b1.join(',')
						+' '+b2.join(',')
						+' '+b.join(',')
						+'C'+c1.join(',')
						+' '+c2.join(',')
						+' '+c.join(',')
						+'C'+d1.join(',')
						+' '+d2.join(',')
						+' '+d.join(',')
						+'C'+e1.join(',')
						+' '+e2.join(',')
						+' '+e.join(',')
						+'C'+f1.join(',')
						+' '+f2.join(',')
						+' '+f.join(',')
						+'C'+a1.join(',')
						+' '+a2.join(',')
						+' '+a.join(',')
						+'z';
// Debug bezier handles
//						+'M'+a.join(',')
//						+'L'+b1.join(',')
//						+'M'+a.join(',')
//						+'L'+a2.join(',')

//						+'M'+c.join(',')
//						+'L'+d1.join(',')
//						+'M'+d.join(',')
//						+'L'+d2.join(',')
//
//						+'M'+e1.join(',')
//						+'L'+e.join(',')
//						+'L'+e2.join(',')
//
//						+'M'+f1.join(',')
//						+'L'+f.join(',')
//						+'L'+f2.join(',')
//						+'z';
			return d;
		};

		self._qs_displayText = function(qs_params){
			switch(qs_params.type){
				case '#circle':
					return self.currentQuickShapeFile.name !== '' ?
						self.currentQuickShapeFile.name : "Circle Ø " + qs_params.circle_radius + ' mm';
					break;
				case '#heart':
					return self.currentQuickShapeFile.name !== '' ?
						self.currentQuickShapeFile.name : "Heart " + qs_params.heart_w + '*' + qs_params.heart_h + ' mm';
					break;
				case '#star':
					return self.currentQuickShapeFile.name !== '' ?
						self.currentQuickShapeFile.name : "Star Ø " + qs_params.circle_radius + ' mm';
					break;
				default: // #rect
					return self.currentQuickShapeFile.name !== '' ?
						self.currentQuickShapeFile.name : "Rectangle " + qs_params.rect_w + '*' + qs_params.rect_h + ' mm';
					break;
			}

		};
		
		self._qs_removeInvalid = function(){
			if(self.currentQuickShapeFile){
				var remove = self.currentQuickShapeFile.invalid;
				if(remove){
					console.info("Removed invalid QuickShape:", self.currentQuickShapeFile);
					self.removeSVG(self.currentQuickShapeFile);
					self.currentQuickShapeFile = null;
				}
			}
		};
		self._qs_dialogClose = function(){
			self._qs_removeInvalid();
			$('#quick_shape_dialog').modal('hide');
		};

        // ***********************************************************
		//  QUICKSHAPE end
        // ***********************************************************

        // ***********************************************************
		//  QUICKTEXT start
        // ***********************************************************

        /**
         * Opens QuickText window and places a new quickText Object
         * to the working_area and file list.
         */
        self.newQuickText = function() {
            var file = self._qt_placeQuicktext();
            self.editQuickText(file);


            var rules = document.styleSheets[0].rules || document.styleSheets[0].cssRules;
            for(var x=0;x<rules.length;x++) {
               // console.log(rules[x].name + " | " +rules[x].cssText);
               // console.log(rules[x].cssText, rules[x]);
            }
        };

        /**
         * Opens QuickText window to edit an existing QuickText object
         * @param file Object representing the QuickText to edit
         */
        self.editQuickText = function(file) {
            self.currentQuickTextFile = file;
            self._qt_currentQuickTextUpdate();
            $('#quick_text_dialog').one('hide', self._qt_currentQuickTextRemoveIfEmpty);
            $('#quick_text_dialog').one('hide', self._qt_currentQuickTextShowTransformHandlesIfNotEmpty);
			// TODO check if necessary
            $('#quick_text_dialog').one('shown', function(){$('#quick_text_dialog_text_input').focus();});
            $('#quick_text_dialog').modal({keyboard: true});
            self.showTransformHandles(self.currentQuickTextFile.previewId, false);
            $('#quick_text_dialog_intensity').val(self.currentQuickTextFile.intensity);
            $('#quick_text_dialog_text_input').focus();
        };

        /**
         * callback/subscription to changes of the text field
         */
        self.currentQuickText.subscribe(function(nuText) {
            if (self.currentQuickTextFile) {
                self.currentQuickTextFile.name = nuText;
            }
            self._qt_currentQuickTextUpdate();
        });

        /**
         * callback/subscription for the intensity slider
         */
        $('#quick_text_dialog_intensity').on("input change", function(e){
            if (self.currentQuickTextFile) {
                self.currentQuickTextFile.intensity = e.currentTarget.value;
                self.lastQuickTextIntensity = self.currentQuickTextFile.intensity;
                self._qt_currentQuickTextUpdate();
            }
        });

        /**
         * callback for the next font button
         */
        self.currentQuickTextFontNext = function() {
            if (self.currentQuickTextFile) {
                self.currentQuickTextFile.fontIndex++;
                if (self.currentQuickTextFile.fontIndex >= self.fontMap.length) {
                    self.currentQuickTextFile.fontIndex = 0;
                }
                self.lastQuickTextFontIndex = self.currentQuickTextFile.fontIndex;
                self._qt_currentQuickTextUpdate();
            }
        };

        /**
         * callback for the previous font button
         */
        self.currentQuickTextFontPrev = function() {
            if (self.currentQuickTextFile) {
                self.currentQuickTextFile.fontIndex--;
                if (self.currentQuickTextFile.fontIndex < 0) {
                    self.currentQuickTextFile.fontIndex = self.fontMap.length-1;
                }
                self.lastQuickTextFontIndex = self.currentQuickTextFile.fontIndex;
                self._qt_currentQuickTextUpdate();
            }
        };

        /**
         * updates the actual SVG object and the file list object and more
         * Needs to be called after all changes to a QuickText object
         *
         * Updates will be done for the QT object self.currentQuickTextFile is pointing to
         */
        self._qt_currentQuickTextUpdate = function(){
            if (self.currentQuickTextFile) {
                self.currentQuickText(self.currentQuickTextFile.name);
                var displayText = self.currentQuickTextFile.name !== '' ?
                    self.currentQuickTextFile.name : $('#quick_text_dialog_text_input').attr('placeholder');

                // update svg object
                var g = snap.select('#' + self.currentQuickTextFile.previewId);
				setTimeout(function () {
					g.ftReportTransformation();
				}, 200);
                var text = g.select('text');
                var ity = self.currentQuickTextFile.intensity;
                text.attr({
                    text: displayText,
                    'font-family': self.fontMap[self.currentQuickTextFile.fontIndex],
                    fill: 'rgb('+ity+','+ity+','+ity+')',
                    // stroke: 'rgb('+ity+','+ity+','+ity+')',
                });
                var bb = text.getBBox();
                g.select('rect').attr({x: bb.x, y: bb.y, width: bb.width, height: bb.height});

                // update font of input field
                var shadowIty = 0;
                if (ity > 200) {
                    shadowIty = (ity - 200) / 100;
                }
                $('#quick_text_dialog_text_input').css('text-shadow', 'rgba(226, 85, 3, '+shadowIty+') 0px 0px 16px');
                $('#quick_text_dialog_text_input').css('color', 'rgb('+ity+','+ity+','+ity+')');

                $('#quick_text_dialog_text_input').css('font-family', self.fontMap[self.currentQuickTextFile.fontIndex]);
                $('#quick_text_dialog_font_name').text(self.fontMap[self.currentQuickTextFile.fontIndex]);

                // update fileslist
                $('#'+self.currentQuickTextFile.id+' .title').text(displayText);
            }
        };

        /**
         * removes an QT object with an empty text from stage
         */
        self._qt_currentQuickTextRemoveIfEmpty = function() {
            if (self.currentQuickTextFile && self.currentQuickTextFile.name === '' ) {
                self.removeSVG(self.currentQuickTextFile);
            }
        };

        /**
         * shows transformation handles on QT if it exists.
         * @private
         */
        self._qt_currentQuickTextShowTransformHandlesIfNotEmpty = function() {
            if (self.currentQuickTextFile && self.currentQuickTextFile.previewId) {
                self.showTransformHandles(self.currentQuickTextFile.previewId, true);
            }
        };

        /**
         * Equivalent to self.placeSVG for QuickText
         * @returns file object
         */
        self._qt_placeQuicktext = function(){
            var placeholderText = $('#quick_text_dialog_text_input').attr('placeholder');

            var file = {
                date: Date.now(),
                name: '',
                id: null,
                previewId: null,
                url: null,
                misfit: false,
                origin: 'local',
                path: null,
                type: "quicktext",
                typePath: ["quicktext"],
                fontIndex: self.lastQuickTextFontIndex,
                intensity: self.lastQuickTextIntensity
            };

            file.id = self.getEntryId('qt');
            file.previewId = self.generateUniqueId(file.id, file); // appends -# if multiple times the same design is placed.

            var uc = snap.select("#userContent");
			var x = self.workingAreaWidthMM()/2;
			var y = self.workingAreaHeightMM()/3;
			var size = self.workingAreaHeightMM()/20;

			// TODO use self._prepareAndInsertSVG(fragment, previewId, origin, '', {showTransformHandles: false, embedGCode: false});
			// replaces all code below.
            var text = uc.text(x, y, placeholderText);
            text.attr('style', 'white-space: pre; font-size: '+size+'; font-family: Ubuntu; text-anchor: middle');

            var box = uc.rect(); // will be placed and sized by self._qt_currentQuickTextUpdateText()
            box.attr({
                opacity: "0",
                // opacity: "0.3",
                // fill: "yellow"
                class: 'deleteBeforeRendering'
            });

            var group = uc.group(text, box);
            group.attr({
                id: file.previewId,
                'mb:id': self._normalize_mb_id(file.previewId),
				class: 'userText'
            });

            group.transformable();
            group.ftRegisterOnTransformCallback(self.svgTransformUpdate);

            self.placedDesigns.push(file);

            return file;
        };

        /**
         * All fonts need to be provided as dataUrl within the SVG when rendered into a canvas. (If they're not
         * installed on the system which we can't assume.)
         * This copies the content of quicktext-fonts.css into the given element. It's expected that this css file
         * contains @font-face entries with wff2 files as dataUrls. Eg:
         * // @font-face {font-family: 'Indie Flower'; src: url(data:application/font-woff2;charset=utf-8;base64,d09GMgABAAAAAKtEABEAAAABh...) format('woff2');}
         * All fonts to be embedded need to be in 'quicktext-fonts.css' or 'packed_plugins.css'
         * AND their fontFamily name must be included in self.fontMap
         * @private
         * @param DomElement to add the font definition into
         */
        self._qt_copyFontsToSvg = function(elem) {
            var styleSheets = document.styleSheets;
            self._qt_removeFontsFromSvg(elem);
            for(var ss=0;ss<styleSheets.length;ss++) {
                if (styleSheets[ss].href &&
                    (styleSheets[ss].href.includes("quicktext-fonts.css") || styleSheets[ss].href.includes("packed_plugins.css"))) {
                    var rules = styleSheets[ss].cssRules;
                    for(var r=0;r<rules.length;r++) {
                         if (rules[r].constructor == CSSFontFaceRule) {
                             // if (rules[r].cssText && rules[r].cssText.includes('MrBeamQuickText')) {
                             if (rules[r].style && rules[r].style.fontFamily) {
                                 var fontName = rules[r].style.fontFamily.replace(/["']/g, '').trim();
                                 if (self.fontMap.indexOf(fontName) > -1) {
                                     $(elem).append(rules[r].cssText);
                                 }
                             }
                         }
                    }
                }
            }
        };

        /**
         * removes the fonts added by _qt_copyFontsToSvg()
         * @private
         */
		self._qt_removeFontsFromSvg = function(elem) {
		    $(elem).empty();
        };

        // ***********************************************************
		//  QUICKTEXT end
        // ***********************************************************

		self.wheel_zoom = function(target, ev){
			if (ev.originalEvent.shiftKey) {
				var wheel = ev.originalEvent.wheelDelta;
				var targetBBox = ev.currentTarget.getBoundingClientRect();
				var xPerc = (ev.clientX - targetBBox.left) / targetBBox.width;
				var yPerc = (ev.clientY - targetBBox.top) / targetBBox.height;
				var deltaZoom = Math.sign(-wheel)/100;
				self.set_zoom_factor(deltaZoom, xPerc, yPerc);
			}
		};

		self.mouse_drag = function(target, ev){
			if (ev.originalEvent.shiftKey) {
				var pos = self._get_pointer_event_position_MM(ev, ev.currentTarget);
				var newOffX = self.zoomOffX() - pos.dx;
				var newOffY = self.zoomOffY() - pos.dy;
				self.set_zoom_offX(newOffX);
				self.set_zoom_offY(newOffY);
			}
		};

		self._get_pointer_event_position_MM = function(event, target){
			var percPos = self._get_pointer_event_position_Percent(event, target);
			var x = percPos.x * self.workingAreaWidthMM() * self.zoom() + self.zoomOffX();
			var y = percPos.y * self.workingAreaHeightMM() * self.zoom() + self.zoomOffY();
			var dx = percPos.dx * self.workingAreaWidthMM() * self.zoom() ;
			var dy = percPos.dy * self.workingAreaHeightMM() * self.zoom();
			return {x: x, y: y, dx: dx, dy: dy};
		};

		self._get_pointer_event_position_Percent = function(event, target){
			var targetBBox = target.getBoundingClientRect();
			var xPerc = (event.clientX - targetBBox.left) / targetBBox.width;
			var yPerc = (event.clientY - targetBBox.top) / targetBBox.height;
			var dxPerc = (event.originalEvent.movementX) / targetBBox.width;
			var dyPerc = (event.originalEvent.movementY) / targetBBox.height;
			return {x: xPerc, y: yPerc, dx: dxPerc, dy: dyPerc};
		};

	}


    // view model class, parameters for constructor, container to bind to
    ADDITIONAL_VIEWMODELS.push([WorkingAreaViewModel,

		["loginStateViewModel", "settingsViewModel", "printerStateViewModel",
			"gcodeFilesViewModel", "laserCutterProfilesViewModel", "cameraViewModel"],
		[document.getElementById("area_preview"),
			document.getElementById("homing_overlay"),
			document.getElementById("working_area_files"),
            document.getElementById("quick_text_dialog"),
            document.getElementById("quick_shape_dialog"),
			document.getElementById("zoomFactor")
		]]);

});
