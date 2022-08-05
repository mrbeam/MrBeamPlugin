$(function () {
    gcParser = function () {
        var self = this;

        self.parse = function (
            gcode,
            pathDelimiter,
            pathCallback,
            imgCallback
        ) {
            var argChar, numSlice;

            var x,
                y,
                z,
                pi,
                pj,
                pp = 0;
            var clockwise = false;
            var laser = 0;
            var prevX = 0,
                prevY = 0,
                prevZ = -1;
            var f,
                lastF = 10000;
            var positionRelative = false;
            var withinPixelCode = false;

            var gcode_lines = gcode.split(/\n/);
            var gcode_regex =
                /^(G0|G00|G1|G01|G2|G02|G3|G03|G90|G91|G92|G28|\$H|M3|M03|M5|M05)\s*(.*)/;

            var model = [];
            for (var i = 0; i < gcode_lines.length; i++) {
                var l = gcode_lines[i];
                if (l.match(/; ?Image/) && !window.MRBEAM_DEBUG_RENDERING) {
                    withinPixelCode = true;
                    // ;Image: 24.71x18.58 @ 2.59,1.70|http://localhost:5000/serve/files/local/filename.png
                    var re =
                        /; ?Image: ([-+]?[0-9]*\.?[0-9]+)x([-+]?[0-9]*\.?[0-9]+) @ ([-+]?[0-9]*\.?[0-9]+),([-+]?[0-9]*\.?[0-9]+)\|(.*)$/;
                    var match = l.match(re);
                    if (match) {
                        var w = parseFloat(match[1]);
                        var h = parseFloat(match[2]);
                        var x = parseFloat(match[3]);
                        var y = parseFloat(match[4]);
                        var file_id = match[5];
                        if (typeof imgCallback === "function") {
                            imgCallback(x, y, w, h, file_id);
                        }
                    }
                }
                if (l.startsWith(";EndImage")) withinPixelCode = false;

                if (withinPixelCode) {
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

                var addToModel = false;
                var convertAndAddToModel = false;
                var move = false;

                //				var gcode_parts = gcode_regex.exec(line);
                //				if(gcode_parts === null) continue;
                //				var command = gcode_parts[1];
                //				var parameters = gcode_parts[2];
                var args = self._split_args(line);
                if (args.length === 0) continue;
                var command = args[0];

                if (
                    command === "G0" ||
                    command === "G1" ||
                    command === "G00" ||
                    command === "G01"
                ) {
                    //					var args = self._split_args(parameters);

                    for (var j = 0; j < args.length; j++) {
                        switch ((argChar = args[j].charAt(0).toLowerCase())) {
                            case "x":
                                if (positionRelative) {
                                    x = prevX + Number(args[j].slice(1));
                                } else {
                                    x = Number(args[j].slice(1));
                                }
                                break;

                            case "y":
                                if (positionRelative) {
                                    y = prevY + Number(args[j].slice(1));
                                } else {
                                    y = Number(args[j].slice(1));
                                }
                                break;

                            case "z":
                                if (positionRelative) {
                                    z = prevZ + Number(args[j].slice(1));
                                } else {
                                    z = Number(args[j].slice(1));
                                }
                                break;

                            case "f":
                                numSlice = parseFloat(args[j].slice(1));
                                lastF = numSlice;
                                break;
                        }
                    }

                    if (
                        typeof x !== "undefined" ||
                        typeof y !== "undefined" ||
                        typeof z !== "undefined"
                    ) {
                        addToModel = true;
                        move = true;
                    }
                } else if (
                    command === "G2" ||
                    command === "G3" ||
                    command === "G02" ||
                    command === "G03"
                ) {
                    //					var args = self._split_args(parameters);
                    var units = "G21"; // mm
                    var lastPos = { x: prevX, y: prevY, z: prevZ };

                    clockwise = command === "G2" || command === "G02";
                    for (var j = 0; j < args.length; j++) {
                        switch ((argChar = args[j].charAt(0).toLowerCase())) {
                            case "x":
                                if (positionRelative) {
                                    x = prevX + Number(args[j].slice(1));
                                } else {
                                    x = Number(args[j].slice(1));
                                }
                                break;

                            case "y":
                                if (positionRelative) {
                                    y = prevY + Number(args[j].slice(1));
                                } else {
                                    y = Number(args[j].slice(1));
                                }
                                break;

                            case "z":
                                if (positionRelative) {
                                    z = prevZ + Number(args[j].slice(1));
                                } else {
                                    z = Number(args[j].slice(1));
                                }
                                break;

                            case "i":
                                pi = Number(args[j].slice(1));
                                break;

                            case "j":
                                pj = Number(args[j].slice(1));
                                break;

                            case "p":
                                pp = Number(args[j].slice(1));
                                break;

                            case "f":
                                numSlice = parseFloat(args[j].slice(1));
                                lastF = numSlice;
                                break;
                        }
                    }

                    if (
                        typeof x !== "undefined" ||
                        typeof y !== "undefined" ||
                        typeof z !== "undefined" ||
                        typeof pi !== "undefined" ||
                        typeof pj !== "undefined" ||
                        typeof pp !== "undefined"
                    ) {
                        convertAndAddToModel = true;
                        move = true;
                    }
                } else if (command === "M3" || command === "M03") {
                    //					var args = self._split_args(parameters);;
                    for (var j = 0; j < args.length; j++) {
                        switch ((argChar = args[j].charAt(0).toLowerCase())) {
                            case "s":
                                laser = Number(args[j].slice(1));
                                break;
                        }
                    }
                } else if (command === "M5" || command === "M05") {
                    laser = 0;
                } else if (command === "G91") {
                    positionRelative = true;
                } else if (command === "G90") {
                    positionRelative = false;
                } else if (command === "G92") {
                    //					var args = self._split_args(parameters);;

                    for (var j = 0; j < args.length; j++) {
                        if (!args[j]) continue;

                        if (args.length === 1) {
                            // G92 without coordinates => reset all axes to 0
                            x = 0;
                            y = 0;
                            z = 0;
                        } else {
                            switch (
                                (argChar = args[j].charAt(0).toLowerCase())
                            ) {
                                case "x":
                                    x = Number(args[j].slice(1));
                                    break;

                                case "y":
                                    y = Number(args[j].slice(1));
                                    break;

                                case "z":
                                    z = Number(args[j].slice(1));
                                    prevZ = z;
                                    break;
                            }
                        }
                    }

                    if (
                        typeof x !== "undefined" ||
                        typeof y !== "undefined" ||
                        typeof z !== "undefined"
                    ) {
                        addToModel = true;
                        move = false;
                    }
                } else if (command === "G28" || command === "$H") {
                    //					var args = self._split_args(parameters);;

                    if (args.length === 1) {
                        // G28 with no arguments => home all axis
                        x = 0;
                        y = 0;
                        z = 0;
                    } else {
                        for (j = 0; j < args.length; j++) {
                            switch (
                                (argChar = args[j].charAt(0).toLowerCase())
                            ) {
                                case "x":
                                    x = 0;
                                    break;
                                case "y":
                                    y = 0;
                                    break;
                                case "z":
                                    z = 0;
                                    break;
                                default:
                                    break;
                            }
                        }
                    }

                    if (
                        typeof x !== "undefined" ||
                        typeof y !== "undefined" ||
                        typeof z !== "undefined"
                    ) {
                        addToModel = true;
                        move = true;
                    }
                }

                // ensure z is set.
                if (typeof z === "undefined") {
                    if (typeof prevZ !== "undefined") {
                        z = prevZ;
                    } else {
                        z = 0;
                    }
                }

                if (addToModel && !isNaN(x) && !isNaN(y)) {
                    // TODO: hack. unclear why y sometimes is undefined.
                    model.push({
                        x: x,
                        y: y,
                        z: z,
                        laser: laser,
                        noMove: !move,
                        prevX: prevX,
                        prevY: prevY,
                        prevZ: prevZ,
                        speed: lastF,
                        gcodeLine: i,
                        percentage: i / gcode_lines.length,
                    });
                }
                if (convertAndAddToModel) {
                    var parts = self._convertG2G3(
                        clockwise,
                        x,
                        y,
                        z,
                        pi,
                        pj,
                        pp,
                        lastPos,
                        units
                    );
                    var lastPart = parts[0];
                    for (var l = 1; l < parts.length; l++) {
                        var part = parts[l];

                        model.push({
                            x: part[0],
                            y: part[1],
                            z: part[2],
                            laser: laser,
                            noMove: !move,
                            prevX: lastPart[0],
                            prevY: lastPart[1],
                            prevZ: lastPart[2],
                            speed: lastF,
                            gcodeLine: i,
                            percentage: i / gcode_lines.length,
                        });

                        lastPart = part;
                    }
                }

                if (move) {
                    if (typeof x !== "undefined") prevX = x;
                    if (typeof y !== "undefined") prevY = y;
                }

                if (
                    model.length > 0 &&
                    typeof pathCallback === "function" &&
                    pathDelimiter !== undefined &&
                    pathDelimiter.test(line)
                ) {
                    pathCallback(model);
                    model = model.slice(-1); // keep the last element as start of the next block
                }
            }

            prevZ = z;
            if (typeof pathCallback === "function" && model.length > 0) {
                pathCallback(model);
            }
        };

        self._convertG2G3 = function (
            clockwise,
            x,
            y,
            z,
            i,
            j,
            p,
            lastPos,
            units
        ) {
            if (typeof x === "undefined") x = lastPos.x;
            if (typeof y === "undefined") y = lastPos.y;
            if (typeof z === "undefined") z = lastPos.z;
            if (typeof i === "undefined") i = 0.0;
            if (typeof j === "undefined") j = 0.0;
            if (typeof p === "undefined") p = 1.0;

            var curveSection = 1.0; // mm
            if (units === "G20") {
                // inches
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
            var steps; // TODO accuracy setting
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

            // This if arc is correct
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
                if (!clockwise) step = s;
                else step = steps - s;

                var ta = angleA + angle * (step / steps);

                parts.push([
                    cX + radius * Math.cos(ta),
                    cY + radius * Math.sin(ta),
                    lastPos.z + ((z - arcStartZ) * s) / steps,
                ]);
            }

            return parts;
        };

        self._split_args = function (str) {
            var result = [];
            var p = null;
            var val = "";
            for (var i = 0; i < str.length; i++) {
                var char = str[i];
                if (/[A-Z;]/.test(char)) {
                    if (p !== null) {
                        result.push(p + val);
                        val = "";
                    }
                    p = char;
                } else {
                    if (char !== " ") {
                        val += char;
                    }
                }
            }
            if (p !== null) {
                result.push(p + val);
            }
            return result;
        };
    };
});
