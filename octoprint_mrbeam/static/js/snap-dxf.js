//"use strict";

//var Snap = require('snapsvg'),
//    dxf = require('./dxf.js');

Snap.plugin(function (Snap, Element, Paper, global, Fragment) {
    Snap.parseDXF = function (dxfString) {
        var convertedSVG = dxf.toSVG(dxf.parseString(dxfString));
        return Snap.parse(convertedSVG);
    };

    Snap.loadDXF = function (url, callback, scope) {
        Snap.ajax(url, function (req) {
            var timestamps = {
                load_done: Date.now(),
                parse_start: Date.now(),
                parse_done: -1,
            };
            var f = Snap.parseDXF(req.responseText);
            timestamps.parse_done = Date.now();
            if (callback)
                scope ? callback.call(scope, f, timestamps) : callback(f, timestamps);
        });
    };
});
