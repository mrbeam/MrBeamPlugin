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
            var f = Snap.parseDXF(req.responseText);
            if (callback)
                scope ? callback.call(scope, f) : callback(f);
        });
    };
});
