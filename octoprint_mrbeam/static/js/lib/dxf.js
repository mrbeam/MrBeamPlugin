(function(f){if(typeof exports==="object"&&typeof module!=="undefined"){module.exports=f()}else if(typeof define==="function"&&define.amd){define([],f)}else{var g;if(typeof window!=="undefined"){g=window}else if(typeof global!=="undefined"){g=global}else if(typeof self!=="undefined"){g=self}else{g=this}g.dxf = f()}})(function(){var define,module,exports;return (function(){function r(e,n,t){function o(i,f){if(!n[i]){if(!e[i]){var c="function"==typeof require&&require;if(!f&&c)return c(i,!0);if(u)return u(i,!0);var a=new Error("Cannot find module '"+i+"'");throw a.code="MODULE_NOT_FOUND",a}var p=n[i]={exports:{}};e[i][0].call(p.exports,function(r){var n=e[i][1][r];return o(n||r)},p,p.exports,r,e,n,t)}return n[i].exports}for(var u="function"==typeof require&&require,i=0;i<t.length;i++)o(t[i]);return o}return r})()({1:[function(require,module,exports){
"use strict";

Object.defineProperty(exports, "__esModule", {
  value: true
});
exports.default = void 0;

var _logger = _interopRequireDefault(require("./util/logger"));

var _parseString = _interopRequireDefault(require("./parseString"));

var _denormalise2 = _interopRequireDefault(require("./denormalise"));

var _toSVG2 = _interopRequireDefault(require("./toSVG"));

var _toPolylines2 = _interopRequireDefault(require("./toPolylines"));

var _groupEntitiesByLayer = _interopRequireDefault(require("./groupEntitiesByLayer"));

function _interopRequireDefault(obj) { return obj && obj.__esModule ? obj : { default: obj }; }

function _classCallCheck(instance, Constructor) { if (!(instance instanceof Constructor)) { throw new TypeError("Cannot call a class as a function"); } }

function _defineProperties(target, props) { for (var i = 0; i < props.length; i++) { var descriptor = props[i]; descriptor.enumerable = descriptor.enumerable || false; descriptor.configurable = true; if ("value" in descriptor) descriptor.writable = true; Object.defineProperty(target, descriptor.key, descriptor); } }

function _createClass(Constructor, protoProps, staticProps) { if (protoProps) _defineProperties(Constructor.prototype, protoProps); if (staticProps) _defineProperties(Constructor, staticProps); return Constructor; }

var Helper =
/*#__PURE__*/
function () {
  function Helper(contents) {
    _classCallCheck(this, Helper);

    if (!(typeof contents === 'string')) {
      throw Error('Helper constructor expects a DXF string');
    }

    this._contents = contents;
    this._parsed = null;
    this._denormalised = null;
  }

  _createClass(Helper, [{
    key: "parse",
    value: function parse() {
      this._parsed = (0, _parseString.default)(this._contents);

      _logger.default.info('parsed:', this.parsed);

      return this._parsed;
    }
  }, {
    key: "denormalise",
    value: function denormalise() {
      this._denormalised = (0, _denormalise2.default)(this.parsed);

      _logger.default.info('denormalised:', this._denormalised);

      return this._denormalised;
    }
  }, {
    key: "group",
    value: function group() {
      this._groups = (0, _groupEntitiesByLayer.default)(this.denormalised);
    }
  }, {
    key: "toSVG",
    value: function toSVG() {
      return (0, _toSVG2.default)(this.parsed);
    }
  }, {
    key: "toPolylines",
    value: function toPolylines() {
      return (0, _toPolylines2.default)(this.parsed);
    }
  }, {
    key: "parsed",
    get: function get() {
      if (this._parsed === null) {
        this.parse();
      }

      return this._parsed;
    }
  }, {
    key: "denormalised",
    get: function get() {
      if (!this._denormalised) {
        this.denormalise();
      }

      return this._denormalised;
    }
  }, {
    key: "groups",
    get: function get() {
      if (!this._groups) {
        this.group();
      }

      return this._groups;
    }
  }]);

  return Helper;
}();

exports.default = Helper;
},{"./denormalise":4,"./groupEntitiesByLayer":7,"./parseString":26,"./toPolylines":27,"./toSVG":28,"./util/logger":33}],2:[function(require,module,exports){
"use strict";

Object.defineProperty(exports, "__esModule", {
  value: true
});
exports.default = void 0;

/**
 * Apply the transforms to the polyline.
 *
 * @param polyline the polyline
 * @param transform the transforms array
 * @returns the transformed polyline
 */
var _default = function _default(polyline, transforms) {
  transforms.forEach(function (transform) {
    polyline = polyline.map(function (p) {
      // Use a copy to avoid side effects
      var p2 = [p[0], p[1]];

      if (transform.scaleX) {
        p2[0] = p2[0] * transform.scaleX;
      }

      if (transform.scaleY) {
        p2[1] = p2[1] * transform.scaleY;
      }

      if (transform.rotation) {
        var angle = transform.rotation / 180 * Math.PI;
        p2 = [p2[0] * Math.cos(angle) - p2[1] * Math.sin(angle), p2[1] * Math.cos(angle) + p2[0] * Math.sin(angle)];
      }

      if (transform.x) {
        p2[0] = p2[0] + transform.x;
      }

      if (transform.y) {
        p2[1] = p2[1] + transform.y;
      } // Observed once in a sample DXF - some cad applications
      // use negative extruxion Z for flipping


      if (transform.extrusionZ === -1) {
        p2[0] = -p2[0];
      }

      return p2;
    });
  });
  return polyline;
};

exports.default = _default;
},{}],3:[function(require,module,exports){
"use strict";

Object.defineProperty(exports, "__esModule", {
  value: true
});
exports.default = void 0;
var _default = {
  verbose: false
};
exports.default = _default;
},{}],4:[function(require,module,exports){
"use strict";

Object.defineProperty(exports, "__esModule", {
  value: true
});
exports.default = void 0;

var _lodash = _interopRequireDefault(require("lodash.clonedeep"));

var _logger = _interopRequireDefault(require("./util/logger"));

function _interopRequireDefault(obj) { return obj && obj.__esModule ? obj : { default: obj }; }

var _default = function _default(parseResult) {
  var blocksByName = parseResult.blocks.reduce(function (acc, b) {
    acc[b.name] = b;
    return acc;
  }, {});

  var gatherEntities = function gatherEntities(entities, transforms) {
    var current = [];
    entities.forEach(function (e) {
      if (e.type === 'INSERT') {
        var insert = e;
        var block = blocksByName[insert.block];

        if (!block) {
          _logger.default.error('no block found for insert. block:', insert.block);

          return;
        }

        var t = {
          x: -block.x + insert.x,
          y: -block.y + insert.y,
          scaleX: insert.scaleX,
          scaleY: insert.scaleY,
          scaleZ: insert.scaleZ,
          extrusionX: insert.extrusionX,
          extrusionY: insert.extrusionY,
          extrusionZ: insert.extrusionZ,
          rotation: insert.rotation // Add the insert transform and recursively add entities

        };
        var transforms2 = transforms.slice(0);
        transforms2.push(t); // Use the insert layer

        var blockEntities = block.entities.map(function (be) {
          var be2 = (0, _lodash.default)(be);
          be2.layer = insert.layer;
          return be2;
        });
        current = current.concat(gatherEntities(blockEntities, transforms2));
      } else {
        // Top-level entity. Clone and add the transforms
        // The transforms are reversed so they occur in
        // order of application - i.e. the transform of the
        // top-level insert is applied last
        var e2 = (0, _lodash.default)(e);
        e2.transforms = transforms.slice().reverse();
        current.push(e2);
      }
    });
    return current;
  };

  return gatherEntities(parseResult.entities, []);
};

exports.default = _default;
},{"./util/logger":33,"lodash.clonedeep":36}],5:[function(require,module,exports){
"use strict";

Object.defineProperty(exports, "__esModule", {
  value: true
});
exports.default = void 0;

var _bSpline = _interopRequireDefault(require("./util/bSpline"));

var _logger = _interopRequireDefault(require("./util/logger"));

var _createArcForLWPolyline = _interopRequireDefault(require("./util/createArcForLWPolyline"));

function _interopRequireDefault(obj) { return obj && obj.__esModule ? obj : { default: obj }; }

/**
 * Rotate a set of points.
 *
 * @param points the points
 * @param angle the rotation angle
 */
var rotate = function rotate(points, angle) {
  return points.map(function (p) {
    return [p[0] * Math.cos(angle) - p[1] * Math.sin(angle), p[1] * Math.cos(angle) + p[0] * Math.sin(angle)];
  });
};
/**
 * Interpolate an ellipse
 * @param cx center X
 * @param cy center Y
 * @param rx radius X
 * @param ry radius Y
 * @param start start angle in radians
 * @param start end angle in radians
 */


var interpolateEllipse = function interpolateEllipse(cx, cy, rx, ry, start, end, rotationAngle) {
  if (end < start) {
    end += Math.PI * 2;
  } // ----- Relative points -----
  // Start point


  var points = [];
  var dTheta = Math.PI * 2 / 72;
  var EPS = 1e-6;

  for (var theta = start; theta < end - EPS; theta += dTheta) {
    points.push([Math.cos(theta) * rx, Math.sin(theta) * ry]);
  }

  points.push([Math.cos(end) * rx, Math.sin(end) * ry]); // ----- Rotate -----

  if (rotationAngle) {
    points = rotate(points, rotationAngle);
  } // ----- Offset center -----


  points = points.map(function (p) {
    return [cx + p[0], cy + p[1]];
  });
  return points;
};
/**
 * Interpolate a b-spline. The algorithm examins the knot vector
 * to create segments for interpolation. The parameterisation value
 * is re-normalised back to [0,1] as that is what the lib expects (
 * and t i de-normalised in the b-spline library)
 *
 * @param controlPoints the control points
 * @param degree the b-spline degree
 * @param knots the knot vector
 * @returns the polyline
 */


var interpolateBSpline = function interpolateBSpline(controlPoints, degree, knots, interpolationsPerSplineSegment) {
  var polyline = [];
  var controlPointsForLib = controlPoints.map(function (p) {
    return [p.x, p.y];
  });
  var segmentTs = [knots[degree]];
  var domain = [knots[degree], knots[knots.length - 1 - degree]];

  for (var k = degree + 1; k < knots.length - degree; ++k) {
    if (segmentTs[segmentTs.length - 1] !== knots[k]) {
      segmentTs.push(knots[k]);
    }
  }

  interpolationsPerSplineSegment = interpolationsPerSplineSegment || 25;

  for (var i = 1; i < segmentTs.length; ++i) {
    var uMin = segmentTs[i - 1];
    var uMax = segmentTs[i];

    for (var _k = 0; _k <= interpolationsPerSplineSegment; ++_k) {
      // https://github.com/bjnortier/dxf/issues/28
      // b-spline interpolation can fail due to a floating point
      // error - ignore these until the lib is fixed
      try {
        var u = _k / interpolationsPerSplineSegment * (uMax - uMin) + uMin;
        var t = (u - domain[0]) / (domain[1] - domain[0]);
        var p = (0, _bSpline.default)(t, degree, controlPointsForLib, knots);
        polyline.push(p);
      } catch (e) {// ignore this point
      }
    }
  }

  return polyline;
};
/**
 * Convert a parsed DXF entity to a polyline. These can be used to render the
 * the DXF in SVG, Canvas, WebGL etc., without depending on native support
 * of primitive objects (ellispe, spline etc.)
 */


var _default = function _default(entity, options) {
  options = options || {};
  var polyline;

  if (entity.type === 'LINE') {
    polyline = [[entity.start.x, entity.start.y], [entity.end.x, entity.end.y]];
  }

  if (entity.type === 'LWPOLYLINE' || entity.type === 'POLYLINE') {
    polyline = [];

    if (entity.polygonMesh || entity.polyfaceMesh) {// Do not attempt to render meshes
    } else if (entity.vertices.length) {
      if (entity.closed) {
        entity.vertices = entity.vertices.concat(entity.vertices[0]);
      }

      for (var i = 0, il = entity.vertices.length; i < il - 1; ++i) {
        var from = [entity.vertices[i].x, entity.vertices[i].y];
        var to = [entity.vertices[i + 1].x, entity.vertices[i + 1].y];
        polyline.push(from);

        if (entity.vertices[i].bulge) {
          polyline = polyline.concat((0, _createArcForLWPolyline.default)(from, to, entity.vertices[i].bulge));
        } // The last iteration of the for loop


        if (i === il - 2) {
          polyline.push(to);
        }
      }
    } else {
      _logger.default.warn('Polyline entity with no vertices');
    }
  }

  if (entity.type === 'CIRCLE') {
    polyline = interpolateEllipse(entity.x, entity.y, entity.r, entity.r, 0, Math.PI * 2);
  }

  if (entity.type === 'ELLIPSE') {
    var rx = Math.sqrt(entity.majorX * entity.majorX + entity.majorY * entity.majorY);
    var ry = entity.axisRatio * rx;
    var majorAxisRotation = -Math.atan2(-entity.majorY, entity.majorX);
    polyline = interpolateEllipse(entity.x, entity.y, rx, ry, entity.startAngle, entity.endAngle, majorAxisRotation);
    var flipY = entity.extrusionZ === -1;

    if (flipY) {
      polyline = polyline.map(function (p) {
        return [-(p[0] - entity.x) + entity.x, p[1]];
      });
    }
  }

  if (entity.type === 'ARC') {
    // Why on earth DXF has degree start & end angles for arc,
    // and radian start & end angles for ellipses is a mystery
    polyline = interpolateEllipse(entity.x, entity.y, entity.r, entity.r, entity.startAngle, entity.endAngle, undefined, false); // I kid you not, ARCs and ELLIPSEs handle this differently,
    // as evidenced by how AutoCAD actually renders these entities

    var _flipY = entity.extrusionZ === -1;

    if (_flipY) {
      polyline = polyline.map(function (p) {
        return [-p[0], p[1]];
      });
    }
  }

  if (entity.type === 'SPLINE') {
    polyline = interpolateBSpline(entity.controlPoints, entity.degree, entity.knots, options.interpolationsPerSplineSegment);
  }

  if (!polyline) {
    _logger.default.warn('unsupported entity for converting to polyline:', entity.type);

    return [];
  }

  return polyline;
};

exports.default = _default;
},{"./util/bSpline":30,"./util/createArcForLWPolyline":32,"./util/logger":33}],6:[function(require,module,exports){
"use strict";

Object.defineProperty(exports, "__esModule", {
  value: true
});
exports.default = void 0;

var _colors = _interopRequireDefault(require("./util/colors"));

var _logger = _interopRequireDefault(require("./util/logger"));

function _interopRequireDefault(obj) { return obj && obj.__esModule ? obj : { default: obj }; }

var _default = function _default(layers, entity) {
  var layerTable = layers[entity.layer];

  if (layerTable) {
    var colorNumber = 'colorNumber' in entity ? entity.colorNumber : layerTable.colorNumber;
    var rgb = _colors.default[colorNumber];

    if (rgb) {
      return rgb;
    } else {
      _logger.default.warn('Color index', colorNumber, 'invalid, defaulting to black');

      return [0, 0, 0];
    }
  } else {
    _logger.default.warn('no layer table for layer:' + entity.layer);

    return [0, 0, 0];
  }
};

exports.default = _default;
},{"./util/colors":31,"./util/logger":33}],7:[function(require,module,exports){
"use strict";

Object.defineProperty(exports, "__esModule", {
  value: true
});
exports.default = void 0;

var _default = function _default(entities) {
  return entities.reduce(function (acc, entity) {
    var layer = entity.layer;

    if (!acc[layer]) {
      acc[layer] = [];
    }

    acc[layer].push(entity);
    return acc;
  }, {});
};

exports.default = _default;
},{}],8:[function(require,module,exports){
"use strict";

Object.defineProperty(exports, "__esModule", {
  value: true
});
exports.default = void 0;

var _entities = _interopRequireDefault(require("./entities"));

function _interopRequireDefault(obj) { return obj && obj.__esModule ? obj : { default: obj }; }

var _default = function _default(tuples) {
  var state;
  var blocks = [];
  var block;
  var entitiesTuples = [];
  tuples.forEach(function (tuple) {
    var type = tuple[0];
    var value = tuple[1];

    if (value === 'BLOCK') {
      state = 'block';
      block = {};
      entitiesTuples = [];
      blocks.push(block);
    } else if (value === 'ENDBLK') {
      if (state === 'entities') {
        block.entities = (0, _entities.default)(entitiesTuples);
      } else {
        block.entities = [];
      }

      entitiesTuples = undefined;
      state = undefined;
    } else if (state === 'block' && type !== 0) {
      switch (type) {
        case 1:
          block.xref = value;
          break;

        case 2:
          block.name = value;
          break;

        case 10:
          block.x = value;
          break;

        case 20:
          block.y = value;
          break;

        case 30:
          block.z = value;
          break;

        default:
          break;
      }
    } else if (state === 'block' && type === 0) {
      state = 'entities';
      entitiesTuples.push(tuple);
    } else if (state === 'entities') {
      entitiesTuples.push(tuple);
    }
  });
  return blocks;
};

exports.default = _default;
},{"./entities":9}],9:[function(require,module,exports){
"use strict";

Object.defineProperty(exports, "__esModule", {
  value: true
});
exports.default = void 0;

var _logger = _interopRequireDefault(require("../util/logger"));

var _point = _interopRequireDefault(require("./entity/point"));

var _line = _interopRequireDefault(require("./entity/line"));

var _lwpolyline = _interopRequireDefault(require("./entity/lwpolyline"));

var _polyline = _interopRequireDefault(require("./entity/polyline"));

var _vertex = _interopRequireDefault(require("./entity/vertex"));

var _circle = _interopRequireDefault(require("./entity/circle"));

var _arc = _interopRequireDefault(require("./entity/arc"));

var _ellipse = _interopRequireDefault(require("./entity/ellipse"));

var _spline = _interopRequireDefault(require("./entity/spline"));

var _solid = _interopRequireDefault(require("./entity/solid"));

var _mtext = _interopRequireDefault(require("./entity/mtext"));

var _insert = _interopRequireDefault(require("./entity/insert"));

function _interopRequireDefault(obj) { return obj && obj.__esModule ? obj : { default: obj }; }

var handlers = [_point.default, _line.default, _lwpolyline.default, _polyline.default, _vertex.default, _circle.default, _arc.default, _ellipse.default, _spline.default, _solid.default, _mtext.default, _insert.default].reduce(function (acc, mod) {
  acc[mod.TYPE] = mod;
  return acc;
}, {});

var _default = function _default(tuples) {
  var entities = [];
  var entityGroups = [];
  var currentEntityTuples; // First group them together for easy processing

  tuples.forEach(function (tuple) {
    var type = tuple[0];

    if (type === 0) {
      currentEntityTuples = [];
      entityGroups.push(currentEntityTuples);
    }

    currentEntityTuples.push(tuple);
  });
  var currentPolyline;
  entityGroups.forEach(function (tuples) {
    var entityType = tuples[0][1];
    var contentTuples = tuples.slice(1);

    if (handlers.hasOwnProperty(entityType)) {
      var e = handlers[entityType].process(contentTuples); // "POLYLINE" cannot be parsed in isolation, it is followed by
      // N "VERTEX" entities and ended with a "SEQEND" entity.
      // Essentially we convert POLYLINE to LWPOLYLINE - the extra
      // vertex flags are not supported

      if (entityType === 'POLYLINE') {
        currentPolyline = e;
        entities.push(e);
      } else if (entityType === 'VERTEX') {
        if (currentPolyline) {
          currentPolyline.vertices.push(e);
        } else {
          _logger.default.error('ignoring invalid VERTEX entity');
        }
      } else if (entityType === 'SEQEND') {
        currentPolyline = undefined;
      } else {
        // All other entities
        entities.push(e);
      }
    } else {
      _logger.default.warn('unsupported type in ENTITIES section:', entityType);
    }
  });
  return entities;
};

exports.default = _default;
},{"../util/logger":33,"./entity/arc":10,"./entity/circle":11,"./entity/ellipse":13,"./entity/insert":14,"./entity/line":15,"./entity/lwpolyline":16,"./entity/mtext":17,"./entity/point":18,"./entity/polyline":19,"./entity/solid":20,"./entity/spline":21,"./entity/vertex":22}],10:[function(require,module,exports){
"use strict";

Object.defineProperty(exports, "__esModule", {
  value: true
});
exports.default = exports.process = exports.TYPE = void 0;

var _common = _interopRequireDefault(require("./common"));

function _interopRequireDefault(obj) { return obj && obj.__esModule ? obj : { default: obj }; }

var TYPE = 'ARC';
exports.TYPE = TYPE;

var process = function process(tuples) {
  return tuples.reduce(function (entity, tuple) {
    var type = tuple[0];
    var value = tuple[1];

    switch (type) {
      case 10:
        entity.x = value;
        break;

      case 20:
        entity.y = value;
        break;

      case 30:
        entity.z = value;
        break;

      case 39:
        entity.thickness = value;
        break;

      case 40:
        entity.r = value;
        break;

      case 50:
        // *Someone* decided that ELLIPSE angles are in radians but
        // ARC angles are in degrees
        entity.startAngle = value / 180 * Math.PI;
        break;

      case 51:
        entity.endAngle = value / 180 * Math.PI;
        break;

      default:
        Object.assign(entity, (0, _common.default)(type, value));
        break;
    }

    return entity;
  }, {
    type: TYPE
  });
};

exports.process = process;
var _default = {
  TYPE: TYPE,
  process: process
};
exports.default = _default;
},{"./common":12}],11:[function(require,module,exports){
"use strict";

Object.defineProperty(exports, "__esModule", {
  value: true
});
exports.default = exports.process = exports.TYPE = void 0;

var _common = _interopRequireDefault(require("./common"));

function _interopRequireDefault(obj) { return obj && obj.__esModule ? obj : { default: obj }; }

var TYPE = 'CIRCLE';
exports.TYPE = TYPE;

var process = function process(tuples) {
  return tuples.reduce(function (entity, tuple) {
    var type = tuple[0];
    var value = tuple[1];

    switch (type) {
      case 10:
        entity.x = value;
        break;

      case 20:
        entity.y = value;
        break;

      case 30:
        entity.z = value;
        break;

      case 40:
        entity.r = value;
        break;

      default:
        Object.assign(entity, (0, _common.default)(type, value));
        break;
    }

    return entity;
  }, {
    type: TYPE
  });
};

exports.process = process;
var _default = {
  TYPE: TYPE,
  process: process
};
exports.default = _default;
},{"./common":12}],12:[function(require,module,exports){
"use strict";

Object.defineProperty(exports, "__esModule", {
  value: true
});
exports.default = void 0;

var _default = function _default(type, value) {
  switch (type) {
    case 6:
      // Linetype name (present if not BYLAYER).
      // The special name BYBLOCK indicates a
      // floating linetype. (optional)
      return {
        lineTypeName: value
      };

    case 8:
      return {
        layer: value
      };

    case 48:
      // Linetype scale (optional)
      return {
        lineTypeScale: value
      };

    case 60:
      // Object visibility (optional): 0 = visible, 1 = invisible.
      return {
        visible: value === 0
      };

    case 62:
      // Color number (present if not BYLAYER).
      // Zero indicates the BYBLOCK (floating) color.
      // 256 indicates BYLAYER.
      // A negative value indicates that the layer is turned off. (optional)
      return {
        colorNumber: value
      };

    case 210:
      return {
        extrusionX: value
      };

    case 220:
      return {
        extrusionY: value
      };

    case 230:
      return {
        extrusionZ: value
      };

    default:
      return {};
  }
};

exports.default = _default;
},{}],13:[function(require,module,exports){
"use strict";

Object.defineProperty(exports, "__esModule", {
  value: true
});
exports.default = exports.process = exports.TYPE = void 0;

var _common = _interopRequireDefault(require("./common"));

function _interopRequireDefault(obj) { return obj && obj.__esModule ? obj : { default: obj }; }

var TYPE = 'ELLIPSE';
exports.TYPE = TYPE;

var process = function process(tuples) {
  return tuples.reduce(function (entity, tuple) {
    var type = tuple[0];
    var value = tuple[1];

    switch (type) {
      case 10:
        entity.x = value;
        break;

      case 11:
        entity.majorX = value;
        break;

      case 20:
        entity.y = value;
        break;

      case 21:
        entity.majorY = value;
        break;

      case 30:
        entity.z = value;
        break;

      case 31:
        entity.majorZ = value;
        break;

      case 40:
        entity.axisRatio = value;
        break;

      case 41:
        entity.startAngle = value;
        break;

      case 42:
        entity.endAngle = value;
        break;

      default:
        Object.assign(entity, (0, _common.default)(type, value));
        break;
    }

    return entity;
  }, {
    type: TYPE
  });
};

exports.process = process;
var _default = {
  TYPE: TYPE,
  process: process
};
exports.default = _default;
},{"./common":12}],14:[function(require,module,exports){
"use strict";

Object.defineProperty(exports, "__esModule", {
  value: true
});
exports.default = exports.process = exports.TYPE = void 0;

var _common = _interopRequireDefault(require("./common"));

function _interopRequireDefault(obj) { return obj && obj.__esModule ? obj : { default: obj }; }

var TYPE = 'INSERT';
exports.TYPE = TYPE;

var process = function process(tuples) {
  return tuples.reduce(function (entity, tuple) {
    var type = tuple[0];
    var value = tuple[1];

    switch (type) {
      case 2:
        entity.block = value;
        break;

      case 10:
        entity.x = value;
        break;

      case 20:
        entity.y = value;
        break;

      case 30:
        entity.z = value;
        break;

      case 41:
        entity.scaleX = value;
        break;

      case 42:
        entity.scaleY = value;
        break;

      case 43:
        entity.scaleZ = value;
        break;

      case 44:
        entity.columnSpacing = value;
        break;

      case 45:
        entity.rowSpacing = value;
        break;

      case 50:
        entity.rotation = value;
        break;

      case 70:
        entity.columnCount = value;
        break;

      case 71:
        entity.rowCount = value;
        break;

      case 210:
        entity.extrusionX = value;
        break;

      case 220:
        entity.extrusionY = value;
        break;

      case 230:
        entity.extrusionZ = value;
        break;

      default:
        Object.assign(entity, (0, _common.default)(type, value));
        break;
    }

    return entity;
  }, {
    type: TYPE
  });
};

exports.process = process;
var _default = {
  TYPE: TYPE,
  process: process
};
exports.default = _default;
},{"./common":12}],15:[function(require,module,exports){
"use strict";

Object.defineProperty(exports, "__esModule", {
  value: true
});
exports.default = exports.process = exports.TYPE = void 0;

var _common = _interopRequireDefault(require("./common"));

function _interopRequireDefault(obj) { return obj && obj.__esModule ? obj : { default: obj }; }

var TYPE = 'LINE';
exports.TYPE = TYPE;

var process = function process(tuples) {
  return tuples.reduce(function (entity, tuple) {
    var type = tuple[0];
    var value = tuple[1];

    switch (type) {
      case 10:
        entity.start.x = value;
        break;

      case 20:
        entity.start.y = value;
        break;

      case 30:
        entity.start.z = value;
        break;

      case 39:
        entity.thickness = value;
        break;

      case 11:
        entity.end.x = value;
        break;

      case 21:
        entity.end.y = value;
        break;

      case 31:
        entity.end.z = value;
        break;

      default:
        Object.assign(entity, (0, _common.default)(type, value));
        break;
    }

    return entity;
  }, {
    type: TYPE,
    start: {},
    end: {}
  });
};

exports.process = process;
var _default = {
  TYPE: TYPE,
  process: process
};
exports.default = _default;
},{"./common":12}],16:[function(require,module,exports){
"use strict";

Object.defineProperty(exports, "__esModule", {
  value: true
});
exports.default = exports.process = exports.TYPE = void 0;

var _common = _interopRequireDefault(require("./common"));

function _interopRequireDefault(obj) { return obj && obj.__esModule ? obj : { default: obj }; }

var TYPE = 'LWPOLYLINE';
exports.TYPE = TYPE;

var process = function process(tuples) {
  var vertex;
  return tuples.reduce(function (entity, tuple) {
    var type = tuple[0];
    var value = tuple[1];

    switch (type) {
      case 70:
        entity.closed = (value & 1) === 1;
        break;

      case 10:
        vertex = {
          x: value,
          y: 0
        };
        entity.vertices.push(vertex);
        break;

      case 20:
        vertex.y = value;
        break;

      case 39:
        entity.thickness = value;
        break;

      case 42:
        // Bulge (multiple entries; one entry for each vertex)  (optional; default = 0).
        vertex.bulge = value;
        break;

      default:
        Object.assign(entity, (0, _common.default)(type, value));
        break;
    }

    return entity;
  }, {
    type: TYPE,
    vertices: []
  });
};

exports.process = process;
var _default = {
  TYPE: TYPE,
  process: process
};
exports.default = _default;
},{"./common":12}],17:[function(require,module,exports){
"use strict";

Object.defineProperty(exports, "__esModule", {
  value: true
});
exports.default = exports.process = exports.TYPE = void 0;

var _common = _interopRequireDefault(require("./common"));

function _interopRequireDefault(obj) { return obj && obj.__esModule ? obj : { default: obj }; }

var TYPE = 'MTEXT';
exports.TYPE = TYPE;
var simpleCodes = {
  10: 'x',
  20: 'y',
  30: 'z',
  40: 'nominalTextHeight',
  41: 'refRectangleWidth',
  71: 'attachmentPoint',
  72: 'drawingDirection',
  7: 'styleName',
  11: 'xAxisX',
  21: 'xAxisY',
  31: 'xAxisZ',
  42: 'horizontalWidth',
  43: 'verticalHeight',
  73: 'lineSpacingStyle',
  44: 'lineSpacingFactor',
  90: 'backgroundFill',
  420: 'bgColorRGB0',
  421: 'bgColorRGB1',
  422: 'bgColorRGB2',
  423: 'bgColorRGB3',
  424: 'bgColorRGB4',
  425: 'bgColorRGB5',
  426: 'bgColorRGB6',
  427: 'bgColorRGB7',
  428: 'bgColorRGB8',
  429: 'bgColorRGB9',
  430: 'bgColorName0',
  431: 'bgColorName1',
  432: 'bgColorName2',
  433: 'bgColorName3',
  434: 'bgColorName4',
  435: 'bgColorName5',
  436: 'bgColorName6',
  437: 'bgColorName7',
  438: 'bgColorName8',
  439: 'bgColorName9',
  45: 'fillBoxStyle',
  63: 'bgFillColor',
  441: 'bgFillTransparency',
  75: 'columnType',
  76: 'columnCount',
  78: 'columnFlowReversed',
  79: 'columnAutoheight',
  48: 'columnWidth',
  49: 'columnGutter',
  50: 'columnHeights'
};

var process = function process(tuples) {
  return tuples.reduce(function (entity, tuple) {
    var type = tuple[0];
    var value = tuple[1];

    if (simpleCodes.hasOwnProperty(type)) {
      entity[simpleCodes[type]] = value;
    } else if (type === 1 || type === 3) {
      entity.string += value;
    } else if (type === 50) {
      // Rotation angle in radians
      entity.xAxisX = Math.cos(value);
      entity.xAxisY = Math.sin(value);
    } else {
      Object.assign(entity, (0, _common.default)(type, value));
    }

    return entity;
  }, {
    type: TYPE,
    string: ''
  });
};

exports.process = process;
var _default = {
  TYPE: TYPE,
  process: process
};
exports.default = _default;
},{"./common":12}],18:[function(require,module,exports){
"use strict";

Object.defineProperty(exports, "__esModule", {
  value: true
});
exports.default = exports.process = exports.TYPE = void 0;

var _common = _interopRequireDefault(require("./common"));

function _interopRequireDefault(obj) { return obj && obj.__esModule ? obj : { default: obj }; }

var TYPE = 'POINT';
exports.TYPE = TYPE;

var process = function process(tuples) {
  return tuples.reduce(function (entity, tuple) {
    var type = tuple[0];
    var value = tuple[1];

    switch (type) {
      case 10:
        entity.x = value;
        break;

      case 20:
        entity.y = value;
        break;

      case 30:
        entity.z = value;
        break;

      case 39:
        entity.thickness = value;
        break;

      default:
        Object.assign(entity, (0, _common.default)(type, value));
        break;
    }

    return entity;
  }, {
    type: TYPE
  });
};

exports.process = process;
var _default = {
  TYPE: TYPE,
  process: process
};
exports.default = _default;
},{"./common":12}],19:[function(require,module,exports){
"use strict";

Object.defineProperty(exports, "__esModule", {
  value: true
});
exports.default = exports.process = exports.TYPE = void 0;

var _common = _interopRequireDefault(require("./common"));

function _interopRequireDefault(obj) { return obj && obj.__esModule ? obj : { default: obj }; }

var TYPE = 'POLYLINE';
exports.TYPE = TYPE;

var process = function process(tuples) {
  return tuples.reduce(function (entity, tuple) {
    var type = tuple[0];
    var value = tuple[1];

    switch (type) {
      case 70:
        entity.closed = (value & 1) === 1;
        entity.polygonMesh = (value & 16) === 16;
        entity.polyfaceMesh = (value & 64) === 64;
        break;

      case 39:
        entity.thickness = value;
        break;

      default:
        Object.assign(entity, (0, _common.default)(type, value));
        break;
    }

    return entity;
  }, {
    type: TYPE,
    vertices: []
  });
};

exports.process = process;
var _default = {
  TYPE: TYPE,
  process: process
};
exports.default = _default;
},{"./common":12}],20:[function(require,module,exports){
"use strict";

Object.defineProperty(exports, "__esModule", {
  value: true
});
exports.default = exports.process = exports.TYPE = void 0;

var _common = _interopRequireDefault(require("./common"));

function _interopRequireDefault(obj) { return obj && obj.__esModule ? obj : { default: obj }; }

var TYPE = 'SOLID';
exports.TYPE = TYPE;

var process = function process(tuples) {
  return tuples.reduce(function (entity, tuple) {
    var type = tuple[0];
    var value = tuple[1];

    switch (type) {
      case 10:
        entity.corners[0].x = value;
        break;

      case 20:
        entity.corners[0].y = value;
        break;

      case 30:
        entity.corners[0].z = value;
        break;

      case 11:
        entity.corners[1].x = value;
        break;

      case 21:
        entity.corners[1].y = value;
        break;

      case 31:
        entity.corners[1].z = value;
        break;

      case 12:
        entity.corners[2].x = value;
        break;

      case 22:
        entity.corners[2].y = value;
        break;

      case 32:
        entity.corners[2].z = value;
        break;

      case 13:
        entity.corners[3].x = value;
        break;

      case 23:
        entity.corners[3].y = value;
        break;

      case 33:
        entity.corners[3].z = value;
        break;

      case 39:
        entity.thickness = value;
        break;

      default:
        Object.assign(entity, (0, _common.default)(type, value));
        break;
    }

    return entity;
  }, {
    type: TYPE,
    corners: [{}, {}, {}, {}]
  });
};

exports.process = process;
var _default = {
  TYPE: TYPE,
  process: process
};
exports.default = _default;
},{"./common":12}],21:[function(require,module,exports){
"use strict";

Object.defineProperty(exports, "__esModule", {
  value: true
});
exports.default = exports.process = exports.TYPE = void 0;

var _common = _interopRequireDefault(require("./common"));

function _interopRequireDefault(obj) { return obj && obj.__esModule ? obj : { default: obj }; }

var TYPE = 'SPLINE';
exports.TYPE = TYPE;

var process = function process(tuples) {
  var controlPoint;
  return tuples.reduce(function (entity, tuple) {
    var type = tuple[0];
    var value = tuple[1];

    switch (type) {
      case 10:
        controlPoint = {
          x: value,
          y: 0
        };
        entity.controlPoints.push(controlPoint);
        break;

      case 20:
        controlPoint.y = value;
        break;

      case 30:
        controlPoint.z = value;
        break;

      case 40:
        entity.knots.push(value);
        break;

      case 42:
        entity.knotTolerance = value;
        break;

      case 43:
        entity.controlPointTolerance = value;
        break;

      case 44:
        entity.fitTolerance = value;
        break;

      case 70:
        // Spline flag (bit coded):
        // 1 = Closed spline
        // 2 = Periodic spline
        // 4 = Rational spline
        // 8 = Planar
        // 16 = Linear (planar bit is also set)
        entity.flag = value;
        entity.closed = (value & 1) === 1;
        break;

      case 71:
        entity.degree = value;
        break;

      case 72:
        entity.numberOfKnots = value;
        break;

      case 73:
        entity.numberOfControlPoints = value;
        break;

      case 74:
        entity.numberOfFitPoints = value;
        break;

      default:
        Object.assign(entity, (0, _common.default)(type, value));
        break;
    }

    return entity;
  }, {
    type: TYPE,
    controlPoints: [],
    knots: []
  });
};

exports.process = process;
var _default = {
  TYPE: TYPE,
  process: process
};
exports.default = _default;
},{"./common":12}],22:[function(require,module,exports){
"use strict";

Object.defineProperty(exports, "__esModule", {
  value: true
});
exports.default = exports.process = exports.TYPE = void 0;
var TYPE = 'VERTEX';
exports.TYPE = TYPE;

var process = function process(tuples) {
  return tuples.reduce(function (entity, tuple) {
    var type = tuple[0];
    var value = tuple[1];

    switch (type) {
      case 10:
        entity.x = value;
        break;

      case 20:
        entity.y = value;
        break;

      case 30:
        entity.z = value;
        break;

      case 42:
        entity.bulge = value;
        break;

      default:
        break;
    }

    return entity;
  }, {});
};

exports.process = process;
var _default = {
  TYPE: TYPE,
  process: process
};
exports.default = _default;
},{}],23:[function(require,module,exports){
"use strict";

Object.defineProperty(exports, "__esModule", {
  value: true
});
exports.default = void 0;

var _default = function _default(tuples) {
  var state;
  var header = {};
  tuples.forEach(function (tuple) {
    var type = tuple[0];
    var value = tuple[1];

    switch (value) {
      case '$EXTMIN':
        header.extMin = {};
        state = 'extMin';
        return;

      case '$EXTMAX':
        header.extMax = {};
        state = 'extMax';
        return;

      default:
        if (state === 'extMin') {
          switch (type) {
            case 10:
              header.extMin.x = value;
              break;

            case 20:
              header.extMin.y = value;
              break;

            case 30:
              header.extMin.z = value;
              state = undefined;
              break;
          }
        }

        if (state === 'extMax') {
          switch (type) {
            case 10:
              header.extMax.x = value;
              break;

            case 20:
              header.extMax.y = value;
              break;

            case 30:
              header.extMax.z = value;
              state = undefined;
              break;
          }
        }

    }
  });
  return header;
};

exports.default = _default;
},{}],24:[function(require,module,exports){
"use strict";

Object.defineProperty(exports, "__esModule", {
  value: true
});
exports.default = void 0;

var _logger = _interopRequireDefault(require("../util/logger"));

function _interopRequireDefault(obj) { return obj && obj.__esModule ? obj : { default: obj }; }

var layerHandler = function layerHandler(tuples) {
  return tuples.reduce(function (layer, tuple) {
    var type = tuple[0];
    var value = tuple[1]; // https://www.autodesk.com/techpubs/autocad/acad2000/dxf/layer_dxf_04.htm

    switch (type) {
      case 2:
        layer.name = value;
        break;

      case 6:
        layer.lineTypeName = value;
        break;

      case 62:
        layer.colorNumber = value;
        break;

      case 70:
        layer.flags = value;
        break;

      case 290:
        layer.plot = parseInt(value) !== 0;
        break;

      case 370:
        layer.lineWeightEnum = value;
        break;

      default:
    }

    return layer;
  }, {
    type: 'LAYER'
  });
};

var styleHandler = function styleHandler(tuples) {
  return tuples.reduce(function (style, tuple) {
    var type = tuple[0];
    var value = tuple[1];

    switch (type) {
      case 2:
        style.name = value;
        break;

      case 6:
        style.lineTypeName = value;
        break;

      case 40:
        style.fixedTextHeight = value;
        break;

      case 41:
        style.widthFactor = value;
        break;

      case 50:
        style.obliqueAngle = value;
        break;

      case 71:
        style.flags = value;
        break;

      case 42:
        style.lastHeightUsed = value;
        break;

      case 3:
        style.primaryFontFileName = value;
        break;

      case 4:
        style.bigFontFileName = value;
        break;

      default:
    }

    return style;
  }, {
    type: 'STYLE'
  });
};

var tableHandler = function tableHandler(tuples, tableType, handler) {
  var tableRowsTuples = [];
  var tableRowTuples;
  tuples.forEach(function (tuple) {
    var type = tuple[0];
    var value = tuple[1];

    if ((type === 0 || type === 2) && value === tableType) {
      tableRowTuples = [];
      tableRowsTuples.push(tableRowTuples);
    } else {
      tableRowTuples.push(tuple);
    }
  });
  return tableRowsTuples.reduce(function (acc, rowTuples) {
    var tableRow = handler(rowTuples);

    if (tableRow.name) {
      acc[tableRow.name] = tableRow;
    } else {
      _logger.default.warn('table row without name:', tableRow);
    }

    return acc;
  }, {});
};

var _default = function _default(tuples) {
  var tableGroups = [];
  var tableTuples;
  tuples.forEach(function (tuple) {
    // const type = tuple[0];
    var value = tuple[1];

    if (value === 'TABLE') {
      tableTuples = [];
      tableGroups.push(tableTuples);
    } else if (value === 'ENDTAB') {
      tableGroups.push(tableTuples);
    } else {
      tableTuples.push(tuple);
    }
  });
  var stylesTuples = [];
  var layersTuples = [];
  tableGroups.forEach(function (group) {
    if (group[0][1] === 'STYLE') {
      stylesTuples = group;
    } else if (group[0][1] === 'LTYPE') {
      _logger.default.warn('LTYPE in tables not supported');
    } else if (group[0][1] === 'LAYER') {
      layersTuples = group;
    }
  });
  return {
    layers: tableHandler(layersTuples, 'LAYER', layerHandler),
    styles: tableHandler(stylesTuples, 'STYLE', styleHandler)
  };
};

exports.default = _default;
},{"../util/logger":33}],25:[function(require,module,exports){
"use strict";

Object.defineProperty(exports, "__esModule", {
  value: true
});
Object.defineProperty(exports, "config", {
  enumerable: true,
  get: function get() {
    return _config.default;
  }
});
Object.defineProperty(exports, "parseString", {
  enumerable: true,
  get: function get() {
    return _parseString.default;
  }
});
Object.defineProperty(exports, "denormalise", {
  enumerable: true,
  get: function get() {
    return _denormalise.default;
  }
});
Object.defineProperty(exports, "groupEntitiesByLayer", {
  enumerable: true,
  get: function get() {
    return _groupEntitiesByLayer.default;
  }
});
Object.defineProperty(exports, "toPolylines", {
  enumerable: true,
  get: function get() {
    return _toPolylines.default;
  }
});
Object.defineProperty(exports, "toSVG", {
  enumerable: true,
  get: function get() {
    return _toSVG.default;
  }
});
Object.defineProperty(exports, "colors", {
  enumerable: true,
  get: function get() {
    return _colors.default;
  }
});
Object.defineProperty(exports, "Helper", {
  enumerable: true,
  get: function get() {
    return _Helper.default;
  }
});

var _config = _interopRequireDefault(require("./config"));

var _parseString = _interopRequireDefault(require("./parseString"));

var _denormalise = _interopRequireDefault(require("./denormalise"));

var _groupEntitiesByLayer = _interopRequireDefault(require("./groupEntitiesByLayer"));

var _toPolylines = _interopRequireDefault(require("./toPolylines"));

var _toSVG = _interopRequireDefault(require("./toSVG"));

var _colors = _interopRequireDefault(require("./util/colors"));

var _Helper = _interopRequireDefault(require("./Helper"));

function _interopRequireDefault(obj) { return obj && obj.__esModule ? obj : { default: obj }; }
},{"./Helper":1,"./config":3,"./denormalise":4,"./groupEntitiesByLayer":7,"./parseString":26,"./toPolylines":27,"./toSVG":28,"./util/colors":31}],26:[function(require,module,exports){
"use strict";

Object.defineProperty(exports, "__esModule", {
  value: true
});
exports.default = void 0;

var _header = _interopRequireDefault(require("./handlers/header"));

var _tables = _interopRequireDefault(require("./handlers/tables"));

var _blocks = _interopRequireDefault(require("./handlers/blocks"));

var _entities = _interopRequireDefault(require("./handlers/entities"));

function _interopRequireDefault(obj) { return obj && obj.__esModule ? obj : { default: obj }; }

// Parse the value into the native representation
var parseValue = function parseValue(type, value) {
  if (type >= 10 && type < 60) {
    return parseFloat(value, 10);
  } else if (type >= 210 && type < 240) {
    return parseFloat(value, 10);
  } else if (type >= 60 && type < 100) {
    return parseInt(value, 10);
  } else {
    return value;
  }
}; // Content lines are alternate lines of type and value


var convertToTypesAndValues = function convertToTypesAndValues(contentLines) {
  var state = 'type';
  var type;
  var typesAndValues = [];
  var _iteratorNormalCompletion = true;
  var _didIteratorError = false;
  var _iteratorError = undefined;

  try {
    for (var _iterator = contentLines[Symbol.iterator](), _step; !(_iteratorNormalCompletion = (_step = _iterator.next()).done); _iteratorNormalCompletion = true) {
      var line = _step.value;

      if (state === 'type') {
        type = parseInt(line, 10);
        state = 'value';
      } else {
        typesAndValues.push([type, parseValue(type, line)]);
        state = 'type';
      }
    }
  } catch (err) {
    _didIteratorError = true;
    _iteratorError = err;
  } finally {
    try {
      if (!_iteratorNormalCompletion && _iterator.return != null) {
        _iterator.return();
      }
    } finally {
      if (_didIteratorError) {
        throw _iteratorError;
      }
    }
  }

  return typesAndValues;
};

var separateSections = function separateSections(tuples) {
  var sectionTuples;
  return tuples.reduce(function (sections, tuple) {
    if (tuple[0] === 0 && tuple[1] === 'SECTION') {
      sectionTuples = [];
    } else if (tuple[0] === 0 && tuple[1] === 'ENDSEC') {
      sections.push(sectionTuples);
      sectionTuples = undefined;
    } else if (sectionTuples !== undefined) {
      sectionTuples.push(tuple);
    }

    return sections;
  }, []);
}; // Each section start with the type tuple, then proceeds
// with the contents of the section


var reduceSection = function reduceSection(acc, section) {
  var sectionType = section[0][1];
  var contentTuples = section.slice(1);

  switch (sectionType) {
    case 'HEADER':
      acc.header = (0, _header.default)(contentTuples);
      break;

    case 'TABLES':
      acc.tables = (0, _tables.default)(contentTuples);
      break;

    case 'BLOCKS':
      acc.blocks = (0, _blocks.default)(contentTuples);
      break;

    case 'ENTITIES':
      acc.entities = (0, _entities.default)(contentTuples);
      break;

    default:
  }

  return acc;
};

var _default = function _default(string) {
  var lines = string.split(/\r\n|\r|\n/g);
  var tuples = convertToTypesAndValues(lines);
  var sections = separateSections(tuples);
  var result = sections.reduce(reduceSection, {
    // Start with empty defaults in the event of empty sections
    header: {},
    blocks: [],
    entities: [],
    tables: {
      layers: {},
      styles: {}
    }
  });
  return result;
};

exports.default = _default;
},{"./handlers/blocks":8,"./handlers/entities":9,"./handlers/header":23,"./handlers/tables":24}],27:[function(require,module,exports){
"use strict";

Object.defineProperty(exports, "__esModule", {
  value: true
});
exports.default = void 0;

var _vecks = require("vecks");

var _colors = _interopRequireDefault(require("./util/colors"));

var _denormalise = _interopRequireDefault(require("./denormalise"));

var _entityToPolyline = _interopRequireDefault(require("./entityToPolyline"));

var _applyTransforms = _interopRequireDefault(require("./applyTransforms"));

var _logger = _interopRequireDefault(require("./util/logger"));

function _interopRequireDefault(obj) { return obj && obj.__esModule ? obj : { default: obj }; }

var _default = function _default(parsed) {
  var entities = (0, _denormalise.default)(parsed);
  var polylines = entities.map(function (entity) {
    var layerTable = parsed.tables.layers[entity.layer];
    var rgb;

    if (layerTable) {
      var colorNumber = 'colorNumber' in entity ? entity.colorNumber : layerTable.colorNumber;
      rgb = _colors.default[colorNumber];

      if (rgb === undefined) {
        _logger.default.warn('Color index', colorNumber, 'invalid, defaulting to black');

        rgb = [0, 0, 0];
      }
    } else {
      _logger.default.warn('no layer table for layer:' + entity.layer);

      rgb = [0, 0, 0];
    }

    return {
      rgb: rgb,
      vertices: (0, _applyTransforms.default)((0, _entityToPolyline.default)(entity), entity.transforms)
    };
  });
  var bbox = new _vecks.Box2();
  polylines.forEach(function (polyline) {
    polyline.vertices.forEach(function (vertex) {
      bbox.expandByPoint({
        x: vertex[0],
        y: vertex[1]
      });
    });
  });
  return {
    bbox: bbox,
    polylines: polylines
  };
};

exports.default = _default;
},{"./applyTransforms":2,"./denormalise":4,"./entityToPolyline":5,"./util/colors":31,"./util/logger":33,"vecks":47}],28:[function(require,module,exports){
"use strict";

Object.defineProperty(exports, "__esModule", {
  value: true
});
exports.default = void 0;

var _prettyData = require("pretty-data");

var _vecks = require("vecks");

var _entityToPolyline = _interopRequireDefault(require("./entityToPolyline"));

var _denormalise = _interopRequireDefault(require("./denormalise"));

var _getRGBForEntity = _interopRequireDefault(require("./getRGBForEntity"));

var _logger = _interopRequireDefault(require("./util/logger"));

var _rotate = _interopRequireDefault(require("./util/rotate"));

var _rgbToColorAttribute = _interopRequireDefault(require("./util/rgbToColorAttribute"));

var _transformBoundingBoxAndElement = _interopRequireDefault(require("./transformBoundingBoxAndElement"));

function _interopRequireDefault(obj) { return obj && obj.__esModule ? obj : { default: obj }; }

function _slicedToArray(arr, i) { return _arrayWithHoles(arr) || _iterableToArrayLimit(arr, i) || _nonIterableRest(); }

function _nonIterableRest() { throw new TypeError("Invalid attempt to destructure non-iterable instance"); }

function _iterableToArrayLimit(arr, i) { var _arr = []; var _n = true; var _d = false; var _e = undefined; try { for (var _i = arr[Symbol.iterator](), _s; !(_n = (_s = _i.next()).done); _n = true) { _arr.push(_s.value); if (i && _arr.length === i) break; } } catch (err) { _d = true; _e = err; } finally { try { if (!_n && _i["return"] != null) _i["return"](); } finally { if (_d) throw _e; } } return _arr; }

function _arrayWithHoles(arr) { if (Array.isArray(arr)) return arr; }

/**
 * Create a <path /> element. Interpolates curved entities.
 */
var polyline = function polyline(entity) {
  var vertices = (0, _entityToPolyline.default)(entity);
  var bbox = vertices.reduce(function (acc, _ref) {
    var _ref2 = _slicedToArray(_ref, 2),
        x = _ref2[0],
        y = _ref2[1];

    return acc.expandByPoint({
      x: x,
      y: y
    });
  }, new _vecks.Box2());
  var d = vertices.reduce(function (acc, point, i) {
    acc += i === 0 ? 'M' : 'L';
    acc += point[0] + ',' + point[1];
    return acc;
  }, '');
  var element = "<path d=\"".concat(d, "\" fill=\"none\" />");
  return (0, _transformBoundingBoxAndElement.default)(bbox, element, entity.transforms);
};
/**
 * Create a <circle /> element for the CIRCLE entity.
 */


var circle = function circle(entity) {
  var bbox = new _vecks.Box2().expandByPoint({
    x: entity.x + entity.r,
    y: entity.y + entity.r
  }).expandByPoint({
    x: entity.x - entity.r,
    y: entity.y - entity.r
  });
  var element = "<circle cx=\"".concat(entity.x, "\" cy=\"").concat(entity.y, "\" r=\"").concat(entity.r, "\" fill=\"none\" />");
  return (0, _transformBoundingBoxAndElement.default)(bbox, element, entity.transforms);
};
/**
 * Create a a <path d="A..." /> or <ellipse /> element for the ARC or ELLIPSE
 * DXF entity (<ellipse /> if start and end point are the same).
 */


var ellipseOrArc = function ellipseOrArc(cx, cy, rx, ry, startAngle, endAngle, rotationAngle) {
  var bbox = [{
    x: rx,
    y: ry
  }, {
    x: rx,
    y: ry
  }, {
    x: -rx,
    y: -ry
  }, {
    x: -rx,
    y: ry
  }].reduce(function (acc, p) {
    var rotated = (0, _rotate.default)(p, rotationAngle);
    acc.expandByPoint({
      x: cx + rotated.x,
      y: cy + rotated.y
    });
    return acc;
  }, new _vecks.Box2());

  if (Math.abs(startAngle - endAngle) < 1e-9 || Math.abs(startAngle - endAngle + Math.PI * 2) < 1e-9) {
    // Use a native <ellipse> when start and end angles are the same, and
    // arc paths with same start and end points don't render (at least on Safari)
    var element = "<g transform=\"rotate(".concat(rotationAngle / Math.PI * 180, " ").concat(cx, ", ").concat(cy, ")\">\n      <ellipse cx=\"").concat(cx, "\" cy=\"").concat(cy, "\" rx=\"").concat(rx, "\" ry=\"").concat(ry, "\" fill=\"none\" />\n    </g>");
    return {
      bbox: bbox,
      element: element
    };
  } else {
    var startOffset = (0, _rotate.default)({
      x: Math.cos(startAngle) * rx,
      y: Math.sin(startAngle) * ry
    }, rotationAngle);
    var startPoint = {
      x: cx + startOffset.x,
      y: cy + startOffset.y
    };
    var endOffset = (0, _rotate.default)({
      x: Math.cos(endAngle) * rx,
      y: Math.sin(endAngle) * ry
    }, rotationAngle);
    var endPoint = {
      x: cx + endOffset.x,
      y: cy + endOffset.y
    };
    var adjustedEndAngle = endAngle < startAngle ? endAngle + Math.PI * 2 : endAngle;
    var largeArcFlag = adjustedEndAngle - startAngle < Math.PI ? 0 : 1;
    var d = "M ".concat(startPoint.x, " ").concat(startPoint.y, " A ").concat(rx, " ").concat(ry, " ").concat(rotationAngle / Math.PI * 180, " ").concat(largeArcFlag, " 1 ").concat(endPoint.x, " ").concat(endPoint.y);

    var _element = "<path d=\"".concat(d, "\" fill=\"none\" />");

    return {
      bbox: bbox,
      element: _element
    };
  }
};
/**
 * An ELLIPSE is defined by the major axis, convert to X and Y radius with
 * a rotation angle
 */


var ellipse = function ellipse(entity) {
  var rx = Math.sqrt(entity.majorX * entity.majorX + entity.majorY * entity.majorY);
  var ry = entity.axisRatio * rx;
  var majorAxisRotation = -Math.atan2(-entity.majorY, entity.majorX);

  var _ellipseOrArc = ellipseOrArc(entity.x, entity.y, rx, ry, entity.startAngle, entity.endAngle, majorAxisRotation),
      bbox = _ellipseOrArc.bbox,
      element = _ellipseOrArc.element;

  return (0, _transformBoundingBoxAndElement.default)(bbox, element, entity.transforms);
};
/**
 * An ARC is an ellipse with equal radii
 */


var arc = function arc(entity) {
  var _ellipseOrArc2 = ellipseOrArc(entity.x, entity.y, entity.r, entity.r, entity.startAngle, entity.endAngle, 0),
      bbox = _ellipseOrArc2.bbox,
      element = _ellipseOrArc2.element;

  return (0, _transformBoundingBoxAndElement.default)(bbox, element, entity.transforms);
};
/**
 * Switcth the appropriate function on entity type. CIRCLE, ARC and ELLIPSE
 * produce native SVG elements, the rest produce interpolated polylines.
 */


var entityToBoundsAndElement = function entityToBoundsAndElement(entity) {
  switch (entity.type) {
    case 'CIRCLE':
      return circle(entity);

    case 'ELLIPSE':
      return ellipse(entity);

    case 'ARC':
      return arc(entity);

    case 'LINE':
    case 'LWPOLYLINE':
    case 'SPLINE':
    case 'POLYLINE':
      {
        return polyline(entity);
      }

    default:
      _logger.default.warn('entity type not supported in SVG rendering:', entity.type);

      return null;
  }
};

var _default = function _default(parsed) {
  var entities = (0, _denormalise.default)(parsed);

  var _entities$reduce = entities.reduce(function (acc, entity) {
    var rgb = (0, _getRGBForEntity.default)(parsed.tables.layers, entity);
    var boundsAndElement = entityToBoundsAndElement(entity); // Ignore entities like MTEXT that don't produce SVG elements

    if (boundsAndElement) {
      var _bbox = boundsAndElement.bbox,
          element = boundsAndElement.element;
      acc.bbox.expandByPoint(_bbox.min);
      acc.bbox.expandByPoint(_bbox.max);
      acc.elements.push("<g stroke=\"".concat((0, _rgbToColorAttribute.default)(rgb), "\">").concat(element, "</g>"));
    }

    return acc;
  }, {
    bbox: new _vecks.Box2(),
    elements: []
  }),
      bbox = _entities$reduce.bbox,
      elements = _entities$reduce.elements; // V3.2.3 MrBeam modification START
  // svgString += ' viewBox="' + [bbox.minX, -bbox.maxY, bbox.width, bbox.height].join(' ') + '"'
  // svgString += ' width="' + bbox.width + '" height="' + bbox.height + '">'
  // svgString += '<!-- Created with dxf.js -->'
  // svgString += paths.join('') + '</svg>'
  // MrBeam modification END


  var viewBox = bbox.min.x === Infinity ? {
    x: 0,
    y: 0,
    width: 0,
    height: 0
  } : {
    x: bbox.min.x,
    y: -bbox.max.y,
    width: bbox.max.x - bbox.min.x,
    height: bbox.max.y - bbox.min.y
  };
  return "<?xml version=\"1.0\"?>\n<svg\n  xmlns=\"http://www.w3.org/2000/svg\"\n  xmlns:xlink=\"http://www.w3.org/1999/xlink\" version=\"1.1\"\n  preserveAspectRatio=\"xMinYMin meet\"\n  viewBox=\"".concat(viewBox.x, " ").concat(viewBox.y, " ").concat(viewBox.width, " ").concat(viewBox.height, "\"\n  width=\"100%\" height=\"100%\"\n><!-- Created with mrbeam/dxf.js -->\n  <g class=\"dxf-import\">\n    ").concat(_prettyData.pd.xml(elements.join('\n')), "\n  </g>\n</svg>");
};

exports.default = _default;
},{"./denormalise":4,"./entityToPolyline":5,"./getRGBForEntity":6,"./transformBoundingBoxAndElement":29,"./util/logger":33,"./util/rgbToColorAttribute":34,"./util/rotate":35,"pretty-data":37,"vecks":47}],29:[function(require,module,exports){
"use strict";

Object.defineProperty(exports, "__esModule", {
  value: true
});
exports.default = void 0;

var _vecks = require("vecks");

function _slicedToArray(arr, i) { return _arrayWithHoles(arr) || _iterableToArrayLimit(arr, i) || _nonIterableRest(); }

function _nonIterableRest() { throw new TypeError("Invalid attempt to destructure non-iterable instance"); }

function _iterableToArrayLimit(arr, i) { var _arr = []; var _n = true; var _d = false; var _e = undefined; try { for (var _i = arr[Symbol.iterator](), _s; !(_n = (_s = _i.next()).done); _n = true) { _arr.push(_s.value); if (i && _arr.length === i) break; } } catch (err) { _d = true; _e = err; } finally { try { if (!_n && _i["return"] != null) _i["return"](); } finally { if (_d) throw _e; } } return _arr; }

function _arrayWithHoles(arr) { if (Array.isArray(arr)) return arr; }

/**
 * Transform the bounding box and the SVG element by the given
 * transforms. The <g> element are created in reverse transform
 * order and the bounding box in the given order.
 */
var _default = function _default(bbox, element, transforms) {
  var transformedElement = '';
  var matrices = transforms.map(function (transform) {
    // Create the transformation matrix
    var tx = transform.x || 0;
    var ty = transform.y || 0;
    var sx = transform.scaleX || 1;
    var sy = transform.scaleY || 1;
    var angle = (transform.rotation || 0) / 180 * Math.PI;
    var cos = Math.cos,
        sin = Math.sin;
    var a, b, c, d, e, f; // In DXF an extrusionZ value of -1 denote a tranform around the Y axis.

    if (transform.extrusionZ === -1) {
      a = -sx * cos(angle);
      b = sx * sin(angle);
      c = sy * sin(angle);
      d = sy * cos(angle);
      e = -tx;
      f = ty;
    } else {
      a = sx * cos(angle);
      b = sx * sin(angle);
      c = -sy * sin(angle);
      d = sy * cos(angle);
      e = tx;
      f = ty;
    }

    return [a, b, c, d, e, f];
  });
  var bboxPoints = [{
    x: bbox.min.x,
    y: bbox.min.y
  }, {
    x: bbox.max.x,
    y: bbox.min.y
  }, {
    x: bbox.max.x,
    y: bbox.max.y
  }, {
    x: bbox.min.x,
    y: bbox.max.y
  }];
  matrices.forEach(function (_ref) {
    var _ref2 = _slicedToArray(_ref, 6),
        a = _ref2[0],
        b = _ref2[1],
        c = _ref2[2],
        d = _ref2[3],
        e = _ref2[4],
        f = _ref2[5];

    bboxPoints = bboxPoints.map(function (point) {
      return {
        x: point.x * a + point.y * c + e,
        y: point.x * b + point.y * d + f
      };
    });
  });
  var transformedBBox = bboxPoints.reduce(function (acc, point) {
    return acc.expandByPoint(point);
  }, new _vecks.Box2());
  matrices.reverse();
  matrices.forEach(function (_ref3) {
    var _ref4 = _slicedToArray(_ref3, 6),
        a = _ref4[0],
        b = _ref4[1],
        c = _ref4[2],
        d = _ref4[3],
        e = _ref4[4],
        f = _ref4[5];

    transformedElement += "<g transform=\"matrix(".concat(a, " ").concat(b, " ").concat(c, " ").concat(d, " ").concat(e, " ").concat(f, ")\">");
  });
  transformedElement += element;
  matrices.forEach(function (transform) {
    transformedElement += '</g>';
  });
  return {
    bbox: transformedBBox,
    element: transformedElement
  };
};

exports.default = _default;
},{"vecks":47}],30:[function(require,module,exports){
"use strict";

Object.defineProperty(exports, "__esModule", {
  value: true
});
exports.default = void 0;

var _round = require("round10");

/**
 * Copied and ported to code standard as the b-spline library is not maintained any longer.
 * Source:
 * https://github.com/thibauts/b-spline
 * Copyright (c) 2015 Thibaut Séguy <thibaut.seguy@gmail.com>
 */
var _default = function _default(t, degree, points, knots, weights) {
  var n = points.length; // points count

  var d = points[0].length; // point dimensionality

  if (t < 0 || t > 1) {
    throw new Error('t out of bounds [0,1]: ' + t);
  }

  if (degree < 1) throw new Error('degree must be at least 1 (linear)');
  if (degree > n - 1) throw new Error('degree must be less than or equal to point count - 1');

  if (!weights) {
    // build weight vector of length [n]
    weights = [];

    for (var i = 0; i < n; i++) {
      weights[i] = 1;
    }
  }

  if (!knots) {
    // build knot vector of length [n + degree + 1]
    knots = [];

    for (var _i = 0; _i < n + degree + 1; _i++) {
      knots[_i] = _i;
    }
  } else {
    if (knots.length !== n + degree + 1) throw new Error('bad knot vector length');
  }

  var domain = [degree, knots.length - 1 - degree]; // remap t to the domain where the spline is defined

  var low = knots[domain[0]];
  var high = knots[domain[1]];
  t = t * (high - low) + low;
  t = Math.max(t, low);
  t = Math.min(t, high); // find s (the spline segment) for the [t] value provided

  var s;

  for (s = domain[0]; s < domain[1]; s++) {
    if (t >= knots[s] && t <= knots[s + 1]) {
      break;
    }
  } // convert points to homogeneous coordinates


  var v = [];

  for (var _i2 = 0; _i2 < n; _i2++) {
    v[_i2] = [];

    for (var j = 0; j < d; j++) {
      v[_i2][j] = points[_i2][j] * weights[_i2];
    }

    v[_i2][d] = weights[_i2];
  } // l (level) goes from 1 to the curve degree + 1


  var alpha;

  for (var l = 1; l <= degree + 1; l++) {
    // build level l of the pyramid
    for (var _i3 = s; _i3 > s - degree - 1 + l; _i3--) {
      alpha = (t - knots[_i3]) / (knots[_i3 + degree + 1 - l] - knots[_i3]); // interpolate each component

      for (var _j = 0; _j < d + 1; _j++) {
        v[_i3][_j] = (1 - alpha) * v[_i3 - 1][_j] + alpha * v[_i3][_j];
      }
    }
  } // convert back to cartesian and return


  var result = [];

  for (var _i4 = 0; _i4 < d; _i4++) {
    result[_i4] = (0, _round.round10)(v[s][_i4] / v[s][d], -9);
  }

  return result;
};

exports.default = _default;
},{"round10":38}],31:[function(require,module,exports){
"use strict";

Object.defineProperty(exports, "__esModule", {
  value: true
});
exports.default = void 0;
var _default = [[0, 0, 0], [255, 0, 0], [255, 255, 0], [0, 255, 0], [0, 255, 255], [0, 0, 255], [255, 0, 255], [255, 255, 255], [65, 65, 65], [128, 128, 128], [255, 0, 0], [255, 170, 170], [189, 0, 0], [189, 126, 126], [129, 0, 0], [129, 86, 86], [104, 0, 0], [104, 69, 69], [79, 0, 0], [79, 53, 53], [255, 63, 0], [255, 191, 170], [189, 46, 0], [189, 141, 126], [129, 31, 0], [129, 96, 86], [104, 25, 0], [104, 78, 69], [79, 19, 0], [79, 59, 53], [255, 127, 0], [255, 212, 170], [189, 94, 0], [189, 157, 126], [129, 64, 0], [129, 107, 86], [104, 52, 0], [104, 86, 69], [79, 39, 0], [79, 66, 53], [255, 191, 0], [255, 234, 170], [189, 141, 0], [189, 173, 126], [129, 96, 0], [129, 118, 86], [104, 78, 0], [104, 95, 69], [79, 59, 0], [79, 73, 53], [255, 255, 0], [255, 255, 170], [189, 189, 0], [189, 189, 126], [129, 129, 0], [129, 129, 86], [104, 104, 0], [104, 104, 69], [79, 79, 0], [79, 79, 53], [191, 255, 0], [234, 255, 170], [141, 189, 0], [173, 189, 126], [96, 129, 0], [118, 129, 86], [78, 104, 0], [95, 104, 69], [59, 79, 0], [73, 79, 53], [127, 255, 0], [212, 255, 170], [94, 189, 0], [157, 189, 126], [64, 129, 0], [107, 129, 86], [52, 104, 0], [86, 104, 69], [39, 79, 0], [66, 79, 53], [63, 255, 0], [191, 255, 170], [46, 189, 0], [141, 189, 126], [31, 129, 0], [96, 129, 86], [25, 104, 0], [78, 104, 69], [19, 79, 0], [59, 79, 53], [0, 255, 0], [170, 255, 170], [0, 189, 0], [126, 189, 126], [0, 129, 0], [86, 129, 86], [0, 104, 0], [69, 104, 69], [0, 79, 0], [53, 79, 53], [0, 255, 63], [170, 255, 191], [0, 189, 46], [126, 189, 141], [0, 129, 31], [86, 129, 96], [0, 104, 25], [69, 104, 78], [0, 79, 19], [53, 79, 59], [0, 255, 127], [170, 255, 212], [0, 189, 94], [126, 189, 157], [0, 129, 64], [86, 129, 107], [0, 104, 52], [69, 104, 86], [0, 79, 39], [53, 79, 66], [0, 255, 191], [170, 255, 234], [0, 189, 141], [126, 189, 173], [0, 129, 96], [86, 129, 118], [0, 104, 78], [69, 104, 95], [0, 79, 59], [53, 79, 73], [0, 255, 255], [170, 255, 255], [0, 189, 189], [126, 189, 189], [0, 129, 129], [86, 129, 129], [0, 104, 104], [69, 104, 104], [0, 79, 79], [53, 79, 79], [0, 191, 255], [170, 234, 255], [0, 141, 189], [126, 173, 189], [0, 96, 129], [86, 118, 129], [0, 78, 104], [69, 95, 104], [0, 59, 79], [53, 73, 79], [0, 127, 255], [170, 212, 255], [0, 94, 189], [126, 157, 189], [0, 64, 129], [86, 107, 129], [0, 52, 104], [69, 86, 104], [0, 39, 79], [53, 66, 79], [0, 63, 255], [170, 191, 255], [0, 46, 189], [126, 141, 189], [0, 31, 129], [86, 96, 129], [0, 25, 104], [69, 78, 104], [0, 19, 79], [53, 59, 79], [0, 0, 255], [170, 170, 255], [0, 0, 189], [126, 126, 189], [0, 0, 129], [86, 86, 129], [0, 0, 104], [69, 69, 104], [0, 0, 79], [53, 53, 79], [63, 0, 255], [191, 170, 255], [46, 0, 189], [141, 126, 189], [31, 0, 129], [96, 86, 129], [25, 0, 104], [78, 69, 104], [19, 0, 79], [59, 53, 79], [127, 0, 255], [212, 170, 255], [94, 0, 189], [157, 126, 189], [64, 0, 129], [107, 86, 129], [52, 0, 104], [86, 69, 104], [39, 0, 79], [66, 53, 79], [191, 0, 255], [234, 170, 255], [141, 0, 189], [173, 126, 189], [96, 0, 129], [118, 86, 129], [78, 0, 104], [95, 69, 104], [59, 0, 79], [73, 53, 79], [255, 0, 255], [255, 170, 255], [189, 0, 189], [189, 126, 189], [129, 0, 129], [129, 86, 129], [104, 0, 104], [104, 69, 104], [79, 0, 79], [79, 53, 79], [255, 0, 191], [255, 170, 234], [189, 0, 141], [189, 126, 173], [129, 0, 96], [129, 86, 118], [104, 0, 78], [104, 69, 95], [79, 0, 59], [79, 53, 73], [255, 0, 127], [255, 170, 212], [189, 0, 94], [189, 126, 157], [129, 0, 64], [129, 86, 107], [104, 0, 52], [104, 69, 86], [79, 0, 39], [79, 53, 66], [255, 0, 63], [255, 170, 191], [189, 0, 46], [189, 126, 141], [129, 0, 31], [129, 86, 96], [104, 0, 25], [104, 69, 78], [79, 0, 19], [79, 53, 59], [51, 51, 51], [80, 80, 80], [105, 105, 105], [130, 130, 130], [190, 190, 190], [255, 255, 255]];
exports.default = _default;
},{}],32:[function(require,module,exports){
"use strict";

Object.defineProperty(exports, "__esModule", {
  value: true
});
exports.default = void 0;

var _vecks = require("vecks");

/**
 * Create the arcs point for a LWPOLYLINE. The start and end are excluded
 *
 * See diagram.png in this directory for description of points and angles used.
 */
var _default = function _default(from, to, bulge, resolution) {
  // Resolution in degrees
  if (!resolution) {
    resolution = 5;
  } // If the bulge is < 0, the arc goes clockwise. So we simply
  // reverse a and b and invert sign
  // Bulge = tan(theta/4)


  var theta;
  var a;
  var b;

  if (bulge < 0) {
    theta = Math.atan(-bulge) * 4;
    a = new _vecks.V2(from[0], from[1]);
    b = new _vecks.V2(to[0], to[1]);
  } else {
    // Default is counter-clockwise
    theta = Math.atan(bulge) * 4;
    a = new _vecks.V2(to[0], to[1]);
    b = new _vecks.V2(from[0], from[1]);
  }

  var ab = b.sub(a);
  var lengthAB = ab.length();
  var c = a.add(ab.multiply(0.5)); // Distance from center of arc to line between form and to points

  var lengthCD = Math.abs(lengthAB / 2 / Math.tan(theta / 2));
  var normAB = ab.norm();
  var d;

  if (theta < Math.PI) {
    var normDC = new _vecks.V2(normAB.x * Math.cos(Math.PI / 2) - normAB.y * Math.sin(Math.PI / 2), normAB.y * Math.cos(Math.PI / 2) + normAB.x * Math.sin(Math.PI / 2)); // D is the center of the arc

    d = c.add(normDC.multiply(-lengthCD));
  } else {
    var normCD = new _vecks.V2(normAB.x * Math.cos(Math.PI / 2) - normAB.y * Math.sin(Math.PI / 2), normAB.y * Math.cos(Math.PI / 2) + normAB.x * Math.sin(Math.PI / 2)); // D is the center of the arc

    d = c.add(normCD.multiply(lengthCD));
  } // Add points between start start and eng angle relative
  // to the center point


  var startAngle = Math.atan2(b.y - d.y, b.x - d.x) / Math.PI * 180;
  var endAngle = Math.atan2(a.y - d.y, a.x - d.x) / Math.PI * 180;

  if (endAngle < startAngle) {
    endAngle += 360;
  }

  var r = b.sub(d).length();
  var startInter = Math.floor(startAngle / resolution) * resolution + resolution;
  var endInter = Math.ceil(endAngle / resolution) * resolution - resolution;
  var points = [];

  for (var i = startInter; i <= endInter; i += resolution) {
    points.push(d.add(new _vecks.V2(Math.cos(i / 180 * Math.PI) * r, Math.sin(i / 180 * Math.PI) * r)));
  } // Maintain the right ordering to join the from and to points


  if (bulge < 0) {
    points.reverse();
  }

  return points.map(function (p) {
    return [p.x, p.y];
  });
};

exports.default = _default;
},{"vecks":47}],33:[function(require,module,exports){
"use strict";

Object.defineProperty(exports, "__esModule", {
  value: true
});
exports.default = void 0;

var _config = _interopRequireDefault(require("../config"));

function _interopRequireDefault(obj) { return obj && obj.__esModule ? obj : { default: obj }; }

function info() {
  if (_config.default.verbose) {
    console.info.apply(undefined, arguments);
  }
}

function warn() {
  if (_config.default.verbose) {
    console.warn.apply(undefined, arguments);
  }
}

function error() {
  console.error.apply(undefined, arguments);
}

var _default = {
  info: info,
  warn: warn,
  error: error
};
exports.default = _default;
},{"../config":3}],34:[function(require,module,exports){
"use strict";

Object.defineProperty(exports, "__esModule", {
  value: true
});
exports.default = void 0;

/**
 * Convert an RGB array to a CSS string definition.
 * Converts white lines to black as the default.
 */
var _default = function _default(rgb) {
  if (rgb[0] === 255 && rgb[1] === 255 && rgb[2] === 255) {
    return 'rgb(0, 0, 0)';
  } else {
    return "rgb(".concat(rgb[0], ", ").concat(rgb[1], ", ").concat(rgb[2], ")");
  }
};

exports.default = _default;
},{}],35:[function(require,module,exports){
"use strict";

Object.defineProperty(exports, "__esModule", {
  value: true
});
exports.default = void 0;

/**
 * Rotate a points by the given angle.
 *
 * @param points the points
 * @param angle the rotation angle
 */
var _default = function _default(p, angle) {
  return {
    x: p.x * Math.cos(angle) - p.y * Math.sin(angle),
    y: p.y * Math.cos(angle) + p.x * Math.sin(angle)
  };
};

exports.default = _default;
},{}],36:[function(require,module,exports){
(function (global){
/**
 * lodash (Custom Build) <https://lodash.com/>
 * Build: `lodash modularize exports="npm" -o ./`
 * Copyright jQuery Foundation and other contributors <https://jquery.org/>
 * Released under MIT license <https://lodash.com/license>
 * Based on Underscore.js 1.8.3 <http://underscorejs.org/LICENSE>
 * Copyright Jeremy Ashkenas, DocumentCloud and Investigative Reporters & Editors
 */

/** Used as the size to enable large array optimizations. */
var LARGE_ARRAY_SIZE = 200;

/** Used to stand-in for `undefined` hash values. */
var HASH_UNDEFINED = '__lodash_hash_undefined__';

/** Used as references for various `Number` constants. */
var MAX_SAFE_INTEGER = 9007199254740991;

/** `Object#toString` result references. */
var argsTag = '[object Arguments]',
    arrayTag = '[object Array]',
    boolTag = '[object Boolean]',
    dateTag = '[object Date]',
    errorTag = '[object Error]',
    funcTag = '[object Function]',
    genTag = '[object GeneratorFunction]',
    mapTag = '[object Map]',
    numberTag = '[object Number]',
    objectTag = '[object Object]',
    promiseTag = '[object Promise]',
    regexpTag = '[object RegExp]',
    setTag = '[object Set]',
    stringTag = '[object String]',
    symbolTag = '[object Symbol]',
    weakMapTag = '[object WeakMap]';

var arrayBufferTag = '[object ArrayBuffer]',
    dataViewTag = '[object DataView]',
    float32Tag = '[object Float32Array]',
    float64Tag = '[object Float64Array]',
    int8Tag = '[object Int8Array]',
    int16Tag = '[object Int16Array]',
    int32Tag = '[object Int32Array]',
    uint8Tag = '[object Uint8Array]',
    uint8ClampedTag = '[object Uint8ClampedArray]',
    uint16Tag = '[object Uint16Array]',
    uint32Tag = '[object Uint32Array]';

/**
 * Used to match `RegExp`
 * [syntax characters](http://ecma-international.org/ecma-262/7.0/#sec-patterns).
 */
var reRegExpChar = /[\\^$.*+?()[\]{}|]/g;

/** Used to match `RegExp` flags from their coerced string values. */
var reFlags = /\w*$/;

/** Used to detect host constructors (Safari). */
var reIsHostCtor = /^\[object .+?Constructor\]$/;

/** Used to detect unsigned integer values. */
var reIsUint = /^(?:0|[1-9]\d*)$/;

/** Used to identify `toStringTag` values supported by `_.clone`. */
var cloneableTags = {};
cloneableTags[argsTag] = cloneableTags[arrayTag] =
cloneableTags[arrayBufferTag] = cloneableTags[dataViewTag] =
cloneableTags[boolTag] = cloneableTags[dateTag] =
cloneableTags[float32Tag] = cloneableTags[float64Tag] =
cloneableTags[int8Tag] = cloneableTags[int16Tag] =
cloneableTags[int32Tag] = cloneableTags[mapTag] =
cloneableTags[numberTag] = cloneableTags[objectTag] =
cloneableTags[regexpTag] = cloneableTags[setTag] =
cloneableTags[stringTag] = cloneableTags[symbolTag] =
cloneableTags[uint8Tag] = cloneableTags[uint8ClampedTag] =
cloneableTags[uint16Tag] = cloneableTags[uint32Tag] = true;
cloneableTags[errorTag] = cloneableTags[funcTag] =
cloneableTags[weakMapTag] = false;

/** Detect free variable `global` from Node.js. */
var freeGlobal = typeof global == 'object' && global && global.Object === Object && global;

/** Detect free variable `self`. */
var freeSelf = typeof self == 'object' && self && self.Object === Object && self;

/** Used as a reference to the global object. */
var root = freeGlobal || freeSelf || Function('return this')();

/** Detect free variable `exports`. */
var freeExports = typeof exports == 'object' && exports && !exports.nodeType && exports;

/** Detect free variable `module`. */
var freeModule = freeExports && typeof module == 'object' && module && !module.nodeType && module;

/** Detect the popular CommonJS extension `module.exports`. */
var moduleExports = freeModule && freeModule.exports === freeExports;

/**
 * Adds the key-value `pair` to `map`.
 *
 * @private
 * @param {Object} map The map to modify.
 * @param {Array} pair The key-value pair to add.
 * @returns {Object} Returns `map`.
 */
function addMapEntry(map, pair) {
  // Don't return `map.set` because it's not chainable in IE 11.
  map.set(pair[0], pair[1]);
  return map;
}

/**
 * Adds `value` to `set`.
 *
 * @private
 * @param {Object} set The set to modify.
 * @param {*} value The value to add.
 * @returns {Object} Returns `set`.
 */
function addSetEntry(set, value) {
  // Don't return `set.add` because it's not chainable in IE 11.
  set.add(value);
  return set;
}

/**
 * A specialized version of `_.forEach` for arrays without support for
 * iteratee shorthands.
 *
 * @private
 * @param {Array} [array] The array to iterate over.
 * @param {Function} iteratee The function invoked per iteration.
 * @returns {Array} Returns `array`.
 */
function arrayEach(array, iteratee) {
  var index = -1,
      length = array ? array.length : 0;

  while (++index < length) {
    if (iteratee(array[index], index, array) === false) {
      break;
    }
  }
  return array;
}

/**
 * Appends the elements of `values` to `array`.
 *
 * @private
 * @param {Array} array The array to modify.
 * @param {Array} values The values to append.
 * @returns {Array} Returns `array`.
 */
function arrayPush(array, values) {
  var index = -1,
      length = values.length,
      offset = array.length;

  while (++index < length) {
    array[offset + index] = values[index];
  }
  return array;
}

/**
 * A specialized version of `_.reduce` for arrays without support for
 * iteratee shorthands.
 *
 * @private
 * @param {Array} [array] The array to iterate over.
 * @param {Function} iteratee The function invoked per iteration.
 * @param {*} [accumulator] The initial value.
 * @param {boolean} [initAccum] Specify using the first element of `array` as
 *  the initial value.
 * @returns {*} Returns the accumulated value.
 */
function arrayReduce(array, iteratee, accumulator, initAccum) {
  var index = -1,
      length = array ? array.length : 0;

  if (initAccum && length) {
    accumulator = array[++index];
  }
  while (++index < length) {
    accumulator = iteratee(accumulator, array[index], index, array);
  }
  return accumulator;
}

/**
 * The base implementation of `_.times` without support for iteratee shorthands
 * or max array length checks.
 *
 * @private
 * @param {number} n The number of times to invoke `iteratee`.
 * @param {Function} iteratee The function invoked per iteration.
 * @returns {Array} Returns the array of results.
 */
function baseTimes(n, iteratee) {
  var index = -1,
      result = Array(n);

  while (++index < n) {
    result[index] = iteratee(index);
  }
  return result;
}

/**
 * Gets the value at `key` of `object`.
 *
 * @private
 * @param {Object} [object] The object to query.
 * @param {string} key The key of the property to get.
 * @returns {*} Returns the property value.
 */
function getValue(object, key) {
  return object == null ? undefined : object[key];
}

/**
 * Checks if `value` is a host object in IE < 9.
 *
 * @private
 * @param {*} value The value to check.
 * @returns {boolean} Returns `true` if `value` is a host object, else `false`.
 */
function isHostObject(value) {
  // Many host objects are `Object` objects that can coerce to strings
  // despite having improperly defined `toString` methods.
  var result = false;
  if (value != null && typeof value.toString != 'function') {
    try {
      result = !!(value + '');
    } catch (e) {}
  }
  return result;
}

/**
 * Converts `map` to its key-value pairs.
 *
 * @private
 * @param {Object} map The map to convert.
 * @returns {Array} Returns the key-value pairs.
 */
function mapToArray(map) {
  var index = -1,
      result = Array(map.size);

  map.forEach(function(value, key) {
    result[++index] = [key, value];
  });
  return result;
}

/**
 * Creates a unary function that invokes `func` with its argument transformed.
 *
 * @private
 * @param {Function} func The function to wrap.
 * @param {Function} transform The argument transform.
 * @returns {Function} Returns the new function.
 */
function overArg(func, transform) {
  return function(arg) {
    return func(transform(arg));
  };
}

/**
 * Converts `set` to an array of its values.
 *
 * @private
 * @param {Object} set The set to convert.
 * @returns {Array} Returns the values.
 */
function setToArray(set) {
  var index = -1,
      result = Array(set.size);

  set.forEach(function(value) {
    result[++index] = value;
  });
  return result;
}

/** Used for built-in method references. */
var arrayProto = Array.prototype,
    funcProto = Function.prototype,
    objectProto = Object.prototype;

/** Used to detect overreaching core-js shims. */
var coreJsData = root['__core-js_shared__'];

/** Used to detect methods masquerading as native. */
var maskSrcKey = (function() {
  var uid = /[^.]+$/.exec(coreJsData && coreJsData.keys && coreJsData.keys.IE_PROTO || '');
  return uid ? ('Symbol(src)_1.' + uid) : '';
}());

/** Used to resolve the decompiled source of functions. */
var funcToString = funcProto.toString;

/** Used to check objects for own properties. */
var hasOwnProperty = objectProto.hasOwnProperty;

/**
 * Used to resolve the
 * [`toStringTag`](http://ecma-international.org/ecma-262/7.0/#sec-object.prototype.tostring)
 * of values.
 */
var objectToString = objectProto.toString;

/** Used to detect if a method is native. */
var reIsNative = RegExp('^' +
  funcToString.call(hasOwnProperty).replace(reRegExpChar, '\\$&')
  .replace(/hasOwnProperty|(function).*?(?=\\\()| for .+?(?=\\\])/g, '$1.*?') + '$'
);

/** Built-in value references. */
var Buffer = moduleExports ? root.Buffer : undefined,
    Symbol = root.Symbol,
    Uint8Array = root.Uint8Array,
    getPrototype = overArg(Object.getPrototypeOf, Object),
    objectCreate = Object.create,
    propertyIsEnumerable = objectProto.propertyIsEnumerable,
    splice = arrayProto.splice;

/* Built-in method references for those with the same name as other `lodash` methods. */
var nativeGetSymbols = Object.getOwnPropertySymbols,
    nativeIsBuffer = Buffer ? Buffer.isBuffer : undefined,
    nativeKeys = overArg(Object.keys, Object);

/* Built-in method references that are verified to be native. */
var DataView = getNative(root, 'DataView'),
    Map = getNative(root, 'Map'),
    Promise = getNative(root, 'Promise'),
    Set = getNative(root, 'Set'),
    WeakMap = getNative(root, 'WeakMap'),
    nativeCreate = getNative(Object, 'create');

/** Used to detect maps, sets, and weakmaps. */
var dataViewCtorString = toSource(DataView),
    mapCtorString = toSource(Map),
    promiseCtorString = toSource(Promise),
    setCtorString = toSource(Set),
    weakMapCtorString = toSource(WeakMap);

/** Used to convert symbols to primitives and strings. */
var symbolProto = Symbol ? Symbol.prototype : undefined,
    symbolValueOf = symbolProto ? symbolProto.valueOf : undefined;

/**
 * Creates a hash object.
 *
 * @private
 * @constructor
 * @param {Array} [entries] The key-value pairs to cache.
 */
function Hash(entries) {
  var index = -1,
      length = entries ? entries.length : 0;

  this.clear();
  while (++index < length) {
    var entry = entries[index];
    this.set(entry[0], entry[1]);
  }
}

/**
 * Removes all key-value entries from the hash.
 *
 * @private
 * @name clear
 * @memberOf Hash
 */
function hashClear() {
  this.__data__ = nativeCreate ? nativeCreate(null) : {};
}

/**
 * Removes `key` and its value from the hash.
 *
 * @private
 * @name delete
 * @memberOf Hash
 * @param {Object} hash The hash to modify.
 * @param {string} key The key of the value to remove.
 * @returns {boolean} Returns `true` if the entry was removed, else `false`.
 */
function hashDelete(key) {
  return this.has(key) && delete this.__data__[key];
}

/**
 * Gets the hash value for `key`.
 *
 * @private
 * @name get
 * @memberOf Hash
 * @param {string} key The key of the value to get.
 * @returns {*} Returns the entry value.
 */
function hashGet(key) {
  var data = this.__data__;
  if (nativeCreate) {
    var result = data[key];
    return result === HASH_UNDEFINED ? undefined : result;
  }
  return hasOwnProperty.call(data, key) ? data[key] : undefined;
}

/**
 * Checks if a hash value for `key` exists.
 *
 * @private
 * @name has
 * @memberOf Hash
 * @param {string} key The key of the entry to check.
 * @returns {boolean} Returns `true` if an entry for `key` exists, else `false`.
 */
function hashHas(key) {
  var data = this.__data__;
  return nativeCreate ? data[key] !== undefined : hasOwnProperty.call(data, key);
}

/**
 * Sets the hash `key` to `value`.
 *
 * @private
 * @name set
 * @memberOf Hash
 * @param {string} key The key of the value to set.
 * @param {*} value The value to set.
 * @returns {Object} Returns the hash instance.
 */
function hashSet(key, value) {
  var data = this.__data__;
  data[key] = (nativeCreate && value === undefined) ? HASH_UNDEFINED : value;
  return this;
}

// Add methods to `Hash`.
Hash.prototype.clear = hashClear;
Hash.prototype['delete'] = hashDelete;
Hash.prototype.get = hashGet;
Hash.prototype.has = hashHas;
Hash.prototype.set = hashSet;

/**
 * Creates an list cache object.
 *
 * @private
 * @constructor
 * @param {Array} [entries] The key-value pairs to cache.
 */
function ListCache(entries) {
  var index = -1,
      length = entries ? entries.length : 0;

  this.clear();
  while (++index < length) {
    var entry = entries[index];
    this.set(entry[0], entry[1]);
  }
}

/**
 * Removes all key-value entries from the list cache.
 *
 * @private
 * @name clear
 * @memberOf ListCache
 */
function listCacheClear() {
  this.__data__ = [];
}

/**
 * Removes `key` and its value from the list cache.
 *
 * @private
 * @name delete
 * @memberOf ListCache
 * @param {string} key The key of the value to remove.
 * @returns {boolean} Returns `true` if the entry was removed, else `false`.
 */
function listCacheDelete(key) {
  var data = this.__data__,
      index = assocIndexOf(data, key);

  if (index < 0) {
    return false;
  }
  var lastIndex = data.length - 1;
  if (index == lastIndex) {
    data.pop();
  } else {
    splice.call(data, index, 1);
  }
  return true;
}

/**
 * Gets the list cache value for `key`.
 *
 * @private
 * @name get
 * @memberOf ListCache
 * @param {string} key The key of the value to get.
 * @returns {*} Returns the entry value.
 */
function listCacheGet(key) {
  var data = this.__data__,
      index = assocIndexOf(data, key);

  return index < 0 ? undefined : data[index][1];
}

/**
 * Checks if a list cache value for `key` exists.
 *
 * @private
 * @name has
 * @memberOf ListCache
 * @param {string} key The key of the entry to check.
 * @returns {boolean} Returns `true` if an entry for `key` exists, else `false`.
 */
function listCacheHas(key) {
  return assocIndexOf(this.__data__, key) > -1;
}

/**
 * Sets the list cache `key` to `value`.
 *
 * @private
 * @name set
 * @memberOf ListCache
 * @param {string} key The key of the value to set.
 * @param {*} value The value to set.
 * @returns {Object} Returns the list cache instance.
 */
function listCacheSet(key, value) {
  var data = this.__data__,
      index = assocIndexOf(data, key);

  if (index < 0) {
    data.push([key, value]);
  } else {
    data[index][1] = value;
  }
  return this;
}

// Add methods to `ListCache`.
ListCache.prototype.clear = listCacheClear;
ListCache.prototype['delete'] = listCacheDelete;
ListCache.prototype.get = listCacheGet;
ListCache.prototype.has = listCacheHas;
ListCache.prototype.set = listCacheSet;

/**
 * Creates a map cache object to store key-value pairs.
 *
 * @private
 * @constructor
 * @param {Array} [entries] The key-value pairs to cache.
 */
function MapCache(entries) {
  var index = -1,
      length = entries ? entries.length : 0;

  this.clear();
  while (++index < length) {
    var entry = entries[index];
    this.set(entry[0], entry[1]);
  }
}

/**
 * Removes all key-value entries from the map.
 *
 * @private
 * @name clear
 * @memberOf MapCache
 */
function mapCacheClear() {
  this.__data__ = {
    'hash': new Hash,
    'map': new (Map || ListCache),
    'string': new Hash
  };
}

/**
 * Removes `key` and its value from the map.
 *
 * @private
 * @name delete
 * @memberOf MapCache
 * @param {string} key The key of the value to remove.
 * @returns {boolean} Returns `true` if the entry was removed, else `false`.
 */
function mapCacheDelete(key) {
  return getMapData(this, key)['delete'](key);
}

/**
 * Gets the map value for `key`.
 *
 * @private
 * @name get
 * @memberOf MapCache
 * @param {string} key The key of the value to get.
 * @returns {*} Returns the entry value.
 */
function mapCacheGet(key) {
  return getMapData(this, key).get(key);
}

/**
 * Checks if a map value for `key` exists.
 *
 * @private
 * @name has
 * @memberOf MapCache
 * @param {string} key The key of the entry to check.
 * @returns {boolean} Returns `true` if an entry for `key` exists, else `false`.
 */
function mapCacheHas(key) {
  return getMapData(this, key).has(key);
}

/**
 * Sets the map `key` to `value`.
 *
 * @private
 * @name set
 * @memberOf MapCache
 * @param {string} key The key of the value to set.
 * @param {*} value The value to set.
 * @returns {Object} Returns the map cache instance.
 */
function mapCacheSet(key, value) {
  getMapData(this, key).set(key, value);
  return this;
}

// Add methods to `MapCache`.
MapCache.prototype.clear = mapCacheClear;
MapCache.prototype['delete'] = mapCacheDelete;
MapCache.prototype.get = mapCacheGet;
MapCache.prototype.has = mapCacheHas;
MapCache.prototype.set = mapCacheSet;

/**
 * Creates a stack cache object to store key-value pairs.
 *
 * @private
 * @constructor
 * @param {Array} [entries] The key-value pairs to cache.
 */
function Stack(entries) {
  this.__data__ = new ListCache(entries);
}

/**
 * Removes all key-value entries from the stack.
 *
 * @private
 * @name clear
 * @memberOf Stack
 */
function stackClear() {
  this.__data__ = new ListCache;
}

/**
 * Removes `key` and its value from the stack.
 *
 * @private
 * @name delete
 * @memberOf Stack
 * @param {string} key The key of the value to remove.
 * @returns {boolean} Returns `true` if the entry was removed, else `false`.
 */
function stackDelete(key) {
  return this.__data__['delete'](key);
}

/**
 * Gets the stack value for `key`.
 *
 * @private
 * @name get
 * @memberOf Stack
 * @param {string} key The key of the value to get.
 * @returns {*} Returns the entry value.
 */
function stackGet(key) {
  return this.__data__.get(key);
}

/**
 * Checks if a stack value for `key` exists.
 *
 * @private
 * @name has
 * @memberOf Stack
 * @param {string} key The key of the entry to check.
 * @returns {boolean} Returns `true` if an entry for `key` exists, else `false`.
 */
function stackHas(key) {
  return this.__data__.has(key);
}

/**
 * Sets the stack `key` to `value`.
 *
 * @private
 * @name set
 * @memberOf Stack
 * @param {string} key The key of the value to set.
 * @param {*} value The value to set.
 * @returns {Object} Returns the stack cache instance.
 */
function stackSet(key, value) {
  var cache = this.__data__;
  if (cache instanceof ListCache) {
    var pairs = cache.__data__;
    if (!Map || (pairs.length < LARGE_ARRAY_SIZE - 1)) {
      pairs.push([key, value]);
      return this;
    }
    cache = this.__data__ = new MapCache(pairs);
  }
  cache.set(key, value);
  return this;
}

// Add methods to `Stack`.
Stack.prototype.clear = stackClear;
Stack.prototype['delete'] = stackDelete;
Stack.prototype.get = stackGet;
Stack.prototype.has = stackHas;
Stack.prototype.set = stackSet;

/**
 * Creates an array of the enumerable property names of the array-like `value`.
 *
 * @private
 * @param {*} value The value to query.
 * @param {boolean} inherited Specify returning inherited property names.
 * @returns {Array} Returns the array of property names.
 */
function arrayLikeKeys(value, inherited) {
  // Safari 8.1 makes `arguments.callee` enumerable in strict mode.
  // Safari 9 makes `arguments.length` enumerable in strict mode.
  var result = (isArray(value) || isArguments(value))
    ? baseTimes(value.length, String)
    : [];

  var length = result.length,
      skipIndexes = !!length;

  for (var key in value) {
    if ((inherited || hasOwnProperty.call(value, key)) &&
        !(skipIndexes && (key == 'length' || isIndex(key, length)))) {
      result.push(key);
    }
  }
  return result;
}

/**
 * Assigns `value` to `key` of `object` if the existing value is not equivalent
 * using [`SameValueZero`](http://ecma-international.org/ecma-262/7.0/#sec-samevaluezero)
 * for equality comparisons.
 *
 * @private
 * @param {Object} object The object to modify.
 * @param {string} key The key of the property to assign.
 * @param {*} value The value to assign.
 */
function assignValue(object, key, value) {
  var objValue = object[key];
  if (!(hasOwnProperty.call(object, key) && eq(objValue, value)) ||
      (value === undefined && !(key in object))) {
    object[key] = value;
  }
}

/**
 * Gets the index at which the `key` is found in `array` of key-value pairs.
 *
 * @private
 * @param {Array} array The array to inspect.
 * @param {*} key The key to search for.
 * @returns {number} Returns the index of the matched value, else `-1`.
 */
function assocIndexOf(array, key) {
  var length = array.length;
  while (length--) {
    if (eq(array[length][0], key)) {
      return length;
    }
  }
  return -1;
}

/**
 * The base implementation of `_.assign` without support for multiple sources
 * or `customizer` functions.
 *
 * @private
 * @param {Object} object The destination object.
 * @param {Object} source The source object.
 * @returns {Object} Returns `object`.
 */
function baseAssign(object, source) {
  return object && copyObject(source, keys(source), object);
}

/**
 * The base implementation of `_.clone` and `_.cloneDeep` which tracks
 * traversed objects.
 *
 * @private
 * @param {*} value The value to clone.
 * @param {boolean} [isDeep] Specify a deep clone.
 * @param {boolean} [isFull] Specify a clone including symbols.
 * @param {Function} [customizer] The function to customize cloning.
 * @param {string} [key] The key of `value`.
 * @param {Object} [object] The parent object of `value`.
 * @param {Object} [stack] Tracks traversed objects and their clone counterparts.
 * @returns {*} Returns the cloned value.
 */
function baseClone(value, isDeep, isFull, customizer, key, object, stack) {
  var result;
  if (customizer) {
    result = object ? customizer(value, key, object, stack) : customizer(value);
  }
  if (result !== undefined) {
    return result;
  }
  if (!isObject(value)) {
    return value;
  }
  var isArr = isArray(value);
  if (isArr) {
    result = initCloneArray(value);
    if (!isDeep) {
      return copyArray(value, result);
    }
  } else {
    var tag = getTag(value),
        isFunc = tag == funcTag || tag == genTag;

    if (isBuffer(value)) {
      return cloneBuffer(value, isDeep);
    }
    if (tag == objectTag || tag == argsTag || (isFunc && !object)) {
      if (isHostObject(value)) {
        return object ? value : {};
      }
      result = initCloneObject(isFunc ? {} : value);
      if (!isDeep) {
        return copySymbols(value, baseAssign(result, value));
      }
    } else {
      if (!cloneableTags[tag]) {
        return object ? value : {};
      }
      result = initCloneByTag(value, tag, baseClone, isDeep);
    }
  }
  // Check for circular references and return its corresponding clone.
  stack || (stack = new Stack);
  var stacked = stack.get(value);
  if (stacked) {
    return stacked;
  }
  stack.set(value, result);

  if (!isArr) {
    var props = isFull ? getAllKeys(value) : keys(value);
  }
  arrayEach(props || value, function(subValue, key) {
    if (props) {
      key = subValue;
      subValue = value[key];
    }
    // Recursively populate clone (susceptible to call stack limits).
    assignValue(result, key, baseClone(subValue, isDeep, isFull, customizer, key, value, stack));
  });
  return result;
}

/**
 * The base implementation of `_.create` without support for assigning
 * properties to the created object.
 *
 * @private
 * @param {Object} prototype The object to inherit from.
 * @returns {Object} Returns the new object.
 */
function baseCreate(proto) {
  return isObject(proto) ? objectCreate(proto) : {};
}

/**
 * The base implementation of `getAllKeys` and `getAllKeysIn` which uses
 * `keysFunc` and `symbolsFunc` to get the enumerable property names and
 * symbols of `object`.
 *
 * @private
 * @param {Object} object The object to query.
 * @param {Function} keysFunc The function to get the keys of `object`.
 * @param {Function} symbolsFunc The function to get the symbols of `object`.
 * @returns {Array} Returns the array of property names and symbols.
 */
function baseGetAllKeys(object, keysFunc, symbolsFunc) {
  var result = keysFunc(object);
  return isArray(object) ? result : arrayPush(result, symbolsFunc(object));
}

/**
 * The base implementation of `getTag`.
 *
 * @private
 * @param {*} value The value to query.
 * @returns {string} Returns the `toStringTag`.
 */
function baseGetTag(value) {
  return objectToString.call(value);
}

/**
 * The base implementation of `_.isNative` without bad shim checks.
 *
 * @private
 * @param {*} value The value to check.
 * @returns {boolean} Returns `true` if `value` is a native function,
 *  else `false`.
 */
function baseIsNative(value) {
  if (!isObject(value) || isMasked(value)) {
    return false;
  }
  var pattern = (isFunction(value) || isHostObject(value)) ? reIsNative : reIsHostCtor;
  return pattern.test(toSource(value));
}

/**
 * The base implementation of `_.keys` which doesn't treat sparse arrays as dense.
 *
 * @private
 * @param {Object} object The object to query.
 * @returns {Array} Returns the array of property names.
 */
function baseKeys(object) {
  if (!isPrototype(object)) {
    return nativeKeys(object);
  }
  var result = [];
  for (var key in Object(object)) {
    if (hasOwnProperty.call(object, key) && key != 'constructor') {
      result.push(key);
    }
  }
  return result;
}

/**
 * Creates a clone of  `buffer`.
 *
 * @private
 * @param {Buffer} buffer The buffer to clone.
 * @param {boolean} [isDeep] Specify a deep clone.
 * @returns {Buffer} Returns the cloned buffer.
 */
function cloneBuffer(buffer, isDeep) {
  if (isDeep) {
    return buffer.slice();
  }
  var result = new buffer.constructor(buffer.length);
  buffer.copy(result);
  return result;
}

/**
 * Creates a clone of `arrayBuffer`.
 *
 * @private
 * @param {ArrayBuffer} arrayBuffer The array buffer to clone.
 * @returns {ArrayBuffer} Returns the cloned array buffer.
 */
function cloneArrayBuffer(arrayBuffer) {
  var result = new arrayBuffer.constructor(arrayBuffer.byteLength);
  new Uint8Array(result).set(new Uint8Array(arrayBuffer));
  return result;
}

/**
 * Creates a clone of `dataView`.
 *
 * @private
 * @param {Object} dataView The data view to clone.
 * @param {boolean} [isDeep] Specify a deep clone.
 * @returns {Object} Returns the cloned data view.
 */
function cloneDataView(dataView, isDeep) {
  var buffer = isDeep ? cloneArrayBuffer(dataView.buffer) : dataView.buffer;
  return new dataView.constructor(buffer, dataView.byteOffset, dataView.byteLength);
}

/**
 * Creates a clone of `map`.
 *
 * @private
 * @param {Object} map The map to clone.
 * @param {Function} cloneFunc The function to clone values.
 * @param {boolean} [isDeep] Specify a deep clone.
 * @returns {Object} Returns the cloned map.
 */
function cloneMap(map, isDeep, cloneFunc) {
  var array = isDeep ? cloneFunc(mapToArray(map), true) : mapToArray(map);
  return arrayReduce(array, addMapEntry, new map.constructor);
}

/**
 * Creates a clone of `regexp`.
 *
 * @private
 * @param {Object} regexp The regexp to clone.
 * @returns {Object} Returns the cloned regexp.
 */
function cloneRegExp(regexp) {
  var result = new regexp.constructor(regexp.source, reFlags.exec(regexp));
  result.lastIndex = regexp.lastIndex;
  return result;
}

/**
 * Creates a clone of `set`.
 *
 * @private
 * @param {Object} set The set to clone.
 * @param {Function} cloneFunc The function to clone values.
 * @param {boolean} [isDeep] Specify a deep clone.
 * @returns {Object} Returns the cloned set.
 */
function cloneSet(set, isDeep, cloneFunc) {
  var array = isDeep ? cloneFunc(setToArray(set), true) : setToArray(set);
  return arrayReduce(array, addSetEntry, new set.constructor);
}

/**
 * Creates a clone of the `symbol` object.
 *
 * @private
 * @param {Object} symbol The symbol object to clone.
 * @returns {Object} Returns the cloned symbol object.
 */
function cloneSymbol(symbol) {
  return symbolValueOf ? Object(symbolValueOf.call(symbol)) : {};
}

/**
 * Creates a clone of `typedArray`.
 *
 * @private
 * @param {Object} typedArray The typed array to clone.
 * @param {boolean} [isDeep] Specify a deep clone.
 * @returns {Object} Returns the cloned typed array.
 */
function cloneTypedArray(typedArray, isDeep) {
  var buffer = isDeep ? cloneArrayBuffer(typedArray.buffer) : typedArray.buffer;
  return new typedArray.constructor(buffer, typedArray.byteOffset, typedArray.length);
}

/**
 * Copies the values of `source` to `array`.
 *
 * @private
 * @param {Array} source The array to copy values from.
 * @param {Array} [array=[]] The array to copy values to.
 * @returns {Array} Returns `array`.
 */
function copyArray(source, array) {
  var index = -1,
      length = source.length;

  array || (array = Array(length));
  while (++index < length) {
    array[index] = source[index];
  }
  return array;
}

/**
 * Copies properties of `source` to `object`.
 *
 * @private
 * @param {Object} source The object to copy properties from.
 * @param {Array} props The property identifiers to copy.
 * @param {Object} [object={}] The object to copy properties to.
 * @param {Function} [customizer] The function to customize copied values.
 * @returns {Object} Returns `object`.
 */
function copyObject(source, props, object, customizer) {
  object || (object = {});

  var index = -1,
      length = props.length;

  while (++index < length) {
    var key = props[index];

    var newValue = customizer
      ? customizer(object[key], source[key], key, object, source)
      : undefined;

    assignValue(object, key, newValue === undefined ? source[key] : newValue);
  }
  return object;
}

/**
 * Copies own symbol properties of `source` to `object`.
 *
 * @private
 * @param {Object} source The object to copy symbols from.
 * @param {Object} [object={}] The object to copy symbols to.
 * @returns {Object} Returns `object`.
 */
function copySymbols(source, object) {
  return copyObject(source, getSymbols(source), object);
}

/**
 * Creates an array of own enumerable property names and symbols of `object`.
 *
 * @private
 * @param {Object} object The object to query.
 * @returns {Array} Returns the array of property names and symbols.
 */
function getAllKeys(object) {
  return baseGetAllKeys(object, keys, getSymbols);
}

/**
 * Gets the data for `map`.
 *
 * @private
 * @param {Object} map The map to query.
 * @param {string} key The reference key.
 * @returns {*} Returns the map data.
 */
function getMapData(map, key) {
  var data = map.__data__;
  return isKeyable(key)
    ? data[typeof key == 'string' ? 'string' : 'hash']
    : data.map;
}

/**
 * Gets the native function at `key` of `object`.
 *
 * @private
 * @param {Object} object The object to query.
 * @param {string} key The key of the method to get.
 * @returns {*} Returns the function if it's native, else `undefined`.
 */
function getNative(object, key) {
  var value = getValue(object, key);
  return baseIsNative(value) ? value : undefined;
}

/**
 * Creates an array of the own enumerable symbol properties of `object`.
 *
 * @private
 * @param {Object} object The object to query.
 * @returns {Array} Returns the array of symbols.
 */
var getSymbols = nativeGetSymbols ? overArg(nativeGetSymbols, Object) : stubArray;

/**
 * Gets the `toStringTag` of `value`.
 *
 * @private
 * @param {*} value The value to query.
 * @returns {string} Returns the `toStringTag`.
 */
var getTag = baseGetTag;

// Fallback for data views, maps, sets, and weak maps in IE 11,
// for data views in Edge < 14, and promises in Node.js.
if ((DataView && getTag(new DataView(new ArrayBuffer(1))) != dataViewTag) ||
    (Map && getTag(new Map) != mapTag) ||
    (Promise && getTag(Promise.resolve()) != promiseTag) ||
    (Set && getTag(new Set) != setTag) ||
    (WeakMap && getTag(new WeakMap) != weakMapTag)) {
  getTag = function(value) {
    var result = objectToString.call(value),
        Ctor = result == objectTag ? value.constructor : undefined,
        ctorString = Ctor ? toSource(Ctor) : undefined;

    if (ctorString) {
      switch (ctorString) {
        case dataViewCtorString: return dataViewTag;
        case mapCtorString: return mapTag;
        case promiseCtorString: return promiseTag;
        case setCtorString: return setTag;
        case weakMapCtorString: return weakMapTag;
      }
    }
    return result;
  };
}

/**
 * Initializes an array clone.
 *
 * @private
 * @param {Array} array The array to clone.
 * @returns {Array} Returns the initialized clone.
 */
function initCloneArray(array) {
  var length = array.length,
      result = array.constructor(length);

  // Add properties assigned by `RegExp#exec`.
  if (length && typeof array[0] == 'string' && hasOwnProperty.call(array, 'index')) {
    result.index = array.index;
    result.input = array.input;
  }
  return result;
}

/**
 * Initializes an object clone.
 *
 * @private
 * @param {Object} object The object to clone.
 * @returns {Object} Returns the initialized clone.
 */
function initCloneObject(object) {
  return (typeof object.constructor == 'function' && !isPrototype(object))
    ? baseCreate(getPrototype(object))
    : {};
}

/**
 * Initializes an object clone based on its `toStringTag`.
 *
 * **Note:** This function only supports cloning values with tags of
 * `Boolean`, `Date`, `Error`, `Number`, `RegExp`, or `String`.
 *
 * @private
 * @param {Object} object The object to clone.
 * @param {string} tag The `toStringTag` of the object to clone.
 * @param {Function} cloneFunc The function to clone values.
 * @param {boolean} [isDeep] Specify a deep clone.
 * @returns {Object} Returns the initialized clone.
 */
function initCloneByTag(object, tag, cloneFunc, isDeep) {
  var Ctor = object.constructor;
  switch (tag) {
    case arrayBufferTag:
      return cloneArrayBuffer(object);

    case boolTag:
    case dateTag:
      return new Ctor(+object);

    case dataViewTag:
      return cloneDataView(object, isDeep);

    case float32Tag: case float64Tag:
    case int8Tag: case int16Tag: case int32Tag:
    case uint8Tag: case uint8ClampedTag: case uint16Tag: case uint32Tag:
      return cloneTypedArray(object, isDeep);

    case mapTag:
      return cloneMap(object, isDeep, cloneFunc);

    case numberTag:
    case stringTag:
      return new Ctor(object);

    case regexpTag:
      return cloneRegExp(object);

    case setTag:
      return cloneSet(object, isDeep, cloneFunc);

    case symbolTag:
      return cloneSymbol(object);
  }
}

/**
 * Checks if `value` is a valid array-like index.
 *
 * @private
 * @param {*} value The value to check.
 * @param {number} [length=MAX_SAFE_INTEGER] The upper bounds of a valid index.
 * @returns {boolean} Returns `true` if `value` is a valid index, else `false`.
 */
function isIndex(value, length) {
  length = length == null ? MAX_SAFE_INTEGER : length;
  return !!length &&
    (typeof value == 'number' || reIsUint.test(value)) &&
    (value > -1 && value % 1 == 0 && value < length);
}

/**
 * Checks if `value` is suitable for use as unique object key.
 *
 * @private
 * @param {*} value The value to check.
 * @returns {boolean} Returns `true` if `value` is suitable, else `false`.
 */
function isKeyable(value) {
  var type = typeof value;
  return (type == 'string' || type == 'number' || type == 'symbol' || type == 'boolean')
    ? (value !== '__proto__')
    : (value === null);
}

/**
 * Checks if `func` has its source masked.
 *
 * @private
 * @param {Function} func The function to check.
 * @returns {boolean} Returns `true` if `func` is masked, else `false`.
 */
function isMasked(func) {
  return !!maskSrcKey && (maskSrcKey in func);
}

/**
 * Checks if `value` is likely a prototype object.
 *
 * @private
 * @param {*} value The value to check.
 * @returns {boolean} Returns `true` if `value` is a prototype, else `false`.
 */
function isPrototype(value) {
  var Ctor = value && value.constructor,
      proto = (typeof Ctor == 'function' && Ctor.prototype) || objectProto;

  return value === proto;
}

/**
 * Converts `func` to its source code.
 *
 * @private
 * @param {Function} func The function to process.
 * @returns {string} Returns the source code.
 */
function toSource(func) {
  if (func != null) {
    try {
      return funcToString.call(func);
    } catch (e) {}
    try {
      return (func + '');
    } catch (e) {}
  }
  return '';
}

/**
 * This method is like `_.clone` except that it recursively clones `value`.
 *
 * @static
 * @memberOf _
 * @since 1.0.0
 * @category Lang
 * @param {*} value The value to recursively clone.
 * @returns {*} Returns the deep cloned value.
 * @see _.clone
 * @example
 *
 * var objects = [{ 'a': 1 }, { 'b': 2 }];
 *
 * var deep = _.cloneDeep(objects);
 * console.log(deep[0] === objects[0]);
 * // => false
 */
function cloneDeep(value) {
  return baseClone(value, true, true);
}

/**
 * Performs a
 * [`SameValueZero`](http://ecma-international.org/ecma-262/7.0/#sec-samevaluezero)
 * comparison between two values to determine if they are equivalent.
 *
 * @static
 * @memberOf _
 * @since 4.0.0
 * @category Lang
 * @param {*} value The value to compare.
 * @param {*} other The other value to compare.
 * @returns {boolean} Returns `true` if the values are equivalent, else `false`.
 * @example
 *
 * var object = { 'a': 1 };
 * var other = { 'a': 1 };
 *
 * _.eq(object, object);
 * // => true
 *
 * _.eq(object, other);
 * // => false
 *
 * _.eq('a', 'a');
 * // => true
 *
 * _.eq('a', Object('a'));
 * // => false
 *
 * _.eq(NaN, NaN);
 * // => true
 */
function eq(value, other) {
  return value === other || (value !== value && other !== other);
}

/**
 * Checks if `value` is likely an `arguments` object.
 *
 * @static
 * @memberOf _
 * @since 0.1.0
 * @category Lang
 * @param {*} value The value to check.
 * @returns {boolean} Returns `true` if `value` is an `arguments` object,
 *  else `false`.
 * @example
 *
 * _.isArguments(function() { return arguments; }());
 * // => true
 *
 * _.isArguments([1, 2, 3]);
 * // => false
 */
function isArguments(value) {
  // Safari 8.1 makes `arguments.callee` enumerable in strict mode.
  return isArrayLikeObject(value) && hasOwnProperty.call(value, 'callee') &&
    (!propertyIsEnumerable.call(value, 'callee') || objectToString.call(value) == argsTag);
}

/**
 * Checks if `value` is classified as an `Array` object.
 *
 * @static
 * @memberOf _
 * @since 0.1.0
 * @category Lang
 * @param {*} value The value to check.
 * @returns {boolean} Returns `true` if `value` is an array, else `false`.
 * @example
 *
 * _.isArray([1, 2, 3]);
 * // => true
 *
 * _.isArray(document.body.children);
 * // => false
 *
 * _.isArray('abc');
 * // => false
 *
 * _.isArray(_.noop);
 * // => false
 */
var isArray = Array.isArray;

/**
 * Checks if `value` is array-like. A value is considered array-like if it's
 * not a function and has a `value.length` that's an integer greater than or
 * equal to `0` and less than or equal to `Number.MAX_SAFE_INTEGER`.
 *
 * @static
 * @memberOf _
 * @since 4.0.0
 * @category Lang
 * @param {*} value The value to check.
 * @returns {boolean} Returns `true` if `value` is array-like, else `false`.
 * @example
 *
 * _.isArrayLike([1, 2, 3]);
 * // => true
 *
 * _.isArrayLike(document.body.children);
 * // => true
 *
 * _.isArrayLike('abc');
 * // => true
 *
 * _.isArrayLike(_.noop);
 * // => false
 */
function isArrayLike(value) {
  return value != null && isLength(value.length) && !isFunction(value);
}

/**
 * This method is like `_.isArrayLike` except that it also checks if `value`
 * is an object.
 *
 * @static
 * @memberOf _
 * @since 4.0.0
 * @category Lang
 * @param {*} value The value to check.
 * @returns {boolean} Returns `true` if `value` is an array-like object,
 *  else `false`.
 * @example
 *
 * _.isArrayLikeObject([1, 2, 3]);
 * // => true
 *
 * _.isArrayLikeObject(document.body.children);
 * // => true
 *
 * _.isArrayLikeObject('abc');
 * // => false
 *
 * _.isArrayLikeObject(_.noop);
 * // => false
 */
function isArrayLikeObject(value) {
  return isObjectLike(value) && isArrayLike(value);
}

/**
 * Checks if `value` is a buffer.
 *
 * @static
 * @memberOf _
 * @since 4.3.0
 * @category Lang
 * @param {*} value The value to check.
 * @returns {boolean} Returns `true` if `value` is a buffer, else `false`.
 * @example
 *
 * _.isBuffer(new Buffer(2));
 * // => true
 *
 * _.isBuffer(new Uint8Array(2));
 * // => false
 */
var isBuffer = nativeIsBuffer || stubFalse;

/**
 * Checks if `value` is classified as a `Function` object.
 *
 * @static
 * @memberOf _
 * @since 0.1.0
 * @category Lang
 * @param {*} value The value to check.
 * @returns {boolean} Returns `true` if `value` is a function, else `false`.
 * @example
 *
 * _.isFunction(_);
 * // => true
 *
 * _.isFunction(/abc/);
 * // => false
 */
function isFunction(value) {
  // The use of `Object#toString` avoids issues with the `typeof` operator
  // in Safari 8-9 which returns 'object' for typed array and other constructors.
  var tag = isObject(value) ? objectToString.call(value) : '';
  return tag == funcTag || tag == genTag;
}

/**
 * Checks if `value` is a valid array-like length.
 *
 * **Note:** This method is loosely based on
 * [`ToLength`](http://ecma-international.org/ecma-262/7.0/#sec-tolength).
 *
 * @static
 * @memberOf _
 * @since 4.0.0
 * @category Lang
 * @param {*} value The value to check.
 * @returns {boolean} Returns `true` if `value` is a valid length, else `false`.
 * @example
 *
 * _.isLength(3);
 * // => true
 *
 * _.isLength(Number.MIN_VALUE);
 * // => false
 *
 * _.isLength(Infinity);
 * // => false
 *
 * _.isLength('3');
 * // => false
 */
function isLength(value) {
  return typeof value == 'number' &&
    value > -1 && value % 1 == 0 && value <= MAX_SAFE_INTEGER;
}

/**
 * Checks if `value` is the
 * [language type](http://www.ecma-international.org/ecma-262/7.0/#sec-ecmascript-language-types)
 * of `Object`. (e.g. arrays, functions, objects, regexes, `new Number(0)`, and `new String('')`)
 *
 * @static
 * @memberOf _
 * @since 0.1.0
 * @category Lang
 * @param {*} value The value to check.
 * @returns {boolean} Returns `true` if `value` is an object, else `false`.
 * @example
 *
 * _.isObject({});
 * // => true
 *
 * _.isObject([1, 2, 3]);
 * // => true
 *
 * _.isObject(_.noop);
 * // => true
 *
 * _.isObject(null);
 * // => false
 */
function isObject(value) {
  var type = typeof value;
  return !!value && (type == 'object' || type == 'function');
}

/**
 * Checks if `value` is object-like. A value is object-like if it's not `null`
 * and has a `typeof` result of "object".
 *
 * @static
 * @memberOf _
 * @since 4.0.0
 * @category Lang
 * @param {*} value The value to check.
 * @returns {boolean} Returns `true` if `value` is object-like, else `false`.
 * @example
 *
 * _.isObjectLike({});
 * // => true
 *
 * _.isObjectLike([1, 2, 3]);
 * // => true
 *
 * _.isObjectLike(_.noop);
 * // => false
 *
 * _.isObjectLike(null);
 * // => false
 */
function isObjectLike(value) {
  return !!value && typeof value == 'object';
}

/**
 * Creates an array of the own enumerable property names of `object`.
 *
 * **Note:** Non-object values are coerced to objects. See the
 * [ES spec](http://ecma-international.org/ecma-262/7.0/#sec-object.keys)
 * for more details.
 *
 * @static
 * @since 0.1.0
 * @memberOf _
 * @category Object
 * @param {Object} object The object to query.
 * @returns {Array} Returns the array of property names.
 * @example
 *
 * function Foo() {
 *   this.a = 1;
 *   this.b = 2;
 * }
 *
 * Foo.prototype.c = 3;
 *
 * _.keys(new Foo);
 * // => ['a', 'b'] (iteration order is not guaranteed)
 *
 * _.keys('hi');
 * // => ['0', '1']
 */
function keys(object) {
  return isArrayLike(object) ? arrayLikeKeys(object) : baseKeys(object);
}

/**
 * This method returns a new empty array.
 *
 * @static
 * @memberOf _
 * @since 4.13.0
 * @category Util
 * @returns {Array} Returns the new empty array.
 * @example
 *
 * var arrays = _.times(2, _.stubArray);
 *
 * console.log(arrays);
 * // => [[], []]
 *
 * console.log(arrays[0] === arrays[1]);
 * // => false
 */
function stubArray() {
  return [];
}

/**
 * This method returns `false`.
 *
 * @static
 * @memberOf _
 * @since 4.13.0
 * @category Util
 * @returns {boolean} Returns `false`.
 * @example
 *
 * _.times(2, _.stubFalse);
 * // => [false, false]
 */
function stubFalse() {
  return false;
}

module.exports = cloneDeep;

}).call(this,typeof global !== "undefined" ? global : typeof self !== "undefined" ? self : typeof window !== "undefined" ? window : {})
},{}],37:[function(require,module,exports){
/**
* pretty-data - nodejs plugin to pretty-print or minify data in XML, JSON and CSS formats.
*  
* Version - 0.40.0
* Copyright (c) 2012 Vadim Kiryukhin
* vkiryukhin @ gmail.com
* http://www.eslinstructor.net/pretty-data/
* 
* Dual licensed under the MIT and GPL licenses:
*   http://www.opensource.org/licenses/mit-license.php
*   http://www.gnu.org/licenses/gpl.html
*
*	pd.xml(data ) - pretty print XML;
*	pd.json(data) - pretty print JSON;
*	pd.css(data ) - pretty print CSS;
*	pd.sql(data)  - pretty print SQL;
*
*	pd.xmlmin(data [, preserveComments] ) - minify XML; 
*	pd.jsonmin(data)                      - minify JSON; 
*	pd.cssmin(data [, preserveComments] ) - minify CSS; 
*	pd.sqlmin(data)                       - minify SQL; 
*
* PARAMETERS:
*
*	@data  			- String; XML, JSON, CSS or SQL text to beautify;
* 	@preserveComments	- Bool (optional, used in minxml and mincss only); 
*				  Set this flag to true to prevent removing comments from @text; 
*	@Return 		- String;
*	
* USAGE:
*	
*	var pd  = require('pretty-data').pd;
*
*	var xml_pp   = pd.xml(xml_text);
*	var xml_min  = pd.xmlmin(xml_text [,true]);
*	var json_pp  = pd.json(json_text);
*	var json_min = pd.jsonmin(json_text);
*	var css_pp   = pd.css(css_text);
*	var css_min  = pd.cssmin(css_text [, true]);
*	var sql_pp   = pd.sql(sql_text);
*	var sql_min  = pd.sqlmin(sql_text);
*
* TEST:
*	comp-name:pretty-data$ node ./test/test_xml
*	comp-name:pretty-data$ node ./test/test_json
*	comp-name:pretty-data$ node ./test/test_css
*	comp-name:pretty-data$ node ./test/test_sql
*/


function pp() {
	this.shift = ['\n']; // array of shifts
	this.step = '  '; // 2 spaces
	var maxdeep = 100; // nesting level
	var ix = 0;

	// initialize array with shifts //
	for(ix=0;ix<maxdeep;ix++){
		this.shift.push(this.shift[ix]+this.step); 
	}

};	
	
// ----------------------- XML section ----------------------------------------------------

pp.prototype.xml = function(text) {

	var ar = text.replace(/>\s{0,}</g,"><")
				 .replace(/</g,"~::~<")
				 .replace(/xmlns\:/g,"~::~xmlns:")
				 .replace(/xmlns\=/g,"~::~xmlns=")
				 .split('~::~'),
		len = ar.length,
		inComment = false,
		deep = 0,
		str = '',
		ix = 0;

		for(ix=0;ix<len;ix++) {
			// start comment or <![CDATA[...]]> or <!DOCTYPE //
			if(ar[ix].search(/<!/) > -1) { 
				str += this.shift[deep]+ar[ix];
				inComment = true; 
				// end comment  or <![CDATA[...]]> //
				if(ar[ix].search(/-->/) > -1 || ar[ix].search(/\]>/) > -1 || ar[ix].search(/!DOCTYPE/) > -1 ) { 
					inComment = false; 
				}
			} else 
			// end comment  or <![CDATA[...]]> //
			if(ar[ix].search(/-->/) > -1 || ar[ix].search(/\]>/) > -1) { 
				str += ar[ix];
				inComment = false; 
			} else 
			// <elm></elm> //
			if( /^<\w/.exec(ar[ix-1]) && /^<\/\w/.exec(ar[ix]) &&
				/^<[\w:\-\.\,]+/.exec(ar[ix-1]) == /^<\/[\w:\-\.\,]+/.exec(ar[ix])[0].replace('/','')) { 
				str += ar[ix];
				if(!inComment) deep--;
			} else
			 // <elm> //
			if(ar[ix].search(/<\w/) > -1 && ar[ix].search(/<\//) == -1 && ar[ix].search(/\/>/) == -1 ) {
				str = !inComment ? str += this.shift[deep++]+ar[ix] : str += ar[ix];
			} else 
			 // <elm>...</elm> //
			if(ar[ix].search(/<\w/) > -1 && ar[ix].search(/<\//) > -1) {
				str = !inComment ? str += this.shift[deep]+ar[ix] : str += ar[ix];
			} else 
			// </elm> //
			if(ar[ix].search(/<\//) > -1) { 
				str = !inComment ? str += this.shift[--deep]+ar[ix] : str += ar[ix];
			} else 
			// <elm/> //
			if(ar[ix].search(/\/>/) > -1 ) { 
				str = !inComment ? str += this.shift[deep]+ar[ix] : str += ar[ix];
			} else 
			// <? xml ... ?> //
			if(ar[ix].search(/<\?/) > -1) { 
				str += this.shift[deep]+ar[ix];
			} else 
			// xmlns //
			if( ar[ix].search(/xmlns\:/) > -1  || ar[ix].search(/xmlns\=/) > -1) { 
				str += this.shift[deep]+ar[ix];
			} 
			
			else {
				str += ar[ix];
			}
		}
		
	return  (str[0] == '\n') ? str.slice(1) : str;
}

// ----------------------- JSON section ----------------------------------------------------

pp.prototype.json = function(text) {

	if ( typeof text === "string" ) {
		return JSON.stringify(JSON.parse(text), null, this.step);
	}
	if ( typeof text === "object" ) {
		return JSON.stringify(text, null, this.step);
	}
	return null;
}

// ----------------------- CSS section ----------------------------------------------------

pp.prototype.css = function(text) {

	var ar = text.replace(/\s{1,}/g,' ')
				.replace(/\{/g,"{~::~")
				.replace(/\}/g,"~::~}~::~")
				.replace(/\;/g,";~::~")
				.replace(/\/\*/g,"~::~/*")
				.replace(/\*\//g,"*/~::~")
				.replace(/~::~\s{0,}~::~/g,"~::~")
				.split('~::~'),
		len = ar.length,
		deep = 0,
		str = '',
		ix = 0;
		
		for(ix=0;ix<len;ix++) {

			if( /\{/.exec(ar[ix]))  { 
				str += this.shift[deep++]+ar[ix];
			} else 
			if( /\}/.exec(ar[ix]))  { 
				str += this.shift[--deep]+ar[ix];
			} else
			if( /\*\\/.exec(ar[ix]))  { 
				str += this.shift[deep]+ar[ix];
			}
			else {
				str += this.shift[deep]+ar[ix];
			}
		}
		return str.replace(/^\n{1,}/,'');
}

// ----------------------- SQL section ----------------------------------------------------

function isSubquery(str, parenthesisLevel) {
  return  parenthesisLevel - (str.replace(/\(/g,'').length - str.replace(/\)/g,'').length )
}

function split_sql(str, tab) {

    return str.replace(/\s{1,}/g," ")

        .replace(/ AND /ig,"~::~"+tab+tab+"AND ")
        .replace(/ BETWEEN /ig,"~::~"+tab+"BETWEEN ")
        .replace(/ CASE /ig,"~::~"+tab+"CASE ")
        .replace(/ ELSE /ig,"~::~"+tab+"ELSE ")
        .replace(/ END /ig,"~::~"+tab+"END ")
        .replace(/ FROM /ig,"~::~FROM ")
        .replace(/ GROUP\s{1,}BY/ig,"~::~GROUP BY ")
        .replace(/ HAVING /ig,"~::~HAVING ")
        //.replace(/ IN /ig,"~::~"+tab+"IN ")
        .replace(/ IN /ig," IN ")
        .replace(/ JOIN /ig,"~::~JOIN ")
        .replace(/ CROSS~::~{1,}JOIN /ig,"~::~CROSS JOIN ")
        .replace(/ INNER~::~{1,}JOIN /ig,"~::~INNER JOIN ")
        .replace(/ LEFT~::~{1,}JOIN /ig,"~::~LEFT JOIN ")
        .replace(/ RIGHT~::~{1,}JOIN /ig,"~::~RIGHT JOIN ")
        .replace(/ ON /ig,"~::~"+tab+"ON ")
        .replace(/ OR /ig,"~::~"+tab+tab+"OR ")
        .replace(/ ORDER\s{1,}BY/ig,"~::~ORDER BY ")
        .replace(/ OVER /ig,"~::~"+tab+"OVER ")
        .replace(/\(\s{0,}SELECT /ig,"~::~(SELECT ")
        .replace(/\)\s{0,}SELECT /ig,")~::~SELECT ")
        .replace(/ THEN /ig," THEN~::~"+tab+"")
        .replace(/ UNION /ig,"~::~UNION~::~")
        .replace(/ USING /ig,"~::~USING ")
        .replace(/ WHEN /ig,"~::~"+tab+"WHEN ")
        .replace(/ WHERE /ig,"~::~WHERE ")
        .replace(/ WITH /ig,"~::~WITH ")
        //.replace(/\,\s{0,}\(/ig,",~::~( ")
        //.replace(/\,/ig,",~::~"+tab+tab+"")
        .replace(/ ALL /ig," ALL ")
        .replace(/ AS /ig," AS ")
        .replace(/ ASC /ig," ASC ") 
        .replace(/ DESC /ig," DESC ") 
        .replace(/ DISTINCT /ig," DISTINCT ")
        .replace(/ EXISTS /ig," EXISTS ")
        .replace(/ NOT /ig," NOT ")
        .replace(/ NULL /ig," NULL ")
        .replace(/ LIKE /ig," LIKE ")
        .replace(/\s{0,}SELECT /ig,"SELECT ")
        .replace(/~::~{1,}/g,"~::~")
        .split('~::~');
}

pp.prototype.sql = function(text) {

    var ar_by_quote = text.replace(/\s{1,}/g," ")
                        .replace(/\'/ig,"~::~\'")
                        .split('~::~'),
        len = ar_by_quote.length,
        ar = [],
        deep = 0,
        tab = this.step,//+this.step,
        inComment = true,
        inQuote = false,
        parenthesisLevel = 0,
        str = '',
        ix = 0;

    for(ix=0;ix<len;ix++) {

        if(ix%2) {
            ar = ar.concat(ar_by_quote[ix]);
        } else {
            ar = ar.concat(split_sql(ar_by_quote[ix], tab) );
        }
    }

    len = ar.length;
    for(ix=0;ix<len;ix++) {

        parenthesisLevel = isSubquery(ar[ix], parenthesisLevel);

        if( /\s{0,}\s{0,}SELECT\s{0,}/.exec(ar[ix]))  { 
            ar[ix] = ar[ix].replace(/\,/g,",\n"+tab+tab+"")
        } 

        if( /\s{0,}\(\s{0,}SELECT\s{0,}/.exec(ar[ix]))  { 
            deep++;
            str += this.shift[deep]+ar[ix];
        } else 
        if( /\'/.exec(ar[ix]) )  { 
            if(parenthesisLevel<1 && deep) {
                deep--;
            }
            str += ar[ix];
        }
        else  { 
            str += this.shift[deep]+ar[ix];
            if(parenthesisLevel<1 && deep) {
                deep--;
            }
        } 
    }

    str = str.replace(/^\n{1,}/,'').replace(/\n{1,}/g,"\n");
    return str;
}

// ----------------------- min section ----------------------------------------------------

pp.prototype.xmlmin = function(text, preserveComments) {

	var str = preserveComments ? text
				   : text.replace(/\<![ \r\n\t]*(--([^\-]|[\r\n]|-[^\-])*--[ \r\n\t]*)\>/g,"");
	return  str.replace(/>\s{0,}</g,"><"); 
}

pp.prototype.jsonmin = function(text) {
								  
    return  text.replace(/\s{0,}\{\s{0,}/g,"{")
                .replace(/\s{0,}\[$/g,"[")
                .replace(/\[\s{0,}/g,"[")
                .replace(/:\s{0,}\[/g,':[')
                .replace(/\s{0,}\}\s{0,}/g,"}")
                .replace(/\s{0,}\]\s{0,}/g,"]")
                .replace(/\"\s{0,}\,/g,'",')
                .replace(/\,\s{0,}\"/g,',"')
                .replace(/\"\s{0,}:/g,'":')
                .replace(/:\s{0,}\"/g,':"')
                .replace(/:\s{0,}\[/g,':[')
                .replace(/\,\s{0,}\[/g,',[')
                .replace(/\,\s{2,}/g,', ')
                .replace(/\]\s{0,},\s{0,}\[/g,'],[');   
}

pp.prototype.cssmin = function(text, preserveComments) {
	
	var str = preserveComments ? text
				   : text.replace(/\/\*([^*]|[\r\n]|(\*+([^*/]|[\r\n])))*\*+\//g,"") ;
	return str.replace(/\s{1,}/g,' ')
			  .replace(/\{\s{1,}/g,"{")
			  .replace(/\}\s{1,}/g,"}")
			  .replace(/\;\s{1,}/g,";")
			  .replace(/\/\*\s{1,}/g,"/*")
			  .replace(/\*\/\s{1,}/g,"*/");
}	

pp.prototype.sqlmin = function(text) {
    return text.replace(/\s{1,}/g," ").replace(/\s{1,}\(/,"(").replace(/\s{1,}\)/,")");
}

// --------------------------------------------------------------------------------------------

exports.pd= new pp;	











},{}],38:[function(require,module,exports){
/**
 * Decimal adjustment of a number.
 *
 * @param {String}  type  The type of adjustment.
 * @param {Number}  value The number.
 * @param {Integer} exp   The exponent (the 10 logarithm of the adjustment base).
 * @returns {Number} The adjusted value.
 */
var decimalAdjust = exports.decimalAdjust = function(type, value, exp) {
    // If the exp is undefined or zero...
    if (typeof exp === 'undefined' || +exp === 0) {
        return Math[type](value);
    }
    value = +value;
    exp = +exp;
    // If the value is not a number or the exp is not an integer...
    if (isNaN(value) || !(typeof exp === 'number' && exp % 1 === 0)) {
        return NaN;
    }
    // Shift
    value = value.toString().split('e');
    value = Math[type](+(value[0] + 'e' + (value[1] ? (+value[1] - exp) : -exp)));
    // Shift back
    value = value.toString().split('e');
    return +(value[0] + 'e' + (value[1] ? (+value[1] + exp) : exp));
}

module.exports = {
    round10: function(value, exp) {
        return decimalAdjust('round', value, exp);
    },
    floor10: function(value, exp) {
        return decimalAdjust('floor', value, exp);
    },
    ceil10: function(value, exp) {
        return decimalAdjust('ceil', value, exp);
    },
};

module.exports.polyfill = function() {
    // Decimal round
    if (!Math.round10) {
        Math.round10 = module.exports.round10;
    }
    // Decimal floor
    if (!Math.floor10) {
        Math.floor10 = module.exports.floor10;
    }
    // Decimal ceil
    if (!Math.ceil10) {
        Math.ceil10 = module.exports.ceil10;
    }
};

},{}],39:[function(require,module,exports){
'use strict';

Object.defineProperty(exports, "__esModule", {
  value: true
});

var _createClass = function () { function defineProperties(target, props) { for (var i = 0; i < props.length; i++) { var descriptor = props[i]; descriptor.enumerable = descriptor.enumerable || false; descriptor.configurable = true; if ("value" in descriptor) descriptor.writable = true; Object.defineProperty(target, descriptor.key, descriptor); } } return function (Constructor, protoProps, staticProps) { if (protoProps) defineProperties(Constructor.prototype, protoProps); if (staticProps) defineProperties(Constructor, staticProps); return Constructor; }; }();

var _V = require('./V2');

var _V2 = _interopRequireDefault(_V);

function _interopRequireDefault(obj) { return obj && obj.__esModule ? obj : { default: obj }; }

function _classCallCheck(instance, Constructor) { if (!(instance instanceof Constructor)) { throw new TypeError("Cannot call a class as a function"); } }

var Box2 = function () {
  function Box2(min, max) {
    _classCallCheck(this, Box2);

    this.min = min || new _V2.default(Infinity, Infinity);
    this.max = max || new _V2.default(-Infinity, -Infinity);
  }

  _createClass(Box2, [{
    key: 'expandByPoint',
    value: function expandByPoint(p) {
      this.min = new _V2.default(Math.min(this.min.x, p.x), Math.min(this.min.y, p.y));
      this.max = new _V2.default(Math.max(this.max.x, p.x), Math.max(this.max.y, p.y));
      return this;
    }
  }, {
    key: 'expandByPoints',
    value: function expandByPoints(points) {
      var _this = this;

      points.forEach(function (point) {
        _this.expandByPoint(point);
      }, this);
      return this;
    }
  }, {
    key: 'isPointInside',
    value: function isPointInside(p) {
      return p.x >= this.min.x && p.y >= this.min.y && p.x <= this.max.x && p.y <= this.max.y;
    }
  }]);

  return Box2;
}();

Box2.fromPoints = function (points) {
  return new Box2().expandByPoints(points);
};

exports.default = Box2;
},{"./V2":45}],40:[function(require,module,exports){
"use strict";

Object.defineProperty(exports, "__esModule", {
  value: true
});

var _createClass = function () { function defineProperties(target, props) { for (var i = 0; i < props.length; i++) { var descriptor = props[i]; descriptor.enumerable = descriptor.enumerable || false; descriptor.configurable = true; if ("value" in descriptor) descriptor.writable = true; Object.defineProperty(target, descriptor.key, descriptor); } } return function (Constructor, protoProps, staticProps) { if (protoProps) defineProperties(Constructor.prototype, protoProps); if (staticProps) defineProperties(Constructor, staticProps); return Constructor; }; }();

function _classCallCheck(instance, Constructor) { if (!(instance instanceof Constructor)) { throw new TypeError("Cannot call a class as a function"); } }

var Box3 = function () {
  function Box3(min, max) {
    _classCallCheck(this, Box3);

    this.min = min || {
      x: Infinity,
      y: Infinity,
      z: Infinity
    };
    this.max = max || {
      x: -Infinity,
      y: -Infinity,
      z: -Infinity
    };
  }

  _createClass(Box3, [{
    key: "expandByPoint",
    value: function expandByPoint(p) {
      this.min = {
        x: Math.min(this.min.x, p.x),
        y: Math.min(this.min.y, p.y),
        z: Math.min(this.min.z, p.z)
      };
      this.max = {
        x: Math.max(this.max.x, p.x),
        y: Math.max(this.max.y, p.y),
        z: Math.max(this.max.z, p.z)
      };
      return this;
    }
  }, {
    key: "expandByPoints",
    value: function expandByPoints(points) {
      var _this = this;

      points.forEach(function (point) {
        _this.expandByPoint(point);
      }, this);
      return this;
    }
  }, {
    key: "isPointInside",
    value: function isPointInside(p) {
      return p.x >= this.min.x && p.y >= this.min.y && p.z >= this.min.z && p.x <= this.max.x && p.y <= this.max.y && p.z <= this.max.z;
    }
  }]);

  return Box3;
}();

Box3.fromPoints = function (points) {
  return new Box3().expandByPoints(points);
};

exports.default = Box3;
},{}],41:[function(require,module,exports){
'use strict';

Object.defineProperty(exports, "__esModule", {
  value: true
});

var _typeof = typeof Symbol === "function" && typeof Symbol.iterator === "symbol" ? function (obj) { return typeof obj; } : function (obj) { return obj && typeof Symbol === "function" && obj.constructor === Symbol && obj !== Symbol.prototype ? "symbol" : typeof obj; };

var _createClass = function () { function defineProperties(target, props) { for (var i = 0; i < props.length; i++) { var descriptor = props[i]; descriptor.enumerable = descriptor.enumerable || false; descriptor.configurable = true; if ("value" in descriptor) descriptor.writable = true; Object.defineProperty(target, descriptor.key, descriptor); } } return function (Constructor, protoProps, staticProps) { if (protoProps) defineProperties(Constructor.prototype, protoProps); if (staticProps) defineProperties(Constructor, staticProps); return Constructor; }; }();

var _V = require('./V2');

var _V2 = _interopRequireDefault(_V);

function _interopRequireDefault(obj) { return obj && obj.__esModule ? obj : { default: obj }; }

function _classCallCheck(instance, Constructor) { if (!(instance instanceof Constructor)) { throw new TypeError("Cannot call a class as a function"); } }

var turn = function turn(p1, p2, p3) {
  var a = p1.x;
  var b = p1.y;
  var c = p2.x;
  var d = p2.y;
  var e = p3.x;
  var f = p3.y;
  var m = (f - b) * (c - a);
  var n = (d - b) * (e - a);
  return m > n + Number.EPSILON ? 1 : m + Number.EPSILON < n ? -1 : 0;
};

// http://stackoverflow.com/a/16725715/35448
var isIntersect = function isIntersect(e1, e2) {
  var p1 = e1.a;
  var p2 = e1.b;
  var p3 = e2.a;
  var p4 = e2.b;
  return turn(p1, p3, p4) !== turn(p2, p3, p4) && turn(p1, p2, p3) !== turn(p1, p2, p4);
};

var _getIntersection = function _getIntersection(m, n) {
  // https://en.wikipedia.org/wiki/Line%E2%80%93line_intersection
  var x1 = m.a.x;
  var x2 = m.b.x;
  var y1 = m.a.y;
  var y2 = m.b.y;

  var x3 = n.a.x;
  var x4 = n.b.x;
  var y3 = n.a.y;
  var y4 = n.b.y;

  var x12 = x1 - x2;
  var x34 = x3 - x4;
  var y12 = y1 - y2;
  var y34 = y3 - y4;
  var c = x12 * y34 - y12 * x34;

  var px = ((x1 * y2 - y1 * x2) * x34 - x12 * (x3 * y4 - y3 * x4)) / c;
  var py = ((x1 * y2 - y1 * x2) * y34 - y12 * (x3 * y4 - y3 * x4)) / c;

  if (isNaN(px) || isNaN(py)) {
    return null;
  } else {
    return new _V2.default(px, py);
  }
};

var dist = function dist(a, b) {
  return Math.sqrt(Math.pow(a.x - b.x, 2) + Math.pow(a.y - b.y, 2));
};

var Line2 = function () {
  function Line2(a, b) {
    _classCallCheck(this, Line2);

    if ((typeof a === 'undefined' ? 'undefined' : _typeof(a)) !== 'object' || a.x === undefined || a.y === undefined) {
      throw Error('expected first argument to have x and y properties');
    }
    if ((typeof b === 'undefined' ? 'undefined' : _typeof(b)) !== 'object' || b.x === undefined || b.y === undefined) {
      throw Error('expected second argument to have x and y properties');
    }
    this.a = new _V2.default(a);
    this.b = new _V2.default(b);
  }

  _createClass(Line2, [{
    key: 'length',
    value: function length() {
      return this.a.sub(this.b).length();
    }
  }, {
    key: 'intersects',
    value: function intersects(other) {
      if (!(other instanceof Line2)) {
        throw new Error('expected argument to be an instance of vecks.Line2');
      }
      return isIntersect(this, other);
    }
  }, {
    key: 'getIntersection',
    value: function getIntersection(other) {
      if (this.intersects(other)) {
        return _getIntersection(this, other);
      } else {
        return null;
      }
    }
  }, {
    key: 'containsPoint',
    value: function containsPoint(point) {
      var eps = arguments.length > 1 && arguments[1] !== undefined ? arguments[1] : 1e-12;

      return Math.abs(dist(this.a, this.b) - dist(point, this.a) - dist(point, this.b)) < eps;
    }
  }]);

  return Line2;
}();

exports.default = Line2;
},{"./V2":45}],42:[function(require,module,exports){
'use strict';

Object.defineProperty(exports, "__esModule", {
  value: true
});

var _typeof = typeof Symbol === "function" && typeof Symbol.iterator === "symbol" ? function (obj) { return typeof obj; } : function (obj) { return obj && typeof Symbol === "function" && obj.constructor === Symbol && obj !== Symbol.prototype ? "symbol" : typeof obj; };

var _createClass = function () { function defineProperties(target, props) { for (var i = 0; i < props.length; i++) { var descriptor = props[i]; descriptor.enumerable = descriptor.enumerable || false; descriptor.configurable = true; if ("value" in descriptor) descriptor.writable = true; Object.defineProperty(target, descriptor.key, descriptor); } } return function (Constructor, protoProps, staticProps) { if (protoProps) defineProperties(Constructor.prototype, protoProps); if (staticProps) defineProperties(Constructor, staticProps); return Constructor; }; }();

var _V = require('./V3');

var _V2 = _interopRequireDefault(_V);

function _interopRequireDefault(obj) { return obj && obj.__esModule ? obj : { default: obj }; }

function _classCallCheck(instance, Constructor) { if (!(instance instanceof Constructor)) { throw new TypeError("Cannot call a class as a function"); } }

var dist = function dist(a, b) {
  return Math.sqrt(Math.pow(a.x - b.x, 2) + Math.pow(a.y - b.y, 2) + Math.pow(a.z - b.z, 2));
};

var Line3 = function () {
  function Line3(a, b) {
    _classCallCheck(this, Line3);

    if ((typeof a === 'undefined' ? 'undefined' : _typeof(a)) !== 'object' || a.x === undefined || a.y === undefined || a.z === undefined) {
      throw Error('expected first argument to have x, y and z properties');
    }
    if ((typeof b === 'undefined' ? 'undefined' : _typeof(b)) !== 'object' || b.x === undefined || b.y === undefined || b.y === undefined) {
      throw Error('expected second argument to have x, y and z properties');
    }
    this.a = new _V2.default(a);
    this.b = new _V2.default(b);
  }

  _createClass(Line3, [{
    key: 'length',
    value: function length() {
      return this.a.sub(this.b).length();
    }
  }, {
    key: 'containsPoint',
    value: function containsPoint(point) {
      var eps = arguments.length > 1 && arguments[1] !== undefined ? arguments[1] : 1e-12;

      return Math.abs(dist(this.a, this.b) - dist(point, this.a) - dist(point, this.b)) < eps;
    }
  }]);

  return Line3;
}();

exports.default = Line3;
},{"./V3":46}],43:[function(require,module,exports){
'use strict';

Object.defineProperty(exports, "__esModule", {
  value: true
});

var _createClass = function () { function defineProperties(target, props) { for (var i = 0; i < props.length; i++) { var descriptor = props[i]; descriptor.enumerable = descriptor.enumerable || false; descriptor.configurable = true; if ("value" in descriptor) descriptor.writable = true; Object.defineProperty(target, descriptor.key, descriptor); } } return function (Constructor, protoProps, staticProps) { if (protoProps) defineProperties(Constructor.prototype, protoProps); if (staticProps) defineProperties(Constructor, staticProps); return Constructor; }; }();

function _classCallCheck(instance, Constructor) { if (!(instance instanceof Constructor)) { throw new TypeError("Cannot call a class as a function"); } }

var Plane3 = function () {
  function Plane3(a, b, c, d) {
    _classCallCheck(this, Plane3);

    this.a = a;
    this.b = b;
    this.c = c;
    this.d = d;
  }

  // Distance to a point
  // http://mathworld.wolfram.com/Point-PlaneDistance.html eq 10


  _createClass(Plane3, [{
    key: 'distanceToPoint',
    value: function distanceToPoint(p0) {
      var dd = (this.a * p0.x + this.b * p0.y + this.c * p0.z + this.d) / Math.sqrt(this.a * this.a + this.b * this.b + this.c * this.c);
      return dd;
    }
  }, {
    key: 'equals',
    value: function equals(other) {
      return this.a === other.a && this.b === other.b && this.c === other.c && this.d === other.d;
    }
  }, {
    key: 'coPlanar',
    value: function coPlanar(other) {
      var coPlanarAndSameNormal = this.a === other.a && this.b === other.b && this.c === other.c && this.d === other.d;
      var coPlanarAndReversedNormal = this.a === -other.a && this.b === -other.b && this.c === -other.c && this.d === -other.d;
      return coPlanarAndSameNormal || coPlanarAndReversedNormal;
    }
  }]);

  return Plane3;
}();

// From point and normal


Plane3.fromPointAndNormal = function (p, n) {
  var a = n.x;
  var b = n.y;
  var c = n.z;
  var d = -(p.x * a + p.y * b + p.z * c);
  return new Plane3(n.x, n.y, n.z, d);
};

Plane3.fromPoints = function (points) {
  var firstCross = void 0;
  for (var i = 0, il = points.length; i < il; ++i) {
    var ab = points[(i + 1) % il].sub(points[i]);
    var bc = points[(i + 2) % il].sub(points[(i + 1) % il]);
    var cross = ab.cross(bc);
    if (!(isNaN(cross.length()) || cross.length() === 0)) {
      if (!firstCross) {
        firstCross = cross.norm();
      } else {
        var same = cross.norm().equals(firstCross, 1e-6);
        var opposite = cross.neg().norm().equals(firstCross, 1e-6);
        if (!(same || opposite)) {
          throw Error('points not on a plane');
        }
      }
    }
  }
  if (!firstCross) {
    throw Error('points not on a plane');
  }
  return Plane3.fromPointAndNormal(points[0], firstCross.norm());
};

exports.default = Plane3;
},{}],44:[function(require,module,exports){
'use strict';

Object.defineProperty(exports, "__esModule", {
  value: true
});

var _createClass = function () { function defineProperties(target, props) { for (var i = 0; i < props.length; i++) { var descriptor = props[i]; descriptor.enumerable = descriptor.enumerable || false; descriptor.configurable = true; if ("value" in descriptor) descriptor.writable = true; Object.defineProperty(target, descriptor.key, descriptor); } } return function (Constructor, protoProps, staticProps) { if (protoProps) defineProperties(Constructor.prototype, protoProps); if (staticProps) defineProperties(Constructor, staticProps); return Constructor; }; }();

var _V = require('./V3');

var _V2 = _interopRequireDefault(_V);

function _interopRequireDefault(obj) { return obj && obj.__esModule ? obj : { default: obj }; }

function _classCallCheck(instance, Constructor) { if (!(instance instanceof Constructor)) { throw new TypeError("Cannot call a class as a function"); } }

// Quaternion implementation heavily adapted from the Quaternion implementation in THREE.js
// https://github.com/mrdoob/three.js/blob/master/src/math/Quaternion.js

var Quaternion = function () {
  function Quaternion(x, y, z, w) {
    _classCallCheck(this, Quaternion);

    this.x = x;
    this.y = y;
    this.z = z;
    this.w = w;
  }

  _createClass(Quaternion, [{
    key: 'applyToVec3',
    value: function applyToVec3(v3) {
      var x = v3.x;
      var y = v3.y;
      var z = v3.z;

      var qx = this.x;
      var qy = this.y;
      var qz = this.z;
      var qw = this.w;

      // calculate quat * vector
      var ix = qw * x + qy * z - qz * y;
      var iy = qw * y + qz * x - qx * z;
      var iz = qw * z + qx * y - qy * x;
      var iw = -qx * x - qy * y - qz * z;

      // calculate result * inverse quat
      return new _V2.default(ix * qw + iw * -qx + iy * -qz - iz * -qy, iy * qw + iw * -qy + iz * -qx - ix * -qz, iz * qw + iw * -qz + ix * -qy - iy * -qx);
    }
  }]);

  return Quaternion;
}();

Quaternion.fromAxisAngle = function (axis, angle) {
  // http://www.euclideanspace.com/maths/geometry/rotations/conversions/angleToQuaternion/index.htm
  var axisNorm = axis.norm();
  var halfAngle = angle / 2;
  var s = Math.sin(halfAngle);
  return new Quaternion(axisNorm.x * s, axisNorm.y * s, axisNorm.z * s, Math.cos(halfAngle));
};

exports.default = Quaternion;
},{"./V3":46}],45:[function(require,module,exports){
'use strict';

Object.defineProperty(exports, "__esModule", {
  value: true
});

var _typeof = typeof Symbol === "function" && typeof Symbol.iterator === "symbol" ? function (obj) { return typeof obj; } : function (obj) { return obj && typeof Symbol === "function" && obj.constructor === Symbol && obj !== Symbol.prototype ? "symbol" : typeof obj; };

var _createClass = function () { function defineProperties(target, props) { for (var i = 0; i < props.length; i++) { var descriptor = props[i]; descriptor.enumerable = descriptor.enumerable || false; descriptor.configurable = true; if ("value" in descriptor) descriptor.writable = true; Object.defineProperty(target, descriptor.key, descriptor); } } return function (Constructor, protoProps, staticProps) { if (protoProps) defineProperties(Constructor.prototype, protoProps); if (staticProps) defineProperties(Constructor, staticProps); return Constructor; }; }();

function _classCallCheck(instance, Constructor) { if (!(instance instanceof Constructor)) { throw new TypeError("Cannot call a class as a function"); } }

var V2 = function () {
  function V2(x, y) {
    _classCallCheck(this, V2);

    if ((typeof x === 'undefined' ? 'undefined' : _typeof(x)) === 'object') {
      this.x = x.x;
      this.y = x.y;
    } else {
      this.x = x;
      this.y = y;
    }
  }

  _createClass(V2, [{
    key: 'equals',
    value: function equals(other) {
      return this.x === other.x && this.y === other.y;
    }
  }, {
    key: 'length',
    value: function length() {
      return Math.sqrt(this.dot(this));
    }
  }, {
    key: 'neg',
    value: function neg() {
      return new V2(-this.x, -this.y);
    }
  }, {
    key: 'add',
    value: function add(b) {
      return new V2(this.x + b.x, this.y + b.y);
    }
  }, {
    key: 'sub',
    value: function sub(b) {
      return new V2(this.x - b.x, this.y - b.y);
    }
  }, {
    key: 'multiply',
    value: function multiply(w) {
      return new V2(this.x * w, this.y * w);
    }
  }, {
    key: 'norm',
    value: function norm() {
      return this.multiply(1 / this.length());
    }
  }, {
    key: 'dot',
    value: function dot(b) {
      return this.x * b.x + this.y * b.y;
    }
  }]);

  return V2;
}();

exports.default = V2;
},{}],46:[function(require,module,exports){
'use strict';

Object.defineProperty(exports, "__esModule", {
  value: true
});

var _typeof = typeof Symbol === "function" && typeof Symbol.iterator === "symbol" ? function (obj) { return typeof obj; } : function (obj) { return obj && typeof Symbol === "function" && obj.constructor === Symbol && obj !== Symbol.prototype ? "symbol" : typeof obj; };

var _createClass = function () { function defineProperties(target, props) { for (var i = 0; i < props.length; i++) { var descriptor = props[i]; descriptor.enumerable = descriptor.enumerable || false; descriptor.configurable = true; if ("value" in descriptor) descriptor.writable = true; Object.defineProperty(target, descriptor.key, descriptor); } } return function (Constructor, protoProps, staticProps) { if (protoProps) defineProperties(Constructor.prototype, protoProps); if (staticProps) defineProperties(Constructor, staticProps); return Constructor; }; }();

function _classCallCheck(instance, Constructor) { if (!(instance instanceof Constructor)) { throw new TypeError("Cannot call a class as a function"); } }

var V3 = function () {
  function V3(x, y, z) {
    _classCallCheck(this, V3);

    if ((typeof x === 'undefined' ? 'undefined' : _typeof(x)) === 'object') {
      this.x = x.x;
      this.y = x.y;
      this.z = x.z;
    } else if (x === undefined) {
      this.x = 0;
      this.y = 0;
      this.z = 0;
    } else {
      this.x = x;
      this.y = y;
      this.z = z;
    }
  }

  _createClass(V3, [{
    key: 'equals',
    value: function equals(other, eps) {
      if (eps === undefined) {
        eps = 0;
      }
      return Math.abs(this.x - other.x) <= eps && Math.abs(this.y - other.y) <= eps && Math.abs(this.z - other.z) <= eps;
    }
  }, {
    key: 'length',
    value: function length() {
      return Math.sqrt(this.dot(this));
    }
  }, {
    key: 'neg',
    value: function neg() {
      return new V3(-this.x, -this.y, -this.z);
    }
  }, {
    key: 'add',
    value: function add(b) {
      return new V3(this.x + b.x, this.y + b.y, this.z + b.z);
    }
  }, {
    key: 'sub',
    value: function sub(b) {
      return new V3(this.x - b.x, this.y - b.y, this.z - b.z);
    }
  }, {
    key: 'multiply',
    value: function multiply(w) {
      return new V3(this.x * w, this.y * w, this.z * w);
    }
  }, {
    key: 'norm',
    value: function norm() {
      return this.multiply(1 / this.length());
    }
  }, {
    key: 'dot',
    value: function dot(b) {
      return this.x * b.x + this.y * b.y + this.z * b.z;
    }
  }, {
    key: 'cross',
    value: function cross(b) {
      return new V3(this.y * b.z - this.z * b.y, this.z * b.x - this.x * b.z, this.x * b.y - this.y * b.x);
    }
  }]);

  return V3;
}();

exports.default = V3;
},{}],47:[function(require,module,exports){
'use strict';

Object.defineProperty(exports, "__esModule", {
  value: true
});
exports.Line3 = exports.Line2 = exports.Quaternion = exports.Plane3 = exports.Box3 = exports.Box2 = exports.V3 = exports.V2 = undefined;

var _V = require('./V2');

var _V2 = _interopRequireDefault(_V);

var _V3 = require('./V3');

var _V4 = _interopRequireDefault(_V3);

var _Box = require('./Box2');

var _Box2 = _interopRequireDefault(_Box);

var _Box3 = require('./Box3');

var _Box4 = _interopRequireDefault(_Box3);

var _Plane = require('./Plane3');

var _Plane2 = _interopRequireDefault(_Plane);

var _Quaternion = require('./Quaternion');

var _Quaternion2 = _interopRequireDefault(_Quaternion);

var _Line = require('./Line2');

var _Line2 = _interopRequireDefault(_Line);

var _Line3 = require('./Line3');

var _Line4 = _interopRequireDefault(_Line3);

function _interopRequireDefault(obj) { return obj && obj.__esModule ? obj : { default: obj }; }

exports.V2 = _V2.default;
exports.V3 = _V4.default;
exports.Box2 = _Box2.default;
exports.Box3 = _Box4.default;
exports.Plane3 = _Plane2.default;
exports.Quaternion = _Quaternion2.default;
exports.Line2 = _Line2.default;
exports.Line3 = _Line4.default;
},{"./Box2":39,"./Box3":40,"./Line2":41,"./Line3":42,"./Plane3":43,"./Quaternion":44,"./V2":45,"./V3":46}]},{},[25])(25)
});
