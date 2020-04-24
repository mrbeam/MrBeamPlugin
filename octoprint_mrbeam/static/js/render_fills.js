//    render_fills.js - a snapsvg.io plugin to render the infill of svg files into a bitmap.
//    Copyright (C) 2015  Teja Philipp <osd@tejaphilipp.de>
//
//    based on work by http://davidwalsh.name/convert-canvas-image
//    and http://getcontext.net/read/svg-images-on-a-html5-canvas
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
	 * @param {elem} elem start point
	 *
	 * @returns {path}
	 */

	Element.prototype.removeUnfilled = function(fillPaths){
		//todo check if remove of all elements with mb:color is also working
		var elem = this;
		var selection = [];
		var children = elem.children();

		if (children.length > 0) {
			var goRecursive = (elem.type !== "defs" && // ignore these tags
				elem.type !== "clipPath" &&
				elem.type !== "metadata" &&
				elem.type !== "rdf:rdf" &&
				elem.type !== "cc:work" &&
				elem.type !== "sodipodi:namedview");

			if(goRecursive) {
				for (var i = 0; i < children.length; i++) {
					var child = children[i];
					selection = selection.concat(child.removeUnfilled(fillPaths));
				}
			}
		} else {
			if(elem.type === 'image' || elem.type === "text" || elem.type === "#text"){
				selection.push(elem);
			} else {
				if(fillPaths && elem.is_filled()){
					selection.push(elem);
				} else {
					elem.remove();
				}
			}
		}
		return selection;
	};

	Element.prototype.is_filled = function(){
		var elem = this;

		// TODO text support
		// TODO opacity support
		if (elem.type !== "circle" &&
			elem.type !== "rect" &&
			elem.type !== "ellipse" &&
			elem.type !== "line" &&
			elem.type !== "polygon" &&
			elem.type !== "polyline" &&
			elem.type !== "path" ){

			return false;
		}

		var fill = elem.attr('fill');
		var opacity = elem.attr('fill-opacity');

		if(fill !== 'none'){
			if(opacity === null || opacity > 0){
				return true;
			}
		}
		return false;
	};

	Element.prototype.embedImage = function(callback){
		var elem = this;
		if(elem.type !== 'image') return;

		var url = elem.attr('href');
		var image = new Image();

		image.onload = function () {
			var canvas = document.createElement('canvas');
			canvas.width = this.naturalWidth; // or 'width' if you want a special/scaled size
			canvas.height = this.naturalHeight; // or 'height' if you want a special/scaled size

			canvas.getContext('2d').drawImage(this, 0, 0);
			var dataUrl = canvas.toDataURL('image/png');
			elem.attr('href', dataUrl);
			canvas.remove();
			if(typeof callback === 'function'){
				callback(elem.attr('id'));
				console.log('embedded img ('+ canvas.width +'*' + canvas.height+' px, dataurl: '+getDataUriSize(dataUrl)+' )');
			}
		};

		image.src = url;

	};

	Element.prototype.renderPNG = function (wPT, hPT, wMM, hMM, pxPerMM, renderBBoxMM=null, callback=null) {
		var elem = this;
		//console.info("renderPNG paper width", elem.paper.attr('width'), wPT);
		console.info("renderPNG: SVG " + wPT + '*' + hPT +" (pt) with viewBox " + wMM + '*' + hMM + ' (mm), rendering @ ' + pxPerMM + ' px/mm, cropping to bbox (mm): '+renderBBoxMM);

		let bbox; // attention, this bbox uses viewBox coordinates (mm)
		if(renderBBoxMM === null){
			// warning: correct result depends upon all resources (img, fonts, ...) have to be fully loaded already.
			bbox = elem.getBBox();
		} else {
			bbox = renderBBoxMM;
		}

        // Quick fix: in some browsers the bbox is too tight, so we just add an extra 10% to all the sides, making the height and width 20% larger in total
        bbox.x = bbox.x - bbox.width * 0.4;
        bbox.y = bbox.y - bbox.height * 0.4;
        bbox.w = bbox.w * 1.8;
        bbox.h = bbox.h * 1.8;

		console.info("enlarged renderBBox (in mm): " + bbox.w +'*'+bbox.h + " @ " + bbox.x + ',' + bbox.y);

		// get svg as dataUrl
		var svgStr = elem.outerSVG();
        // on iOS (Safari and Chrome) embedded images are linked with NS1:href which doesn't work later on...
        svgStr = svgStr.replace(/NS1:href=/gi, 'xmlns:xlink="http://www.w3.org/1999/xlink" xlink:href=');
		var svgDataUri = 'data:image/svg+xml;base64,' + window.btoa(unescape(encodeURIComponent(svgStr))); //deprecated unescape needed!

		// init render canvas and attach to page
		var renderCanvas = document.createElement('canvas');
		renderCanvas.id = "renderCanvas";
		renderCanvas.width = bbox.w * pxPerMM;
		renderCanvas.height = bbox.h * pxPerMM;
		document.getElementsByTagName('body')[0].appendChild(renderCanvas);
		var renderCanvasContext = renderCanvas.getContext('2d');
		renderCanvasContext.fillStyle = 'white'; // avoids one backend rendering step (has to be disabled in the backend)
		renderCanvasContext.fillRect(0, 0, renderCanvas.width, renderCanvas.height);

        var source = new Image();

		// render SVG image to the canvas once it loads.
		source.onload = function () {

			var srcScale = wPT / wMM; // canvas.drawImage refers to <svg> coordinates - not viewBox coordinates.

			// drawImage(source, src.x, src.y, src.width, src.height, dest.x, dest.y, dest.width, dest.height);
			renderCanvasContext.drawImage(source, bbox.x * srcScale, bbox.y * srcScale, bbox.w * srcScale, bbox.h * srcScale, 0, 0, renderCanvas.width, renderCanvas.height);

			// place fill bitmap into svg
			var fillBitmap = renderCanvas.toDataURL("image/png");
			console.info("renderPNG rendered dataurl has " + getDataUriSize(fillBitmap));
			if(typeof callback === 'function'){
				callback(fillBitmap, bbox.x, bbox.y, bbox.w, bbox.h);
			}
			renderCanvas.remove();
		};

		// catch browsers without native svg support
		source.onerror = function(e) {
//            var len = svgDataUri ? svgDataUri.length : -1;
            var len = getDataUriSize(svgDataUri, 'B');
            var msg = "Error during conversion: Loading SVG dataUri into image element failed. (dataUri.length: "+len+")";
            console.error(msg, e);
            var error = "<p>" + gettext("The SVG file contains clipPath elements.<br/>clipPath is not supported yet and has been removed from file.") + "</p>";
			new PNotify({
				title: gettext("Conversion failed"),
				text: msg,
				type: "error",
				hide: false
			});
        };

		source.src = svgDataUri;
	};

	function getDataUriSize(datauri, unit){
		if(! datauri) return -1;
		var bytes = datauri.length;
		switch(unit) {
			case 'B':
				return bytes;
			case 'kB':
				return Math.floor(bytes / 1024);
			case 'MB':
				return Math.floor(bytes / (1024*1024));
			default:
				if(bytes < 1024) return bytes + " Byte";
				else if(bytes < 1024*1024) return Math.floor(bytes / 1024) + " kByte";
				else return Math.floor(bytes / (1024*1024)) + " MByte";
		}
	}


});









