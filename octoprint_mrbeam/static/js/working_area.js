/* global snap, ko, $, Snap, API_BASEURL, _, CONFIG_WEBCAM_STREAM, ADDITIONAL_VIEWMODELS, mina */

MRBEAM_PX2MM_FACTOR_WITH_ZOOM = 1; // global available in this viewmodel and in snap plugins at the same time.

$(function(){

	// Opera 8.0+
	var isOpera = (!!window.opr && !!opr.addons) || !!window.opera || navigator.userAgent.indexOf(' OPR/') >= 0;
	// Firefox 1.0+
	var isFirefox = typeof InstallTrigger !== 'undefined';
	// At least Safari 3+: "[object HTMLElementConstructor]"
	var isSafari = Object.prototype.toString.call(window.HTMLElement).indexOf('Constructor') > 0;
	// Internet Explorer 6-11
	var isIE = /*@cc_on!@*/false || !!document.documentMode;
	// Edge 20+
	var isEdge = !isIE && !!window.StyleMedia;
	// Chrome 1+
	var isChrome = !!window.chrome && !!window.chrome.webstore;
	// Blink engine detection
	var isBlink = (isChrome || isOpera) && !!window.CSS;

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

		self.workingAreaWidthMM = ko.computed(function(){
			return self.profile.currentProfileData().volume.width() - self.profile.currentProfileData().volume.origin_offset_x();
		}, self);
		self.workingAreaHeightMM = ko.computed(function(){
			return self.profile.currentProfileData().volume.depth() - self.profile.currentProfileData().volume.origin_offset_y();
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
        self.fontMap = ['Ubuntu', 'Roboto', 'Libre Baskerville', 'Indie Flower', 'VT323'];
        self.currentQuickTextFile = undefined;
        self.currentQuickText = ko.observable();
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
            if (file["type"] == 'quicktext') {
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
				g.attr({id: previewId, 'mb:id':previewId});
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
			snap.select('#' + previewId).remove();
			self.placedDesigns.remove(file);
		};

		self.placeSVG = function(file, callback) {
			var url = self._getSVGserveUrl(file);
			cb = function (fragment) {
				var id = self.getEntryId();
				var previewId = self.generateUniqueId(id, file); // appends -# if multiple times the same design is placed.
				var origin = file["refs"]["download"];
				file.id = id; // list entry id
				file.previewId = previewId;
				file.url = url;
				file.misfit = "";
				self.placedDesigns.push(file);
				var insertedId = self._prepareAndInsertSVG(fragment, previewId, origin);
				if(typeof callback === 'function') callback(insertedId);
			};
			self.loadSVG(url, cb);
		};
		
		self._prepareAndInsertSVG = function(fragment, id, origin){
				var f = self._removeUnsupportedSvgElements(fragment);
				var generator_info = self._get_generator_info(f);

				// get original svg attributes
				var newSvgAttrs = self._getDocumentNamespaceAttributes(f);
				var doc_dimensions = self._getDocumentDimensionAttributes(f);
				var unitScaleX = self._getDocumentScaleToMM(doc_dimensions.units_x, generator_info);
				var unitScaleY = self._getDocumentScaleToMM(doc_dimensions.units_y, generator_info);

				// scale matrix
				var mat = self.getDocumentViewBoxMatrix(doc_dimensions, doc_dimensions.viewbox);
//				var dpiscale = 90 / self.settings.settings.plugins.mrbeam.svgDPI() * (25.4/90);
//				var dpiscale = 25.4 / self.settings.settings.plugins.mrbeam.svgDPI();
//                var scaleMatrixStr = new Snap.Matrix(mat[0][0],mat[0][1],mat[1][0],mat[1][1],mat[0][2],mat[1][2]).scale(dpiscale).toTransformString();
                var scaleMatrixStr = new Snap.Matrix(mat[0][0],mat[0][1],mat[1][0],mat[1][1],mat[0][2],mat[1][2])
						.scale(unitScaleX, unitScaleY).toTransformString();
                newSvgAttrs['transform'] = scaleMatrixStr;

				var newSvg = snap.group(f.selectAll("svg>*"));

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
				newSvg.bake(); // remove transforms
				newSvg.selectAll('path').attr({strokeWidth: '0.8', class:'vector_outline'});
				newSvg.attr({
					id: id,
                    'mb:id':id,
					class: 'userSVG',
					'mb:origin': origin,
				});
				snap.select("#userContent").append(newSvg);
				newSvg.transformable();
				newSvg.ftRegisterOnTransformCallback(self.svgTransformUpdate);
				newSvg.ftRegisterBeforeTransformCallback(function(){
					newSvg.clean_gc();
				});
				newSvg.ftRegisterAfterTransformCallback(function(){
				    var mb_meta = self._set_mb_attributes(newSvg);
					newSvg.embed_gc(self.flipYMatrix(), self.gc_options(), mb_meta);
				});

				var mb_meta = self._set_mb_attributes(newSvg);
				newSvg.embed_gc(self.flipYMatrix(), self.gc_options(), mb_meta);

				setTimeout(function(){
					newSvg.ftReportTransformation();
				}, 200);

				return id;
		};
		
		self._removeUnsupportedSvgElements = function(fragment){
			// find clippath elements and remove them
				var clipPathEl = fragment.selectAll('clipPath');
				if(clipPathEl.length !== 0){
					console.warn("Warning: removed unsupported clipPath element in SVG");
					self.svg_contains_clipPath_warning();
					clipPathEl.remove();
				}

				// find flowroot elements and remove them
				var flowrootEl = fragment.selectAll('flowRoot');
				if(flowrootEl.length !== 0){
					console.warn("Warning: removed unsupported flowRoot element in SVG");
					self.svg_contains_flowRoot_warning();
					flowrootEl.remove();
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
			svg.data('fitMatrix', null);
			$('#'+file.id).removeClass('misfit');
			self.svgTransformUpdate(svg);

			var mb_meta = self._set_mb_attributes(svg);
			svg.embed_gc(self.flipYMatrix(), self.gc_options(), mb_meta);
		};

		self.placeDXF = function(file) {
			var url = self._getSVGserveUrl(file);

			cb = function (f) {
				var doc_dimensions = self._getDocumentDimensionAttributes(f);
				var newSvgAttrs = self._getDocumentNamespaceAttributes(f);

				// scale matrix
				var mat = self.getDocumentViewBoxMatrix(doc_dimensions, doc_dimensions.viewbox);
				var dpiscale = 25.4 ; // assumption: dxf is in inches, scale to mm
                var scaleMatrixStr = new Snap.Matrix(mat[0][0],mat[0][1],mat[1][0],mat[1][1],mat[0][2],mat[1][2]).scale(dpiscale).toTransformString();

				var newSvg = snap.group(f.selectAll("svg>*"));
				newSvg.attr('transform', scaleMatrixStr);

				newSvg.bake(); // remove transforms
				newSvg.selectAll('path').attr({strokeWidth: '0.5', 'vector-effect':'non-scaling-stroke'});
				newSvg.attr(newSvgAttrs);
				var id = self.getEntryId();
				var previewId = self.generateUniqueId(id, file); // appends -# if multiple times the same design is placed.
				newSvg.attr({id: previewId, 'mb:id':previewId});
				snap.select("#userContent").append(newSvg);
				newSvg.transformable();
				newSvg.ftRegisterOnTransformCallback(self.svgTransformUpdate);
				setTimeout(function(){
					newSvg.ftReportTransformation();
				}, 200);
				file.id = id; // list entry id
				file.previewId = previewId;
				file.url = url;
				file.misfit = "";

				self.placedDesigns.push(file);
			};
			Snap.loadDXF(url, cb);
		};

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
				version = inkscape_version;
				console.log("Generator:", gen, version);
				return {generator: gen, version: version};
			}

			// detect Corel
//				return {generator: gen, version: version};

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
						console.log("Generator:", gen, version);
						return { generator: gen, version: version };
					}
				}
			}

			// detect Illustrator by data-name (for 'export as svg')
			if(root_attrs && root_attrs['data-name']){
				gen = 'illustrator';
				version = '?';
				console.log("Generator:", gen, version);
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
						console.log("Generator:", gen, version);
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
						console.log("Generator:", gen, version);
						return { generator: gen, version: version };
					}
				}
			}

			console.log("Generator:", gen, version);
			return { generator: 'unknown', version: 'unknown' };
		};

		self._getDocumentDimensionAttributes = function(file){
			if(file.select('svg') === null){
				root_attrs = file.node.attributes;
			} else {
				var root_attrs = file.select('svg').node.attributes;
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
				console.log("unit '" + declaredUnit + "' not found. Assuming 'px'");
				declaredUnit = 'px';
			}
			if(declaredUnit === 'px' || declaredUnit === ''){
				if(generator.generator === 'inkscape'){
					if(versionCompare(generator.version, '0.91') <= 0){
						console.log("old inkscape, px @ 90dpi");
						declaredUnit = 'px_inkscape_old';
					} else {
						console.log("new inkscape, px @ 96dpi");
						declaredUnit = 'px_inkscape_new';
					}
				} else if (generator.generator === 'corel draw'){
					console.log("corel draw, px @ 90dpi");

				} else if (generator.generator === 'illustrator') {
					console.log("illustrator, px @ 72dpi");
					declaredUnit = 'px_illustrator';
				} else if (generator.generator === 'unknown'){
					console.log('unable to detect generator, using settings->svgDPI:', self.svgDPI());
					declaredUnit = 'px_settings';
					self.uuconv.px_settings = self.svgDPI() / 90; // scale to our internal 90
				}
			}
			var declaredUnitValue = self.uuconv[declaredUnit];
			var scale = declaredUnitValue / self.uuconv.mm;
			console.log("Units: " + declaredUnit, " => scale factor to mm: " + scale);
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
			var clone_id = srcElem.attr('mb:clone_of') || src.previewId;
			var newSvg = srcElem.clone();
			newSvg.clean_gc();
			var file = {url: src.url, origin: src.origin, name: src.name, type: src.type, refs:{download: src.url}};
			var id = self.getEntryId();
			var previewId = self.generateUniqueId(id, file);
			newSvg.attr({id: previewId,
                'mb:id': previewId,
                'mb:clone_of':clone_id,
                class: 'userSVG'});
			snap.select("#userContent").append(newSvg);

			file.id = id; // list entry id
			file.previewId = previewId;
			file.misfit = "";

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

            var mb_meta = self._set_mb_attributes(newSvg);
			newSvg.embed_gc(self.flipYMatrix(), self.gc_options(), mb_meta);
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

		self.toggleTransformHandles = function(file){
			var el = snap.select('#'+file.previewId);
			if(el){
				el.ftToggleHandles();
			}
		};

		self.showTransformHandles = function(file, show){
			var el = snap.select('#'+file.previewId);
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

				svg.ftManualTransform({tx: ntx, ty: nty});
			}
		};
		self.svgManualRotate = function(data, event) {
			if (event.keyCode === 13 || event.type === 'blur') {
				self.abortFreeTransforms();
				var svg = snap.select('#'+data.previewId);
				var newRotate = parseFloat(event.target.value);
				svg.ftManualTransform({angle: newRotate});
			}
		};
		self.svgManualScale = function(data, event) {
			if (event.keyCode === 13 || event.type === 'blur') {
				self.abortFreeTransforms();
				var svg = snap.select('#'+data.previewId);
				var newScale = parseFloat(event.target.value) / 100.0;
				svg.ftManualTransform({scale: newScale});
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

		self.svg_contains_clipPath_warning = function(){
			var error = "<p>" + gettext("The SVG file contains clipPath elements.<br/>clipPath is not supported yet and has been removed from file.") + "</p>";
			new PNotify({
				title: "clipPath elements removed",
				text: error,
				type: "warn",
				hide: false
			});
		};

		self.svg_contains_flowRoot_warning = function(){
			var error = "<p>" + gettext("The SVG file contains flowRoot elements.<br/>flowRoot is not supported yet and has been removed from file.") + "</p>";
			new PNotify({
				title: "flowRoot elements removed",
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

		self.svg_misfitting_warning = function(svg, misfitting){
			var outside = gettext("<br/>It has been moved to (0,0). ");
			var oversized = gettext("<br/>It has resized to %d %. ", misfitting.scale);
            var error = "<p>" + gettext("The design was originally not fitting into the working area.")
					+ outside + oversized + gettext("<br/>Please check the result.") + "</p>";
            new PNotify({
                title: "Design moved",
                text: error,
                type: "warn",
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
				var imgWrapper = snap.group().attr({id: previewId, 'mb:id':previewId, class: 'userIMG'});
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
				// TODO check if this can be made simpler
				var elem = snap.select('._freeTransformInProgress');
				if(elem !== null && elem.data('handlesGroup')){
					elem.ftRemoveHandles();
				}
			});

			$('#coordGrid').on('dblclick', function (event) {
				self.move_laser({}, event);
			});
		};

		self.draw_coord_grid = function(){
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
			self.check_sizes_and_placements();
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
                if (my_meta['mb:id'] && id != my_meta['mb:id'] && !my_meta['mb:clone_of']) {
                    element.attr('mb:clone_of', my_meta['mb:id']);
                    my_meta['mb:clone_of'] = my_meta['mb:id'];
                }

                element.attr("mb:id", id);

                my_meta['mb:id'] = id;
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
		    self.svgDPI = self.settings.settings.plugins.mrbeam.svgDPI;
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
				self.check_sizes_and_placements();
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

		self.check_sizes_and_placements = function(){
			ko.utils.arrayForEach(self.placedDesigns(), function(design) {
				if(design.type === 'model' || design.type === 'quicktext'){
					var svg = snap.select('#' + design.previewId);
					var misfitting = self.outsideWorkingArea(svg);
					// console.log("Misfitting: ", misfitting);
					if(misfitting.oversized || misfitting.outside){
						svg.data('fitMatrix', misfitting);
						$('#'+design.id).addClass('misfit');

					} else {
						$('#'+design.id).removeClass('misfit');
						svg.data('fitMatrix', null);
					}
				}
			});
		};

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

            $('#quick_text_dialog').on('hide.bs.modal', self._qt_currentQuickTextRemoveIfEmpty);
            $('#quick_text_dialog').on('shown.bs.modal', function(){$('#quick_text_dialog_text_input').focus();});
            $('#quick_text_dialog').modal({keyboard: true});
            self.showTransformHandles(self.currentQuickTextFile, false);
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
                misfit: "",
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
                'mb:id': file.previewId,
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
         * @private
         * @param DomElement to add the font definition into
         */
        self._qt_copyFontsToSvg = function(elem) {
            var styleSheets = document.styleSheets;
			for(var ss=0;ss<styleSheets.length;ss++) {
			    if (styleSheets[ss].href && styleSheets[ss].href.endsWith("quicktext-fonts.css")) {
			        self._qt_removeFontsFromSvg(elem);
			        var rules = styleSheets[ss].cssRules;
			        for(var r=0;r<rules.length;r++) {
                        if (rules[r].cssText) {
                            $(elem).append(rules[r].cssText);
                        }
                    }
                    break; // this file appears usually twice....
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
			document.getElementById("zoomFactor")
		]]);

});
