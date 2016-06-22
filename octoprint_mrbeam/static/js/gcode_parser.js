$(function() {
	gcParser = function() {
		self = this;

		self.toolOffsets = [{x: 0, y: 0}];

		self.parse = function(gcode, pathDelimiter, pathCallback, imgCallback ) {
			var argChar, numSlice;

			var x, y, z, pi, pj, pp = 0;
			var clockwise = false;
			var laser = 0;
			var prevX = 0, prevY = 0, prevZ = -1;
			var f, lastF = 4000;
			var extrude = false, extrudeRelative = false, retract = 0;
			var positionRelative = false;
			var withinPixelCode = false;

			var dcExtrude = false;
			var assumeNonDC = false;

			var tool = 0;
			var prev_extrude = [{a: 0, b: 0, c: 0, e: 0, abs: 0}];
			var prev_retract = [0];
			var offset = self.toolOffsets[0];

			var gcode_lines = gcode.split(/\n/);

			var model = [];
			for (var i = 0; i < gcode_lines.length; i++) {
				var l = gcode_lines[i];
				if(l.startsWith(';Image')) {
					withinPixelCode = true;
					// ;Image: 24.71x18.58 @ 2.59,1.70|http://localhost:5000/serve/files/local/filename.png
					var re = /;Image: ([-+]?[0-9]*\.?[0-9]+)x([-+]?[0-9]*\.?[0-9]+) @ ([-+]?[0-9]*\.?[0-9]+),([-+]?[0-9]*\.?[0-9]+)\|(.*)$/;
					var match = l.match(re);
					if(match){
						var w = parseFloat(match[1]);
						var h = parseFloat(match[2]);
						var x = parseFloat(match[3]);
						var y = parseFloat(match[4]);
						var file_id = match[5];
						if(typeof imgCallback === 'function'){
							imgCallback(x,y,w,h, file_id);
						}
					}
				}
				if(l.startsWith(';EndImage')) withinPixelCode = false;

				if(withinPixelCode){
					continue;
				}
				var line = l.split(/[\(;]/)[0];
				
				x = undefined;
				y = undefined;
				z = undefined;
				pi = undefined;
				pj = undefined;
				pp = undefined;
				clockwise = false;
				retract = 0;

				extrude = false;

				var addToModel = false;
				var convertAndAddToModel = false;
				var move = false;


				if (/^(?:G0|G00|G1|G01)\s+/i.test(line)) {
					var args = line.split(/\s+/);

					for (var j = 0; j < args.length; j++) {
						switch (argChar = args[j].charAt(0).toLowerCase()) {
							case 'x':
								if (positionRelative) {
									x = prevX + Number(args[j].slice(1)) + offset.x;
								} else {
									x = Number(args[j].slice(1)) + offset.x;
								}

								break;

							case 'y':
								if (positionRelative) {
									y = prevY + Number(args[j].slice(1)) + offset.y;
								} else {
									y = Number(args[j].slice(1)) + offset.y;
//									console.log('#', gcode_lines[i-2], gcode_lines[i-1], line, y);
								}

								break;

							case 'z':
								if (positionRelative) {
									z = prevZ + Number(args[j].slice(1));
								} else {
									z = Number(args[j].slice(1));
								}

								break;

							case 'e':
							case 'a':
							case 'b':
							case 'c':
								assumeNonDC = true;
								numSlice = Number(args[j].slice(1));

								if (!extrudeRelative) {
									// absolute extrusion positioning
									prev_extrude[tool]["abs"] = numSlice - prev_extrude[tool][argChar];
									prev_extrude[tool][argChar] = numSlice;
								} else {
									prev_extrude[tool]["abs"] = numSlice;
									prev_extrude[tool][argChar] += numSlice;
								}

								extrude = prev_extrude[tool]["abs"] > 0;
								if (prev_extrude[tool]["abs"] < 0) {
									prev_retract[tool] = -1;
									retract = -1;
								} else if (prev_extrude[tool]["abs"] === 0) {
									retract = 0;
								} else if (prev_extrude[tool]["abs"] > 0 && prev_retract[tool] < 0) {
									prev_retract[tool] = 0;
									retract = 1;
								} else {
									retract = 0;
								}

								break;

							case 'f':
								numSlice = parseFloat(args[j].slice(1));
								lastF = numSlice;
								break;
						}
					}

					if (dcExtrude && !assumeNonDC) {
						extrude = true;
						prev_extrude[tool]["abs"] = Math.sqrt((prevX - x) * (prevX - x) + (prevY - y) * (prevY - y));
					}

					if (typeof (x) !== 'undefined' || typeof (y) !== 'undefined' || typeof (z) !== 'undefined' || retract !== 0) {
						addToModel = true;
						move = true;
					}
				} else if (/^(?:G2|G02|G3|G03)\s+/i.test(line)) {
					var units = "G21"; // mm
					var args = line.split(/\s+/);
					var lastPos = {x: prevX, y: prevY, z: prevZ};

					clockwise = /^(?:G2|G02)/i.test(args[0]);
					for (var j = 0; j < args.length; j++) {
						switch (argChar = args[j].charAt(0).toLowerCase()) {
							case 'x':
								if (positionRelative) {
									x = prevX + Number(args[j].slice(1)) + offset.x;
								} else {
									x = Number(args[j].slice(1)) + offset.x;
								}

								break;

							case 'y':
								if (positionRelative) {
									y = prevY + Number(args[j].slice(1)) + offset.y;
								} else {
									y = Number(args[j].slice(1)) + offset.y;
								}

								break;

							case 'z':
								if (positionRelative) {
									z = prevZ + Number(args[j].slice(1));
								} else {
									z = Number(args[j].slice(1));
								}

								break;

							case 'i':
								pi = Number(args[j].slice(1)) + offset.x;

								break;

							case 'j':
								pj = Number(args[j].slice(1)) + offset.y;

								break;

							case 'p':
								pp = Number(args[j].slice(1));

								break;

							case 'e':
							case 'a':
							case 'b':
							case 'c':
								assumeNonDC = true;
								numSlice = Number(args[j].slice(1));

								if (!extrudeRelative) {
									// absolute extrusion positioning
									prev_extrude[tool]["abs"] = numSlice - prev_extrude[tool][argChar];
									prev_extrude[tool][argChar] = numSlice;
								} else {
									prev_extrude[tool]["abs"] = numSlice;
									prev_extrude[tool][argChar] += numSlice;
								}

								extrude = prev_extrude[tool]["abs"] > 0;
								if (prev_extrude[tool]["abs"] < 0) {
									prev_retract[tool] = -1;
									retract = -1;
								} else if (prev_extrude[tool]["abs"] === 0) {
									retract = 0;
								} else if (prev_extrude[tool]["abs"] > 0 && prev_retract[tool] < 0) {
									prev_retract[tool] = 0;
									retract = 1;
								} else {
									retract = 0;
								}

								break;

							case 'f':
								numSlice = parseFloat(args[j].slice(1));
								lastF = numSlice;
								break;
						}
					}

					if (dcExtrude && !assumeNonDC) {
						extrude = true;
						prev_extrude[tool]["abs"] = Math.sqrt((prevX - x) * (prevX - x) + (prevY - y) * (prevY - y));
					}

					if (typeof (x) !== 'undefined' || typeof (y) !== 'undefined' || typeof (z) !== 'undefined'
							|| typeof (pi) !== 'undefined' || typeof (pj) !== 'undefined' || typeof (pp) !== 'undefined' || retract !== 0) {

						convertAndAddToModel = true;
						move = true;
					}
//				} else if (/^(?:M82)/i.test(line)) {
//					extrudeRelative = false;
				} else if (/^(?:M3|M03)/i.test(line)) {
					var args = line.split(/\s+/);
					for (var j = 0; j < args.length; j++) {
						switch (argChar = args[j].charAt(0).toLowerCase()) {
							case 's':
								laser = Number(args[j].slice(1));
								break;
						}
					}
				} else if (/^(?:M5|M05)/i.test(line)) {
					laser = 0;
				} else if (/^(?:G91)/i.test(line)) {
					positionRelative = true;
					extrudeRelative = true;
				} else if (/^(?:G90)/i.test(line)) {
					positionRelative = false;
					extrudeRelative = false;
//				} else if (/^(?:M83)/i.test(line)) {
//					extrudeRelative = true;
//				} else if (/^(?:M101)/i.test(line)) {
//					dcExtrude = true;
//				} else if (/^(?:M103)/i.test(line)) {
//					dcExtrude = false;
				} else if (/^(?:G92)/i.test(line)) {
					var args = line.split(/\s/);

					for (var j = 0; j < args.length; j++) {
						if (!args[j])
							continue;

						if (args.length === 1) {
							// G92 without coordinates => reset all axes to 0
							x = 0;
							y = 0;
							z = 0;
							prev_extrude[tool]["e"] = 0;
							prev_extrude[tool]["a"] = 0;
							prev_extrude[tool]["b"] = 0;
							prev_extrude[tool]["c"] = 0;
						} else {
							switch (argChar = args[j].charAt(0).toLowerCase()) {
								case 'x':
									x = Number(args[j].slice(1)) + offset.x;
									break;

								case 'y':
									y = Number(args[j].slice(1)) + offset.y;
									break;

								case 'z':
									z = Number(args[j].slice(1));
									prevZ = z;
									break;

								case 'e':
								case 'a':
								case 'b':
								case 'c':
									numSlice = Number(args[j].slice(1));
									if (!extrudeRelative)
										prev_extrude[tool][argChar] = 0;
									else {
										prev_extrude[tool][argChar] = numSlice;
									}
									break;
							}
						}
					}

					if (typeof (x) !== 'undefined' || typeof (y) !== 'undefined' || typeof (z) !== 'undefined') {
						addToModel = true;
						move = false;
					}

				} else if (/^(?:G28|$H)/i.test(line)) {
					var args = line.split(/\s/);

					if (args.length === 1) {
						// G28 with no arguments => home all axis
						x = 0;
						y = 0;
						z = 0;
					} else {
						for (j = 0; j < args.length; j++) {
							switch (argChar = args[j].charAt(0).toLowerCase()) {
								case 'x':
									x = 0;
									break;
								case 'y':
									y = 0;
									break;
								case 'z':
									z = 0;
									break;
								default:
									break;
							}
						}
					}

					if (typeof (x) !== 'undefined' || typeof (y) !== 'undefined' || typeof (z) !== 'undefined' || retract !== 0) {
						addToModel = true;
						move = true;
					}
				} else if (/^(?:T\d+)/i.test(line)) {
					tool = Number(line.split(/\s/)[0].slice(1));
					if (!prev_extrude[tool])
						prev_extrude[tool] = {a: 0, b: 0, c: 0, e: 0, abs: 0};
					if (!prev_retract[tool])
						prev_retract[tool] = 0;

					offset = self.toolOffsets[tool] || {x: 0, y: 0};
				}

				// ensure z is set.
				if (typeof (z) === 'undefined') {
					if (typeof (prevZ) !== 'undefined') {
						z = prevZ;
					} else {
						z = 0;
					}
				}
				
				if (addToModel && !isNaN(x) && !isNaN(y)) { // TODO: hack. unclear why y sometimes is undefined.
					model.push({
						x: x,
						y: y,
						z: z,
						extrude: extrude,
						laser: laser,
						retract: retract,
						noMove: !move,
						extrusion: (extrude || retract) && prev_extrude[tool]["abs"] ? prev_extrude[tool]["abs"] : 0,
						prevX: prevX,
						prevY: prevY,
						prevZ: prevZ,
						speed: lastF,
						gcodeLine: i,
						percentage: i / gcode_lines.length,
						tool: tool
					});
				}
				if (convertAndAddToModel) {
					var parts = self._convertG2G3(clockwise, x, y, z, pi, pj, pp, lastPos, units);
					var lastPart = parts[0];
					for (var l = 1; l < parts.length; l++) {
						var part = parts[l];

						model.push({
							x: part[0],
							y: part[1],
							z: part[2],
							extrude: extrude,
							laser: laser,
							retract: retract,
							noMove: !move,
							extrusion: (extrude || retract) && prev_extrude[tool]["abs"] ? prev_extrude[tool]["abs"] : 0,
							prevX: lastPart[0],
							prevY: lastPart[1],
							prevZ: lastPart[2],
							speed: lastF,
							gcodeLine: i,
							percentage: i / gcode_lines.length,
							tool: tool
						});

						lastPart = part;
					}
				}

				if (move) {
					if (typeof (x) !== 'undefined')
						prevX = x;
					if (typeof (y) !== 'undefined')
						prevY = y;
				}

				if (typeof (pathCallback) === 'function' && typeof (pathDelimiter) !== 'undefined' && pathDelimiter.test(line)) {
					pathCallback(model);
					model = model.slice(-1); // keep the last element as start of the next block
				}
			}

			prevZ = z;
			if (typeof (pathCallback) === 'function' && model.length > 0) {
				pathCallback(model);
			}
		};

		self._convertG2G3 = function(clockwise, x, y, z, i, j, p, lastPos, units) {
			if (typeof (x) === 'undefined')
				x = lastPos.x;
			if (typeof (y) === 'undefined')
				y = lastPos.y;
			if (typeof (z) === 'undefined')
				z = lastPos.z;
			if (typeof (i) === 'undefined')
				i = 0.0;
			if (typeof (j) === 'undefined')
				j = 0.0;
			if (typeof (p) === 'undefined')
				p = 1.0;

			var curveSection = 1.0; // mm
			if (units === "G20") { // inches
				curveSection = 1.0 / 25.4;
			}

			// angle variables.
			var angleA;
			var angleB;
			var angle;

			// delta variables.
			var aX;
			var aY;
			var bX;
			var bY;


			// center of rotation
			var cX = lastPos.x + i;
			var cY = lastPos.y + j;

			aX = lastPos.x - cX;
			aY = lastPos.y - cY;
			bX = x - cX;
			bY = y - cY;

			// Clockwise
			if (clockwise) {
				angleA = Math.atan2(bY, bX);
				angleB = Math.atan2(aY, aX);
			} else {
				angleA = Math.atan2(aY, aX);
				angleB = Math.atan2(bY, bX);
			}

			// Make sure angleB is always greater than angleA
			// and if not add 2PI so that it is (this also takes
			// care of the special case of angleA == angleB,
			// ie we want a complete circle)
			if (angleB <= angleA) {
				angleB += 2 * Math.PI * p;
			}
			angle = angleB - angleA;

			// calculate a couple useful things.
			var radius = Math.sqrt(aX * aX + aY * aY);
			var length = radius * angle;

			// for doing the actual move.
			var steps;  // TODO accuracy setting
			var s;

			// Maximum of either 2.4 times the angle in radians
			// or the length of the curve divided by the curve section constant
			steps = Math.ceil(Math.max(angle * 2.4, length / curveSection));


			var fta;
			if (!clockwise) {
				fta = angleA + angle;
			} else {
				fta = angleA;
			}

			// THis if arc is correct
			// TODO move this into the validator
			var r2 = Math.sqrt(bX * bX + bY * bY);
			var percentage;
			if (r2 > radius) {
				percentage = Math.abs(radius / r2) * 100.0;
			} else {
				percentage = Math.abs(r2 / radius) * 100.0;
			}

			if (percentage < 99.7) {
				var sb = "";
				sb += "Radius to end of arc differs from radius to start:\n";
				sb += "r1=" + radius + "\n";
				sb += "r2=" + r2 + "\n";
				console.warn("gcode_parser.js convertG2G3", sb);
			}

			// this is the real line calculation.
			var parts = [];
			var arcStartZ = lastPos.z;
			for (s = 1; s <= steps; s++) {
				var step;
				if (!clockwise)
					step = s;
				else
					step = steps - s;

				var ta = (angleA + angle * (step / steps));

				parts.push([cX + radius * Math.cos(ta), cY + radius * Math.sin(ta), lastPos.z + (z - arcStartZ) * s / steps]);

			}

			return parts;
		};

	};
});