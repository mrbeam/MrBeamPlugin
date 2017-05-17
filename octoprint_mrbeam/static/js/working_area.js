/* global snap, Snap */

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

	function WorkingAreaViewModel(params) {
		var self = this;

		self.parser = new gcParser();

		self.loginState = params[0];
		self.settings = params[1];
		self.state = params[2];
		self.files = params[3];
		self.profile = params[4];

		self.log = [];

		self.command = ko.observable(undefined);

		self.availableHeight = ko.observable(undefined);
		self.availableWidth = ko.observable(undefined);
		self.px2mm_factor = 1; // initial value
		self.svgDPI = ko.observable(90); // TODO fetch from settings

		self.workingAreaWidthMM = ko.computed(function(){
			return self.profile.currentProfileData().volume.width() - self.profile.currentProfileData().volume.origin_offset_x();
		}, self);
		self.workingAreaHeightMM = ko.computed(function(){
			return self.profile.currentProfileData().volume.depth() - self.profile.currentProfileData().volume.origin_offset_y();
		},self);

        // QuickText fields
        self.fontMap = ['Ubuntu', 'Roboto', 'Libre Baskerville', 'Indie Flower', 'VT323'];
        self.currentQuickTextFile = undefined;
        self.currentQuickText = ko.observable();
        self.lastQuickTextFontIndex = 0;
        self.lastQuickTextIntensity = 0; // rgb values: 0=black, 155=white

        self.camera_offset_x = ko.observable(0);
		self.camera_offset_y = ko.observable(0);
		self.camera_scale = ko.observable(1.0);
		self.camera_rotation = ko.observable(0.0);


		self.hwRatio = ko.computed(function(){
			// y/x = 297/216 junior, respectively 594/432 senior
			var w = self.workingAreaWidthMM();
			var h = self.workingAreaHeightMM();
			var ratio = h / w;
			return ratio;
		}, self);

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
			return self.workingAreaWidthMM() / self.workingAreaWidthPx();
		});

		self.camTransform = ko.computed(function(){
			return "scale("+self.camera_scale()+") rotate("+self.camera_rotation()+"deg) translate("+self.camera_offset_x()+"px, "+self.camera_offset_y()+"px)"
		});


		// matrix scales svg units to display_pixels
		self.scaleMatrix = ko.computed(function(){
			var m = new Snap.Matrix();
			var factor = 25.4/self.svgDPI() * 1/self.px2mm_factor();
			if(!isNaN(factor)){
				m.scale(factor);
				return m;
			}
			return m;
		});

		// matrix scales svg units to display_pixels
		self.scaleMatrixMMtoDisplay = ko.computed(function(){
			var m = new Snap.Matrix();
			var factor = self.svgDPI()/25.4; // scale mm to 90dpi pixels
			var yShift = self.workingAreaHeightMM(); // 0,0 origin of the gcode is bottom left. (top left in the svg)
			if(!isNaN(factor)){
				m.scale(factor, -factor).translate(0,-yShift);
				return m;
			}
			return m;
		});

		self.scaleMatrixCrosshair = function(){
		    var x = self.crosshairX != undefined ? self.crosshairX() : 0;
		    var y = self.crosshairY != undefined ? self.crosshairY() : 0;
		    var m = "matrix(0.09, 0, 0, 0.09, " + x + ", " + y + ")";
		    return m;
        };

		self.placedDesigns = ko.observableArray([]);
		self.working_area_empty = ko.computed(function(){
			return self.placedDesigns().length === 0;
		});

		self.initCameraCalibration = function(){
			var s = self.settings.settings.plugins.mrbeam;
			s.camera_offset_x.subscribe(function(newValue) {
				self.camera_offset_x(newValue);
			});
			s.camera_offset_y.subscribe(function(newValue) {
				self.camera_offset_y(newValue);
			});
			s.camera_scale.subscribe(function(newValue) {
				self.camera_scale(newValue);
			});
			s.camera_rotation.subscribe(function(newValue) {
				self.camera_rotation(newValue);
			});

			s.camera_offset_x.notifySubscribers(s.camera_offset_x());
			s.camera_offset_y.notifySubscribers(s.camera_offset_y());
			s.camera_scale.notifySubscribers(s.camera_scale());
			s.camera_rotation.notifySubscribers(s.camera_rotation());

		};

		self.clear = function(){
			self.abortFreeTransforms();
			snap.selectAll('#userContent>*:not(defs)').remove();
			snap.selectAll('#placedGcodes>*').remove();
            snap.selectAll('rect:not(#coordGrid)').remove();
			self.placedDesigns([]);
		};

		self.colorNamer = new ColorClassifier();
		self.getUsedColors = function () {
			var colHash = {};
			var colFound = [];
			snap.selectAll('#userContent *[stroke]:not(#bbox)').forEach(function (el) {
				var colHex = el.attr().stroke;
				if (typeof(colHex) !== 'undefined' && colHex !== 'none' && typeof(colHash[colHex]) === 'undefined') {
					var colName = self.colorNamer.classify(colHex);
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
			if(self.state.isOperational() && !self.state.isPrinting()){
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
			return pos !== undefined ? (self.mm2px(pos.x)  - 15) : -100; // subtract width/2;

		};
		self.crosshairY = function(){
			var h = self.workingAreaDim != undefined ? self.workingAreaDim()[1] : 0;
			var pos = self.state.currentPos();
			return pos !== undefined ? (h - self.mm2px(pos.y)  - 15) : -100; // subtract height/2;
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

		self.placeGcode = function(file){
			var previewId = self.getEntryId(file);

			// TODO think about if double placing a gcode file is a problem.
//			if(snap.select('#'+previewId)){
//				console.error("working_area placeGcode: file already placed.");
//				return;
//			} else {
				var g = snap.group();
				g.attr({id: previewId});
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
					self.draw_gcode_img_placeholder(x,y,w,h,url, '#'+previewId)
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

		self.placeSVG = function(file) {
			var url = self._getSVGserveUrl(file);
			callback = function (f) {

				// find clippath elements
				var clipPathEl = f.selectAll('clipPath');
				if(clipPathEl.length !== 0){
					console.warn("Warning: removed unsupported clipPath element in SVG");
					self.svg_contains_clipPath_warning();
					clipPathEl.remove();
				}

				var svgClasses = {};
				f.selectAll('path').forEach(function (el, i) {
					var elClass = el.attr('class');
					if(svgClasses[elClass] === undefined){
						console.log(elClass);
					}
				});
				// find all elements with "display=none" and remove them
				f.selectAll("[display=none]").remove();

				// find Illustrator comment and notify
				Array.from(f.node.childNodes).forEach(function(entry) {
					if(entry.nodeType === 8) { // Nodetype 8 = comment
						if(entry.textContent.indexOf('Illustrator') > -1) {
							new PNotify({title: gettext("Illustrator SVG Detected"), text: "Illustrator SVG detected! To preserve coorect scale, please go to the \'Settings\' menu and change the \'SVG dpi\' field under \'Plugins/Svg Conversion\' according to your file. And add it again.", type: "info", hide: false});
						}
					}
				});
				
				// get original svg attributes
				var newSvgAttrs = self._getDocumentNamespaceAttributes(f);
				var doc_dimensions = self._getDocumentDimensionAttributes(f);

				// scale matrix
				var mat = self.getDocumentViewBoxMatrix(doc_dimensions.width, doc_dimensions.height, doc_dimensions.viewbox);
				var dpiscale = 90 / self.settings.settings.plugins.mrbeam.svgDPI();
                var scaleMatrixStr = new Snap.Matrix(mat[0][0],mat[0][1],mat[1][0],mat[1][1],mat[0][2],mat[1][2]).scale(dpiscale).toTransformString();
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

				newSvg.bake(); // remove transforms
				newSvg.selectAll('path').attr({strokeWidth: '0.5'});
				newSvg.attr(newSvgAttrs);
				var id = self.getEntryId(file);
				var previewId = self.generateUniqueId(id); // appends -# if multiple times the same design is placed.
				newSvg.attr({id: previewId});
				snap.select("#userContent").append(newSvg);
				newSvg.transformable();
				newSvg.ftRegisterCallback(self.svgTransformUpdate);

				file.id = id; // list entry id
				file.previewId = previewId;
				file.url = url;
				file.misfit = "";

				self.placedDesigns.push(file);
			};
			self.loadSVG(url, callback);
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
		};

		self.placeDXF = function(file) {
			var url = self._getSVGserveUrl(file);
			
			callback = function (f) {
				var doc_dimensions = self._getDocumentDimensionAttributes(f);
				var newSvgAttrs = self._getDocumentNamespaceAttributes(f);

				// scale matrix
				var mat = self.getDocumentViewBoxMatrix(doc_dimensions.width, doc_dimensions.height, doc_dimensions.viewbox);
				var dpiscale = 90; // self.settings.settings.plugins.mrbeam.svgDPI();
                var scaleMatrixStr = new Snap.Matrix(mat[0][0],mat[0][1],mat[1][0],mat[1][1],mat[0][2],mat[1][2]).scale(dpiscale).toTransformString();

				var newSvg = snap.group(f.selectAll("svg>*"));
				newSvg.attr('transform', scaleMatrixStr);

				newSvg.bake(); // remove transforms
				newSvg.selectAll('path').attr({strokeWidth: '0.5', 'vector-effect':'non-scaling-stroke'});
				newSvg.attr(newSvgAttrs);
				var id = self.getEntryId(file);
				var previewId = self.generateUniqueId(id); // appends -# if multiple times the same design is placed.
				newSvg.attr({id: previewId});
				snap.select("#userContent").append(newSvg);
				newSvg.transformable();
				newSvg.ftRegisterCallback(self.svgTransformUpdate);

				file.id = id; // list entry id
				file.previewId = previewId;
				file.url = url;
				file.misfit = "";

				self.placedDesigns.push(file);
			};
			Snap.loadDXF(url, callback);
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

			// iterate svg tag attributes
			for(var i = 0; i < root_attrs.length; i++){
				var attr = root_attrs[i];

				// get dimensions
				if(attr.name === "width") doc_width = attr.value;
				if(attr.name === "height") doc_height = attr.value;
				if(attr.name === "viewBox") doc_viewbox = attr.value;
			}
			return {
				width: doc_width,
				height: doc_height,
				viewbox: doc_viewbox
			};
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
            var transform = svg.transform();
            var bbox = svg.getBBox();
            var tx = self.px2mm(bbox.x * globalScale);
            var ty = self.workingAreaHeightMM() - self.px2mm(bbox.y2 * globalScale);
            var startIdx = transform.local.indexOf('r') + 1;
            var endIdx = transform.local.indexOf(',', startIdx);
            var rot = parseFloat(transform.local.substring(startIdx, endIdx)) || 0;
            var horizontal = self.px2mm((bbox.x2 - bbox.x) * globalScale);
            var vertical = self.px2mm((bbox.y2 - bbox.y) * globalScale);
            var id = svg.attr('id');
            var label_id = id.substr(0, id.indexOf('-'));
			$('#'+label_id+' .translation').text(tx.toFixed(1) + ',' + ty.toFixed(1));
			$('#'+label_id+' .horizontal').text(horizontal.toFixed() + 'mm');
			$('#'+label_id+' .vertical').text(vertical.toFixed() + 'mm');
			$('#'+label_id+' .rotation').text(rot.toFixed(1) + '°');
			var scale = Math.sqrt((transform.localMatrix.a * transform.localMatrix.a) + (transform.localMatrix.c * transform.localMatrix.c));
			var dpiscale = 90 / self.settings.settings.plugins.mrbeam.svgDPI();
			$('#'+label_id+' .scale').text((scale/dpiscale*100).toFixed(1) + '%');
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

				var dimPT = self.getUsefulDimensions(wpx, hpx);
				var wPT = dimPT[0];
				var hPT = dimPT[1];

				var y = self.mm2svgUnits(self.workingAreaHeightMM()) - hPT;
				var newImg = snap.image(url, 0, y, wPT, hPT);
				var id = self.getEntryId(file);
				var previewId = self.generateUniqueId(id); // appends # if multiple times the same design is placed.
				newImg.attr({id: previewId, filter: 'url(#grayscale_filter)', 'data-serveurl': url});
				snap.select("#userContent").append(newImg);
				newImg.transformable();
				//newImg.ftDisableRotate();
				newImg.ftRegisterCallback(self.svgTransformUpdate);
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
			var destWidthPT = self.mm2svgUnits(destWidthMM);
			var destHeightPT = self.mm2svgUnits(destHeightMM);
			return [destWidthPT, destHeightPT];
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

		self.getDocumentViewBoxMatrix = function(widthStr, heightStr, vbox){
			var dim = self.getDocumentDimensionsInPt(widthStr, heightStr, vbox);
			if(vbox !== null ){
				var widthPx = dim[0];
				var heightPx = dim[1];
				var parts = vbox.split(' ');
				if(parts.length === 4){
					var offsetVBoxX = parseFloat(parts[0]);
					var offsetVBoxY = parseFloat(parts[1]);
					var widthVBox = parseFloat(parts[2]);// - parseFloat(parts[0]);
					var heightVBox = parseFloat(parts[3]);// - parseFloat(parts[1]);

					var fx = widthPx / widthVBox;
					var fy = heightPx / heightVBox;
					var dx = offsetVBoxX * fx;
					var dy = offsetVBoxY * fy;
					return [[fx,0,0],[0,fy,0], [dx,dy,1]];

				}
			}
			return [[1,0,0],[0,1,0], [0,0,1]];
		};

		//a dictionary of unit to user unit conversion factors
		self.uuconv = {
			'in':90.0,
			'pt':1.25,
			'px':1,
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

		self.getEntryId = function(file) {
			return "wa_" + md5(file["origin"] + file["name"] + Date.now());
		};

		self.init = function(){
			// init snap.svg
			snap = Snap('#area_preview');
			self.px2mm_factor.subscribe(function(newVal){
				if(!isNaN(newVal))
					self.draw_coord_grid();
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
				self.move_laser({}, event)
			});
		};

		self.draw_coord_grid = function(){
			var grid = snap.select('#coordGrid');
			var w = self.mm2svgUnits(self.workingAreaWidthMM());
			var h = self.mm2svgUnits(self.workingAreaHeightMM());

			if( grid.attr('width') !== w || grid.attr('height') !== h || grid.attr('fill') === 'none'){
				var max_lines = 20;

				var linedistMM = Math.floor(Math.max(self.workingAreaWidthMM(), self.workingAreaHeightMM()) / (max_lines * 10))*10;
				var yPatternOffset = self.mm2svgUnits(self.workingAreaHeightMM() % linedistMM);
				var linedist = self.mm2svgUnits(linedistMM);

				var marker = snap.circle(linedist/2, linedist/2, 1).attr({
					fill: "#000000",
					stroke: "none",
					strokeWidth: 1,
                    r: 2
				});

				// dot pattern
				var p = marker.pattern(0, 0, linedist, linedist);
				p.attr({
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

		self.generateUniqueId = function(idBase){
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

		self.getCompositionSVG = function(fillAreas, cutOutlines, callback){
			self.abortFreeTransforms();
			var wMM = self.workingAreaWidthMM();
			var hMM = self.workingAreaHeightMM();
			var wPT = wMM * 90 / 25.4;
			var hPT = hMM * 90 / 25.4;

			var compSvg = Snap(wPT, hPT);
			compSvg.attr('id', 'compSvg');
			var userContent = snap.select("#userContent").clone();
			compSvg.append(userContent);

			// remove all items maked with deleteBeforeRendering class
			var dels = compSvg.selectAll('.deleteBeforeRendering');
            if (dels && dels.length > 0) {
                for(var i=0; i<dels.length; i++) {
                    dels[i].remove();
                }
            }

            // embed the fonts as dataUris
            $('#compSvg defs').append('<style id="quickTextFontPlaceholder" class="quickTextFontPlaceholder deleteAfterRendering"></style>')
            self._qt_copyFontsToSvg(compSvg.select(".quickTextFontPlaceholder").node);

			self.renderInfill(compSvg, fillAreas, cutOutlines, wMM, hMM, 10, function(svgWithRenderedInfill){
				callback( self._wrapInSvgAndScale(svgWithRenderedInfill));
				$('#compSvg').remove();
			});
		};

		self._wrapInSvgAndScale = function(content){
			var svgStr = content.innerSVG();
			if(svgStr !== ''){
				var dpiFactor = self.svgDPI()/25.4; // convert mm to pix 90dpi for inkscape, 72 for illustrator
				var w = dpiFactor * self.workingAreaWidthMM();
				var h = dpiFactor * self.workingAreaHeightMM();

				// TODO: look for better solution to solve this Firefox bug problem
				svgStr = svgStr.replace("(\\\"","(");
				svgStr = svgStr.replace("\\\")",")");

				var svg = '<svg height="'+ h +'" version="1.1" width="'+ w +'" xmlns="http://www.w3.org/2000/svg"  xmlns:mb="http://www.mr-beam.org/mbns"><defs/>'+svgStr+'</svg>';
				return svg;
			} else {
				return;
			}
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
				return true
			}else{
				return false
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
				strokeWidth: 1
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

			// check this on tab change as before the bounding boxes are sized 0.
			$('#wa_tab_btn').on('shown.bs.tab', function (e) {
				self.trigger_resize();
				self.check_sizes_and_placements();
			});
			$(window).resize(function(){
				self.trigger_resize();
			});
			self.trigger_resize(); // initialize
			self.onTabChange('#workingarea', '#notab');
			var webcam_image = document.getElementById('webcam_image');
			$(webcam_image).load(function(){
			  $(this).removeClass('broken'); // does not work with inline SVG
//				webcam_image.setAttribute("class", "");
			}).error(function () {
				$(this).addClass('broken'); // does not work with inline SVG
//				webcam_image.setAttribute("class", "broken");
			});

			self.init();
		};

		self.onStartupComplete = function(){
			self.initCameraCalibration();
		};

		self.onBrowserTabVisibilityChange = function(state){
			var currentTab = $('#mrbeam-main-tabs li.active a').attr('href');
			if(typeof currentTab !== undefined && currentTab === "#workingarea"){
				if(state === true){
					self.onTabChange('#workingarea', '#notab');
				}

				if(state === false){
					self.onTabChange('#notab', '#workingarea');
				}
			}
		};

		self.check_sizes_and_placements = function(){
			ko.utils.arrayForEach(self.placedDesigns(), function(design) {
				if(design.type === 'model'){
					var svg = snap.select('#' + design.previewId);
					var misfitting = self.outsideWorkingArea(svg);
					console.log("Misfitting: ", misfitting);
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
				if(i.attr('xlink:href') != null) {
					return !i.attr('xlink:href').startsWith('data:');
				} else if(i.attr('href') != null) {
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
		}

		// render the infill and inject it as an image into the svg
		self.renderInfill = function (svg, fillAreas, cutOutlines, wMM, hMM, pxPerMM, callback) {
			//TODO cutOutlines use it and make it work
			var wPT = wMM * 90 / 25.4;
			var hPT = hMM * 90 / 25.4;
			var tmpSvg = Snap(wPT, hPT).attr('id', 'tmpSvg');
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
							var strippedFilters = style.replace(/filter.+?;/, '');
							item.attr('style', strippedFilters);
						}
					} else {
						// remove stroke from other elements
						var styleNoStroke = 'stroke: none;';
						if (style !== null) {
							styleNoStroke += style.replace(/stroke.+?;/, '');
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

		self.onTabChange = function (current, previous) {
            if (current === "#workingarea") {
                if (self.webcamDisableTimeout != undefined) {
                    clearTimeout(self.webcamDisableTimeout);
                }
                var webcamImage = $("#webcam_image");
                var currentSrc = webcamImage.attr("src");

                if (currentSrc === undefined || currentSrc === "none" || currentSrc.trim() === "") {
                    var newSrc = CONFIG_WEBCAM_STREAM;
                    if (CONFIG_WEBCAM_STREAM.lastIndexOf("?") > -1) {
                        newSrc += "&";
                    } else {
                        newSrc += "?";
                    }
                    newSrc += new Date().getTime();
//                    console.log("webcam src set", newSrc);
                    webcamImage.attr("src", newSrc);
                }
                photoupdate = setInterval(myTimer, 5000);
                function myTimer() {
                    var newSrc = CONFIG_WEBCAM_STREAM;
                    if (CONFIG_WEBCAM_STREAM.lastIndexOf("?") > -1) {
                        newSrc += "&";
                    } else {
                        newSrc += "?";
                    }
                    newSrc += new Date().getTime();
//                    console.log("webcam src set", newSrc);
                    webcamImage.attr("src", newSrc);
                }
                console.log("webcam enabled");
            } else if (previous === "#workingarea") {
                // only disable webcam stream if tab is out of focus for more than 5s, otherwise we might cause
                // more load by the constant connection creation than by the actual webcam stream
                self.webcamDisableTimeout = setTimeout(function () {
                    $("#webcam_image").css("background-image", "none");
                }, 5000);
                window.clearInterval(photoupdate)
            }
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
            self.editQuickText(file)


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
            $('#quick_text_dialog').on('shown.bs.modal', function(){$('#quick_text_dialog_text_input').focus()});
            $('#quick_text_dialog').modal({keyboard: true});
            self.showTransformHandles(self.currentQuickTextFile, false);
            $('#quick_text_dialog_intensity').val(self.currentQuickTextFile.intensity);
            $('#quick_text_dialog_text_input').focus();
        }

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
        })

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
        }

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
        }

        /**
         * updates the actual SVG object and the file list object and more
         * Needs to be called after all changes to a QuickText object
         *
         * Updates will be done for the QT object self.currentQuickTextFile is pointing to
         */
        self._qt_currentQuickTextUpdate = function(){
            if (self.currentQuickTextFile) {
                self.currentQuickText(self.currentQuickTextFile.name);
                var displayText = self.currentQuickTextFile.name != '' ?
                    self.currentQuickTextFile.name : $('#quick_text_dialog_text_input').attr('placeholder');

                // update svg object
                var g = snap.select('#' + self.currentQuickTextFile.previewId);
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
            if (self.currentQuickTextFile && self.currentQuickTextFile.name == '' ) {
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

            file.id = self.getEntryId(file);
            file.previewId = self.generateUniqueId(file.id); // appends -# if multiple times the same design is placed.

            var uc = snap.select("#userContent");
            var text = uc.text(400, 300, placeholderText);
            text.attr('style', 'white-space: pre; font-size: 70; font-family: Ubuntu');

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
            });

            group.transformable();
            group.ftRegisterCallback(self.svgTransformUpdate);

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
        }


        // ***********************************************************
		//  QUICKTEXT end
        // ***********************************************************

	}


    // view model class, parameters for constructor, container to bind to
    ADDITIONAL_VIEWMODELS.push([WorkingAreaViewModel,

		["loginStateViewModel", "settingsViewModel", "printerStateViewModel",  "gcodeFilesViewModel", "laserCutterProfilesViewModel"],
		[document.getElementById("area_preview"),
			document.getElementById("color_classifier"),
			document.getElementById("working_area_files"),
            document.getElementById("quick_text_dialog"),
            document.getElementById("working_area_addstuff"),
			//document.getElementById("webcam_wrapper")
		]]);

});
