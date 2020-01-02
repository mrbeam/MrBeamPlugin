/* global snap, ko, $, Snap, API_BASEURL, _, CONFIG_WEBCAM_STREAM, ADDITIONAL_VIEWMODELS, mina, BEAMOS_DISPLAY_VERSION */

MRBEAM_PX2MM_FACTOR_WITH_ZOOM = 1; // global available in this viewmodel and in snap plugins at the same time.
MRBEAM_DEBUG_RENDERING = false;
if(MRBEAM_DEBUG_RENDERING){
	function debugBase64(base64URL, target="") {
		var dbg_link = "<a target='_blank' href='"+base64URL+"'>Right click -> Open in new tab</a>"; // debug message, no need to translate
			new PNotify({
				title: "render debug output " + target,
				text: dbg_link,
				type: "warn",
				hide: false
			});
		}
}

$(function(){


	function WorkingAreaViewModel(params) {
		var self = this;
		window.mrbeam.viewModels['workingAreaViewModel'] = self;

		self.parser = new gcParser();

		self.loginState = params[0];
		self.settings = params[1];
		self.state = params[2];
		self.files = params[3];
		self.profile = params[4];
		self.camera = params[5];
		self.readyToLaser = params[6];
		self.tour = params[7];
		self.analytics = params[8];

		self.log = [];
		self.gc_meta = {};

		self.command = ko.observable(undefined);
		self.id_counter = 1000;

		self.availableHeight = ko.observable(undefined);
		self.availableWidth = ko.observable(undefined);
		self.px2mm_factor = 1; // initial value
		self.svgDPI = function(){return 90}; // initial value, gets overwritten by settings in onAllBound()
		self.dxfScale =  function(){return 1}; // initial value, gets overwritten by settings in onAllBound()
		self.previewImgOpacity = ko.observable(1);

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
		self.currentQuickTextAnalyticsData = undefined;
		self.currentQuickText = ko.observable();
		self.quickShapeNames = new Map([['rect', gettext('Rectangle')], ['circle', gettext('Circle')],
			['star', gettext('Star')], ['heart', gettext('Heart')]]);
		self.currentQuickShapeFile = undefined;
		self.currentQuickShapeAnalyticsData = undefined;
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

		self.getUsedColors = function () {
			let colFound = self._getColorsOfSelector('.vector_outline', 'stroke', snap.select('#userContent'));
			return colFound;
		};
		
		self._getColorsOfSelector = function(selector, color_attr = 'stroke', elem = null){
			let root = elem === null ? snap : elem;
			
			let colors = [];
			let items = root.selectAll(selector + '['+color_attr+']');
			for (var i = 0; i < items.length; i++) {
				let col = items[i].attr()[color_attr];
				if(col !== 'undefined' && col !== 'none' && col !== null && col !== ''){
					colors.push(col);
				}
			}
			colors = _.uniq(colors); // unique
			return colors;
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

		self.startTour = function(){
			self.tour.startTour();
		};

		/**
		 * 
		 * @param {type} file (OctoPrint "file" object - example: {url: elem.url, origin: elem.origin, name: name, type: "split", refs:{download: elem.url}};)
		 * @returns {Boolean}
		 */
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
			var start_ts = Date.now();
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
				var duration_load = Date.now() - start_ts;
				start_ts = Date.now();
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

				// analytics
				var re = / beamOS:([0-9.]+) /;
				var match = re.exec(gcode.substring(0, 1000));
				var beamos_vers = match.length > 1 ? match[1] : null;
				var analyticsData = {
					id: previewId,
					file_type: 'gco',
					filename_hash: file.hash,
					size: file.size,
					duration_load: duration_load,
					duration_processing: Date.now() - start_ts,
					gco_generator_info: {
						generator: beamos_vers ? 'beamOS' : null,
						version: beamos_vers ? beamos_vers : null,
					}
				};
				self._analyticsPlaceGco(analyticsData);
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
			var start_ts = Date.now();
			var url = self._getSVGserveUrl(file);
			cb = function (fragment) {
				var duration_load = Date.now() - start_ts;
				start_ts = Date.now();
				if(WorkingAreaHelper.isBinaryData(fragment.node.textContent)) { // workaround: only catching one loading error
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
				var generator_info = WorkingAreaHelper.getGeneratorInfo(fragment);
				var doc_dimensions = self._getDocumentDimensionAttributes(fragment);
				var unitScaleX = self._getDocumentScaleToMM(doc_dimensions.units_x, generator_info);
				var unitScaleY = self._getDocumentScaleToMM(doc_dimensions.units_y, generator_info);
				var mat = self.getDocumentViewBoxMatrix(doc_dimensions, doc_dimensions.viewbox);
				var scaleMatrixStr = new Snap.Matrix(mat[0][0],mat[0][1],mat[1][0],mat[1][1],mat[0][2],mat[1][2]).scale(unitScaleX, unitScaleY).toTransformString();

				var analyticsData = {};
				analyticsData.file_type = 'svg';
				analyticsData.svg_generator_info = generator_info;
				analyticsData.svg_generator_info.generator = analyticsData.svg_generator_info.generator == 'unknown' ? null : analyticsData.svg_generator_info.generator;
				analyticsData.svg_generator_info.version = analyticsData.svg_generator_info.version == 'unknown' ? null : analyticsData.svg_generator_info.version;
				analyticsData.duration_load = duration_load;
				analyticsData.duration_preprocessing = Date.now() - start_ts;
				var insertedId = self._prepareAndInsertSVG(fragment, previewId, origin, scaleMatrixStr, {}, analyticsData, file);
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
			var start_ts = Date.now();
			var url = self._getSVGserveUrl(file);
			cb = function (fragment, timestamps) {
				var duration_load = timestamps.load_done ? timestamps.load_done - start_ts : null;
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

				var analyticsData = {};
				analyticsData.file_type = 'dxf';
				analyticsData.duration_load = duration_load;
				analyticsData.duration_preprocessing = timestamps.parse_start && timestamps.parse_done ? timestamps.parse_done - timestamps.parse_start : null;
				var insertedId = self._prepareAndInsertSVG(fragment, previewId, origin, scaleMatrixStr, {}, analyticsData, file);
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
		self._prepareAndInsertSVG = function(fragment, id, origin, scaleMatrixStr, flags, analyticsData, fileObj, start_ts){
			analyticsData = analyticsData || {};
			fileObj = fileObj || {};
			origin = origin || '';
			start_ts = start_ts || Date.now();

			if (!analyticsData._skip) { // this is a flag used by quickShape
				analyticsData.id = fileObj ? fileObj.id : id;
				analyticsData.file_type = analyticsData.file_type || (fileObj.display ? fileObj.display.split('.').slice(-1)[0] : origin.split('.').slice(-1)[0]);
				analyticsData.filename_hash = fileObj.hash || origin.split('/downloads/files/local/').slice(-1)[0].hashCode();
				analyticsData.size = fileObj.size;
				analyticsData.node_count = 0;
				analyticsData.node_types = {};
				analyticsData.path_char_lengths = [];
				analyticsData.text_font_families = [];
				analyticsData.removed_unsupported_elements = {};
				analyticsData.removed_unnecessary_elements = {};
				analyticsData.removed_import_references = {};
				analyticsData.ignored_elements = {};
				analyticsData.namespaces = [];

				let allNodes = fragment.selectAll("*");
				analyticsData.node_count = allNodes.length;
				for (let i = 0; i < allNodes.length; i++) {
					if (!(allNodes[i].type in analyticsData.node_types)) {
						analyticsData.node_types[allNodes[i].type] = 0;
					}
					analyticsData.node_types[allNodes[i].type]++;
					if (allNodes[i].type == 'path') {
						analyticsData.path_char_lengths.push(allNodes[i].attr('d').length);
					}
					if (allNodes[i].type == 'text') {
						let fontFam = allNodes[i].node.style.fontFamily;
						fontFam = fontFam ? fontFam.replace(/"/g, '').replace(/'/g, "") : null;
						if (!fontFam || !Boolean(fontFam.trim())){
							fontFam = allNodes[i].node.getAttribute("font-family");
						}
						fontFam = fontFam ? fontFam.replace(/"/g, '').replace(/'/g, "") : null;
						analyticsData.text_font_families.push(fontFam);
					}
				}
			}

			try {
				var switches = $.extend({showTransformHandles: true, embedGCode: true, bakeTransforms: true}, flags);
				fragment = self._removeUnsupportedSvgElements(fragment, analyticsData);

				// get original svg attributes
				var newSvgAttrs = self._getDocumentNamespaceAttributes(fragment, analyticsData);
				if (scaleMatrixStr) {
					newSvgAttrs['transform'] = scaleMatrixStr;
				}

				// assign id directly after placement. otherwise it is not UI-removable in case of exceptions during placement.
				var newSvg = snap.group(fragment.selectAll("svg>*"));
				newSvg.attr({
					id: id,
					'mb:id': self._normalize_mb_id(id),
					class: 'userSVG',
					'mb:origin': origin
				});

				newSvg.unref(true);

				// handle texts
				var hasText = newSvg.selectAll('text,tspan');
				if (hasText && hasText.length > 0) {
					self.svg_contains_text_warning(newSvg);
				}

				// remove style elements with online references
				var hasStyle = newSvg.selectAll('style');
				if (hasStyle && hasStyle.length > 0) {
					for (var y = 0; y < hasStyle.length; y++) {
						if (hasStyle[y].node.innerHTML && hasStyle[y].node.innerHTML.search("@import ") >= 0) {
							self.svg_contains_online_style_warning();
							console.warn("Removing style element: web references not supported: ", hasStyle[y].node.innerHTML);
							if (!(hasStyle[y].type in analyticsData.removed_import_references)) {analyticsData.removed_import_references[hasStyle[y].type] = 0};
							analyticsData.removed_import_references[hasStyle[y].type]++;
							hasStyle[y].node.remove();
						}
					}
				}

				newSvg.attr(newSvgAttrs);
				if (switches.bakeTransforms) {
					window.mrbeam.bake_progress = 0;
					var ignoredElements = newSvg.bake(self._bake_progress_callback); // remove transforms
					for (var i=0; i < ignoredElements.length; i++) {
						if (!(ignoredElements[i] in analyticsData.ignored_elements)) analyticsData.ignored_elements[ignoredElements[i]] = 0;
						analyticsData.ignored_elements[ignoredElements[i]]++;
					}
				}
				newSvg.selectAll('path').attr({strokeWidth: '0.8', class: 'vector_outline'});
				// replace all fancy color definitions (rgba(...), hsl(...), 'pink', ...) with hex values
				newSvg.selectAll('*[stroke]:not(#bbox)').forEach(function (el) {
					var colStr = el.attr().stroke;
					// handle stroke="" default value (#000000)
					if (typeof (colStr) !== 'undefined' && colStr !== 'none') {
						var colHex = WorkingAreaHelper.getHexColorStr(colStr);
						el.attr('stroke', colHex);
					}
				});
				newSvg.selectAll('*[fill]:not(#bbox)').forEach(function (el) {
					var colStr = el.attr().fill;
					// handle fill="" default value (#000000)
					if (typeof (colStr) !== 'undefined' && colStr !== 'none') {
						var colHex = WorkingAreaHelper.getHexColorStr(colStr);
						el.attr('fill', colHex);
					}
				});

				snap.select("#userContent").append(newSvg);
				self._makeItTransformable(newSvg);

				return id;
			} catch(e) {
				analyticsData['error'] = e.stack;
				console.error(e)
				self.svg_place_general_error(e.stack);
			} finally {
				analyticsData.duration_processing = Date.now() - start_ts;
				self._analyticsPrepareAndInsertSVG(analyticsData)
			}
		};

		self._bake_progress_callback = function(percent, done, total) {
			window.mrbeam.bake_progress = percent;
			// console.log("_bake_progress_callback() "+percent.toFixed()+"% | " + done + " / " + total);
		};

		/**
		 * Removes unsupported elements from fragment.
		 * List of elements to remove is defined within this function in var unsupportedElems
		 * @param fragment
		 * @param analyticsData obj - this object gets modiyfied but not returned!!
		 * @returns fragment
		 * @private
		 */
		self._removeUnsupportedSvgElements = function(fragment, analyticsData){

			// add more elements that need to be removed here
			var unsupportedElems = ['clipPath', 'flowRoot', 'switch', '#adobe_illustrator_pgf'];
//			var unsupportedElems = ['flowRoot', 'switch', '#adobe_illustrator_pgf'];
			//
			for (var i = 0; i < unsupportedElems.length; i++) {
				var myElem = fragment.selectAll(unsupportedElems[i]);
				if (myElem.length !== 0) {
					analyticsData.removed_unsupported_elements[unsupportedElems[i]] = myElem.length;
					console.warn("Warning: removed unsupported '"+unsupportedElems[i]+"' element in SVG");
					self.svg_contains_unsupported_element_warning(unsupportedElems[i]);
					myElem.remove();
				}
			}

			// remove other unnecessary or invisible ("display=none") elements
			let removeElements = fragment.selectAll("metadata, script, [display=none]");
			for (var i = 0; i < removeElements.length; i++) {
				if (!(removeElements[i] in analyticsData.removed_unnecessary_elements)) analyticsData.removed_unnecessary_elements[removeElements[i].type] = 0;
				analyticsData.removed_unnecessary_elements[removeElements[i].type]++;
			}
			removeElements.remove();
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
			// svg.embed_gc(self.flipYMatrix(), self.gc_options(), mb_meta);
		};




		/**
		 * Finds dimensions (wifth, height, etc..) of an SVG
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
					if(WorkingAreaHelper.versionCompare(generator.version, '0.91') <= 0){
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

		self._getDocumentNamespaceAttributes = function(file, analyticsData){
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
					analyticsData.namespaces[attr.name] = attr.value;
				}
			}
			return namespaces;
		};

		self.highlightDesign = function(data){
			var svgEl = $('#'+data.previewId);
			svgEl.addClass('designHighlight');
		};
		self.removeHighlight = function(data){
			var svgEl = $('#'+data.previewId);
			svgEl.removeClass('designHighlight');
		};

		self.splitSVG = function(elem, event, method) {
			self.abortFreeTransforms();
			let srcElem = snap.select('#'+elem.previewId);
			
			let parts;
			switch(method){
				case 'stroke-color':
					parts = srcElem.separate_by_stroke_colors();
					if(parts.length <= 1) failReason = "Didn't find different stroke colors.";
					break;
				case 'non-intersecting': // TODO: provide cancel check and proper progress callback
					parts = srcElem.separate_by_non_intersecting_bbox(null, function(n){ console.log("Separate non intersecting shapes: ", n); });
					if(parts.length <= 1) failReason = "Didn't find different stroke colors.";
					break;
				case 'divide':
				default:
					parts = srcElem.separate_by_native_elements(2);
					if(parts.length <= 1) failReason = "Looks like a single path.";
			}
			
			if(parts.length > 1){
				self.removeSVG(elem);
				for (let i = 0; i < parts.length; i++) {
					const name = elem.name + "."+(i+1);
					let file = {url: elem.url, origin: elem.origin, name: name, type: "split", refs:{download: elem.url}};
					const id = self.getEntryId();
					const previewId = self.generateUniqueId(id, file);
					let fragment = parts[i];
					fragment.clean_gc();
					fragment.attr({id: previewId})
					snap.select("#userContent").append(fragment);

					file.id = id; // list entry id
					file.previewId = previewId;
					file.misfit = false;
					file.typePath = file.typePath;

					self.placedDesigns.push(file);
					self._makeItTransformable(fragment);

					let mb_meta = self._set_mb_attributes(fragment);
					// remove class which was added by mouseover in the list.
					self.removeHighlight(file);
				}
			} else {
				let failReason = "";
				switch (method) {
					case 'stroke-color':
						failReason = "Didn't find different stroke colors.";
						break;
					case 'non-intersecting':
						failReason = "Didn't find non-intersecting shapes.";
						break;
					case 'divide':
						failReason = "Looks like a single path.";
				}
				new PNotify({
					title: gettext("Element not splittable with this method."),
					text: gettext("Can't split this design. " + failReason),
					type: "info",
					hide: true
				});
			}
		};

		self.duplicateSVG = function(src) {
			self.abortFreeTransforms();
			var srcElem = snap.select('#'+src.previewId);
			var clone_id = srcElem.attr('mb:clone_of') || self._normalize_mb_id(src.previewId);
			var newSvg = srcElem.clone();
			newSvg.clean_gc();
			let prefix = clone_id.substr(0, clone_id.indexOf('_'));
			var id = self.getEntryId(prefix);
			var file = _.cloneDeep(src); // clone from src as quicktext has additional fields here.
			var previewId = self.generateUniqueId(id, file);
			file.id = id; // list entry id
			file.previewId = previewId;
			file.misfit = false;
			file.typePath = src.typePath; 
			newSvg.attr({id: previewId,
				'mb:id': self._normalize_mb_id(previewId),
				'mb:clone_of':clone_id,
				class: srcElem.attr('class')});
			self.removeHighlight(newSvg);

			if (newSvg.attr('class').includes('userIMG')) {
				let url = self._getIMGserveUrl(file);
				self._create_img_filter(previewId);
				newSvg.children()[0].attr({filter: 'url(#'+self._get_img_filter_id(previewId)+')', 'data-serveurl': url});
			}

			snap.select("#userContent").append(newSvg);


			self.placedDesigns.push(file);
			self.placeSmart(newSvg);
			self.removeHighlight(file);
			self._makeItTransformable(newSvg);
			self.check_sizes_and_placements();
		};
		

		self.placeSmart = function(elem){ // TODO: bug - should not place outside working area
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

		self._makeItTransformable = function(fragment){
			fragment.transformable();
			fragment.ftRegisterOnTransformCallback(self.svgTransformUpdate);
			fragment.ftRegisterBeforeTransformCallback(function () {
				fragment.clean_gc();
			});
			fragment.ftRegisterAfterTransformCallback(function () {
				var mb_meta = self._set_mb_attributes(fragment);
			});
			setTimeout(function () {
				fragment.ftReportTransformation();
			}, 200);
		}

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
				const colsRowsStr = event.target.value;
				const result = self._svgMultiplyUpdate(data, colsRowsStr);
				event.target.value = result;
			}
		};
		self._svgMultiplyUpdate = function(data, colsRowsStr){
			self.abortFreeTransforms();
			var svg = snap.select('#'+data.previewId);
			var gridsize = colsRowsStr.split(/\D+/);
			var cols = gridsize[0] || 1;
			var rows = gridsize[1] || 1;
			var dist = 2;
			svg.grid(cols, rows, dist);
			var mb_meta = self._set_mb_attributes(svg);
			svg.ftStoreInitialTransformMatrix();
			svg.ftUpdateTransform();
			self.check_sizes_and_placements();
			return cols+"×"+rows;
		}
		self.imgManualAdjust = function(data, event) {
			if (event.type === 'input' || event.type === 'blur' || event.type === 'keyUp') {
				self.abortFreeTransforms();
				var newContrast = $('#'+data.id+' .contrast').val(); // 0..2, 1 means no adjustment
				var newBrightness = $('#'+data.id+' .brightness').val(); // -1..1, 0 means no adjustment
				var newGamma = $('#'+data.id+' .gamma').val(); // // 0.2..1.8, 1 means no adjustment
				var contrastVal = parseFloat(newContrast);
				var brCorrection = (1 - contrastVal) / 2; // 0.5..-0.5 // TODO investigate if we should take gamma into account as well
				var brightnessVal = parseFloat(newBrightness) + brCorrection;
				var gammaVal = parseFloat(newGamma);
				self.set_img_contrast(data.previewId, contrastVal, brightnessVal, gammaVal);
			}
		};

		self.imgManualSharpen = function(data, event) {
			if (event.type === 'input' || event.type === 'blur' || event.type === 'keyUp') {
				self.abortFreeTransforms();
				var newVal = $('#'+data.id+' .sharpen').val(); // 0..10, 0 means no adjustment
				var sharpenVal = parseFloat(newVal);
				self.set_img_sharpen(data.previewId, sharpenVal);
			}
		};
		
		self.imgManualCrop = function(data, event) {
			if (event.type === 'input' || event.type === 'blur' || event.type === 'keyUp') {
				let t = parseFloat($('#'+data.id+' .crop_top').val());
				let l = parseFloat($('#'+data.id+' .crop_left').val());
				let r = parseFloat($('#'+data.id+' .crop_right').val());
				let b = parseFloat($('#'+data.id+' .crop_bottom').val());
				self.set_img_crop(data.previewId, t, l, r, b);
				if(l + r > 99) $('#'+data.id+' .crop_right').val(100-l-1);
				if(t + b > 99) $('#'+data.id+' .crop_bottom').val(100-t-1);
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
			var error = "<p>" + _.sprintf(gettext("The SVG file contains unsupported elements: '%(elemName)s' These elements got removed."), {elemName: elemName}) + "</p>";
			new PNotify({
				title: _.sprintf(gettext("Unsupported elements in SVG: '%(elemName)s'"), {elemName: elemName}),
				text: error,
				type: "warn",
				hide: false
			});
		};

		self.svg_contains_text_warning = function(svg){
			var error = "<p>" + _.sprintf(gettext("The SVG file contains text elements.%(br)sIf you want to laser just their outlines,%(br)splease convert them to paths.%(br)sOtherwise they will be engraved with infill."), {br: "<br/>"}) + "</p>";
			new PNotify({
				title: gettext("Text elements found"),
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
				title: gettext("Style elements removed"),
				text: error,
				type: "warn",
				hide: false,
				buttons: {
					sticker: false
				}
			});
		};

		self.file_not_readable = function(){
			var error = "<p>" + _.sprintf(gettext("Something went wrong while reading this file.%(topen)sSorry!%(tclose)sPlease check it with another application. If it works there, our support team would be happy to take a look."), {topen: "<br/><h3 style='text-align:center;'>", tclose: "</h3><br/>"}) + "</p>";
			new PNotify({
				// Translators: "in the sense of Ouch!"
				title: gettext("Oops."),
				text: error,
				type: "error",
				hide: false,
				buttons: {
					sticker: false
				}
			});
		};

		self.svg_place_general_error = function(stack){
			var error = "<p>" + _.sprintf(gettext("An unknown error occurred while processing this design file.")) + "</p>";
			error += "<p>" + _.sprintf(gettext("Please try reloading this browser window and try again. If this error remains, contact the Mr Beam Support Team. Make sure you provide the error message below together with the design file you're trying to process.")) + "</p>";
			error += "<p><strong>"+ _.sprintf(gettext("Error"))+ ":</strong><br/><textarea spellcheck=\"false\" style=\"width: 95%; background-color: inherit; font-size: 12px; line-height: normal; height: 70px; color: inherit; background-color: inherit;\">" +stack+ "</textarea></p>";
			new PNotify({
				title: gettext("Error"),
				text: error,
				type: "error",
				hide: false,
				buttons: {
					sticker: false
				}
			});
		};

		self.placeIMG = function (file) {
			var start_ts = Date.now();
			var url = self._getIMGserveUrl(file);
			var img = new Image();
			img.onload = function () {
				var duration_load = Date.now() - start_ts;
				start_ts = Date.now();

				var wpx = this.width;
				var hpx = this.height;

				var dimMM = self.getUsefulDimensions(wpx, hpx);
				var wMM = dimMM[0];
				var hMM = dimMM[1];

				var y = self.workingAreaHeightMM() - hMM;
				var imgWrapper = snap.group();
				var newImg = imgWrapper.image(url, 0, y, wMM, hMM); //.attr({transform: 'matrix(1,0,0,-1,0,'+hMM+')'});
				var id = self.getEntryId();
				var previewId = self.generateUniqueId(id, file); // appends # if multiple times the same design is placed.
				self._create_img_filter(previewId);
				newImg.attr('data-serveurl', url);
                if (!window.mrbeam.browser.is_safari) {
                    // svg filters don't really work in safari: https://github.com/mrbeam/MrBeamPlugin/issues/586
                    newImg.attr('filter', 'url(#' + self._get_img_filter_id(previewId) + ')');
                }
				var imgWrapper = snap.group().attr({
					id: previewId,
					'mb:id':self._normalize_mb_id(previewId),
					class: 'userIMG',
					'mb:origin': origin
				});

				imgWrapper.append(newImg);
				snap.select("#userContent").append(imgWrapper);
//				imgWrapper.transformable();
//				imgWrapper.ftRegisterOnTransformCallback(self.svgTransformUpdate);
//				setTimeout(function(){
//					imgWrapper.ftReportTransformation();
//				}, 200);
				self._makeItTransformable(imgWrapper);
				
				file.id = id;
				file.previewId = previewId;
				file.url = url;
				file.subtype = "bitmap";
				self.placedDesigns.push(file);

				// analytics
				let analyticsData = {
					id: id,
					pixel_width: wpx,
					pixel_height: hpx,
					size: file.size,
					duration_load: duration_load,
					duration_processing: (Date.now() - start_ts),
					file_type: file.display.split('.').slice(-1)[0],
					filename_hash: file.hash,
				};
				self._analyticsPlaceImage(analyticsData)
			};
			img.src = url;
		};

		self.removeIMG = function(file){
			self._remove_img_filter(file.previewId);
			self.removeSVG(file);
		};

		self._create_img_filter = function(previewId){
			var id = self._get_img_filter_id(previewId);
			var str = "<feComponentTransfer class='contrast_filter' in='colormatrix' result='contrast_result'>"
			+ "<feFuncR type='gamma' amplitude='1' offset='0' exponent='1'/>"
			+ "<feFuncG type='gamma' amplitude='1' offset='0' exponent='1'/>"
			+ "<feFuncB type='gamma' amplitude='1' offset='0' exponent='1'/>"
			+ "<feFuncA type='identity' />"
			+ "</feComponentTransfer>"
			+ "<feColorMatrix class='gray_scale_filter' type='saturate' values='0' in='contrast_result' result='gray_scale'/>"
			+ "<feConvolveMatrix class='sharpening_filter' order='3 3' kernelMatrix='0 0 0 0 1 0 0 0 0' divisor='1' bias='0' targetX='1' targetY='1' edgeMode='duplicate' preserveAlpha='true' in='gray_scale' result='sharpened'/>"
			;
			snap.filter(str).attr({id: id, filterUnits:'objectBoundingBox', x:'0%', y:'0%', width:'100%', height:'100%'});
			return id;
		};

		self._remove_img_filter = function(previewId){
			var id =  self._get_img_filter_id(previewId);
			var filter = snap.select('#'+id);
			if(filter !== null) filter.remove();
		};

		self._get_img_filter_id = function(previewId){
			return "filter_" + previewId.replace('-', '__');
		};

		self.set_img_contrast = function(previewId, contrastValue, brightnessValue, gammaValue){
			if(isNaN(contrastValue) || isNaN(brightnessValue) || isNaN(gammaValue)){
				return;
			}
			var filter = snap.select('#'+self._get_img_filter_id(previewId));
			filter.select('feFuncR').attr({amplitude: contrastValue, offset: brightnessValue, exponent: gammaValue});
			filter.select('feFuncG').attr({amplitude: contrastValue, offset: brightnessValue, exponent: gammaValue});
			filter.select('feFuncB').attr({amplitude: contrastValue, offset: brightnessValue, exponent: gammaValue});
		};

		self.set_img_sharpen = function(previewId, value){
			if(isNaN(value)){
				return;
			}
			// 3x3 matrix (1px radius) looks like this:
			// -i/9  -i/9  -i/9
			// -i/9 1+8i/9 -i/9
			// -i/9  -i/9  -i/9
			// i is the intensity factor: 0..40, 0 means identity projection.
			var n = -value / 9.0;
			var c = 1 + 8 * value / 9.0;
			var matrix = [n,n,n,n,c,n,n,n,n].join(' ');
			var filter = snap.select('#'+self._get_img_filter_id(previewId));
			filter.select('feConvolveMatrix').attr({kernelMatrix: matrix});
		};
		
		self.set_img_crop = function(previewId, top, left, right, bottom){
			let filter = snap.select('#'+self._get_img_filter_id(previewId));
			let x = Math.min(left, 100 - right);
			let y = Math.min(top, 100 - bottom);
			let width = Math.max(100 - right - left, 0);
			let height = Math.max(100 - top - bottom, 0);
			filter.attr({x: left+'%', y: top+'%', width: width+'%', height: height+'%' });
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
				svg.ftManualTransform({tx_rel: ntx, ty_rel: nty, diffType:'absolute'})
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
			} else if (data.type === "recentjob" || data.type === "split") {
				return "wa_template_model_svg";
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
			return prefix + "_" + WorkingAreaHelper.getHumanReadableId(length);
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
				if(isNaN(yPatternOffset)){
					yPatternOffset = 0;
				}

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

		self.getCompositionSVG = function(fillAreas, pxPerMM, engraveStroke, callback){
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
			// TODO only if Quick Text is present
			$('#compSvg defs').append('<style id="quickTextFontPlaceholder" class="quickTextFontPlaceholder deleteAfterRendering"></style>');
			self._qt_copyFontsToSvg(compSvg.select(".quickTextFontPlaceholder").node);

			self.renderInfill(compSvg, wPT, hPT, fillAreas, engraveStroke, wMM, hMM, pxPerMM, function(svgWithRenderedInfill){
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

				svgStr = WorkingAreaHelper.fix_svg_string(svgStr); // Firefox bug workaround.
				var gc_otions_str = self.gc_options_as_string().replace('"', "'");

				var svg = '<svg version="1.1" xmlns="http://www.w3.org/2000/svg" xmlns:mb="http://www.mr-beam.org/mbns" mb:beamOS_version="'+BEAMOS_VERSION+'"'
						+ ' width="'+ w +'" height="'+ h +'"  viewBox="'+ viewBox +'" mb:gc_options="'+gc_otions_str+'"><defs/>'+svgStr+'</svg>';
				return svg;
			} else {
				return;
			}
		};

		self._normalize_mb_id = function(id) {
			return id ? id.replace(/\s/g, '_') : '';
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
				var normalized_id = self._normalize_mb_id(id);
				if (my_meta['mb:id'] && normalized_id != my_meta['mb:id'] && !my_meta['mb:clone_of']) {
					element.attr('mb:clone_of', my_meta['mb:id']);
					my_meta['mb:clone_of'] = my_meta['mb:id'];
				}

				element.attr("mb:id", normalized_id);

				my_meta['mb:id'] = normalized_id;
				mb_meta[id] = my_meta;
				self.gc_meta[id] = my_meta;
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
					transform: 'matrix(1,0,0,-1,0,'+ String(h+y*2) +')',
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
			// init tinyColorPicker if not done yet
			$("#qs_colorPicker_stroke").tinycolorpicker();
			$("#qs_colorPicker_stroke").bind("change", self._qs_currentQuickShapeUpdate);
			$("#qs_colorPicker_fill").tinycolorpicker();
			$("#qs_colorPicker_fill").bind("change", self._qs_currentQuickShapeUpdate);
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
				self._qs_dialogClose();
			});
			$('#quick_text_dialog').on('hidden', function(){
				self._qt_dialogClose();
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
				svg.selectAll('*').forEach(function(e){e.addClass('misfit');});
				svg.data('fitMatrix', fitMatrix);
			} else {
				design.misfit = false;
				$('#'+design.id).removeClass('misfit');
				svg.removeClass('misfit');
				svg.selectAll('*').forEach(function(e){e.removeClass('misfit');});
				svg.data('fitMatrix', null);
			}
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
		self.renderInfill = function (svg, svgWidthPT, svgHeightPT, fillAreas, engraveStroke, wMM, hMM, pxPerMM, callback) {
			//TODO engraveStroke use it and make it work
			var tmpSvg = self.getNewSvg('tmpSvg', svgWidthPT, svgHeightPT);
			var attrs = {viewBox: "0 0 " + wMM + " " + hMM};
			tmpSvg.attr(attrs);
			// get only filled items and embed the images
			var userContent = svg.clone();
			tmpSvg.append(userContent);

			// copy defs for filters
			var originalFilters = snap.selectAll('defs>filter');
			var target = userContent.select('defs');
			for (var i = 0; i < originalFilters.length; i++) {
				var original_id = originalFilters[i].attr('id');
				var clone = originalFilters[i].clone();
				var destFilter = clone.appendTo(target);
				// restore id to keep references working
				destFilter.attr({id: original_id});
			}

			self._embedAllImages(tmpSvg, function(){
				var fillings = userContent.removeUnfilled(fillAreas);
				for (var i = 0; i < fillings.length; i++) {
					var item = fillings[i];

					if (item.type !== 'image' && item.type !== "text" && item.type !== "#text") {
						var style = item.attr('style');
						// remove stroke from other elements
						var styleNoStroke = 'stroke: none;';
						if (style !== null) {
							styleNoStroke += style.replace(/stroke.+?;/g, '');
						}
						item.attr('stroke', 'none');
						item.attr('style', styleNoStroke);
					}
				}

				var cb = function(result, x, y, w, h) {
					if (MRBEAM_DEBUG_RENDERING) {
						debugBase64(result, 'png_debug');
					}

					if(fillings.length > 0){

						// fill rendering replaces all
						svg.selectAll('image').remove();
						svg.selectAll('.deleteAfterRendering').remove();
						svg.selectAll('text,tspan').remove();

						if(result !== null){
							var fillImage = snap.image(result, x, y, w, h);
							fillImage.attr('id', 'fillRendering');
							svg.append(fillImage);
						}
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
				if(fillAreas){
					tmpSvg.renderPNG(svgWidthPT, svgHeightPT, wMM, hMM, pxPerMM, cb);
				} else {
					cb(null)
				}
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
			self.abortFreeTransforms();
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
					stroke: true,
					color: '#e25303',
					fill: false,
					fill_color: '#000000',
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

			var d = QuickShapeHelper.getRect(w,h,r);
			var shapeSvg = '<svg><g><path d="'+d+'" stroke-width="1" stroke="'+file.qs_params.color+'" fill="#ffffff" fill-opacity="0" /></g></svg>';
			var fragment = Snap.parse(shapeSvg);

			var scaleMatrixStr = new Snap.Matrix(1,0,0,1,x,y).toString();
			self._prepareAndInsertSVG(fragment, previewId, origin, '', {showTransformHandles: false, embedGCode: false}, {_skip: true});
			$('#'+previewId).attr('transform', scaleMatrixStr);

			return file;
		};

		/**
		 * Opens QuickShape window to edit an existing QuickShape object
		 * @param file Object representing the QuickShape to edit
		 */
		self.editQuickShape = function (file) {
			var params = file.qs_params;
			self.showTransformHandles(file.previewId, false);
			self.currentQuickShapeFile = null;
			$('#quick_shape_dialog').modal({keyboard: true});
			$('#quick_shape_dialog').one('hide', self._qs_currentQuickShapeShowTransformHandlesIfNotEmpty);
			// firing those change events is necessary to work around a bug in chrome|knockout|js. 
			// Otherwise entering numbers directly does not fire the change event if the number 
			// is accidentially equal to the field content it had before .val(..).
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
			$('#quick_shape_stroke').prop("checked", params.stroke);
			$("#qs_colorPicker_stroke").data('plugin_tinycolorpicker').setColor(params.color);
//			$('#quick_shape_color').val(params.color).change();
			$('#quick_shape_fill').prop("checked", params.fill);
			$("#qs_colorPicker_fill").data('plugin_tinycolorpicker').setColor(params.fill_color);
//			$('#quick_shape_fill_brightness').val(params.fill_brightness).change();
			self.currentQuickShapeFile = file;

			$('#shape_tab_link_'+params.type.substr(1)).tab('show');
			$('#quick_shape_dialog div.tab-pane.active input:first').focus();
			self._qs_currentQuickShapeUpdate();
		};

		/**
		 * shows transformation handles on QS if it exists.
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
//				var type = $('#shape_tabs li.active a').attr('href');
				var type = self.currentQuickShapeFile.qs_params.type;
				let name = self.quickShapeNames.get(type.substr(1));
				self.currentQuickShapeFile.name = name;
				self.currentQuickShape(self.currentQuickShapeFile.name);
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
					heart_lr: parseFloat($('#quick_shape_heart_lr').val()),
					stroke: $('#quick_shape_stroke').prop('checked'),
					fill_color: $('#quick_shape_fill_brightness').val(),
					fill: $('#quick_shape_fill').prop('checked')
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
						d = QuickShapeHelper.getCircle(qs_params.circle_radius);
						break;
					case '#star':
						d = QuickShapeHelper.getStar(qs_params.star_radius,qs_params.star_corners,qs_params.star_sharpness);
						break;
					case '#heart':
						d = QuickShapeHelper.getHeart(qs_params.heart_w,qs_params.heart_h,qs_params.heart_lr);
						break;
					default: // #rect
						d = QuickShapeHelper.getRect(qs_params.rect_w,qs_params.rect_h,qs_params.rect_radius);
						break;
				}
				let stroke = qs_params.stroke ? qs_params.color : 'none';
				let fill = '#ffffff'; 
				let fill_op = 0;
				if(qs_params.fill){
					fill = qs_params.fill_color;
					fill_op = 1;
				}
				shape.attr({d: d, stroke: stroke, fill: fill, 'fill-opacity': fill_op});
				self.currentQuickShapeFile.qs_params = qs_params;
				if(d === "" || (qs_params.stroke === false && qs_params.fill === false)){
					self.currentQuickShapeFile.invalid = true;
				} else {
					self.currentQuickShapeFile.invalid = false;
				}

				// update fileslist
				$('#'+self.currentQuickShapeFile.id+' .title').text(name);

				// analytics
				var analyticsData = {
					id: self.currentQuickShapeFile.id,
					file_type: 'quickShape',
					type: type.substr(1),
					color: qs_params.color,
					name: name,
				}
				for (let myKey in qs_params) {
					if (myKey.startsWith(analyticsData.type)) {
						analyticsData[myKey] = qs_params[myKey];
					}
				}

				// actual analytics are written when the dialog is closed
				self.currentQuickShapeAnalyticsData = analyticsData;
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
			self._analyticsQuickShapeUpdate(self.currentQuickShapeAnalyticsData);
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
				// update clones
				let multiply_str = $('#'+self.currentQuickTextFile.id+' input.multiply').val();
				self._svgMultiplyUpdate(self.currentQuickTextFile, multiply_str);

				self.currentQuickTextAnalyticsData = {
					id: self.currentQuickTextFile.id,
					file_type: 'quickText',
					text_length: self.currentQuickTextFile.name.length,
					brightness: self.currentQuickTextFile.intensity,
					font: self.fontMap[self.currentQuickTextFile.fontIndex],
					font_index: self.currentQuickTextFile.fontIndex,
				}
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
			var start_ts = Date.now();
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
			text.attr('style', 'white-space: pre; font-size: '+size+'px; font-family: Ubuntu; text-anchor: middle');

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
				class: 'userText',
				'mb:origin': origin
			});

			self._makeItTransformable(group);
//			group.transformable();
//			group.ftRegisterOnTransformCallback(self.svgTransformUpdate);

			self.placedDesigns.push(file);

			// var dur = ((Date.now() - start_ts) /1000);
			// console.log("_qt_placeQuicktext() DONE "+ dur + "s");
			// // self._analyticsPlaceDesign('quickText', dur, file.previewId);
			// self._analyticsQuickTextUpdate()

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
							 if (rules[r].style) {
								 var fontName = rules[r].style.getPropertyValue('font-family');
								 fontName = fontName.replace(/["']/g, '').trim();
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

		self._qt_dialogClose = function() {
            if(self.currentQuickTextAnalyticsData.text_length !== 0) {
                self._analyticsQuickTextUpdate(self.currentQuickTextAnalyticsData);
            }
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

		/**
		 * Analytics Stuff
		 */

		self._analyticsPrepareAndInsertSVG = function(analyticsData){
			if (analyticsData._skip) {return}
			analyticsData.file_type = analyticsData.file_type || null;
			self._sendAnalytics('workingarea_place_svg_generic', analyticsData);
			console.log("workingarea_place_svg_generic: ", analyticsData);
		};

		self._analyticsPlaceImage = function(analyticsData){
			if (analyticsData._skip) {return}
			analyticsData.file_type = analyticsData.file_type || null;
			self._sendAnalytics('workingarea_place_image', analyticsData);
			console.log("workingarea_place_image: ", analyticsData);
		};

		self._analyticsQuickShapeUpdate = function(analyticsData){
			if (analyticsData) {
				self._sendAnalytics('workingarea_place_quickshape_update', analyticsData);
				console.log("workingarea_place_quickshape_update: ", analyticsData);
			}
		};

		self._analyticsQuickTextUpdate = function(analyticsData){
			if (analyticsData) {
				self._sendAnalytics('workingarea_place_quicktext_update', analyticsData);
				console.log("workingarea_place_quicktext_update: ", analyticsData);
			}
		};

		self._analyticsPlaceGco = function(analyticsData){
			if (analyticsData) {
				self._sendAnalytics('workingarea_place_gcode', analyticsData);
				console.log("workingarea_place_gcode: ", analyticsData);
			}
		};

		self._sendAnalytics = function(event, payload){
			self.analytics.send_fontend_event(event, payload);
		};


	}


	// view model class, parameters for constructor, container to bind to
	ADDITIONAL_VIEWMODELS.push([WorkingAreaViewModel,
		["loginStateViewModel", "settingsViewModel", "printerStateViewModel",
			"gcodeFilesViewModel", "laserCutterProfilesViewModel", "cameraViewModel",
			"readyToLaserViewModel", "tourViewModel", "analyticsViewModel"],
		[document.getElementById("area_preview"),
			document.getElementById("homing_overlay"),
			document.getElementById("working_area_files"),
			document.getElementById("quick_text_dialog"),
			document.getElementById("quick_shape_dialog"),
			document.getElementById("camera_brightness"),
			document.getElementById("zoomFactor")
		]]);

});
