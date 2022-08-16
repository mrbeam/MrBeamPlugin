// https://sourceforge.net/projects/jsclipper/files/
/*******************************************************************************
 *                                                                              *
 * Author    :  Angus Johnson                                                   *
 * Version   :  6.4.2                                                           *
 * Date      :  27 February 2017                                                *
 * Website   :  http://www.angusj.com                                           *
 * Copyright :  Angus Johnson 2010-2017                                         *
 *                                                                              *
 * License:                                                                     *
 * Use, modification & distribution is subject to Boost Software License Ver 1. *
 * http://www.boost.org/LICENSE_1_0.txt                                         *
 *                                                                              *
 * Attributions:                                                                *
 * The code in this library is an extension of Bala Vatti's clipping algorithm: *
 * "A generic solution to polygon clipping"                                     *
 * Communications of the ACM, Vol 35, Issue 7 (July 1992) pp 56-63.             *
 * http://portal.acm.org/citation.cfm?id=129906                                 *
 *                                                                              *
 * Computer graphics and geometric modeling: implementation and algorithms      *
 * By Max K. Agoston                                                            *
 * Springer; 1 edition (January 4, 2005)                                        *
 * http://books.google.com/books?q=vatti+clipping+agoston                       *
 *                                                                              *
 * See also:                                                                    *
 * "Polygon Offsetting by Computing Winding Numbers"                            *
 * Paper no. DETC2005-85513 pp. 565-575                                         *
 * ASME 2005 International Design Engineering Technical Conferences             *
 * and Computers and Information in Engineering Conference (IDETC/CIE2005)      *
 * September 24-28, 2005 , Long Beach, California, USA                          *
 * http://www.me.berkeley.edu/~mcmains/pubs/DAC05OffsetPolygon.pdf              *
 *                                                                              *
 *******************************************************************************/
/*******************************************************************************
 *                                                                              *
 * Author    :  Timo                                                            *
 * Version   :  6.4.2.2                                                         *
 * Date      :  8 September 2017                                                 *
 *                                                                              *
 * This is a translation of the C# Clipper library to Javascript.               *
 * Int128 struct of C# is implemented using JSBN of Tom Wu.                     *
 * Because Javascript lacks support for 64-bit integers, the space              *
 * is a little more restricted than in C# version.                              *
 *                                                                              *
 * C# version has support for coordinate space:                                 *
 * +-4611686018427387903 ( sqrt(2^127 -1)/2 )                                   *
 * while Javascript version has support for space:                              *
 * +-4503599627370495 ( sqrt(2^106 -1)/2 )                                      *
 *                                                                              *
 * Tom Wu's JSBN proved to be the fastest big integer library:                  *
 * http://jsperf.com/big-integer-library-test                                   *
 *                                                                              *
 * This class can be made simpler when (if ever) 64-bit integer support comes   *
 * or floating point Clipper is released.                                       *
 *                                                                              *
 *******************************************************************************/
/*******************************************************************************
 *                                                                              *
 * Basic JavaScript BN library - subset useful for RSA encryption.              *
 * http://www-cs-students.stanford.edu/~tjw/jsbn/                               *
 * Copyright (c) 2005  Tom Wu                                                   *
 * All Rights Reserved.                                                         *
 * See "LICENSE" for details:                                                   *
 * http://www-cs-students.stanford.edu/~tjw/jsbn/LICENSE                        *
 *                                                                              *
 *******************************************************************************/
(function () {
    function k(a, b, c) {
        d.biginteger_used = 1;
        null != a &&
            ("number" == typeof a && "undefined" == typeof b
                ? this.fromInt(a)
                : "number" == typeof a
                ? this.fromNumber(a, b, c)
                : null == b && "string" != typeof a
                ? this.fromString(a, 256)
                : this.fromString(a, b));
    }
    function q() {
        return new k(null, void 0, void 0);
    }
    function R(a, b, c, e, d, g) {
        for (; 0 <= --g; ) {
            var f = b * this[a++] + c[e] + d;
            d = Math.floor(f / 67108864);
            c[e++] = f & 67108863;
        }
        return d;
    }
    function S(a, b, c, e, d, g) {
        var f = b & 32767;
        for (b >>= 15; 0 <= --g; ) {
            var m = this[a] & 32767,
                k = this[a++] >> 15,
                n = b * m + k * f;
            m = f * m + ((n & 32767) << 15) + c[e] + (d & 1073741823);
            d = (m >>> 30) + (n >>> 15) + b * k + (d >>> 30);
            c[e++] = m & 1073741823;
        }
        return d;
    }
    function T(a, b, c, e, d, g) {
        var f = b & 16383;
        for (b >>= 14; 0 <= --g; ) {
            var m = this[a] & 16383,
                k = this[a++] >> 14,
                n = b * m + k * f;
            m = f * m + ((n & 16383) << 14) + c[e] + d;
            d = (m >> 28) + (n >> 14) + b * k;
            c[e++] = m & 268435455;
        }
        return d;
    }
    function M(a, b) {
        var c = E[a.charCodeAt(b)];
        return null == c ? -1 : c;
    }
    function y(a) {
        var b = q();
        b.fromInt(a);
        return b;
    }
    function F(a) {
        var b = 1,
            c;
        0 != (c = a >>> 16) && ((a = c), (b += 16));
        0 != (c = a >> 8) && ((a = c), (b += 8));
        0 != (c = a >> 4) && ((a = c), (b += 4));
        0 != (c = a >> 2) && ((a = c), (b += 2));
        0 != a >> 1 && (b += 1);
        return b;
    }
    function z(a) {
        this.m = a;
    }
    function B(a) {
        this.m = a;
        this.mp = a.invDigit();
        this.mpl = this.mp & 32767;
        this.mph = this.mp >> 15;
        this.um = (1 << (a.DB - 15)) - 1;
        this.mt2 = 2 * a.t;
    }
    function U(a, b) {
        return a & b;
    }
    function H(a, b) {
        return a | b;
    }
    function N(a, b) {
        return a ^ b;
    }
    function O(a, b) {
        return a & ~b;
    }
    function D() {}
    function P(a) {
        return a;
    }
    function C(a) {
        this.r2 = q();
        this.q3 = q();
        k.ONE.dlShiftTo(2 * a.t, this.r2);
        this.mu = this.r2.divide(a);
        this.m = a;
    }
    var d = { version: "6.4.2.2", use_lines: !0, use_xyz: !1 },
        G = !1;
    "undefined" !== typeof module && module.exports
        ? ((module.exports = d), (G = !0))
        : "undefined" !== typeof document
        ? (window.ClipperLib = d)
        : (self.ClipperLib = d);
    if (G) {
        var u = "chrome";
        var v = "Netscape";
    } else
        (u = navigator.userAgent.toString().toLowerCase()),
            (v = navigator.appName);
    var I = -1 != u.indexOf("chrome") && -1 == u.indexOf("chromium") ? 1 : 0;
    G = -1 != u.indexOf("chromium") ? 1 : 0;
    var Q =
        -1 != u.indexOf("safari") &&
        -1 == u.indexOf("chrome") &&
        -1 == u.indexOf("chromium")
            ? 1
            : 0;
    var J = -1 != u.indexOf("firefox") ? 1 : 0;
    u.indexOf("firefox/17");
    u.indexOf("firefox/15");
    u.indexOf("firefox/3");
    var K = -1 != u.indexOf("opera") ? 1 : 0;
    u.indexOf("msie 10");
    u.indexOf("msie 9");
    var L = -1 != u.indexOf("msie 8") ? 1 : 0;
    var V = -1 != u.indexOf("msie 7") ? 1 : 0;
    u = -1 != u.indexOf("msie ") ? 1 : 0;
    d.biginteger_used = null;
    "Microsoft Internet Explorer" == v
        ? ((k.prototype.am = S), (v = 30))
        : "Netscape" != v
        ? ((k.prototype.am = R), (v = 26))
        : ((k.prototype.am = T), (v = 28));
    k.prototype.DB = v;
    k.prototype.DM = (1 << v) - 1;
    k.prototype.DV = 1 << v;
    k.prototype.FV = Math.pow(2, 52);
    k.prototype.F1 = 52 - v;
    k.prototype.F2 = 2 * v - 52;
    var E = [],
        x;
    v = 48;
    for (x = 0; 9 >= x; ++x) E[v++] = x;
    v = 97;
    for (x = 10; 36 > x; ++x) E[v++] = x;
    v = 65;
    for (x = 10; 36 > x; ++x) E[v++] = x;
    z.prototype.convert = function (a) {
        return 0 > a.s || 0 <= a.compareTo(this.m) ? a.mod(this.m) : a;
    };
    z.prototype.revert = function (a) {
        return a;
    };
    z.prototype.reduce = function (a) {
        a.divRemTo(this.m, null, a);
    };
    z.prototype.mulTo = function (a, b, c) {
        a.multiplyTo(b, c);
        this.reduce(c);
    };
    z.prototype.sqrTo = function (a, b) {
        a.squareTo(b);
        this.reduce(b);
    };
    B.prototype.convert = function (a) {
        var b = q();
        a.abs().dlShiftTo(this.m.t, b);
        b.divRemTo(this.m, null, b);
        0 > a.s && 0 < b.compareTo(k.ZERO) && this.m.subTo(b, b);
        return b;
    };
    B.prototype.revert = function (a) {
        var b = q();
        a.copyTo(b);
        this.reduce(b);
        return b;
    };
    B.prototype.reduce = function (a) {
        for (; a.t <= this.mt2; ) a[a.t++] = 0;
        for (var b = 0; b < this.m.t; ++b) {
            var c = a[b] & 32767,
                e =
                    (c * this.mpl +
                        (((c * this.mph + (a[b] >> 15) * this.mpl) & this.um) <<
                            15)) &
                    a.DM;
            c = b + this.m.t;
            for (a[c] += this.m.am(0, e, a, b, 0, this.m.t); a[c] >= a.DV; )
                (a[c] -= a.DV), a[++c]++;
        }
        a.clamp();
        a.drShiftTo(this.m.t, a);
        0 <= a.compareTo(this.m) && a.subTo(this.m, a);
    };
    B.prototype.mulTo = function (a, b, c) {
        a.multiplyTo(b, c);
        this.reduce(c);
    };
    B.prototype.sqrTo = function (a, b) {
        a.squareTo(b);
        this.reduce(b);
    };
    k.prototype.copyTo = function (a) {
        for (var b = this.t - 1; 0 <= b; --b) a[b] = this[b];
        a.t = this.t;
        a.s = this.s;
    };
    k.prototype.fromInt = function (a) {
        this.t = 1;
        this.s = 0 > a ? -1 : 0;
        0 < a ? (this[0] = a) : -1 > a ? (this[0] = a + this.DV) : (this.t = 0);
    };
    k.prototype.fromString = function (a, b) {
        if (16 == b) var c = 4;
        else if (8 == b) c = 3;
        else if (256 == b) c = 8;
        else if (2 == b) c = 1;
        else if (32 == b) c = 5;
        else if (4 == b) c = 2;
        else {
            this.fromRadix(a, b);
            return;
        }
        this.s = this.t = 0;
        for (var e = a.length, d = !1, g = 0; 0 <= --e; ) {
            var h = 8 == c ? a[e] & 255 : M(a, e);
            0 > h
                ? "-" == a.charAt(e) && (d = !0)
                : ((d = !1),
                  0 == g
                      ? (this[this.t++] = h)
                      : g + c > this.DB
                      ? ((this[this.t - 1] |=
                            (h & ((1 << (this.DB - g)) - 1)) << g),
                        (this[this.t++] = h >> (this.DB - g)))
                      : (this[this.t - 1] |= h << g),
                  (g += c),
                  g >= this.DB && (g -= this.DB));
        }
        8 == c &&
            0 != (a[0] & 128) &&
            ((this.s = -1),
            0 < g && (this[this.t - 1] |= ((1 << (this.DB - g)) - 1) << g));
        this.clamp();
        d && k.ZERO.subTo(this, this);
    };
    k.prototype.clamp = function () {
        for (var a = this.s & this.DM; 0 < this.t && this[this.t - 1] == a; )
            --this.t;
    };
    k.prototype.dlShiftTo = function (a, b) {
        var c;
        for (c = this.t - 1; 0 <= c; --c) b[c + a] = this[c];
        for (c = a - 1; 0 <= c; --c) b[c] = 0;
        b.t = this.t + a;
        b.s = this.s;
    };
    k.prototype.drShiftTo = function (a, b) {
        for (var c = a; c < this.t; ++c) b[c - a] = this[c];
        b.t = Math.max(this.t - a, 0);
        b.s = this.s;
    };
    k.prototype.lShiftTo = function (a, b) {
        var c = a % this.DB,
            e = this.DB - c,
            d = (1 << e) - 1,
            g = Math.floor(a / this.DB),
            h = (this.s << c) & this.DM,
            m;
        for (m = this.t - 1; 0 <= m; --m)
            (b[m + g + 1] = (this[m] >> e) | h), (h = (this[m] & d) << c);
        for (m = g - 1; 0 <= m; --m) b[m] = 0;
        b[g] = h;
        b.t = this.t + g + 1;
        b.s = this.s;
        b.clamp();
    };
    k.prototype.rShiftTo = function (a, b) {
        b.s = this.s;
        var c = Math.floor(a / this.DB);
        if (c >= this.t) b.t = 0;
        else {
            var e = a % this.DB,
                d = this.DB - e,
                g = (1 << e) - 1;
            b[0] = this[c] >> e;
            for (var h = c + 1; h < this.t; ++h)
                (b[h - c - 1] |= (this[h] & g) << d), (b[h - c] = this[h] >> e);
            0 < e && (b[this.t - c - 1] |= (this.s & g) << d);
            b.t = this.t - c;
            b.clamp();
        }
    };
    k.prototype.subTo = function (a, b) {
        for (var c = 0, e = 0, d = Math.min(a.t, this.t); c < d; )
            (e += this[c] - a[c]), (b[c++] = e & this.DM), (e >>= this.DB);
        if (a.t < this.t) {
            for (e -= a.s; c < this.t; )
                (e += this[c]), (b[c++] = e & this.DM), (e >>= this.DB);
            e += this.s;
        } else {
            for (e += this.s; c < a.t; )
                (e -= a[c]), (b[c++] = e & this.DM), (e >>= this.DB);
            e -= a.s;
        }
        b.s = 0 > e ? -1 : 0;
        -1 > e ? (b[c++] = this.DV + e) : 0 < e && (b[c++] = e);
        b.t = c;
        b.clamp();
    };
    k.prototype.multiplyTo = function (a, b) {
        var c = this.abs(),
            e = a.abs(),
            d = c.t;
        for (b.t = d + e.t; 0 <= --d; ) b[d] = 0;
        for (d = 0; d < e.t; ++d) b[d + c.t] = c.am(0, e[d], b, d, 0, c.t);
        b.s = 0;
        b.clamp();
        this.s != a.s && k.ZERO.subTo(b, b);
    };
    k.prototype.squareTo = function (a) {
        for (var b = this.abs(), c = (a.t = 2 * b.t); 0 <= --c; ) a[c] = 0;
        for (c = 0; c < b.t - 1; ++c) {
            var e = b.am(c, b[c], a, 2 * c, 0, 1);
            (a[c + b.t] += b.am(
                c + 1,
                2 * b[c],
                a,
                2 * c + 1,
                e,
                b.t - c - 1
            )) >= b.DV && ((a[c + b.t] -= b.DV), (a[c + b.t + 1] = 1));
        }
        0 < a.t && (a[a.t - 1] += b.am(c, b[c], a, 2 * c, 0, 1));
        a.s = 0;
        a.clamp();
    };
    k.prototype.divRemTo = function (a, b, c) {
        var e = a.abs();
        if (!(0 >= e.t)) {
            var d = this.abs();
            if (d.t < e.t)
                null != b && b.fromInt(0), null != c && this.copyTo(c);
            else {
                null == c && (c = q());
                var g = q(),
                    h = this.s;
                a = a.s;
                var m = this.DB - F(e[e.t - 1]);
                0 < m
                    ? (e.lShiftTo(m, g), d.lShiftTo(m, c))
                    : (e.copyTo(g), d.copyTo(c));
                e = g.t;
                d = g[e - 1];
                if (0 != d) {
                    var l =
                            d * (1 << this.F1) +
                            (1 < e ? g[e - 2] >> this.F2 : 0),
                        n = this.FV / l;
                    l = (1 << this.F1) / l;
                    var r = 1 << this.F2,
                        p = c.t,
                        t = p - e,
                        u = null == b ? q() : b;
                    g.dlShiftTo(t, u);
                    0 <= c.compareTo(u) && ((c[c.t++] = 1), c.subTo(u, c));
                    k.ONE.dlShiftTo(e, u);
                    for (u.subTo(g, g); g.t < e; ) g[g.t++] = 0;
                    for (; 0 <= --t; ) {
                        var v =
                            c[--p] == d
                                ? this.DM
                                : Math.floor(c[p] * n + (c[p - 1] + r) * l);
                        if ((c[p] += g.am(0, v, c, t, 0, e)) < v)
                            for (g.dlShiftTo(t, u), c.subTo(u, c); c[p] < --v; )
                                c.subTo(u, c);
                    }
                    null != b &&
                        (c.drShiftTo(e, b), h != a && k.ZERO.subTo(b, b));
                    c.t = e;
                    c.clamp();
                    0 < m && c.rShiftTo(m, c);
                    0 > h && k.ZERO.subTo(c, c);
                }
            }
        }
    };
    k.prototype.invDigit = function () {
        if (1 > this.t) return 0;
        var a = this[0];
        if (0 == (a & 1)) return 0;
        var b = a & 3;
        b = (b * (2 - (a & 15) * b)) & 15;
        b = (b * (2 - (a & 255) * b)) & 255;
        b = (b * (2 - (((a & 65535) * b) & 65535))) & 65535;
        b = (b * (2 - ((a * b) % this.DV))) % this.DV;
        return 0 < b ? this.DV - b : -b;
    };
    k.prototype.isEven = function () {
        return 0 == (0 < this.t ? this[0] & 1 : this.s);
    };
    k.prototype.exp = function (a, b) {
        if (4294967295 < a || 1 > a) return k.ONE;
        var c = q(),
            e = q(),
            d = b.convert(this),
            g = F(a) - 1;
        for (d.copyTo(c); 0 <= --g; )
            if ((b.sqrTo(c, e), 0 < (a & (1 << g)))) b.mulTo(e, d, c);
            else {
                var h = c;
                c = e;
                e = h;
            }
        return b.revert(c);
    };
    k.prototype.toString = function (a) {
        if (0 > this.s) return "-" + this.negate().toString(a);
        if (16 == a) a = 4;
        else if (8 == a) a = 3;
        else if (2 == a) a = 1;
        else if (32 == a) a = 5;
        else if (4 == a) a = 2;
        else return this.toRadix(a);
        var b = (1 << a) - 1,
            c,
            e = !1,
            d = "",
            g = this.t,
            h = this.DB - ((g * this.DB) % a);
        if (0 < g--)
            for (
                h < this.DB &&
                0 < (c = this[g] >> h) &&
                ((e = !0),
                (d = "0123456789abcdefghijklmnopqrstuvwxyz".charAt(c)));
                0 <= g;

            )
                h < a
                    ? ((c = (this[g] & ((1 << h) - 1)) << (a - h)),
                      (c |= this[--g] >> (h += this.DB - a)))
                    : ((c = (this[g] >> (h -= a)) & b),
                      0 >= h && ((h += this.DB), --g)),
                    0 < c && (e = !0),
                    e &&
                        (d += "0123456789abcdefghijklmnopqrstuvwxyz".charAt(c));
        return e ? d : "0";
    };
    k.prototype.negate = function () {
        var a = q();
        k.ZERO.subTo(this, a);
        return a;
    };
    k.prototype.abs = function () {
        return 0 > this.s ? this.negate() : this;
    };
    k.prototype.compareTo = function (a) {
        var b = this.s - a.s;
        if (0 != b) return b;
        var c = this.t;
        b = c - a.t;
        if (0 != b) return 0 > this.s ? -b : b;
        for (; 0 <= --c; ) if (0 != (b = this[c] - a[c])) return b;
        return 0;
    };
    k.prototype.bitLength = function () {
        return 0 >= this.t
            ? 0
            : this.DB * (this.t - 1) + F(this[this.t - 1] ^ (this.s & this.DM));
    };
    k.prototype.mod = function (a) {
        var b = q();
        this.abs().divRemTo(a, null, b);
        0 > this.s && 0 < b.compareTo(k.ZERO) && a.subTo(b, b);
        return b;
    };
    k.prototype.modPowInt = function (a, b) {
        var c = 256 > a || b.isEven() ? new z(b) : new B(b);
        return this.exp(a, c);
    };
    k.ZERO = y(0);
    k.ONE = y(1);
    D.prototype.convert = P;
    D.prototype.revert = P;
    D.prototype.mulTo = function (a, b, c) {
        a.multiplyTo(b, c);
    };
    D.prototype.sqrTo = function (a, b) {
        a.squareTo(b);
    };
    C.prototype.convert = function (a) {
        if (0 > a.s || a.t > 2 * this.m.t) return a.mod(this.m);
        if (0 > a.compareTo(this.m)) return a;
        var b = q();
        a.copyTo(b);
        this.reduce(b);
        return b;
    };
    C.prototype.revert = function (a) {
        return a;
    };
    C.prototype.reduce = function (a) {
        a.drShiftTo(this.m.t - 1, this.r2);
        a.t > this.m.t + 1 && ((a.t = this.m.t + 1), a.clamp());
        this.mu.multiplyUpperTo(this.r2, this.m.t + 1, this.q3);
        for (
            this.m.multiplyLowerTo(this.q3, this.m.t + 1, this.r2);
            0 > a.compareTo(this.r2);

        )
            a.dAddOffset(1, this.m.t + 1);
        for (a.subTo(this.r2, a); 0 <= a.compareTo(this.m); )
            a.subTo(this.m, a);
    };
    C.prototype.mulTo = function (a, b, c) {
        a.multiplyTo(b, c);
        this.reduce(c);
    };
    C.prototype.sqrTo = function (a, b) {
        a.squareTo(b);
        this.reduce(b);
    };
    var w = [
            2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37, 41, 43, 47, 53, 59, 61,
            67, 71, 73, 79, 83, 89, 97, 101, 103, 107, 109, 113, 127, 131, 137,
            139, 149, 151, 157, 163, 167, 173, 179, 181, 191, 193, 197, 199,
            211, 223, 227, 229, 233, 239, 241, 251, 257, 263, 269, 271, 277,
            281, 283, 293, 307, 311, 313, 317, 331, 337, 347, 349, 353, 359,
            367, 373, 379, 383, 389, 397, 401, 409, 419, 421, 431, 433, 439,
            443, 449, 457, 461, 463, 467, 479, 487, 491, 499, 503, 509, 521,
            523, 541, 547, 557, 563, 569, 571, 577, 587, 593, 599, 601, 607,
            613, 617, 619, 631, 641, 643, 647, 653, 659, 661, 673, 677, 683,
            691, 701, 709, 719, 727, 733, 739, 743, 751, 757, 761, 769, 773,
            787, 797, 809, 811, 821, 823, 827, 829, 839, 853, 857, 859, 863,
            877, 881, 883, 887, 907, 911, 919, 929, 937, 941, 947, 953, 967,
            971, 977, 983, 991, 997,
        ],
        W = 67108864 / w[w.length - 1];
    k.prototype.chunkSize = function (a) {
        return Math.floor((Math.LN2 * this.DB) / Math.log(a));
    };
    k.prototype.toRadix = function (a) {
        null == a && (a = 10);
        if (0 == this.signum() || 2 > a || 36 < a) return "0";
        var b = this.chunkSize(a);
        b = Math.pow(a, b);
        var c = y(b),
            e = q(),
            d = q(),
            g = "";
        for (this.divRemTo(c, e, d); 0 < e.signum(); )
            (g = (b + d.intValue()).toString(a).substr(1) + g),
                e.divRemTo(c, e, d);
        return d.intValue().toString(a) + g;
    };
    k.prototype.fromRadix = function (a, b) {
        this.fromInt(0);
        null == b && (b = 10);
        for (
            var c = this.chunkSize(b),
                e = Math.pow(b, c),
                d = !1,
                g = 0,
                h = 0,
                m = 0;
            m < a.length;
            ++m
        ) {
            var l = M(a, m);
            0 > l
                ? "-" == a.charAt(m) && 0 == this.signum() && (d = !0)
                : ((h = b * h + l),
                  ++g >= c &&
                      (this.dMultiply(e), this.dAddOffset(h, 0), (h = g = 0)));
        }
        0 < g && (this.dMultiply(Math.pow(b, g)), this.dAddOffset(h, 0));
        d && k.ZERO.subTo(this, this);
    };
    k.prototype.fromNumber = function (a, b, c) {
        if ("number" == typeof b)
            if (2 > a) this.fromInt(1);
            else
                for (
                    this.fromNumber(a, c),
                        this.testBit(a - 1) ||
                            this.bitwiseTo(k.ONE.shiftLeft(a - 1), H, this),
                        this.isEven() && this.dAddOffset(1, 0);
                    !this.isProbablePrime(b);

                )
                    this.dAddOffset(2, 0),
                        this.bitLength() > a &&
                            this.subTo(k.ONE.shiftLeft(a - 1), this);
        else {
            c = [];
            var e = a & 7;
            c.length = (a >> 3) + 1;
            b.nextBytes(c);
            c[0] = 0 < e ? c[0] & ((1 << e) - 1) : 0;
            this.fromString(c, 256);
        }
    };
    k.prototype.bitwiseTo = function (a, b, c) {
        var e,
            d = Math.min(a.t, this.t);
        for (e = 0; e < d; ++e) c[e] = b(this[e], a[e]);
        if (a.t < this.t) {
            var g = a.s & this.DM;
            for (e = d; e < this.t; ++e) c[e] = b(this[e], g);
            c.t = this.t;
        } else {
            g = this.s & this.DM;
            for (e = d; e < a.t; ++e) c[e] = b(g, a[e]);
            c.t = a.t;
        }
        c.s = b(this.s, a.s);
        c.clamp();
    };
    k.prototype.changeBit = function (a, b) {
        var c = k.ONE.shiftLeft(a);
        this.bitwiseTo(c, b, c);
        return c;
    };
    k.prototype.addTo = function (a, b) {
        for (var c = 0, e = 0, d = Math.min(a.t, this.t); c < d; )
            (e += this[c] + a[c]), (b[c++] = e & this.DM), (e >>= this.DB);
        if (a.t < this.t) {
            for (e += a.s; c < this.t; )
                (e += this[c]), (b[c++] = e & this.DM), (e >>= this.DB);
            e += this.s;
        } else {
            for (e += this.s; c < a.t; )
                (e += a[c]), (b[c++] = e & this.DM), (e >>= this.DB);
            e += a.s;
        }
        b.s = 0 > e ? -1 : 0;
        0 < e ? (b[c++] = e) : -1 > e && (b[c++] = this.DV + e);
        b.t = c;
        b.clamp();
    };
    k.prototype.dMultiply = function (a) {
        this[this.t] = this.am(0, a - 1, this, 0, 0, this.t);
        ++this.t;
        this.clamp();
    };
    k.prototype.dAddOffset = function (a, b) {
        if (0 != a) {
            for (; this.t <= b; ) this[this.t++] = 0;
            for (this[b] += a; this[b] >= this.DV; )
                (this[b] -= this.DV),
                    ++b >= this.t && (this[this.t++] = 0),
                    ++this[b];
        }
    };
    k.prototype.multiplyLowerTo = function (a, b, c) {
        var e = Math.min(this.t + a.t, b);
        c.s = 0;
        for (c.t = e; 0 < e; ) c[--e] = 0;
        var d;
        for (d = c.t - this.t; e < d; ++e)
            c[e + this.t] = this.am(0, a[e], c, e, 0, this.t);
        for (d = Math.min(a.t, b); e < d; ++e) this.am(0, a[e], c, e, 0, b - e);
        c.clamp();
    };
    k.prototype.multiplyUpperTo = function (a, b, c) {
        --b;
        var e = (c.t = this.t + a.t - b);
        for (c.s = 0; 0 <= --e; ) c[e] = 0;
        for (e = Math.max(b - this.t, 0); e < a.t; ++e)
            c[this.t + e - b] = this.am(b - e, a[e], c, 0, 0, this.t + e - b);
        c.clamp();
        c.drShiftTo(1, c);
    };
    k.prototype.modInt = function (a) {
        if (0 >= a) return 0;
        var b = this.DV % a,
            c = 0 > this.s ? a - 1 : 0;
        if (0 < this.t)
            if (0 == b) c = this[0] % a;
            else
                for (var e = this.t - 1; 0 <= e; --e) c = (b * c + this[e]) % a;
        return c;
    };
    k.prototype.millerRabin = function (a) {
        var b = this.subtract(k.ONE),
            c = b.getLowestSetBit();
        if (0 >= c) return !1;
        var e = b.shiftRight(c);
        a = (a + 1) >> 1;
        a > w.length && (a = w.length);
        for (var d = q(), g = 0; g < a; ++g) {
            d.fromInt(w[Math.floor(Math.random() * w.length)]);
            var h = d.modPow(e, this);
            if (0 != h.compareTo(k.ONE) && 0 != h.compareTo(b)) {
                for (var m = 1; m++ < c && 0 != h.compareTo(b); )
                    if (((h = h.modPowInt(2, this)), 0 == h.compareTo(k.ONE)))
                        return !1;
                if (0 != h.compareTo(b)) return !1;
            }
        }
        return !0;
    };
    k.prototype.clone = function () {
        var a = q();
        this.copyTo(a);
        return a;
    };
    k.prototype.intValue = function () {
        if (0 > this.s) {
            if (1 == this.t) return this[0] - this.DV;
            if (0 == this.t) return -1;
        } else {
            if (1 == this.t) return this[0];
            if (0 == this.t) return 0;
        }
        return ((this[1] & ((1 << (32 - this.DB)) - 1)) << this.DB) | this[0];
    };
    k.prototype.byteValue = function () {
        return 0 == this.t ? this.s : (this[0] << 24) >> 24;
    };
    k.prototype.shortValue = function () {
        return 0 == this.t ? this.s : (this[0] << 16) >> 16;
    };
    k.prototype.signum = function () {
        return 0 > this.s
            ? -1
            : 0 >= this.t || (1 == this.t && 0 >= this[0])
            ? 0
            : 1;
    };
    k.prototype.toByteArray = function () {
        var a = this.t,
            b = [];
        b[0] = this.s;
        var c = this.DB - ((a * this.DB) % 8),
            e,
            d = 0;
        if (0 < a--)
            for (
                c < this.DB &&
                (e = this[a] >> c) != (this.s & this.DM) >> c &&
                (b[d++] = e | (this.s << (this.DB - c)));
                0 <= a;

            )
                if (
                    (8 > c
                        ? ((e = (this[a] & ((1 << c) - 1)) << (8 - c)),
                          (e |= this[--a] >> (c += this.DB - 8)))
                        : ((e = (this[a] >> (c -= 8)) & 255),
                          0 >= c && ((c += this.DB), --a)),
                    0 != (e & 128) && (e |= -256),
                    0 == d && (this.s & 128) != (e & 128) && ++d,
                    0 < d || e != this.s)
                )
                    b[d++] = e;
        return b;
    };
    k.prototype.equals = function (a) {
        return 0 == this.compareTo(a);
    };
    k.prototype.min = function (a) {
        return 0 > this.compareTo(a) ? this : a;
    };
    k.prototype.max = function (a) {
        return 0 < this.compareTo(a) ? this : a;
    };
    k.prototype.and = function (a) {
        var b = q();
        this.bitwiseTo(a, U, b);
        return b;
    };
    k.prototype.or = function (a) {
        var b = q();
        this.bitwiseTo(a, H, b);
        return b;
    };
    k.prototype.xor = function (a) {
        var b = q();
        this.bitwiseTo(a, N, b);
        return b;
    };
    k.prototype.andNot = function (a) {
        var b = q();
        this.bitwiseTo(a, O, b);
        return b;
    };
    k.prototype.not = function () {
        for (var a = q(), b = 0; b < this.t; ++b) a[b] = this.DM & ~this[b];
        a.t = this.t;
        a.s = ~this.s;
        return a;
    };
    k.prototype.shiftLeft = function (a) {
        var b = q();
        0 > a ? this.rShiftTo(-a, b) : this.lShiftTo(a, b);
        return b;
    };
    k.prototype.shiftRight = function (a) {
        var b = q();
        0 > a ? this.lShiftTo(-a, b) : this.rShiftTo(a, b);
        return b;
    };
    k.prototype.getLowestSetBit = function () {
        for (var a = 0; a < this.t; ++a)
            if (0 != this[a]) {
                var b = a * this.DB;
                a = this[a];
                if (0 == a) a = -1;
                else {
                    var c = 0;
                    0 == (a & 65535) && ((a >>= 16), (c += 16));
                    0 == (a & 255) && ((a >>= 8), (c += 8));
                    0 == (a & 15) && ((a >>= 4), (c += 4));
                    0 == (a & 3) && ((a >>= 2), (c += 2));
                    0 == (a & 1) && ++c;
                    a = c;
                }
                return b + a;
            }
        return 0 > this.s ? this.t * this.DB : -1;
    };
    k.prototype.bitCount = function () {
        for (var a = 0, b = this.s & this.DM, c = 0; c < this.t; ++c) {
            for (var e = this[c] ^ b, d = 0; 0 != e; ) (e &= e - 1), ++d;
            a += d;
        }
        return a;
    };
    k.prototype.testBit = function (a) {
        var b = Math.floor(a / this.DB);
        return b >= this.t ? 0 != this.s : 0 != (this[b] & (1 << a % this.DB));
    };
    k.prototype.setBit = function (a) {
        return this.changeBit(a, H);
    };
    k.prototype.clearBit = function (a) {
        return this.changeBit(a, O);
    };
    k.prototype.flipBit = function (a) {
        return this.changeBit(a, N);
    };
    k.prototype.add = function (a) {
        var b = q();
        this.addTo(a, b);
        return b;
    };
    k.prototype.subtract = function (a) {
        var b = q();
        this.subTo(a, b);
        return b;
    };
    k.prototype.multiply = function (a) {
        var b = q();
        this.multiplyTo(a, b);
        return b;
    };
    k.prototype.divide = function (a) {
        var b = q();
        this.divRemTo(a, b, null);
        return b;
    };
    k.prototype.remainder = function (a) {
        var b = q();
        this.divRemTo(a, null, b);
        return b;
    };
    k.prototype.divideAndRemainder = function (a) {
        var b = q(),
            c = q();
        this.divRemTo(a, b, c);
        return [b, c];
    };
    k.prototype.modPow = function (a, b) {
        var c = a.bitLength(),
            e = y(1);
        if (0 >= c) return e;
        var d = 18 > c ? 1 : 48 > c ? 3 : 144 > c ? 4 : 768 > c ? 5 : 6;
        var g = 8 > c ? new z(b) : b.isEven() ? new C(b) : new B(b);
        var h = [],
            m = 3,
            k = d - 1,
            n = (1 << d) - 1;
        h[1] = g.convert(this);
        if (1 < d)
            for (c = q(), g.sqrTo(h[1], c); m <= n; )
                (h[m] = q()), g.mulTo(c, h[m - 2], h[m]), (m += 2);
        var r = a.t - 1,
            p = !0,
            t = q();
        for (c = F(a[r]) - 1; 0 <= r; ) {
            if (c >= k) var u = (a[r] >> (c - k)) & n;
            else
                (u = (a[r] & ((1 << (c + 1)) - 1)) << (k - c)),
                    0 < r && (u |= a[r - 1] >> (this.DB + c - k));
            for (m = d; 0 == (u & 1); ) (u >>= 1), --m;
            0 > (c -= m) && ((c += this.DB), --r);
            if (p) h[u].copyTo(e), (p = !1);
            else {
                for (; 1 < m; ) g.sqrTo(e, t), g.sqrTo(t, e), (m -= 2);
                0 < m ? g.sqrTo(e, t) : ((m = e), (e = t), (t = m));
                g.mulTo(t, h[u], e);
            }
            for (; 0 <= r && 0 == (a[r] & (1 << c)); )
                g.sqrTo(e, t),
                    (m = e),
                    (e = t),
                    (t = m),
                    0 > --c && ((c = this.DB - 1), --r);
        }
        return g.revert(e);
    };
    k.prototype.modInverse = function (a) {
        var b = a.isEven();
        if ((this.isEven() && b) || 0 == a.signum()) return k.ZERO;
        for (
            var c = a.clone(),
                e = this.clone(),
                d = y(1),
                g = y(0),
                h = y(0),
                m = y(1);
            0 != c.signum();

        ) {
            for (; c.isEven(); )
                c.rShiftTo(1, c),
                    b
                        ? ((d.isEven() && g.isEven()) ||
                              (d.addTo(this, d), g.subTo(a, g)),
                          d.rShiftTo(1, d))
                        : g.isEven() || g.subTo(a, g),
                    g.rShiftTo(1, g);
            for (; e.isEven(); )
                e.rShiftTo(1, e),
                    b
                        ? ((h.isEven() && m.isEven()) ||
                              (h.addTo(this, h), m.subTo(a, m)),
                          h.rShiftTo(1, h))
                        : m.isEven() || m.subTo(a, m),
                    m.rShiftTo(1, m);
            0 <= c.compareTo(e)
                ? (c.subTo(e, c), b && d.subTo(h, d), g.subTo(m, g))
                : (e.subTo(c, e), b && h.subTo(d, h), m.subTo(g, m));
        }
        if (0 != e.compareTo(k.ONE)) return k.ZERO;
        if (0 <= m.compareTo(a)) return m.subtract(a);
        if (0 > m.signum()) m.addTo(a, m);
        else return m;
        return 0 > m.signum() ? m.add(a) : m;
    };
    k.prototype.pow = function (a) {
        return this.exp(a, new D());
    };
    k.prototype.gcd = function (a) {
        var b = 0 > this.s ? this.negate() : this.clone();
        a = 0 > a.s ? a.negate() : a.clone();
        if (0 > b.compareTo(a)) {
            var c = b;
            b = a;
            a = c;
        }
        c = b.getLowestSetBit();
        var e = a.getLowestSetBit();
        if (0 > e) return b;
        c < e && (e = c);
        0 < e && (b.rShiftTo(e, b), a.rShiftTo(e, a));
        for (; 0 < b.signum(); )
            0 < (c = b.getLowestSetBit()) && b.rShiftTo(c, b),
                0 < (c = a.getLowestSetBit()) && a.rShiftTo(c, a),
                0 <= b.compareTo(a)
                    ? (b.subTo(a, b), b.rShiftTo(1, b))
                    : (a.subTo(b, a), a.rShiftTo(1, a));
        0 < e && a.lShiftTo(e, a);
        return a;
    };
    k.prototype.isProbablePrime = function (a) {
        var b,
            c = this.abs();
        if (1 == c.t && c[0] <= w[w.length - 1]) {
            for (b = 0; b < w.length; ++b) if (c[0] == w[b]) return !0;
            return !1;
        }
        if (c.isEven()) return !1;
        for (b = 1; b < w.length; ) {
            for (var e = w[b], d = b + 1; d < w.length && e < W; ) e *= w[d++];
            for (e = c.modInt(e); b < d; ) if (0 == e % w[b++]) return !1;
        }
        return c.millerRabin(a);
    };
    k.prototype.square = function () {
        var a = q();
        this.squareTo(a);
        return a;
    };
    k.prototype.IsNegative = function () {
        return -1 == this.compareTo(k.ZERO) ? !0 : !1;
    };
    k.op_Equality = function (a, b) {
        return 0 == a.compareTo(b) ? !0 : !1;
    };
    k.op_Inequality = function (a, b) {
        return 0 != a.compareTo(b) ? !0 : !1;
    };
    k.op_GreaterThan = function (a, b) {
        return 0 < a.compareTo(b) ? !0 : !1;
    };
    k.op_LessThan = function (a, b) {
        return 0 > a.compareTo(b) ? !0 : !1;
    };
    k.op_Addition = function (a, b) {
        return new k(a, void 0, void 0).add(new k(b, void 0, void 0));
    };
    k.op_Subtraction = function (a, b) {
        return new k(a, void 0, void 0).subtract(new k(b, void 0, void 0));
    };
    k.Int128Mul = function (a, b) {
        return new k(a, void 0, void 0).multiply(new k(b, void 0, void 0));
    };
    k.op_Division = function (a, b) {
        return a.divide(b);
    };
    k.prototype.ToDouble = function () {
        return parseFloat(this.toString());
    };
    v = function (a, b) {
        var c;
        if ("undefined" === typeof Object.getOwnPropertyNames)
            for (c in b.prototype) {
                if (
                    "undefined" === typeof a.prototype[c] ||
                    a.prototype[c] === Object.prototype[c]
                )
                    a.prototype[c] = b.prototype[c];
            }
        else
            for (
                var e = Object.getOwnPropertyNames(b.prototype), d = 0;
                d < e.length;
                d++
            )
                "undefined" ===
                    typeof Object.getOwnPropertyDescriptor(a.prototype, e[d]) &&
                    Object.defineProperty(
                        a.prototype,
                        e[d],
                        Object.getOwnPropertyDescriptor(b.prototype, e[d])
                    );
        for (c in b) "undefined" === typeof a[c] && (a[c] = b[c]);
        a.$baseCtor = b;
    };
    d.Path = function () {
        return [];
    };
    d.Path.prototype.push = Array.prototype.push;
    d.Paths = function () {
        return [];
    };
    d.Paths.prototype.push = Array.prototype.push;
    d.DoublePoint = function () {
        var a = arguments;
        this.Y = this.X = 0;
        1 === a.length
            ? ((this.X = a[0].X), (this.Y = a[0].Y))
            : 2 === a.length && ((this.X = a[0]), (this.Y = a[1]));
    };
    d.DoublePoint0 = function () {
        this.Y = this.X = 0;
    };
    d.DoublePoint0.prototype = d.DoublePoint.prototype;
    d.DoublePoint1 = function (a) {
        this.X = a.X;
        this.Y = a.Y;
    };
    d.DoublePoint1.prototype = d.DoublePoint.prototype;
    d.DoublePoint2 = function (a, b) {
        this.X = a;
        this.Y = b;
    };
    d.DoublePoint2.prototype = d.DoublePoint.prototype;
    d.PolyNode = function () {
        this.m_Parent = null;
        this.m_polygon = new d.Path();
        this.m_endtype = this.m_jointype = this.m_Index = 0;
        this.m_Childs = [];
        this.IsOpen = !1;
    };
    d.PolyNode.prototype.IsHoleNode = function () {
        for (var a = !0, b = this.m_Parent; null !== b; )
            (a = !a), (b = b.m_Parent);
        return a;
    };
    d.PolyNode.prototype.ChildCount = function () {
        return this.m_Childs.length;
    };
    d.PolyNode.prototype.Contour = function () {
        return this.m_polygon;
    };
    d.PolyNode.prototype.AddChild = function (a) {
        var b = this.m_Childs.length;
        this.m_Childs.push(a);
        a.m_Parent = this;
        a.m_Index = b;
    };
    d.PolyNode.prototype.GetNext = function () {
        return 0 < this.m_Childs.length
            ? this.m_Childs[0]
            : this.GetNextSiblingUp();
    };
    d.PolyNode.prototype.GetNextSiblingUp = function () {
        return null === this.m_Parent
            ? null
            : this.m_Index === this.m_Parent.m_Childs.length - 1
            ? this.m_Parent.GetNextSiblingUp()
            : this.m_Parent.m_Childs[this.m_Index + 1];
    };
    d.PolyNode.prototype.Childs = function () {
        return this.m_Childs;
    };
    d.PolyNode.prototype.Parent = function () {
        return this.m_Parent;
    };
    d.PolyNode.prototype.IsHole = function () {
        return this.IsHoleNode();
    };
    d.PolyTree = function () {
        this.m_AllPolys = [];
        d.PolyNode.call(this);
    };
    d.PolyTree.prototype.Clear = function () {
        for (var a = 0, b = this.m_AllPolys.length; a < b; a++)
            this.m_AllPolys[a] = null;
        this.m_AllPolys.length = 0;
        this.m_Childs.length = 0;
    };
    d.PolyTree.prototype.GetFirst = function () {
        return 0 < this.m_Childs.length ? this.m_Childs[0] : null;
    };
    d.PolyTree.prototype.Total = function () {
        var a = this.m_AllPolys.length;
        0 < a && this.m_Childs[0] !== this.m_AllPolys[0] && a--;
        return a;
    };
    v(d.PolyTree, d.PolyNode);
    d.Math_Abs_Int64 =
        d.Math_Abs_Int32 =
        d.Math_Abs_Double =
            function (a) {
                return Math.abs(a);
            };
    d.Math_Max_Int32_Int32 = function (a, b) {
        return Math.max(a, b);
    };
    d.Cast_Int32 =
        u || K || Q
            ? function (a) {
                  return a | 0;
              }
            : function (a) {
                  return ~~a;
              };
    "undefined" === typeof Number.toInteger && (Number.toInteger = null);
    d.Cast_Int64 = I
        ? function (a) {
              return -2147483648 > a || 2147483647 < a
                  ? 0 > a
                      ? Math.ceil(a)
                      : Math.floor(a)
                  : ~~a;
          }
        : J && "function" === typeof Number.toInteger
        ? function (a) {
              return Number.toInteger(a);
          }
        : V || L
        ? function (a) {
              return parseInt(a, 10);
          }
        : u
        ? function (a) {
              return -2147483648 > a || 2147483647 < a
                  ? 0 > a
                      ? Math.ceil(a)
                      : Math.floor(a)
                  : a | 0;
          }
        : function (a) {
              return 0 > a ? Math.ceil(a) : Math.floor(a);
          };
    d.Clear = function (a) {
        a.length = 0;
    };
    d.PI = 3.141592653589793;
    d.PI2 = 6.283185307179586;
    d.IntPoint = function () {
        var a = arguments;
        var b = a.length;
        this.Y = this.X = 0;
        d.use_xyz
            ? ((this.Z = 0),
              3 === b
                  ? ((this.X = a[0]), (this.Y = a[1]), (this.Z = a[2]))
                  : 2 === b
                  ? ((this.X = a[0]), (this.Y = a[1]), (this.Z = 0))
                  : 1 === b
                  ? a[0] instanceof d.DoublePoint
                      ? ((a = a[0]),
                        (this.X = d.Clipper.Round(a.X)),
                        (this.Y = d.Clipper.Round(a.Y)),
                        (this.Z = 0))
                      : ((a = a[0]),
                        "undefined" === typeof a.Z && (a.Z = 0),
                        (this.X = a.X),
                        (this.Y = a.Y),
                        (this.Z = a.Z))
                  : (this.Z = this.Y = this.X = 0))
            : 2 === b
            ? ((this.X = a[0]), (this.Y = a[1]))
            : 1 === b
            ? a[0] instanceof d.DoublePoint
                ? ((a = a[0]),
                  (this.X = d.Clipper.Round(a.X)),
                  (this.Y = d.Clipper.Round(a.Y)))
                : ((a = a[0]), (this.X = a.X), (this.Y = a.Y))
            : (this.Y = this.X = 0);
    };
    d.IntPoint.op_Equality = function (a, b) {
        return a.X === b.X && a.Y === b.Y;
    };
    d.IntPoint.op_Inequality = function (a, b) {
        return a.X !== b.X || a.Y !== b.Y;
    };
    d.IntPoint0 = function () {
        this.Y = this.X = 0;
        d.use_xyz && (this.Z = 0);
    };
    d.IntPoint0.prototype = d.IntPoint.prototype;
    d.IntPoint1 = function (a) {
        this.X = a.X;
        this.Y = a.Y;
        d.use_xyz && (this.Z = "undefined" === typeof a.Z ? 0 : a.Z);
    };
    d.IntPoint1.prototype = d.IntPoint.prototype;
    d.IntPoint1dp = function (a) {
        this.X = d.Clipper.Round(a.X);
        this.Y = d.Clipper.Round(a.Y);
        d.use_xyz && (this.Z = 0);
    };
    d.IntPoint1dp.prototype = d.IntPoint.prototype;
    d.IntPoint2 = function (a, b, c) {
        this.X = a;
        this.Y = b;
        d.use_xyz && (this.Z = "undefined" === typeof c ? 0 : c);
    };
    d.IntPoint2.prototype = d.IntPoint.prototype;
    d.IntRect = function () {
        var a = arguments,
            b = a.length;
        4 === b
            ? ((this.left = a[0]),
              (this.top = a[1]),
              (this.right = a[2]),
              (this.bottom = a[3]))
            : 1 === b
            ? ((a = a[0]),
              (this.left = a.left),
              (this.top = a.top),
              (this.right = a.right),
              (this.bottom = a.bottom))
            : (this.bottom = this.right = this.top = this.left = 0);
    };
    d.IntRect0 = function () {
        this.bottom = this.right = this.top = this.left = 0;
    };
    d.IntRect0.prototype = d.IntRect.prototype;
    d.IntRect1 = function (a) {
        this.left = a.left;
        this.top = a.top;
        this.right = a.right;
        this.bottom = a.bottom;
    };
    d.IntRect1.prototype = d.IntRect.prototype;
    d.IntRect4 = function (a, b, c, e) {
        this.left = a;
        this.top = b;
        this.right = c;
        this.bottom = e;
    };
    d.IntRect4.prototype = d.IntRect.prototype;
    d.ClipType = { ctIntersection: 0, ctUnion: 1, ctDifference: 2, ctXor: 3 };
    d.PolyType = { ptSubject: 0, ptClip: 1 };
    d.PolyFillType = {
        pftEvenOdd: 0,
        pftNonZero: 1,
        pftPositive: 2,
        pftNegative: 3,
    };
    d.JoinType = { jtSquare: 0, jtRound: 1, jtMiter: 2 };
    d.EndType = {
        etOpenSquare: 0,
        etOpenRound: 1,
        etOpenButt: 2,
        etClosedLine: 3,
        etClosedPolygon: 4,
    };
    d.EdgeSide = { esLeft: 0, esRight: 1 };
    d.Direction = { dRightToLeft: 0, dLeftToRight: 1 };
    d.TEdge = function () {
        this.Bot = new d.IntPoint0();
        this.Curr = new d.IntPoint0();
        this.Top = new d.IntPoint0();
        this.Delta = new d.IntPoint0();
        this.Dx = 0;
        this.PolyTyp = d.PolyType.ptSubject;
        this.Side = d.EdgeSide.esLeft;
        this.OutIdx = this.WindCnt2 = this.WindCnt = this.WindDelta = 0;
        this.PrevInSEL =
            this.NextInSEL =
            this.PrevInAEL =
            this.NextInAEL =
            this.NextInLML =
            this.Prev =
            this.Next =
                null;
    };
    d.IntersectNode = function () {
        this.Edge2 = this.Edge1 = null;
        this.Pt = new d.IntPoint0();
    };
    d.MyIntersectNodeSort = function () {};
    d.MyIntersectNodeSort.Compare = function (a, b) {
        var c = b.Pt.Y - a.Pt.Y;
        return 0 < c ? 1 : 0 > c ? -1 : 0;
    };
    d.LocalMinima = function () {
        this.Y = 0;
        this.Next = this.RightBound = this.LeftBound = null;
    };
    d.Scanbeam = function () {
        this.Y = 0;
        this.Next = null;
    };
    d.Maxima = function () {
        this.X = 0;
        this.Prev = this.Next = null;
    };
    d.OutRec = function () {
        this.Idx = 0;
        this.IsOpen = this.IsHole = !1;
        this.PolyNode = this.BottomPt = this.Pts = this.FirstLeft = null;
    };
    d.OutPt = function () {
        this.Idx = 0;
        this.Pt = new d.IntPoint0();
        this.Prev = this.Next = null;
    };
    d.Join = function () {
        this.OutPt2 = this.OutPt1 = null;
        this.OffPt = new d.IntPoint0();
    };
    d.ClipperBase = function () {
        this.m_CurrentLM = this.m_MinimaList = null;
        this.m_edges = [];
        this.PreserveCollinear = this.m_HasOpenPaths = this.m_UseFullRange = !1;
        this.m_ActiveEdges = this.m_PolyOuts = this.m_Scanbeam = null;
    };
    d.ClipperBase.horizontal = -9007199254740992;
    d.ClipperBase.Skip = -2;
    d.ClipperBase.Unassigned = -1;
    d.ClipperBase.tolerance = 1e-20;
    d.ClipperBase.loRange = 47453132;
    d.ClipperBase.hiRange = 0xfffffffffffff;
    d.ClipperBase.near_zero = function (a) {
        return a > -d.ClipperBase.tolerance && a < d.ClipperBase.tolerance;
    };
    d.ClipperBase.IsHorizontal = function (a) {
        return 0 === a.Delta.Y;
    };
    d.ClipperBase.prototype.PointIsVertex = function (a, b) {
        var c = b;
        do {
            if (d.IntPoint.op_Equality(c.Pt, a)) return !0;
            c = c.Next;
        } while (c !== b);
        return !1;
    };
    d.ClipperBase.prototype.PointOnLineSegment = function (a, b, c, e) {
        return e
            ? (a.X === b.X && a.Y === b.Y) ||
                  (a.X === c.X && a.Y === c.Y) ||
                  (a.X > b.X === a.X < c.X &&
                      a.Y > b.Y === a.Y < c.Y &&
                      k.op_Equality(
                          k.Int128Mul(a.X - b.X, c.Y - b.Y),
                          k.Int128Mul(c.X - b.X, a.Y - b.Y)
                      ))
            : (a.X === b.X && a.Y === b.Y) ||
                  (a.X === c.X && a.Y === c.Y) ||
                  (a.X > b.X === a.X < c.X &&
                      a.Y > b.Y === a.Y < c.Y &&
                      (a.X - b.X) * (c.Y - b.Y) === (c.X - b.X) * (a.Y - b.Y));
    };
    d.ClipperBase.prototype.PointOnPolygon = function (a, b, c) {
        for (var e = b; ; ) {
            if (this.PointOnLineSegment(a, e.Pt, e.Next.Pt, c)) return !0;
            e = e.Next;
            if (e === b) break;
        }
        return !1;
    };
    d.ClipperBase.prototype.SlopesEqual = d.ClipperBase.SlopesEqual =
        function () {
            var a = arguments,
                b = a.length;
            if (3 === b) {
                b = a[0];
                var c = a[1];
                return (a = a[2])
                    ? k.op_Equality(
                          k.Int128Mul(b.Delta.Y, c.Delta.X),
                          k.Int128Mul(b.Delta.X, c.Delta.Y)
                      )
                    : d.Cast_Int64(b.Delta.Y * c.Delta.X) ===
                          d.Cast_Int64(b.Delta.X * c.Delta.Y);
            }
            if (4 === b) {
                b = a[0];
                c = a[1];
                var e = a[2];
                return (a = a[3])
                    ? k.op_Equality(
                          k.Int128Mul(b.Y - c.Y, c.X - e.X),
                          k.Int128Mul(b.X - c.X, c.Y - e.Y)
                      )
                    : 0 ===
                          d.Cast_Int64((b.Y - c.Y) * (c.X - e.X)) -
                              d.Cast_Int64((b.X - c.X) * (c.Y - e.Y));
            }
            b = a[0];
            c = a[1];
            e = a[2];
            var f = a[3];
            return (a = a[4])
                ? k.op_Equality(
                      k.Int128Mul(b.Y - c.Y, e.X - f.X),
                      k.Int128Mul(b.X - c.X, e.Y - f.Y)
                  )
                : 0 ===
                      d.Cast_Int64((b.Y - c.Y) * (e.X - f.X)) -
                          d.Cast_Int64((b.X - c.X) * (e.Y - f.Y));
        };
    d.ClipperBase.SlopesEqual3 = function (a, b, c) {
        return c
            ? k.op_Equality(
                  k.Int128Mul(a.Delta.Y, b.Delta.X),
                  k.Int128Mul(a.Delta.X, b.Delta.Y)
              )
            : d.Cast_Int64(a.Delta.Y * b.Delta.X) ===
                  d.Cast_Int64(a.Delta.X * b.Delta.Y);
    };
    d.ClipperBase.SlopesEqual4 = function (a, b, c, e) {
        return e
            ? k.op_Equality(
                  k.Int128Mul(a.Y - b.Y, b.X - c.X),
                  k.Int128Mul(a.X - b.X, b.Y - c.Y)
              )
            : 0 ===
                  d.Cast_Int64((a.Y - b.Y) * (b.X - c.X)) -
                      d.Cast_Int64((a.X - b.X) * (b.Y - c.Y));
    };
    d.ClipperBase.SlopesEqual5 = function (a, b, c, e, f) {
        return f
            ? k.op_Equality(
                  k.Int128Mul(a.Y - b.Y, c.X - e.X),
                  k.Int128Mul(a.X - b.X, c.Y - e.Y)
              )
            : 0 ===
                  d.Cast_Int64((a.Y - b.Y) * (c.X - e.X)) -
                      d.Cast_Int64((a.X - b.X) * (c.Y - e.Y));
    };
    d.ClipperBase.prototype.Clear = function () {
        this.DisposeLocalMinimaList();
        for (var a = 0, b = this.m_edges.length; a < b; ++a) {
            for (var c = 0, e = this.m_edges[a].length; c < e; ++c)
                this.m_edges[a][c] = null;
            d.Clear(this.m_edges[a]);
        }
        d.Clear(this.m_edges);
        this.m_HasOpenPaths = this.m_UseFullRange = !1;
    };
    d.ClipperBase.prototype.DisposeLocalMinimaList = function () {
        for (; null !== this.m_MinimaList; ) {
            var a = this.m_MinimaList.Next;
            this.m_MinimaList = null;
            this.m_MinimaList = a;
        }
        this.m_CurrentLM = null;
    };
    d.ClipperBase.prototype.RangeTest = function (a, b) {
        if (b.Value)
            (a.X > d.ClipperBase.hiRange ||
                a.Y > d.ClipperBase.hiRange ||
                -a.X > d.ClipperBase.hiRange ||
                -a.Y > d.ClipperBase.hiRange) &&
                d.Error("Coordinate outside allowed range in RangeTest().");
        else if (
            a.X > d.ClipperBase.loRange ||
            a.Y > d.ClipperBase.loRange ||
            -a.X > d.ClipperBase.loRange ||
            -a.Y > d.ClipperBase.loRange
        )
            (b.Value = !0), this.RangeTest(a, b);
    };
    d.ClipperBase.prototype.InitEdge = function (a, b, c, e) {
        a.Next = b;
        a.Prev = c;
        a.Curr.X = e.X;
        a.Curr.Y = e.Y;
        d.use_xyz && (a.Curr.Z = e.Z);
        a.OutIdx = -1;
    };
    d.ClipperBase.prototype.InitEdge2 = function (a, b) {
        a.Curr.Y >= a.Next.Curr.Y
            ? ((a.Bot.X = a.Curr.X),
              (a.Bot.Y = a.Curr.Y),
              d.use_xyz && (a.Bot.Z = a.Curr.Z),
              (a.Top.X = a.Next.Curr.X),
              (a.Top.Y = a.Next.Curr.Y),
              d.use_xyz && (a.Top.Z = a.Next.Curr.Z))
            : ((a.Top.X = a.Curr.X),
              (a.Top.Y = a.Curr.Y),
              d.use_xyz && (a.Top.Z = a.Curr.Z),
              (a.Bot.X = a.Next.Curr.X),
              (a.Bot.Y = a.Next.Curr.Y),
              d.use_xyz && (a.Bot.Z = a.Next.Curr.Z));
        this.SetDx(a);
        a.PolyTyp = b;
    };
    d.ClipperBase.prototype.FindNextLocMin = function (a) {
        for (var b; ; ) {
            for (
                ;
                d.IntPoint.op_Inequality(a.Bot, a.Prev.Bot) ||
                d.IntPoint.op_Equality(a.Curr, a.Top);

            )
                a = a.Next;
            if (
                a.Dx !== d.ClipperBase.horizontal &&
                a.Prev.Dx !== d.ClipperBase.horizontal
            )
                break;
            for (; a.Prev.Dx === d.ClipperBase.horizontal; ) a = a.Prev;
            for (b = a; a.Dx === d.ClipperBase.horizontal; ) a = a.Next;
            if (a.Top.Y !== a.Prev.Bot.Y) {
                b.Prev.Bot.X < a.Bot.X && (a = b);
                break;
            }
        }
        return a;
    };
    d.ClipperBase.prototype.ProcessBound = function (a, b) {
        var c = a,
            e;
        if (c.OutIdx === d.ClipperBase.Skip) {
            a = c;
            if (b) {
                for (; a.Top.Y === a.Next.Bot.Y; ) a = a.Next;
                for (; a !== c && a.Dx === d.ClipperBase.horizontal; )
                    a = a.Prev;
            } else {
                for (; a.Top.Y === a.Prev.Bot.Y; ) a = a.Prev;
                for (; a !== c && a.Dx === d.ClipperBase.horizontal; )
                    a = a.Next;
            }
            if (a === c) c = b ? a.Next : a.Prev;
            else {
                a = b ? c.Next : c.Prev;
                var f = new d.LocalMinima();
                f.Next = null;
                f.Y = a.Bot.Y;
                f.LeftBound = null;
                f.RightBound = a;
                a.WindDelta = 0;
                c = this.ProcessBound(a, b);
                this.InsertLocalMinima(f);
            }
            return c;
        }
        a.Dx === d.ClipperBase.horizontal &&
            ((f = b ? a.Prev : a.Next),
            f.Dx === d.ClipperBase.horizontal
                ? f.Bot.X !== a.Bot.X &&
                  f.Top.X !== a.Bot.X &&
                  this.ReverseHorizontal(a)
                : f.Bot.X !== a.Bot.X && this.ReverseHorizontal(a));
        f = a;
        if (b) {
            for (
                ;
                c.Top.Y === c.Next.Bot.Y &&
                c.Next.OutIdx !== d.ClipperBase.Skip;

            )
                c = c.Next;
            if (
                c.Dx === d.ClipperBase.horizontal &&
                c.Next.OutIdx !== d.ClipperBase.Skip
            ) {
                for (e = c; e.Prev.Dx === d.ClipperBase.horizontal; )
                    e = e.Prev;
                e.Prev.Top.X > c.Next.Top.X && (c = e.Prev);
            }
            for (; a !== c; )
                (a.NextInLML = a.Next),
                    a.Dx === d.ClipperBase.horizontal &&
                        a !== f &&
                        a.Bot.X !== a.Prev.Top.X &&
                        this.ReverseHorizontal(a),
                    (a = a.Next);
            a.Dx === d.ClipperBase.horizontal &&
                a !== f &&
                a.Bot.X !== a.Prev.Top.X &&
                this.ReverseHorizontal(a);
            c = c.Next;
        } else {
            for (
                ;
                c.Top.Y === c.Prev.Bot.Y &&
                c.Prev.OutIdx !== d.ClipperBase.Skip;

            )
                c = c.Prev;
            if (
                c.Dx === d.ClipperBase.horizontal &&
                c.Prev.OutIdx !== d.ClipperBase.Skip
            ) {
                for (e = c; e.Next.Dx === d.ClipperBase.horizontal; )
                    e = e.Next;
                if (
                    e.Next.Top.X === c.Prev.Top.X ||
                    e.Next.Top.X > c.Prev.Top.X
                )
                    c = e.Next;
            }
            for (; a !== c; )
                (a.NextInLML = a.Prev),
                    a.Dx === d.ClipperBase.horizontal &&
                        a !== f &&
                        a.Bot.X !== a.Next.Top.X &&
                        this.ReverseHorizontal(a),
                    (a = a.Prev);
            a.Dx === d.ClipperBase.horizontal &&
                a !== f &&
                a.Bot.X !== a.Next.Top.X &&
                this.ReverseHorizontal(a);
            c = c.Prev;
        }
        return c;
    };
    d.ClipperBase.prototype.AddPath = function (a, b, c) {
        d.use_lines
            ? c ||
              b !== d.PolyType.ptClip ||
              d.Error("AddPath: Open paths must be subject.")
            : c || d.Error("AddPath: Open paths have been disabled.");
        var e = a.length - 1;
        if (c) for (; 0 < e && d.IntPoint.op_Equality(a[e], a[0]); ) --e;
        for (; 0 < e && d.IntPoint.op_Equality(a[e], a[e - 1]); ) --e;
        if ((c && 2 > e) || (!c && 1 > e)) return !1;
        for (var f = [], g = 0; g <= e; g++) f.push(new d.TEdge());
        var h = !0;
        f[1].Curr.X = a[1].X;
        f[1].Curr.Y = a[1].Y;
        d.use_xyz && (f[1].Curr.Z = a[1].Z);
        var m = { Value: this.m_UseFullRange };
        this.RangeTest(a[0], m);
        this.m_UseFullRange = m.Value;
        m.Value = this.m_UseFullRange;
        this.RangeTest(a[e], m);
        this.m_UseFullRange = m.Value;
        this.InitEdge(f[0], f[1], f[e], a[0]);
        this.InitEdge(f[e], f[0], f[e - 1], a[e]);
        for (g = e - 1; 1 <= g; --g)
            (m.Value = this.m_UseFullRange),
                this.RangeTest(a[g], m),
                (this.m_UseFullRange = m.Value),
                this.InitEdge(f[g], f[g + 1], f[g - 1], a[g]);
        for (g = a = e = f[0]; ; )
            if (a.Curr !== a.Next.Curr || (!c && a.Next === e)) {
                if (a.Prev === a.Next) break;
                else if (
                    c &&
                    d.ClipperBase.SlopesEqual4(
                        a.Prev.Curr,
                        a.Curr,
                        a.Next.Curr,
                        this.m_UseFullRange
                    ) &&
                    (!this.PreserveCollinear ||
                        !this.Pt2IsBetweenPt1AndPt3(
                            a.Prev.Curr,
                            a.Curr,
                            a.Next.Curr
                        ))
                ) {
                    a === e && (e = a.Next);
                    a = this.RemoveEdge(a);
                    g = a = a.Prev;
                    continue;
                }
                a = a.Next;
                if (a === g || (!c && a.Next === e)) break;
            } else {
                if (a === a.Next) break;
                a === e && (e = a.Next);
                g = a = this.RemoveEdge(a);
            }
        if ((!c && a === a.Next) || (c && a.Prev === a.Next)) return !1;
        c || ((this.m_HasOpenPaths = !0), (e.Prev.OutIdx = d.ClipperBase.Skip));
        a = e;
        do
            this.InitEdge2(a, b),
                (a = a.Next),
                h && a.Curr.Y !== e.Curr.Y && (h = !1);
        while (a !== e);
        if (h) {
            if (c) return !1;
            a.Prev.OutIdx = d.ClipperBase.Skip;
            b = new d.LocalMinima();
            b.Next = null;
            b.Y = a.Bot.Y;
            b.LeftBound = null;
            b.RightBound = a;
            b.RightBound.Side = d.EdgeSide.esRight;
            for (b.RightBound.WindDelta = 0; ; ) {
                a.Bot.X !== a.Prev.Top.X && this.ReverseHorizontal(a);
                if (a.Next.OutIdx === d.ClipperBase.Skip) break;
                a = a.NextInLML = a.Next;
            }
            this.InsertLocalMinima(b);
            this.m_edges.push(f);
            return !0;
        }
        this.m_edges.push(f);
        h = null;
        d.IntPoint.op_Equality(a.Prev.Bot, a.Prev.Top) && (a = a.Next);
        for (;;) {
            a = this.FindNextLocMin(a);
            if (a === h) break;
            else null === h && (h = a);
            b = new d.LocalMinima();
            b.Next = null;
            b.Y = a.Bot.Y;
            a.Dx < a.Prev.Dx
                ? ((b.LeftBound = a.Prev), (b.RightBound = a), (f = !1))
                : ((b.LeftBound = a), (b.RightBound = a.Prev), (f = !0));
            b.LeftBound.Side = d.EdgeSide.esLeft;
            b.RightBound.Side = d.EdgeSide.esRight;
            b.LeftBound.WindDelta = c
                ? b.LeftBound.Next === b.RightBound
                    ? -1
                    : 1
                : 0;
            b.RightBound.WindDelta = -b.LeftBound.WindDelta;
            a = this.ProcessBound(b.LeftBound, f);
            a.OutIdx === d.ClipperBase.Skip && (a = this.ProcessBound(a, f));
            e = this.ProcessBound(b.RightBound, !f);
            e.OutIdx === d.ClipperBase.Skip && (e = this.ProcessBound(e, !f));
            b.LeftBound.OutIdx === d.ClipperBase.Skip
                ? (b.LeftBound = null)
                : b.RightBound.OutIdx === d.ClipperBase.Skip &&
                  (b.RightBound = null);
            this.InsertLocalMinima(b);
            f || (a = e);
        }
        return !0;
    };
    d.ClipperBase.prototype.AddPaths = function (a, b, c) {
        for (var e = !1, d = 0, g = a.length; d < g; ++d)
            this.AddPath(a[d], b, c) && (e = !0);
        return e;
    };
    d.ClipperBase.prototype.Pt2IsBetweenPt1AndPt3 = function (a, b, c) {
        return d.IntPoint.op_Equality(a, c) ||
            d.IntPoint.op_Equality(a, b) ||
            d.IntPoint.op_Equality(c, b)
            ? !1
            : a.X !== c.X
            ? b.X > a.X === b.X < c.X
            : b.Y > a.Y === b.Y < c.Y;
    };
    d.ClipperBase.prototype.RemoveEdge = function (a) {
        a.Prev.Next = a.Next;
        a.Next.Prev = a.Prev;
        var b = a.Next;
        a.Prev = null;
        return b;
    };
    d.ClipperBase.prototype.SetDx = function (a) {
        a.Delta.X = a.Top.X - a.Bot.X;
        a.Delta.Y = a.Top.Y - a.Bot.Y;
        a.Dx =
            0 === a.Delta.Y ? d.ClipperBase.horizontal : a.Delta.X / a.Delta.Y;
    };
    d.ClipperBase.prototype.InsertLocalMinima = function (a) {
        if (null === this.m_MinimaList) this.m_MinimaList = a;
        else if (a.Y >= this.m_MinimaList.Y)
            (a.Next = this.m_MinimaList), (this.m_MinimaList = a);
        else {
            for (var b = this.m_MinimaList; null !== b.Next && a.Y < b.Next.Y; )
                b = b.Next;
            a.Next = b.Next;
            b.Next = a;
        }
    };
    d.ClipperBase.prototype.PopLocalMinima = function (a, b) {
        b.v = this.m_CurrentLM;
        return null !== this.m_CurrentLM && this.m_CurrentLM.Y === a
            ? ((this.m_CurrentLM = this.m_CurrentLM.Next), !0)
            : !1;
    };
    d.ClipperBase.prototype.ReverseHorizontal = function (a) {
        var b = a.Top.X;
        a.Top.X = a.Bot.X;
        a.Bot.X = b;
        d.use_xyz && ((b = a.Top.Z), (a.Top.Z = a.Bot.Z), (a.Bot.Z = b));
    };
    d.ClipperBase.prototype.Reset = function () {
        this.m_CurrentLM = this.m_MinimaList;
        if (null !== this.m_CurrentLM) {
            this.m_Scanbeam = null;
            for (var a = this.m_MinimaList; null !== a; ) {
                this.InsertScanbeam(a.Y);
                var b = a.LeftBound;
                null !== b &&
                    ((b.Curr.X = b.Bot.X),
                    (b.Curr.Y = b.Bot.Y),
                    d.use_xyz && (b.Curr.Z = b.Bot.Z),
                    (b.OutIdx = d.ClipperBase.Unassigned));
                b = a.RightBound;
                null !== b &&
                    ((b.Curr.X = b.Bot.X),
                    (b.Curr.Y = b.Bot.Y),
                    d.use_xyz && (b.Curr.Z = b.Bot.Z),
                    (b.OutIdx = d.ClipperBase.Unassigned));
                a = a.Next;
            }
            this.m_ActiveEdges = null;
        }
    };
    d.ClipperBase.prototype.InsertScanbeam = function (a) {
        if (null === this.m_Scanbeam)
            (this.m_Scanbeam = new d.Scanbeam()),
                (this.m_Scanbeam.Next = null),
                (this.m_Scanbeam.Y = a);
        else if (a > this.m_Scanbeam.Y) {
            var b = new d.Scanbeam();
            b.Y = a;
            b.Next = this.m_Scanbeam;
            this.m_Scanbeam = b;
        } else {
            for (b = this.m_Scanbeam; null !== b.Next && a <= b.Next.Y; )
                b = b.Next;
            if (a !== b.Y) {
                var c = new d.Scanbeam();
                c.Y = a;
                c.Next = b.Next;
                b.Next = c;
            }
        }
    };
    d.ClipperBase.prototype.PopScanbeam = function (a) {
        if (null === this.m_Scanbeam) return (a.v = 0), !1;
        a.v = this.m_Scanbeam.Y;
        this.m_Scanbeam = this.m_Scanbeam.Next;
        return !0;
    };
    d.ClipperBase.prototype.LocalMinimaPending = function () {
        return null !== this.m_CurrentLM;
    };
    d.ClipperBase.prototype.CreateOutRec = function () {
        var a = new d.OutRec();
        a.Idx = d.ClipperBase.Unassigned;
        a.IsHole = !1;
        a.IsOpen = !1;
        a.FirstLeft = null;
        a.Pts = null;
        a.BottomPt = null;
        a.PolyNode = null;
        this.m_PolyOuts.push(a);
        a.Idx = this.m_PolyOuts.length - 1;
        return a;
    };
    d.ClipperBase.prototype.DisposeOutRec = function (a) {
        this.m_PolyOuts[a].Pts = null;
        this.m_PolyOuts[a] = null;
    };
    d.ClipperBase.prototype.UpdateEdgeIntoAEL = function (a) {
        null === a.NextInLML && d.Error("UpdateEdgeIntoAEL: invalid call");
        var b = a.PrevInAEL,
            c = a.NextInAEL;
        a.NextInLML.OutIdx = a.OutIdx;
        null !== b
            ? (b.NextInAEL = a.NextInLML)
            : (this.m_ActiveEdges = a.NextInLML);
        null !== c && (c.PrevInAEL = a.NextInLML);
        a.NextInLML.Side = a.Side;
        a.NextInLML.WindDelta = a.WindDelta;
        a.NextInLML.WindCnt = a.WindCnt;
        a.NextInLML.WindCnt2 = a.WindCnt2;
        a = a.NextInLML;
        a.Curr.X = a.Bot.X;
        a.Curr.Y = a.Bot.Y;
        a.PrevInAEL = b;
        a.NextInAEL = c;
        d.ClipperBase.IsHorizontal(a) || this.InsertScanbeam(a.Top.Y);
        return a;
    };
    d.ClipperBase.prototype.SwapPositionsInAEL = function (a, b) {
        if (a.NextInAEL !== a.PrevInAEL && b.NextInAEL !== b.PrevInAEL) {
            if (a.NextInAEL === b) {
                var c = b.NextInAEL;
                null !== c && (c.PrevInAEL = a);
                var e = a.PrevInAEL;
                null !== e && (e.NextInAEL = b);
                b.PrevInAEL = e;
                b.NextInAEL = a;
                a.PrevInAEL = b;
                a.NextInAEL = c;
            } else
                b.NextInAEL === a
                    ? ((c = a.NextInAEL),
                      null !== c && (c.PrevInAEL = b),
                      (e = b.PrevInAEL),
                      null !== e && (e.NextInAEL = a),
                      (a.PrevInAEL = e),
                      (a.NextInAEL = b),
                      (b.PrevInAEL = a),
                      (b.NextInAEL = c))
                    : ((c = a.NextInAEL),
                      (e = a.PrevInAEL),
                      (a.NextInAEL = b.NextInAEL),
                      null !== a.NextInAEL && (a.NextInAEL.PrevInAEL = a),
                      (a.PrevInAEL = b.PrevInAEL),
                      null !== a.PrevInAEL && (a.PrevInAEL.NextInAEL = a),
                      (b.NextInAEL = c),
                      null !== b.NextInAEL && (b.NextInAEL.PrevInAEL = b),
                      (b.PrevInAEL = e),
                      null !== b.PrevInAEL && (b.PrevInAEL.NextInAEL = b));
            null === a.PrevInAEL
                ? (this.m_ActiveEdges = a)
                : null === b.PrevInAEL && (this.m_ActiveEdges = b);
        }
    };
    d.ClipperBase.prototype.DeleteFromAEL = function (a) {
        var b = a.PrevInAEL,
            c = a.NextInAEL;
        if (null !== b || null !== c || a === this.m_ActiveEdges)
            null !== b ? (b.NextInAEL = c) : (this.m_ActiveEdges = c),
                null !== c && (c.PrevInAEL = b),
                (a.NextInAEL = null),
                (a.PrevInAEL = null);
    };
    d.Clipper = function (a) {
        "undefined" === typeof a && (a = 0);
        this.m_PolyOuts = null;
        this.m_ClipType = d.ClipType.ctIntersection;
        this.m_IntersectNodeComparer =
            this.m_IntersectList =
            this.m_SortedEdges =
            this.m_ActiveEdges =
            this.m_Maxima =
            this.m_Scanbeam =
                null;
        this.m_ExecuteLocked = !1;
        this.m_SubjFillType = this.m_ClipFillType = d.PolyFillType.pftEvenOdd;
        this.m_GhostJoins = this.m_Joins = null;
        this.StrictlySimple = this.ReverseSolution = this.m_UsingPolyTree = !1;
        d.ClipperBase.call(this);
        this.m_SortedEdges =
            this.m_ActiveEdges =
            this.m_Maxima =
            this.m_Scanbeam =
                null;
        this.m_IntersectList = [];
        this.m_IntersectNodeComparer = d.MyIntersectNodeSort.Compare;
        this.m_UsingPolyTree = this.m_ExecuteLocked = !1;
        this.m_PolyOuts = [];
        this.m_Joins = [];
        this.m_GhostJoins = [];
        this.ReverseSolution = 0 !== (1 & a);
        this.StrictlySimple = 0 !== (2 & a);
        this.PreserveCollinear = 0 !== (4 & a);
        d.use_xyz && (this.ZFillFunction = null);
    };
    d.Clipper.ioReverseSolution = 1;
    d.Clipper.ioStrictlySimple = 2;
    d.Clipper.ioPreserveCollinear = 4;
    d.Clipper.prototype.Clear = function () {
        0 !== this.m_edges.length &&
            (this.DisposeAllPolyPts(),
            d.ClipperBase.prototype.Clear.call(this));
    };
    d.Clipper.prototype.InsertMaxima = function (a) {
        var b = new d.Maxima();
        b.X = a;
        if (null === this.m_Maxima)
            (this.m_Maxima = b),
                (this.m_Maxima.Next = null),
                (this.m_Maxima.Prev = null);
        else if (a < this.m_Maxima.X)
            (b.Next = this.m_Maxima), (b.Prev = null), (this.m_Maxima = b);
        else {
            for (var c = this.m_Maxima; null !== c.Next && a >= c.Next.X; )
                c = c.Next;
            a !== c.X &&
                ((b.Next = c.Next),
                (b.Prev = c),
                null !== c.Next && (c.Next.Prev = b),
                (c.Next = b));
        }
    };
    d.Clipper.prototype.Execute = function () {
        var a;
        var b = arguments;
        var c = b.length;
        var e = b[1] instanceof d.PolyTree;
        if (4 !== c || e) {
            if (4 === c && e) {
                c = b[0];
                var f = b[1];
                e = b[2];
                b = b[3];
                if (this.m_ExecuteLocked) return !1;
                this.m_ExecuteLocked = !0;
                this.m_SubjFillType = e;
                this.m_ClipFillType = b;
                this.m_ClipType = c;
                this.m_UsingPolyTree = !0;
                try {
                    (a = this.ExecuteInternal()) && this.BuildResult2(f);
                } finally {
                    this.DisposeAllPolyPts(), (this.m_ExecuteLocked = !1);
                }
                return a;
            }
            if ((2 === c && !e) || (2 === c && e))
                return (
                    (c = b[0]),
                    (f = b[1]),
                    this.Execute(
                        c,
                        f,
                        d.PolyFillType.pftEvenOdd,
                        d.PolyFillType.pftEvenOdd
                    )
                );
        } else {
            c = b[0];
            f = b[1];
            e = b[2];
            b = b[3];
            if (this.m_ExecuteLocked) return !1;
            this.m_HasOpenPaths &&
                d.Error(
                    "Error: PolyTree struct is needed for open path clipping."
                );
            this.m_ExecuteLocked = !0;
            d.Clear(f);
            this.m_SubjFillType = e;
            this.m_ClipFillType = b;
            this.m_ClipType = c;
            this.m_UsingPolyTree = !1;
            try {
                (a = this.ExecuteInternal()) && this.BuildResult(f);
            } finally {
                this.DisposeAllPolyPts(), (this.m_ExecuteLocked = !1);
            }
            return a;
        }
    };
    d.Clipper.prototype.FixHoleLinkage = function (a) {
        if (
            null !== a.FirstLeft &&
            (a.IsHole === a.FirstLeft.IsHole || null === a.FirstLeft.Pts)
        ) {
            for (
                var b = a.FirstLeft;
                null !== b && (b.IsHole === a.IsHole || null === b.Pts);

            )
                b = b.FirstLeft;
            a.FirstLeft = b;
        }
    };
    d.Clipper.prototype.ExecuteInternal = function () {
        try {
            this.Reset();
            this.m_Maxima = this.m_SortedEdges = null;
            var a = {},
                b = {};
            if (!this.PopScanbeam(a)) return !1;
            for (
                this.InsertLocalMinimaIntoAEL(a.v);
                this.PopScanbeam(b) || this.LocalMinimaPending();

            ) {
                this.ProcessHorizontals();
                this.m_GhostJoins.length = 0;
                if (!this.ProcessIntersections(b.v)) return !1;
                this.ProcessEdgesAtTopOfScanbeam(b.v);
                a.v = b.v;
                this.InsertLocalMinimaIntoAEL(a.v);
            }
            var c;
            var e = 0;
            for (c = this.m_PolyOuts.length; e < c; e++) {
                var d = this.m_PolyOuts[e];
                null === d.Pts ||
                    d.IsOpen ||
                    ((d.IsHole ^ this.ReverseSolution) == 0 < this.Area$1(d) &&
                        this.ReversePolyPtLinks(d.Pts));
            }
            this.JoinCommonEdges();
            e = 0;
            for (c = this.m_PolyOuts.length; e < c; e++)
                (d = this.m_PolyOuts[e]),
                    null !== d.Pts &&
                        (d.IsOpen
                            ? this.FixupOutPolyline(d)
                            : this.FixupOutPolygon(d));
            this.StrictlySimple && this.DoSimplePolygons();
            return !0;
        } finally {
            (this.m_Joins.length = 0), (this.m_GhostJoins.length = 0);
        }
    };
    d.Clipper.prototype.DisposeAllPolyPts = function () {
        for (var a = 0, b = this.m_PolyOuts.length; a < b; ++a)
            this.DisposeOutRec(a);
        d.Clear(this.m_PolyOuts);
    };
    d.Clipper.prototype.AddJoin = function (a, b, c) {
        var e = new d.Join();
        e.OutPt1 = a;
        e.OutPt2 = b;
        e.OffPt.X = c.X;
        e.OffPt.Y = c.Y;
        d.use_xyz && (e.OffPt.Z = c.Z);
        this.m_Joins.push(e);
    };
    d.Clipper.prototype.AddGhostJoin = function (a, b) {
        var c = new d.Join();
        c.OutPt1 = a;
        c.OffPt.X = b.X;
        c.OffPt.Y = b.Y;
        d.use_xyz && (c.OffPt.Z = b.Z);
        this.m_GhostJoins.push(c);
    };
    d.Clipper.prototype.SetZ = function (a, b, c) {
        null !== this.ZFillFunction &&
            0 === a.Z &&
            null !== this.ZFillFunction &&
            (d.IntPoint.op_Equality(a, b.Bot)
                ? (a.Z = b.Bot.Z)
                : d.IntPoint.op_Equality(a, b.Top)
                ? (a.Z = b.Top.Z)
                : d.IntPoint.op_Equality(a, c.Bot)
                ? (a.Z = c.Bot.Z)
                : d.IntPoint.op_Equality(a, c.Top)
                ? (a.Z = c.Top.Z)
                : this.ZFillFunction(b.Bot, b.Top, c.Bot, c.Top, a));
    };
    d.Clipper.prototype.InsertLocalMinimaIntoAEL = function (a) {
        for (var b, c = {}, e, f; this.PopLocalMinima(a, c); ) {
            e = c.v.LeftBound;
            f = c.v.RightBound;
            var g = null;
            null === e
                ? (this.InsertEdgeIntoAEL(f, null),
                  this.SetWindingCount(f),
                  this.IsContributing(f) && (g = this.AddOutPt(f, f.Bot)))
                : (null === f
                      ? (this.InsertEdgeIntoAEL(e, null),
                        this.SetWindingCount(e),
                        this.IsContributing(e) && (g = this.AddOutPt(e, e.Bot)))
                      : (this.InsertEdgeIntoAEL(e, null),
                        this.InsertEdgeIntoAEL(f, e),
                        this.SetWindingCount(e),
                        (f.WindCnt = e.WindCnt),
                        (f.WindCnt2 = e.WindCnt2),
                        this.IsContributing(e) &&
                            (g = this.AddLocalMinPoly(e, f, e.Bot))),
                  this.InsertScanbeam(e.Top.Y));
            null !== f &&
                (d.ClipperBase.IsHorizontal(f)
                    ? (null !== f.NextInLML &&
                          this.InsertScanbeam(f.NextInLML.Top.Y),
                      this.AddEdgeToSEL(f))
                    : this.InsertScanbeam(f.Top.Y));
            if (null !== e && null !== f) {
                if (
                    null !== g &&
                    d.ClipperBase.IsHorizontal(f) &&
                    0 < this.m_GhostJoins.length &&
                    0 !== f.WindDelta
                ) {
                    b = 0;
                    for (var h = this.m_GhostJoins.length; b < h; b++) {
                        var m = this.m_GhostJoins[b];
                        this.HorzSegmentsOverlap(
                            m.OutPt1.Pt.X,
                            m.OffPt.X,
                            f.Bot.X,
                            f.Top.X
                        ) && this.AddJoin(m.OutPt1, g, m.OffPt);
                    }
                }
                0 <= e.OutIdx &&
                    null !== e.PrevInAEL &&
                    e.PrevInAEL.Curr.X === e.Bot.X &&
                    0 <= e.PrevInAEL.OutIdx &&
                    d.ClipperBase.SlopesEqual5(
                        e.PrevInAEL.Curr,
                        e.PrevInAEL.Top,
                        e.Curr,
                        e.Top,
                        this.m_UseFullRange
                    ) &&
                    0 !== e.WindDelta &&
                    0 !== e.PrevInAEL.WindDelta &&
                    ((b = this.AddOutPt(e.PrevInAEL, e.Bot)),
                    this.AddJoin(g, b, e.Top));
                if (
                    e.NextInAEL !== f &&
                    (0 <= f.OutIdx &&
                        0 <= f.PrevInAEL.OutIdx &&
                        d.ClipperBase.SlopesEqual5(
                            f.PrevInAEL.Curr,
                            f.PrevInAEL.Top,
                            f.Curr,
                            f.Top,
                            this.m_UseFullRange
                        ) &&
                        0 !== f.WindDelta &&
                        0 !== f.PrevInAEL.WindDelta &&
                        ((b = this.AddOutPt(f.PrevInAEL, f.Bot)),
                        this.AddJoin(g, b, f.Top)),
                    (g = e.NextInAEL),
                    null !== g)
                )
                    for (; g !== f; )
                        this.IntersectEdges(f, g, e.Curr), (g = g.NextInAEL);
            }
        }
    };
    d.Clipper.prototype.InsertEdgeIntoAEL = function (a, b) {
        if (null === this.m_ActiveEdges)
            (a.PrevInAEL = null),
                (a.NextInAEL = null),
                (this.m_ActiveEdges = a);
        else if (null === b && this.E2InsertsBeforeE1(this.m_ActiveEdges, a))
            (a.PrevInAEL = null),
                (a.NextInAEL = this.m_ActiveEdges),
                (this.m_ActiveEdges = this.m_ActiveEdges.PrevInAEL = a);
        else {
            null === b && (b = this.m_ActiveEdges);
            for (
                ;
                null !== b.NextInAEL && !this.E2InsertsBeforeE1(b.NextInAEL, a);

            )
                b = b.NextInAEL;
            a.NextInAEL = b.NextInAEL;
            null !== b.NextInAEL && (b.NextInAEL.PrevInAEL = a);
            a.PrevInAEL = b;
            b.NextInAEL = a;
        }
    };
    d.Clipper.prototype.E2InsertsBeforeE1 = function (a, b) {
        return b.Curr.X === a.Curr.X
            ? b.Top.Y > a.Top.Y
                ? b.Top.X < d.Clipper.TopX(a, b.Top.Y)
                : a.Top.X > d.Clipper.TopX(b, a.Top.Y)
            : b.Curr.X < a.Curr.X;
    };
    d.Clipper.prototype.IsEvenOddFillType = function (a) {
        return a.PolyTyp === d.PolyType.ptSubject
            ? this.m_SubjFillType === d.PolyFillType.pftEvenOdd
            : this.m_ClipFillType === d.PolyFillType.pftEvenOdd;
    };
    d.Clipper.prototype.IsEvenOddAltFillType = function (a) {
        return a.PolyTyp === d.PolyType.ptSubject
            ? this.m_ClipFillType === d.PolyFillType.pftEvenOdd
            : this.m_SubjFillType === d.PolyFillType.pftEvenOdd;
    };
    d.Clipper.prototype.IsContributing = function (a) {
        if (a.PolyTyp === d.PolyType.ptSubject) {
            var b = this.m_SubjFillType;
            var c = this.m_ClipFillType;
        } else (b = this.m_ClipFillType), (c = this.m_SubjFillType);
        switch (b) {
            case d.PolyFillType.pftEvenOdd:
                if (0 === a.WindDelta && 1 !== a.WindCnt) return !1;
                break;
            case d.PolyFillType.pftNonZero:
                if (1 !== Math.abs(a.WindCnt)) return !1;
                break;
            case d.PolyFillType.pftPositive:
                if (1 !== a.WindCnt) return !1;
                break;
            default:
                if (-1 !== a.WindCnt) return !1;
        }
        switch (this.m_ClipType) {
            case d.ClipType.ctIntersection:
                switch (c) {
                    case d.PolyFillType.pftEvenOdd:
                    case d.PolyFillType.pftNonZero:
                        return 0 !== a.WindCnt2;
                    case d.PolyFillType.pftPositive:
                        return 0 < a.WindCnt2;
                    default:
                        return 0 > a.WindCnt2;
                }
            case d.ClipType.ctUnion:
                switch (c) {
                    case d.PolyFillType.pftEvenOdd:
                    case d.PolyFillType.pftNonZero:
                        return 0 === a.WindCnt2;
                    case d.PolyFillType.pftPositive:
                        return 0 >= a.WindCnt2;
                    default:
                        return 0 <= a.WindCnt2;
                }
            case d.ClipType.ctDifference:
                if (a.PolyTyp === d.PolyType.ptSubject)
                    switch (c) {
                        case d.PolyFillType.pftEvenOdd:
                        case d.PolyFillType.pftNonZero:
                            return 0 === a.WindCnt2;
                        case d.PolyFillType.pftPositive:
                            return 0 >= a.WindCnt2;
                        default:
                            return 0 <= a.WindCnt2;
                    }
                else
                    switch (c) {
                        case d.PolyFillType.pftEvenOdd:
                        case d.PolyFillType.pftNonZero:
                            return 0 !== a.WindCnt2;
                        case d.PolyFillType.pftPositive:
                            return 0 < a.WindCnt2;
                        default:
                            return 0 > a.WindCnt2;
                    }
            case d.ClipType.ctXor:
                if (0 === a.WindDelta)
                    switch (c) {
                        case d.PolyFillType.pftEvenOdd:
                        case d.PolyFillType.pftNonZero:
                            return 0 === a.WindCnt2;
                        case d.PolyFillType.pftPositive:
                            return 0 >= a.WindCnt2;
                        default:
                            return 0 <= a.WindCnt2;
                    }
        }
        return !0;
    };
    d.Clipper.prototype.SetWindingCount = function (a) {
        for (
            var b = a.PrevInAEL;
            null !== b && (b.PolyTyp !== a.PolyTyp || 0 === b.WindDelta);

        )
            b = b.PrevInAEL;
        if (null === b)
            (b =
                a.PolyTyp === d.PolyType.ptSubject
                    ? this.m_SubjFillType
                    : this.m_ClipFillType),
                (a.WindCnt =
                    0 === a.WindDelta
                        ? b === d.PolyFillType.pftNegative
                            ? -1
                            : 1
                        : a.WindDelta),
                (a.WindCnt2 = 0),
                (b = this.m_ActiveEdges);
        else {
            if (0 === a.WindDelta && this.m_ClipType !== d.ClipType.ctUnion)
                a.WindCnt = 1;
            else if (this.IsEvenOddFillType(a))
                if (0 === a.WindDelta) {
                    for (var c = !0, e = b.PrevInAEL; null !== e; )
                        e.PolyTyp === b.PolyTyp &&
                            0 !== e.WindDelta &&
                            (c = !c),
                            (e = e.PrevInAEL);
                    a.WindCnt = c ? 0 : 1;
                } else a.WindCnt = a.WindDelta;
            else
                a.WindCnt =
                    0 > b.WindCnt * b.WindDelta
                        ? 1 < Math.abs(b.WindCnt)
                            ? 0 > b.WindDelta * a.WindDelta
                                ? b.WindCnt
                                : b.WindCnt + a.WindDelta
                            : 0 === a.WindDelta
                            ? 1
                            : a.WindDelta
                        : 0 === a.WindDelta
                        ? 0 > b.WindCnt
                            ? b.WindCnt - 1
                            : b.WindCnt + 1
                        : 0 > b.WindDelta * a.WindDelta
                        ? b.WindCnt
                        : b.WindCnt + a.WindDelta;
            a.WindCnt2 = b.WindCnt2;
            b = b.NextInAEL;
        }
        if (this.IsEvenOddAltFillType(a))
            for (; b !== a; )
                0 !== b.WindDelta && (a.WindCnt2 = 0 === a.WindCnt2 ? 1 : 0),
                    (b = b.NextInAEL);
        else for (; b !== a; ) (a.WindCnt2 += b.WindDelta), (b = b.NextInAEL);
    };
    d.Clipper.prototype.AddEdgeToSEL = function (a) {
        null === this.m_SortedEdges
            ? ((this.m_SortedEdges = a),
              (a.PrevInSEL = null),
              (a.NextInSEL = null))
            : ((a.NextInSEL = this.m_SortedEdges),
              (a.PrevInSEL = null),
              (this.m_SortedEdges = this.m_SortedEdges.PrevInSEL = a));
    };
    d.Clipper.prototype.PopEdgeFromSEL = function (a) {
        a.v = this.m_SortedEdges;
        if (null === a.v) return !1;
        var b = a.v;
        this.m_SortedEdges = a.v.NextInSEL;
        null !== this.m_SortedEdges && (this.m_SortedEdges.PrevInSEL = null);
        b.NextInSEL = null;
        b.PrevInSEL = null;
        return !0;
    };
    d.Clipper.prototype.CopyAELToSEL = function () {
        var a = this.m_ActiveEdges;
        for (this.m_SortedEdges = a; null !== a; )
            (a.PrevInSEL = a.PrevInAEL), (a = a.NextInSEL = a.NextInAEL);
    };
    d.Clipper.prototype.SwapPositionsInSEL = function (a, b) {
        if (null !== a.NextInSEL || null !== a.PrevInSEL)
            if (null !== b.NextInSEL || null !== b.PrevInSEL) {
                if (a.NextInSEL === b) {
                    var c = b.NextInSEL;
                    null !== c && (c.PrevInSEL = a);
                    var e = a.PrevInSEL;
                    null !== e && (e.NextInSEL = b);
                    b.PrevInSEL = e;
                    b.NextInSEL = a;
                    a.PrevInSEL = b;
                    a.NextInSEL = c;
                } else
                    b.NextInSEL === a
                        ? ((c = a.NextInSEL),
                          null !== c && (c.PrevInSEL = b),
                          (e = b.PrevInSEL),
                          null !== e && (e.NextInSEL = a),
                          (a.PrevInSEL = e),
                          (a.NextInSEL = b),
                          (b.PrevInSEL = a),
                          (b.NextInSEL = c))
                        : ((c = a.NextInSEL),
                          (e = a.PrevInSEL),
                          (a.NextInSEL = b.NextInSEL),
                          null !== a.NextInSEL && (a.NextInSEL.PrevInSEL = a),
                          (a.PrevInSEL = b.PrevInSEL),
                          null !== a.PrevInSEL && (a.PrevInSEL.NextInSEL = a),
                          (b.NextInSEL = c),
                          null !== b.NextInSEL && (b.NextInSEL.PrevInSEL = b),
                          (b.PrevInSEL = e),
                          null !== b.PrevInSEL && (b.PrevInSEL.NextInSEL = b));
                null === a.PrevInSEL
                    ? (this.m_SortedEdges = a)
                    : null === b.PrevInSEL && (this.m_SortedEdges = b);
            }
    };
    d.Clipper.prototype.AddLocalMaxPoly = function (a, b, c) {
        this.AddOutPt(a, c);
        0 === b.WindDelta && this.AddOutPt(b, c);
        a.OutIdx === b.OutIdx
            ? ((a.OutIdx = -1), (b.OutIdx = -1))
            : a.OutIdx < b.OutIdx
            ? this.AppendPolygon(a, b)
            : this.AppendPolygon(b, a);
    };
    d.Clipper.prototype.AddLocalMinPoly = function (a, b, c) {
        if (d.ClipperBase.IsHorizontal(b) || a.Dx > b.Dx) {
            var e = this.AddOutPt(a, c);
            b.OutIdx = a.OutIdx;
            a.Side = d.EdgeSide.esLeft;
            b.Side = d.EdgeSide.esRight;
            var f = a;
            a = f.PrevInAEL === b ? b.PrevInAEL : f.PrevInAEL;
        } else
            (e = this.AddOutPt(b, c)),
                (a.OutIdx = b.OutIdx),
                (a.Side = d.EdgeSide.esRight),
                (b.Side = d.EdgeSide.esLeft),
                (f = b),
                (a = f.PrevInAEL === a ? a.PrevInAEL : f.PrevInAEL);
        if (null !== a && 0 <= a.OutIdx && a.Top.Y < c.Y && f.Top.Y < c.Y) {
            b = d.Clipper.TopX(a, c.Y);
            var g = d.Clipper.TopX(f, c.Y);
            b === g &&
                0 !== f.WindDelta &&
                0 !== a.WindDelta &&
                d.ClipperBase.SlopesEqual5(
                    new d.IntPoint2(b, c.Y),
                    a.Top,
                    new d.IntPoint2(g, c.Y),
                    f.Top,
                    this.m_UseFullRange
                ) &&
                ((c = this.AddOutPt(a, c)), this.AddJoin(e, c, f.Top));
        }
        return e;
    };
    d.Clipper.prototype.AddOutPt = function (a, b) {
        if (0 > a.OutIdx) {
            var c = this.CreateOutRec();
            c.IsOpen = 0 === a.WindDelta;
            var e = new d.OutPt();
            c.Pts = e;
            e.Idx = c.Idx;
            e.Pt.X = b.X;
            e.Pt.Y = b.Y;
            d.use_xyz && (e.Pt.Z = b.Z);
            e.Next = e;
            e.Prev = e;
            c.IsOpen || this.SetHoleState(a, c);
            a.OutIdx = c.Idx;
        } else {
            c = this.m_PolyOuts[a.OutIdx];
            var f = c.Pts,
                g = a.Side === d.EdgeSide.esLeft;
            if (g && d.IntPoint.op_Equality(b, f.Pt)) return f;
            if (!g && d.IntPoint.op_Equality(b, f.Prev.Pt)) return f.Prev;
            e = new d.OutPt();
            e.Idx = c.Idx;
            e.Pt.X = b.X;
            e.Pt.Y = b.Y;
            d.use_xyz && (e.Pt.Z = b.Z);
            e.Next = f;
            e.Prev = f.Prev;
            e.Prev.Next = e;
            f.Prev = e;
            g && (c.Pts = e);
        }
        return e;
    };
    d.Clipper.prototype.GetLastOutPt = function (a) {
        var b = this.m_PolyOuts[a.OutIdx];
        return a.Side === d.EdgeSide.esLeft ? b.Pts : b.Pts.Prev;
    };
    d.Clipper.prototype.SwapPoints = function (a, b) {
        var c = new d.IntPoint1(a.Value);
        a.Value.X = b.Value.X;
        a.Value.Y = b.Value.Y;
        d.use_xyz && (a.Value.Z = b.Value.Z);
        b.Value.X = c.X;
        b.Value.Y = c.Y;
        d.use_xyz && (b.Value.Z = c.Z);
    };
    d.Clipper.prototype.HorzSegmentsOverlap = function (a, b, c, e) {
        if (a > b) {
            var d = a;
            a = b;
            b = d;
        }
        c > e && ((d = c), (c = e), (e = d));
        return a < e && c < b;
    };
    d.Clipper.prototype.SetHoleState = function (a, b) {
        for (var c = a.PrevInAEL, e = null; null !== c; )
            0 <= c.OutIdx &&
                0 !== c.WindDelta &&
                (null === e ? (e = c) : e.OutIdx === c.OutIdx && (e = null)),
                (c = c.PrevInAEL);
        null === e
            ? ((b.FirstLeft = null), (b.IsHole = !1))
            : ((b.FirstLeft = this.m_PolyOuts[e.OutIdx]),
              (b.IsHole = !b.FirstLeft.IsHole));
    };
    d.Clipper.prototype.GetDx = function (a, b) {
        return a.Y === b.Y
            ? d.ClipperBase.horizontal
            : (b.X - a.X) / (b.Y - a.Y);
    };
    d.Clipper.prototype.FirstIsBottomPt = function (a, b) {
        for (var c = a.Prev; d.IntPoint.op_Equality(c.Pt, a.Pt) && c !== a; )
            c = c.Prev;
        var e = Math.abs(this.GetDx(a.Pt, c.Pt));
        for (c = a.Next; d.IntPoint.op_Equality(c.Pt, a.Pt) && c !== a; )
            c = c.Next;
        var f = Math.abs(this.GetDx(a.Pt, c.Pt));
        for (c = b.Prev; d.IntPoint.op_Equality(c.Pt, b.Pt) && c !== b; )
            c = c.Prev;
        var g = Math.abs(this.GetDx(b.Pt, c.Pt));
        for (c = b.Next; d.IntPoint.op_Equality(c.Pt, b.Pt) && c !== b; )
            c = c.Next;
        c = Math.abs(this.GetDx(b.Pt, c.Pt));
        return Math.max(e, f) === Math.max(g, c) &&
            Math.min(e, f) === Math.min(g, c)
            ? 0 < this.Area(a)
            : (e >= g && e >= c) || (f >= g && f >= c);
    };
    d.Clipper.prototype.GetBottomPt = function (a) {
        for (var b = null, c = a.Next; c !== a; )
            c.Pt.Y > a.Pt.Y
                ? ((a = c), (b = null))
                : c.Pt.Y === a.Pt.Y &&
                  c.Pt.X <= a.Pt.X &&
                  (c.Pt.X < a.Pt.X
                      ? ((b = null), (a = c))
                      : c.Next !== a && c.Prev !== a && (b = c)),
                (c = c.Next);
        if (null !== b)
            for (; b !== c; )
                for (
                    this.FirstIsBottomPt(c, b) || (a = b), b = b.Next;
                    d.IntPoint.op_Inequality(b.Pt, a.Pt);

                )
                    b = b.Next;
        return a;
    };
    d.Clipper.prototype.GetLowermostRec = function (a, b) {
        null === a.BottomPt && (a.BottomPt = this.GetBottomPt(a.Pts));
        null === b.BottomPt && (b.BottomPt = this.GetBottomPt(b.Pts));
        var c = a.BottomPt,
            e = b.BottomPt;
        return c.Pt.Y > e.Pt.Y
            ? a
            : c.Pt.Y < e.Pt.Y
            ? b
            : c.Pt.X < e.Pt.X
            ? a
            : c.Pt.X > e.Pt.X
            ? b
            : c.Next === c
            ? b
            : e.Next === e
            ? a
            : this.FirstIsBottomPt(c, e)
            ? a
            : b;
    };
    d.Clipper.prototype.OutRec1RightOfOutRec2 = function (a, b) {
        do if (((a = a.FirstLeft), a === b)) return !0;
        while (null !== a);
        return !1;
    };
    d.Clipper.prototype.GetOutRec = function (a) {
        for (a = this.m_PolyOuts[a]; a !== this.m_PolyOuts[a.Idx]; )
            a = this.m_PolyOuts[a.Idx];
        return a;
    };
    d.Clipper.prototype.AppendPolygon = function (a, b) {
        var c = this.m_PolyOuts[a.OutIdx],
            e = this.m_PolyOuts[b.OutIdx];
        var f = this.OutRec1RightOfOutRec2(c, e)
            ? e
            : this.OutRec1RightOfOutRec2(e, c)
            ? c
            : this.GetLowermostRec(c, e);
        var g = c.Pts,
            h = g.Prev,
            m = e.Pts,
            k = m.Prev;
        a.Side === d.EdgeSide.esLeft
            ? b.Side === d.EdgeSide.esLeft
                ? (this.ReversePolyPtLinks(m),
                  (m.Next = g),
                  (g.Prev = m),
                  (h.Next = k),
                  (k.Prev = h),
                  (c.Pts = k))
                : ((k.Next = g),
                  (g.Prev = k),
                  (m.Prev = h),
                  (h.Next = m),
                  (c.Pts = m))
            : b.Side === d.EdgeSide.esRight
            ? (this.ReversePolyPtLinks(m),
              (h.Next = k),
              (k.Prev = h),
              (m.Next = g),
              (g.Prev = m))
            : ((h.Next = m), (m.Prev = h), (g.Prev = k), (k.Next = g));
        c.BottomPt = null;
        f === e &&
            (e.FirstLeft !== c && (c.FirstLeft = e.FirstLeft),
            (c.IsHole = e.IsHole));
        e.Pts = null;
        e.BottomPt = null;
        e.FirstLeft = c;
        f = a.OutIdx;
        g = b.OutIdx;
        a.OutIdx = -1;
        b.OutIdx = -1;
        for (h = this.m_ActiveEdges; null !== h; ) {
            if (h.OutIdx === g) {
                h.OutIdx = f;
                h.Side = a.Side;
                break;
            }
            h = h.NextInAEL;
        }
        e.Idx = c.Idx;
    };
    d.Clipper.prototype.ReversePolyPtLinks = function (a) {
        if (null !== a) {
            var b = a;
            do {
                var c = b.Next;
                b.Next = b.Prev;
                b = b.Prev = c;
            } while (b !== a);
        }
    };
    d.Clipper.SwapSides = function (a, b) {
        var c = a.Side;
        a.Side = b.Side;
        b.Side = c;
    };
    d.Clipper.SwapPolyIndexes = function (a, b) {
        var c = a.OutIdx;
        a.OutIdx = b.OutIdx;
        b.OutIdx = c;
    };
    d.Clipper.prototype.IntersectEdges = function (a, b, c) {
        var e = 0 <= a.OutIdx,
            f = 0 <= b.OutIdx;
        d.use_xyz && this.SetZ(c, a, b);
        if (!d.use_lines || (0 !== a.WindDelta && 0 !== b.WindDelta)) {
            if (a.PolyTyp === b.PolyTyp)
                if (this.IsEvenOddFillType(a)) {
                    var g = a.WindCnt;
                    a.WindCnt = b.WindCnt;
                    b.WindCnt = g;
                } else
                    (a.WindCnt =
                        0 === a.WindCnt + b.WindDelta
                            ? -a.WindCnt
                            : a.WindCnt + b.WindDelta),
                        (b.WindCnt =
                            0 === b.WindCnt - a.WindDelta
                                ? -b.WindCnt
                                : b.WindCnt - a.WindDelta);
            else
                this.IsEvenOddFillType(b)
                    ? (a.WindCnt2 = 0 === a.WindCnt2 ? 1 : 0)
                    : (a.WindCnt2 += b.WindDelta),
                    this.IsEvenOddFillType(a)
                        ? (b.WindCnt2 = 0 === b.WindCnt2 ? 1 : 0)
                        : (b.WindCnt2 -= a.WindDelta);
            if (a.PolyTyp === d.PolyType.ptSubject) {
                var h = this.m_SubjFillType;
                var k = this.m_ClipFillType;
            } else (h = this.m_ClipFillType), (k = this.m_SubjFillType);
            if (b.PolyTyp === d.PolyType.ptSubject) {
                var l = this.m_SubjFillType;
                g = this.m_ClipFillType;
            } else (l = this.m_ClipFillType), (g = this.m_SubjFillType);
            switch (h) {
                case d.PolyFillType.pftPositive:
                    h = a.WindCnt;
                    break;
                case d.PolyFillType.pftNegative:
                    h = -a.WindCnt;
                    break;
                default:
                    h = Math.abs(a.WindCnt);
            }
            switch (l) {
                case d.PolyFillType.pftPositive:
                    l = b.WindCnt;
                    break;
                case d.PolyFillType.pftNegative:
                    l = -b.WindCnt;
                    break;
                default:
                    l = Math.abs(b.WindCnt);
            }
            if (e && f)
                (0 !== h && 1 !== h) ||
                (0 !== l && 1 !== l) ||
                (a.PolyTyp !== b.PolyTyp &&
                    this.m_ClipType !== d.ClipType.ctXor)
                    ? this.AddLocalMaxPoly(a, b, c)
                    : (this.AddOutPt(a, c),
                      this.AddOutPt(b, c),
                      d.Clipper.SwapSides(a, b),
                      d.Clipper.SwapPolyIndexes(a, b));
            else if (e) {
                if (0 === l || 1 === l)
                    this.AddOutPt(a, c),
                        d.Clipper.SwapSides(a, b),
                        d.Clipper.SwapPolyIndexes(a, b);
            } else if (f) {
                if (0 === h || 1 === h)
                    this.AddOutPt(b, c),
                        d.Clipper.SwapSides(a, b),
                        d.Clipper.SwapPolyIndexes(a, b);
            } else if (!((0 !== h && 1 !== h) || (0 !== l && 1 !== l))) {
                switch (k) {
                    case d.PolyFillType.pftPositive:
                        e = a.WindCnt2;
                        break;
                    case d.PolyFillType.pftNegative:
                        e = -a.WindCnt2;
                        break;
                    default:
                        e = Math.abs(a.WindCnt2);
                }
                switch (g) {
                    case d.PolyFillType.pftPositive:
                        f = b.WindCnt2;
                        break;
                    case d.PolyFillType.pftNegative:
                        f = -b.WindCnt2;
                        break;
                    default:
                        f = Math.abs(b.WindCnt2);
                }
                if (a.PolyTyp !== b.PolyTyp) this.AddLocalMinPoly(a, b, c);
                else if (1 === h && 1 === l)
                    switch (this.m_ClipType) {
                        case d.ClipType.ctIntersection:
                            0 < e && 0 < f && this.AddLocalMinPoly(a, b, c);
                            break;
                        case d.ClipType.ctUnion:
                            0 >= e && 0 >= f && this.AddLocalMinPoly(a, b, c);
                            break;
                        case d.ClipType.ctDifference:
                            ((a.PolyTyp === d.PolyType.ptClip &&
                                0 < e &&
                                0 < f) ||
                                (a.PolyTyp === d.PolyType.ptSubject &&
                                    0 >= e &&
                                    0 >= f)) &&
                                this.AddLocalMinPoly(a, b, c);
                            break;
                        case d.ClipType.ctXor:
                            this.AddLocalMinPoly(a, b, c);
                    }
                else d.Clipper.SwapSides(a, b);
            }
        } else if (0 !== a.WindDelta || 0 !== b.WindDelta)
            a.PolyTyp === b.PolyTyp &&
            a.WindDelta !== b.WindDelta &&
            this.m_ClipType === d.ClipType.ctUnion
                ? 0 === a.WindDelta
                    ? f && (this.AddOutPt(a, c), e && (a.OutIdx = -1))
                    : e && (this.AddOutPt(b, c), f && (b.OutIdx = -1))
                : a.PolyTyp !== b.PolyTyp &&
                  (0 !== a.WindDelta ||
                  1 !== Math.abs(b.WindCnt) ||
                  (this.m_ClipType === d.ClipType.ctUnion && 0 !== b.WindCnt2)
                      ? 0 !== b.WindDelta ||
                        1 !== Math.abs(a.WindCnt) ||
                        (this.m_ClipType === d.ClipType.ctUnion &&
                            0 !== a.WindCnt2) ||
                        (this.AddOutPt(b, c), f && (b.OutIdx = -1))
                      : (this.AddOutPt(a, c), e && (a.OutIdx = -1)));
    };
    d.Clipper.prototype.DeleteFromSEL = function (a) {
        var b = a.PrevInSEL,
            c = a.NextInSEL;
        if (null !== b || null !== c || a === this.m_SortedEdges)
            null !== b ? (b.NextInSEL = c) : (this.m_SortedEdges = c),
                null !== c && (c.PrevInSEL = b),
                (a.NextInSEL = null),
                (a.PrevInSEL = null);
    };
    d.Clipper.prototype.ProcessHorizontals = function () {
        for (var a = {}; this.PopEdgeFromSEL(a); ) this.ProcessHorizontal(a.v);
    };
    d.Clipper.prototype.GetHorzDirection = function (a, b) {
        a.Bot.X < a.Top.X
            ? ((b.Left = a.Bot.X),
              (b.Right = a.Top.X),
              (b.Dir = d.Direction.dLeftToRight))
            : ((b.Left = a.Top.X),
              (b.Right = a.Bot.X),
              (b.Dir = d.Direction.dRightToLeft));
    };
    d.Clipper.prototype.ProcessHorizontal = function (a) {
        var b,
            c = { Dir: null, Left: null, Right: null };
        this.GetHorzDirection(a, c);
        var e = c.Dir,
            f = c.Left;
        c = c.Right;
        for (
            var g = 0 === a.WindDelta, h = a, k = null;
            null !== h.NextInLML && d.ClipperBase.IsHorizontal(h.NextInLML);

        )
            h = h.NextInLML;
        null === h.NextInLML && (k = this.GetMaximaPair(h));
        var l = this.m_Maxima;
        if (null !== l)
            if (e === d.Direction.dLeftToRight) {
                for (; null !== l && l.X <= a.Bot.X; ) l = l.Next;
                null !== l && l.X >= h.Top.X && (l = null);
            } else {
                for (; null !== l.Next && l.Next.X < a.Bot.X; ) l = l.Next;
                l.X <= h.Top.X && (l = null);
            }
        for (var n = null; ; ) {
            for (var r = a === h, p = this.GetNextInAEL(a, e); null !== p; ) {
                if (null !== l)
                    if (e === d.Direction.dLeftToRight)
                        for (; null !== l && l.X < p.Curr.X; )
                            0 <= a.OutIdx &&
                                !g &&
                                this.AddOutPt(a, new d.IntPoint2(l.X, a.Bot.Y)),
                                (l = l.Next);
                    else
                        for (; null !== l && l.X > p.Curr.X; )
                            0 <= a.OutIdx &&
                                !g &&
                                this.AddOutPt(a, new d.IntPoint2(l.X, a.Bot.Y)),
                                (l = l.Prev);
                if (
                    (e === d.Direction.dLeftToRight && p.Curr.X > c) ||
                    (e === d.Direction.dRightToLeft && p.Curr.X < f)
                )
                    break;
                if (
                    p.Curr.X === a.Top.X &&
                    null !== a.NextInLML &&
                    p.Dx < a.NextInLML.Dx
                )
                    break;
                if (0 <= a.OutIdx && !g) {
                    d.use_xyz &&
                        (e === d.Direction.dLeftToRight
                            ? this.SetZ(p.Curr, a, p)
                            : this.SetZ(p.Curr, p, a));
                    n = this.AddOutPt(a, p.Curr);
                    for (b = this.m_SortedEdges; null !== b; ) {
                        if (
                            0 <= b.OutIdx &&
                            this.HorzSegmentsOverlap(
                                a.Bot.X,
                                a.Top.X,
                                b.Bot.X,
                                b.Top.X
                            )
                        ) {
                            var t = this.GetLastOutPt(b);
                            this.AddJoin(t, n, b.Top);
                        }
                        b = b.NextInSEL;
                    }
                    this.AddGhostJoin(n, a.Bot);
                }
                if (p === k && r) {
                    0 <= a.OutIdx && this.AddLocalMaxPoly(a, k, a.Top);
                    this.DeleteFromAEL(a);
                    this.DeleteFromAEL(k);
                    return;
                }
                e === d.Direction.dLeftToRight
                    ? ((t = new d.IntPoint2(p.Curr.X, a.Curr.Y)),
                      this.IntersectEdges(a, p, t))
                    : ((t = new d.IntPoint2(p.Curr.X, a.Curr.Y)),
                      this.IntersectEdges(p, a, t));
                t = this.GetNextInAEL(p, e);
                this.SwapPositionsInAEL(a, p);
                p = t;
            }
            if (
                null === a.NextInLML ||
                !d.ClipperBase.IsHorizontal(a.NextInLML)
            )
                break;
            a = this.UpdateEdgeIntoAEL(a);
            0 <= a.OutIdx && this.AddOutPt(a, a.Bot);
            c = { Dir: e, Left: f, Right: c };
            this.GetHorzDirection(a, c);
            e = c.Dir;
            f = c.Left;
            c = c.Right;
        }
        if (0 <= a.OutIdx && null === n) {
            n = this.GetLastOutPt(a);
            for (b = this.m_SortedEdges; null !== b; )
                0 <= b.OutIdx &&
                    this.HorzSegmentsOverlap(
                        a.Bot.X,
                        a.Top.X,
                        b.Bot.X,
                        b.Top.X
                    ) &&
                    ((t = this.GetLastOutPt(b)), this.AddJoin(t, n, b.Top)),
                    (b = b.NextInSEL);
            this.AddGhostJoin(n, a.Top);
        }
        null !== a.NextInLML
            ? 0 <= a.OutIdx
                ? ((n = this.AddOutPt(a, a.Top)),
                  (a = this.UpdateEdgeIntoAEL(a)),
                  0 !== a.WindDelta &&
                      ((e = a.PrevInAEL),
                      (t = a.NextInAEL),
                      null !== e &&
                      e.Curr.X === a.Bot.X &&
                      e.Curr.Y === a.Bot.Y &&
                      0 === e.WindDelta &&
                      0 <= e.OutIdx &&
                      e.Curr.Y > e.Top.Y &&
                      d.ClipperBase.SlopesEqual3(a, e, this.m_UseFullRange)
                          ? ((t = this.AddOutPt(e, a.Bot)),
                            this.AddJoin(n, t, a.Top))
                          : null !== t &&
                            t.Curr.X === a.Bot.X &&
                            t.Curr.Y === a.Bot.Y &&
                            0 !== t.WindDelta &&
                            0 <= t.OutIdx &&
                            t.Curr.Y > t.Top.Y &&
                            d.ClipperBase.SlopesEqual3(
                                a,
                                t,
                                this.m_UseFullRange
                            ) &&
                            ((t = this.AddOutPt(t, a.Bot)),
                            this.AddJoin(n, t, a.Top))))
                : this.UpdateEdgeIntoAEL(a)
            : (0 <= a.OutIdx && this.AddOutPt(a, a.Top), this.DeleteFromAEL(a));
    };
    d.Clipper.prototype.GetNextInAEL = function (a, b) {
        return b === d.Direction.dLeftToRight ? a.NextInAEL : a.PrevInAEL;
    };
    d.Clipper.prototype.IsMinima = function (a) {
        return null !== a && a.Prev.NextInLML !== a && a.Next.NextInLML !== a;
    };
    d.Clipper.prototype.IsMaxima = function (a, b) {
        return null !== a && a.Top.Y === b && null === a.NextInLML;
    };
    d.Clipper.prototype.IsIntermediate = function (a, b) {
        return a.Top.Y === b && null !== a.NextInLML;
    };
    d.Clipper.prototype.GetMaximaPair = function (a) {
        return d.IntPoint.op_Equality(a.Next.Top, a.Top) &&
            null === a.Next.NextInLML
            ? a.Next
            : d.IntPoint.op_Equality(a.Prev.Top, a.Top) &&
              null === a.Prev.NextInLML
            ? a.Prev
            : null;
    };
    d.Clipper.prototype.GetMaximaPairEx = function (a) {
        a = this.GetMaximaPair(a);
        return null === a ||
            a.OutIdx === d.ClipperBase.Skip ||
            (a.NextInAEL === a.PrevInAEL && !d.ClipperBase.IsHorizontal(a))
            ? null
            : a;
    };
    d.Clipper.prototype.ProcessIntersections = function (a) {
        if (null === this.m_ActiveEdges) return !0;
        try {
            this.BuildIntersectList(a);
            if (0 === this.m_IntersectList.length) return !0;
            if (
                1 === this.m_IntersectList.length ||
                this.FixupIntersectionOrder()
            )
                this.ProcessIntersectList();
            else return !1;
        } catch (b) {
            (this.m_SortedEdges = null),
                (this.m_IntersectList.length = 0),
                d.Error("ProcessIntersections error");
        }
        this.m_SortedEdges = null;
        return !0;
    };
    d.Clipper.prototype.BuildIntersectList = function (a) {
        if (null !== this.m_ActiveEdges) {
            var b = this.m_ActiveEdges;
            for (this.m_SortedEdges = b; null !== b; )
                (b.PrevInSEL = b.PrevInAEL),
                    (b.NextInSEL = b.NextInAEL),
                    (b.Curr.X = d.Clipper.TopX(b, a)),
                    (b = b.NextInAEL);
            for (var c = !0; c && null !== this.m_SortedEdges; ) {
                c = !1;
                for (b = this.m_SortedEdges; null !== b.NextInSEL; ) {
                    var e = b.NextInSEL,
                        f = new d.IntPoint0();
                    b.Curr.X > e.Curr.X
                        ? (this.IntersectPoint(b, e, f),
                          f.Y < a &&
                              (f = new d.IntPoint2(d.Clipper.TopX(b, a), a)),
                          (c = new d.IntersectNode()),
                          (c.Edge1 = b),
                          (c.Edge2 = e),
                          (c.Pt.X = f.X),
                          (c.Pt.Y = f.Y),
                          d.use_xyz && (c.Pt.Z = f.Z),
                          this.m_IntersectList.push(c),
                          this.SwapPositionsInSEL(b, e),
                          (c = !0))
                        : (b = e);
                }
                if (null !== b.PrevInSEL) b.PrevInSEL.NextInSEL = null;
                else break;
            }
            this.m_SortedEdges = null;
        }
    };
    d.Clipper.prototype.EdgesAdjacent = function (a) {
        return a.Edge1.NextInSEL === a.Edge2 || a.Edge1.PrevInSEL === a.Edge2;
    };
    d.Clipper.IntersectNodeSort = function (a, b) {
        return b.Pt.Y - a.Pt.Y;
    };
    d.Clipper.prototype.FixupIntersectionOrder = function () {
        this.m_IntersectList.sort(this.m_IntersectNodeComparer);
        this.CopyAELToSEL();
        for (var a = this.m_IntersectList.length, b = 0; b < a; b++) {
            if (!this.EdgesAdjacent(this.m_IntersectList[b])) {
                for (
                    var c = b + 1;
                    c < a && !this.EdgesAdjacent(this.m_IntersectList[c]);

                )
                    c++;
                if (c === a) return !1;
                var e = this.m_IntersectList[b];
                this.m_IntersectList[b] = this.m_IntersectList[c];
                this.m_IntersectList[c] = e;
            }
            this.SwapPositionsInSEL(
                this.m_IntersectList[b].Edge1,
                this.m_IntersectList[b].Edge2
            );
        }
        return !0;
    };
    d.Clipper.prototype.ProcessIntersectList = function () {
        for (var a = 0, b = this.m_IntersectList.length; a < b; a++) {
            var c = this.m_IntersectList[a];
            this.IntersectEdges(c.Edge1, c.Edge2, c.Pt);
            this.SwapPositionsInAEL(c.Edge1, c.Edge2);
        }
        this.m_IntersectList.length = 0;
    };
    I = function (a) {
        return 0 > a ? Math.ceil(a - 0.5) : Math.round(a);
    };
    J = function (a) {
        return 0 > a ? Math.ceil(a - 0.5) : Math.floor(a + 0.5);
    };
    K = function (a) {
        return 0 > a ? -Math.round(Math.abs(a)) : Math.round(a);
    };
    L = function (a) {
        if (0 > a) return (a -= 0.5), -2147483648 > a ? Math.ceil(a) : a | 0;
        a += 0.5;
        return 2147483647 < a ? Math.floor(a) : a | 0;
    };
    d.Clipper.Round = u ? I : G ? K : Q ? L : J;
    d.Clipper.TopX = function (a, b) {
        return b === a.Top.Y
            ? a.Top.X
            : a.Bot.X + d.Clipper.Round(a.Dx * (b - a.Bot.Y));
    };
    d.Clipper.prototype.IntersectPoint = function (a, b, c) {
        c.X = 0;
        c.Y = 0;
        if (a.Dx === b.Dx) (c.Y = a.Curr.Y), (c.X = d.Clipper.TopX(a, c.Y));
        else {
            if (0 === a.Delta.X)
                if (((c.X = a.Bot.X), d.ClipperBase.IsHorizontal(b)))
                    c.Y = b.Bot.Y;
                else {
                    var e = b.Bot.Y - b.Bot.X / b.Dx;
                    c.Y = d.Clipper.Round(c.X / b.Dx + e);
                }
            else if (0 === b.Delta.X)
                if (((c.X = b.Bot.X), d.ClipperBase.IsHorizontal(a)))
                    c.Y = a.Bot.Y;
                else {
                    var f = a.Bot.Y - a.Bot.X / a.Dx;
                    c.Y = d.Clipper.Round(c.X / a.Dx + f);
                }
            else {
                f = a.Bot.X - a.Bot.Y * a.Dx;
                e = b.Bot.X - b.Bot.Y * b.Dx;
                var g = (e - f) / (a.Dx - b.Dx);
                c.Y = d.Clipper.Round(g);
                c.X =
                    Math.abs(a.Dx) < Math.abs(b.Dx)
                        ? d.Clipper.Round(a.Dx * g + f)
                        : d.Clipper.Round(b.Dx * g + e);
            }
            if (c.Y < a.Top.Y || c.Y < b.Top.Y) {
                if (a.Top.Y > b.Top.Y)
                    return (
                        (c.Y = a.Top.Y),
                        (c.X = d.Clipper.TopX(b, a.Top.Y)),
                        c.X < a.Top.X
                    );
                c.Y = b.Top.Y;
                c.X =
                    Math.abs(a.Dx) < Math.abs(b.Dx)
                        ? d.Clipper.TopX(a, c.Y)
                        : d.Clipper.TopX(b, c.Y);
            }
            c.Y > a.Curr.Y &&
                ((c.Y = a.Curr.Y),
                (c.X =
                    Math.abs(a.Dx) > Math.abs(b.Dx)
                        ? d.Clipper.TopX(b, c.Y)
                        : d.Clipper.TopX(a, c.Y)));
        }
    };
    d.Clipper.prototype.ProcessEdgesAtTopOfScanbeam = function (a) {
        for (var b, c, e = this.m_ActiveEdges; null !== e; ) {
            if ((c = this.IsMaxima(e, a)))
                (c = this.GetMaximaPairEx(e)),
                    (c = null === c || !d.ClipperBase.IsHorizontal(c));
            if (c)
                this.StrictlySimple && this.InsertMaxima(e.Top.X),
                    (b = e.PrevInAEL),
                    this.DoMaxima(e),
                    (e = null === b ? this.m_ActiveEdges : b.NextInAEL);
            else {
                this.IsIntermediate(e, a) &&
                d.ClipperBase.IsHorizontal(e.NextInLML)
                    ? ((e = this.UpdateEdgeIntoAEL(e)),
                      0 <= e.OutIdx && this.AddOutPt(e, e.Bot),
                      this.AddEdgeToSEL(e))
                    : ((e.Curr.X = d.Clipper.TopX(e, a)), (e.Curr.Y = a));
                d.use_xyz &&
                    (e.Curr.Z =
                        e.Top.Y === a ? e.Top.Z : e.Bot.Y === a ? e.Bot.Z : 0);
                if (
                    this.StrictlySimple &&
                    ((b = e.PrevInAEL),
                    0 <= e.OutIdx &&
                        0 !== e.WindDelta &&
                        null !== b &&
                        0 <= b.OutIdx &&
                        b.Curr.X === e.Curr.X &&
                        0 !== b.WindDelta)
                ) {
                    var f = new d.IntPoint1(e.Curr);
                    d.use_xyz && this.SetZ(f, b, e);
                    c = this.AddOutPt(b, f);
                    b = this.AddOutPt(e, f);
                    this.AddJoin(c, b, f);
                }
                e = e.NextInAEL;
            }
        }
        this.ProcessHorizontals();
        this.m_Maxima = null;
        for (e = this.m_ActiveEdges; null !== e; )
            this.IsIntermediate(e, a) &&
                ((c = null),
                0 <= e.OutIdx && (c = this.AddOutPt(e, e.Top)),
                (e = this.UpdateEdgeIntoAEL(e)),
                (b = e.PrevInAEL),
                (f = e.NextInAEL),
                null !== b &&
                b.Curr.X === e.Bot.X &&
                b.Curr.Y === e.Bot.Y &&
                null !== c &&
                0 <= b.OutIdx &&
                b.Curr.Y === b.Top.Y &&
                d.ClipperBase.SlopesEqual5(
                    e.Curr,
                    e.Top,
                    b.Curr,
                    b.Top,
                    this.m_UseFullRange
                ) &&
                0 !== e.WindDelta &&
                0 !== b.WindDelta
                    ? ((b = this.AddOutPt(ePrev2, e.Bot)),
                      this.AddJoin(c, b, e.Top))
                    : null !== f &&
                      f.Curr.X === e.Bot.X &&
                      f.Curr.Y === e.Bot.Y &&
                      null !== c &&
                      0 <= f.OutIdx &&
                      f.Curr.Y === f.Top.Y &&
                      d.ClipperBase.SlopesEqual5(
                          e.Curr,
                          e.Top,
                          f.Curr,
                          f.Top,
                          this.m_UseFullRange
                      ) &&
                      0 !== e.WindDelta &&
                      0 !== f.WindDelta &&
                      ((b = this.AddOutPt(f, e.Bot)),
                      this.AddJoin(c, b, e.Top))),
                (e = e.NextInAEL);
    };
    d.Clipper.prototype.DoMaxima = function (a) {
        var b = this.GetMaximaPairEx(a);
        if (null === b)
            0 <= a.OutIdx && this.AddOutPt(a, a.Top), this.DeleteFromAEL(a);
        else {
            for (var c = a.NextInAEL; null !== c && c !== b; )
                this.IntersectEdges(a, c, a.Top),
                    this.SwapPositionsInAEL(a, c),
                    (c = a.NextInAEL);
            -1 === a.OutIdx && -1 === b.OutIdx
                ? (this.DeleteFromAEL(a), this.DeleteFromAEL(b))
                : 0 <= a.OutIdx && 0 <= b.OutIdx
                ? (0 <= a.OutIdx && this.AddLocalMaxPoly(a, b, a.Top),
                  this.DeleteFromAEL(a),
                  this.DeleteFromAEL(b))
                : d.use_lines && 0 === a.WindDelta
                ? (0 <= a.OutIdx &&
                      (this.AddOutPt(a, a.Top),
                      (a.OutIdx = d.ClipperBase.Unassigned)),
                  this.DeleteFromAEL(a),
                  0 <= b.OutIdx &&
                      (this.AddOutPt(b, a.Top),
                      (b.OutIdx = d.ClipperBase.Unassigned)),
                  this.DeleteFromAEL(b))
                : d.Error("DoMaxima error");
        }
    };
    d.Clipper.ReversePaths = function (a) {
        for (var b = 0, c = a.length; b < c; b++) a[b].reverse();
    };
    d.Clipper.Orientation = function (a) {
        return 0 <= d.Clipper.Area(a);
    };
    d.Clipper.prototype.PointCount = function (a) {
        if (null === a) return 0;
        var b = 0,
            c = a;
        do b++, (c = c.Next);
        while (c !== a);
        return b;
    };
    d.Clipper.prototype.BuildResult = function (a) {
        d.Clear(a);
        for (var b = 0, c = this.m_PolyOuts.length; b < c; b++) {
            var e = this.m_PolyOuts[b];
            if (null !== e.Pts) {
                e = e.Pts.Prev;
                var f = this.PointCount(e);
                if (!(2 > f)) {
                    for (var g = Array(f), h = 0; h < f; h++)
                        (g[h] = e.Pt), (e = e.Prev);
                    a.push(g);
                }
            }
        }
    };
    d.Clipper.prototype.BuildResult2 = function (a) {
        a.Clear();
        for (var b = 0, c = this.m_PolyOuts.length; b < c; b++) {
            var e = this.m_PolyOuts[b];
            var f = this.PointCount(e.Pts);
            if (!((e.IsOpen && 2 > f) || (!e.IsOpen && 3 > f))) {
                this.FixHoleLinkage(e);
                var g = new d.PolyNode();
                a.m_AllPolys.push(g);
                e.PolyNode = g;
                g.m_polygon.length = f;
                e = e.Pts.Prev;
                for (var h = 0; h < f; h++)
                    (g.m_polygon[h] = e.Pt), (e = e.Prev);
            }
        }
        b = 0;
        for (c = this.m_PolyOuts.length; b < c; b++)
            (e = this.m_PolyOuts[b]),
                null !== e.PolyNode &&
                    (e.IsOpen
                        ? ((e.PolyNode.IsOpen = !0), a.AddChild(e.PolyNode))
                        : null !== e.FirstLeft && null !== e.FirstLeft.PolyNode
                        ? e.FirstLeft.PolyNode.AddChild(e.PolyNode)
                        : a.AddChild(e.PolyNode));
    };
    d.Clipper.prototype.FixupOutPolyline = function (a) {
        for (var b = a.Pts, c = b.Prev; b !== c; )
            if (((b = b.Next), d.IntPoint.op_Equality(b.Pt, b.Prev.Pt))) {
                b === c && (c = b.Prev);
                var e = b.Prev;
                e.Next = b.Next;
                b = b.Next.Prev = e;
            }
        b === b.Prev && (a.Pts = null);
    };
    d.Clipper.prototype.FixupOutPolygon = function (a) {
        var b = null;
        a.BottomPt = null;
        for (
            var c = a.Pts, e = this.PreserveCollinear || this.StrictlySimple;
            ;

        ) {
            if (c.Prev === c || c.Prev === c.Next) {
                a.Pts = null;
                return;
            }
            if (
                d.IntPoint.op_Equality(c.Pt, c.Next.Pt) ||
                d.IntPoint.op_Equality(c.Pt, c.Prev.Pt) ||
                (d.ClipperBase.SlopesEqual4(
                    c.Prev.Pt,
                    c.Pt,
                    c.Next.Pt,
                    this.m_UseFullRange
                ) &&
                    (!e ||
                        !this.Pt2IsBetweenPt1AndPt3(
                            c.Prev.Pt,
                            c.Pt,
                            c.Next.Pt
                        )))
            )
                (b = null), (c.Prev.Next = c.Next), (c = c.Next.Prev = c.Prev);
            else if (c === b) break;
            else null === b && (b = c), (c = c.Next);
        }
        a.Pts = c;
    };
    d.Clipper.prototype.DupOutPt = function (a, b) {
        var c = new d.OutPt();
        c.Pt.X = a.Pt.X;
        c.Pt.Y = a.Pt.Y;
        d.use_xyz && (c.Pt.Z = a.Pt.Z);
        c.Idx = a.Idx;
        b
            ? ((c.Next = a.Next), (c.Prev = a), (a.Next.Prev = c), (a.Next = c))
            : ((c.Prev = a.Prev),
              (c.Next = a),
              (a.Prev.Next = c),
              (a.Prev = c));
        return c;
    };
    d.Clipper.prototype.GetOverlap = function (a, b, c, e, d) {
        a < b
            ? c < e
                ? ((d.Left = Math.max(a, c)), (d.Right = Math.min(b, e)))
                : ((d.Left = Math.max(a, e)), (d.Right = Math.min(b, c)))
            : c < e
            ? ((d.Left = Math.max(b, c)), (d.Right = Math.min(a, e)))
            : ((d.Left = Math.max(b, e)), (d.Right = Math.min(a, c)));
        return d.Left < d.Right;
    };
    d.Clipper.prototype.JoinHorz = function (a, b, c, e, f, g) {
        var h =
            a.Pt.X > b.Pt.X
                ? d.Direction.dRightToLeft
                : d.Direction.dLeftToRight;
        e =
            c.Pt.X > e.Pt.X
                ? d.Direction.dRightToLeft
                : d.Direction.dLeftToRight;
        if (h === e) return !1;
        if (h === d.Direction.dLeftToRight) {
            for (
                ;
                a.Next.Pt.X <= f.X &&
                a.Next.Pt.X >= a.Pt.X &&
                a.Next.Pt.Y === f.Y;

            )
                a = a.Next;
            g && a.Pt.X !== f.X && (a = a.Next);
            b = this.DupOutPt(a, !g);
            d.IntPoint.op_Inequality(b.Pt, f) &&
                ((a = b),
                (a.Pt.X = f.X),
                (a.Pt.Y = f.Y),
                d.use_xyz && (a.Pt.Z = f.Z),
                (b = this.DupOutPt(a, !g)));
        } else {
            for (
                ;
                a.Next.Pt.X >= f.X &&
                a.Next.Pt.X <= a.Pt.X &&
                a.Next.Pt.Y === f.Y;

            )
                a = a.Next;
            g || a.Pt.X === f.X || (a = a.Next);
            b = this.DupOutPt(a, g);
            d.IntPoint.op_Inequality(b.Pt, f) &&
                ((a = b),
                (a.Pt.X = f.X),
                (a.Pt.Y = f.Y),
                d.use_xyz && (a.Pt.Z = f.Z),
                (b = this.DupOutPt(a, g)));
        }
        if (e === d.Direction.dLeftToRight) {
            for (
                ;
                c.Next.Pt.X <= f.X &&
                c.Next.Pt.X >= c.Pt.X &&
                c.Next.Pt.Y === f.Y;

            )
                c = c.Next;
            g && c.Pt.X !== f.X && (c = c.Next);
            e = this.DupOutPt(c, !g);
            d.IntPoint.op_Inequality(e.Pt, f) &&
                ((c = e),
                (c.Pt.X = f.X),
                (c.Pt.Y = f.Y),
                d.use_xyz && (c.Pt.Z = f.Z),
                (e = this.DupOutPt(c, !g)));
        } else {
            for (
                ;
                c.Next.Pt.X >= f.X &&
                c.Next.Pt.X <= c.Pt.X &&
                c.Next.Pt.Y === f.Y;

            )
                c = c.Next;
            g || c.Pt.X === f.X || (c = c.Next);
            e = this.DupOutPt(c, g);
            d.IntPoint.op_Inequality(e.Pt, f) &&
                ((c = e),
                (c.Pt.X = f.X),
                (c.Pt.Y = f.Y),
                d.use_xyz && (c.Pt.Z = f.Z),
                (e = this.DupOutPt(c, g)));
        }
        (h === d.Direction.dLeftToRight) === g
            ? ((a.Prev = c), (c.Next = a), (b.Next = e), (e.Prev = b))
            : ((a.Next = c), (c.Prev = a), (b.Prev = e), (e.Next = b));
        return !0;
    };
    d.Clipper.prototype.JoinPoints = function (a, b, c) {
        var e = a.OutPt1,
            f;
        new d.OutPt();
        var g = a.OutPt2,
            h;
        new d.OutPt();
        if (
            (h = a.OutPt1.Pt.Y === a.OffPt.Y) &&
            d.IntPoint.op_Equality(a.OffPt, a.OutPt1.Pt) &&
            d.IntPoint.op_Equality(a.OffPt, a.OutPt2.Pt)
        ) {
            if (b !== c) return !1;
            for (
                f = a.OutPt1.Next;
                f !== e && d.IntPoint.op_Equality(f.Pt, a.OffPt);

            )
                f = f.Next;
            f = f.Pt.Y > a.OffPt.Y;
            for (
                h = a.OutPt2.Next;
                h !== g && d.IntPoint.op_Equality(h.Pt, a.OffPt);

            )
                h = h.Next;
            if (f === h.Pt.Y > a.OffPt.Y) return !1;
            f
                ? ((f = this.DupOutPt(e, !1)),
                  (h = this.DupOutPt(g, !0)),
                  (e.Prev = g),
                  (g.Next = e),
                  (f.Next = h),
                  (h.Prev = f))
                : ((f = this.DupOutPt(e, !0)),
                  (h = this.DupOutPt(g, !1)),
                  (e.Next = g),
                  (g.Prev = e),
                  (f.Prev = h),
                  (h.Next = f));
            a.OutPt1 = e;
            a.OutPt2 = f;
            return !0;
        }
        if (h) {
            for (
                f = e;
                e.Prev.Pt.Y === e.Pt.Y && e.Prev !== f && e.Prev !== g;

            )
                e = e.Prev;
            for (; f.Next.Pt.Y === f.Pt.Y && f.Next !== e && f.Next !== g; )
                f = f.Next;
            if (f.Next === e || f.Next === g) return !1;
            for (
                h = g;
                g.Prev.Pt.Y === g.Pt.Y && g.Prev !== h && g.Prev !== f;

            )
                g = g.Prev;
            for (; h.Next.Pt.Y === h.Pt.Y && h.Next !== g && h.Next !== e; )
                h = h.Next;
            if (h.Next === g || h.Next === e) return !1;
            c = { Left: null, Right: null };
            if (!this.GetOverlap(e.Pt.X, f.Pt.X, g.Pt.X, h.Pt.X, c)) return !1;
            b = c.Left;
            var k = c.Right;
            c = new d.IntPoint0();
            e.Pt.X >= b && e.Pt.X <= k
                ? ((c.X = e.Pt.X),
                  (c.Y = e.Pt.Y),
                  d.use_xyz && (c.Z = e.Pt.Z),
                  (b = e.Pt.X > f.Pt.X))
                : g.Pt.X >= b && g.Pt.X <= k
                ? ((c.X = g.Pt.X),
                  (c.Y = g.Pt.Y),
                  d.use_xyz && (c.Z = g.Pt.Z),
                  (b = g.Pt.X > h.Pt.X))
                : f.Pt.X >= b && f.Pt.X <= k
                ? ((c.X = f.Pt.X),
                  (c.Y = f.Pt.Y),
                  d.use_xyz && (c.Z = f.Pt.Z),
                  (b = f.Pt.X > e.Pt.X))
                : ((c.X = h.Pt.X),
                  (c.Y = h.Pt.Y),
                  d.use_xyz && (c.Z = h.Pt.Z),
                  (b = h.Pt.X > g.Pt.X));
            a.OutPt1 = e;
            a.OutPt2 = g;
            return this.JoinHorz(e, f, g, h, c, b);
        }
        for (f = e.Next; d.IntPoint.op_Equality(f.Pt, e.Pt) && f !== e; )
            f = f.Next;
        if (
            (k =
                f.Pt.Y > e.Pt.Y ||
                !d.ClipperBase.SlopesEqual4(
                    e.Pt,
                    f.Pt,
                    a.OffPt,
                    this.m_UseFullRange
                ))
        ) {
            for (f = e.Prev; d.IntPoint.op_Equality(f.Pt, e.Pt) && f !== e; )
                f = f.Prev;
            if (
                f.Pt.Y > e.Pt.Y ||
                !d.ClipperBase.SlopesEqual4(
                    e.Pt,
                    f.Pt,
                    a.OffPt,
                    this.m_UseFullRange
                )
            )
                return !1;
        }
        for (h = g.Next; d.IntPoint.op_Equality(h.Pt, g.Pt) && h !== g; )
            h = h.Next;
        var l =
            h.Pt.Y > g.Pt.Y ||
            !d.ClipperBase.SlopesEqual4(
                g.Pt,
                h.Pt,
                a.OffPt,
                this.m_UseFullRange
            );
        if (l) {
            for (h = g.Prev; d.IntPoint.op_Equality(h.Pt, g.Pt) && h !== g; )
                h = h.Prev;
            if (
                h.Pt.Y > g.Pt.Y ||
                !d.ClipperBase.SlopesEqual4(
                    g.Pt,
                    h.Pt,
                    a.OffPt,
                    this.m_UseFullRange
                )
            )
                return !1;
        }
        if (f === e || h === g || f === h || (b === c && k === l)) return !1;
        k
            ? ((f = this.DupOutPt(e, !1)),
              (h = this.DupOutPt(g, !0)),
              (e.Prev = g),
              (g.Next = e),
              (f.Next = h),
              (h.Prev = f))
            : ((f = this.DupOutPt(e, !0)),
              (h = this.DupOutPt(g, !1)),
              (e.Next = g),
              (g.Prev = e),
              (f.Prev = h),
              (h.Next = f));
        a.OutPt1 = e;
        a.OutPt2 = f;
        return !0;
    };
    d.Clipper.GetBounds = function (a) {
        for (var b = 0, c = a.length; b < c && 0 === a[b].length; ) b++;
        if (b === c) return new d.IntRect(0, 0, 0, 0);
        var e = new d.IntRect();
        e.left = a[b][0].X;
        e.right = e.left;
        e.top = a[b][0].Y;
        for (e.bottom = e.top; b < c; b++)
            for (var f = 0, g = a[b].length; f < g; f++)
                a[b][f].X < e.left
                    ? (e.left = a[b][f].X)
                    : a[b][f].X > e.right && (e.right = a[b][f].X),
                    a[b][f].Y < e.top
                        ? (e.top = a[b][f].Y)
                        : a[b][f].Y > e.bottom && (e.bottom = a[b][f].Y);
        return e;
    };
    d.Clipper.prototype.GetBounds2 = function (a) {
        var b = a,
            c = new d.IntRect();
        c.left = a.Pt.X;
        c.right = a.Pt.X;
        c.top = a.Pt.Y;
        c.bottom = a.Pt.Y;
        for (a = a.Next; a !== b; )
            a.Pt.X < c.left && (c.left = a.Pt.X),
                a.Pt.X > c.right && (c.right = a.Pt.X),
                a.Pt.Y < c.top && (c.top = a.Pt.Y),
                a.Pt.Y > c.bottom && (c.bottom = a.Pt.Y),
                (a = a.Next);
        return c;
    };
    d.Clipper.PointInPolygon = function (a, b) {
        var c = 0,
            e = b.length;
        if (3 > e) return 0;
        for (var d = b[0], g = 1; g <= e; ++g) {
            var h = g === e ? b[0] : b[g];
            if (
                h.Y === a.Y &&
                (h.X === a.X || (d.Y === a.Y && h.X > a.X === d.X < a.X))
            )
                return -1;
            if (d.Y < a.Y !== h.Y < a.Y)
                if (d.X >= a.X)
                    if (h.X > a.X) c = 1 - c;
                    else {
                        var k =
                            (d.X - a.X) * (h.Y - a.Y) -
                            (h.X - a.X) * (d.Y - a.Y);
                        if (0 === k) return -1;
                        0 < k === h.Y > d.Y && (c = 1 - c);
                    }
                else if (h.X > a.X) {
                    k = (d.X - a.X) * (h.Y - a.Y) - (h.X - a.X) * (d.Y - a.Y);
                    if (0 === k) return -1;
                    0 < k === h.Y > d.Y && (c = 1 - c);
                }
            d = h;
        }
        return c;
    };
    d.Clipper.prototype.PointInPolygon = function (a, b) {
        var c = 0,
            d = b,
            f = a.X,
            g = a.Y;
        var h = b.Pt.X;
        var k = b.Pt.Y;
        do {
            b = b.Next;
            var l = b.Pt.X,
                n = b.Pt.Y;
            if (n === g && (l === f || (k === g && l > f === h < f))) return -1;
            if (k < g !== n < g)
                if (h >= f)
                    if (l > f) c = 1 - c;
                    else {
                        h = (h - f) * (n - g) - (l - f) * (k - g);
                        if (0 === h) return -1;
                        0 < h === n > k && (c = 1 - c);
                    }
                else if (l > f) {
                    h = (h - f) * (n - g) - (l - f) * (k - g);
                    if (0 === h) return -1;
                    0 < h === n > k && (c = 1 - c);
                }
            h = l;
            k = n;
        } while (d !== b);
        return c;
    };
    d.Clipper.prototype.Poly2ContainsPoly1 = function (a, b) {
        var c = a;
        do {
            var d = this.PointInPolygon(c.Pt, b);
            if (0 <= d) return 0 < d;
            c = c.Next;
        } while (c !== a);
        return !0;
    };
    d.Clipper.prototype.FixupFirstLefts1 = function (a, b) {
        for (var c, e, f = 0, g = this.m_PolyOuts.length; f < g; f++)
            (c = this.m_PolyOuts[f]),
                (e = d.Clipper.ParseFirstLeft(c.FirstLeft)),
                null !== c.Pts &&
                    e === a &&
                    this.Poly2ContainsPoly1(c.Pts, b.Pts) &&
                    (c.FirstLeft = b);
    };
    d.Clipper.prototype.FixupFirstLefts2 = function (a, b) {
        for (
            var c = b.FirstLeft, e, f, g = 0, h = this.m_PolyOuts.length;
            g < h;
            g++
        )
            if (
                ((e = this.m_PolyOuts[g]),
                null !== e.Pts &&
                    e !== b &&
                    e !== a &&
                    ((f = d.Clipper.ParseFirstLeft(e.FirstLeft)),
                    f === c || f === a || f === b))
            )
                if (this.Poly2ContainsPoly1(e.Pts, a.Pts)) e.FirstLeft = a;
                else if (this.Poly2ContainsPoly1(e.Pts, b.Pts)) e.FirstLeft = b;
                else if (e.FirstLeft === a || e.FirstLeft === b)
                    e.FirstLeft = c;
    };
    d.Clipper.prototype.FixupFirstLefts3 = function (a, b) {
        for (var c, e, f = 0, g = this.m_PolyOuts.length; f < g; f++)
            (c = this.m_PolyOuts[f]),
                (e = d.Clipper.ParseFirstLeft(c.FirstLeft)),
                null !== c.Pts && e === a && (c.FirstLeft = b);
    };
    d.Clipper.ParseFirstLeft = function (a) {
        for (; null !== a && null === a.Pts; ) a = a.FirstLeft;
        return a;
    };
    d.Clipper.prototype.JoinCommonEdges = function () {
        for (var a = 0, b = this.m_Joins.length; a < b; a++) {
            var c = this.m_Joins[a],
                d = this.GetOutRec(c.OutPt1.Idx),
                f = this.GetOutRec(c.OutPt2.Idx);
            if (null !== d.Pts && null !== f.Pts && !d.IsOpen && !f.IsOpen) {
                var g =
                    d === f
                        ? d
                        : this.OutRec1RightOfOutRec2(d, f)
                        ? f
                        : this.OutRec1RightOfOutRec2(f, d)
                        ? d
                        : this.GetLowermostRec(d, f);
                this.JoinPoints(c, d, f) &&
                    (d === f
                        ? ((d.Pts = c.OutPt1),
                          (d.BottomPt = null),
                          (f = this.CreateOutRec()),
                          (f.Pts = c.OutPt2),
                          this.UpdateOutPtIdxs(f),
                          this.Poly2ContainsPoly1(f.Pts, d.Pts)
                              ? ((f.IsHole = !d.IsHole),
                                (f.FirstLeft = d),
                                this.m_UsingPolyTree &&
                                    this.FixupFirstLefts2(f, d),
                                (f.IsHole ^ this.ReverseSolution) ==
                                    0 < this.Area$1(f) &&
                                    this.ReversePolyPtLinks(f.Pts))
                              : this.Poly2ContainsPoly1(d.Pts, f.Pts)
                              ? ((f.IsHole = d.IsHole),
                                (d.IsHole = !f.IsHole),
                                (f.FirstLeft = d.FirstLeft),
                                (d.FirstLeft = f),
                                this.m_UsingPolyTree &&
                                    this.FixupFirstLefts2(d, f),
                                (d.IsHole ^ this.ReverseSolution) ==
                                    0 < this.Area$1(d) &&
                                    this.ReversePolyPtLinks(d.Pts))
                              : ((f.IsHole = d.IsHole),
                                (f.FirstLeft = d.FirstLeft),
                                this.m_UsingPolyTree &&
                                    this.FixupFirstLefts1(d, f)))
                        : ((f.Pts = null),
                          (f.BottomPt = null),
                          (f.Idx = d.Idx),
                          (d.IsHole = g.IsHole),
                          g === f && (d.FirstLeft = f.FirstLeft),
                          (f.FirstLeft = d),
                          this.m_UsingPolyTree && this.FixupFirstLefts3(f, d)));
            }
        }
    };
    d.Clipper.prototype.UpdateOutPtIdxs = function (a) {
        var b = a.Pts;
        do (b.Idx = a.Idx), (b = b.Prev);
        while (b !== a.Pts);
    };
    d.Clipper.prototype.DoSimplePolygons = function () {
        for (var a = 0; a < this.m_PolyOuts.length; ) {
            var b = this.m_PolyOuts[a++],
                c = b.Pts;
            if (null !== c && !b.IsOpen) {
                do {
                    for (var e = c.Next; e !== b.Pts; ) {
                        if (
                            d.IntPoint.op_Equality(c.Pt, e.Pt) &&
                            e.Next !== c &&
                            e.Prev !== c
                        ) {
                            var f = c.Prev,
                                g = e.Prev;
                            c.Prev = g;
                            g.Next = c;
                            e.Prev = f;
                            f.Next = e;
                            b.Pts = c;
                            f = this.CreateOutRec();
                            f.Pts = e;
                            this.UpdateOutPtIdxs(f);
                            this.Poly2ContainsPoly1(f.Pts, b.Pts)
                                ? ((f.IsHole = !b.IsHole),
                                  (f.FirstLeft = b),
                                  this.m_UsingPolyTree &&
                                      this.FixupFirstLefts2(f, b))
                                : this.Poly2ContainsPoly1(b.Pts, f.Pts)
                                ? ((f.IsHole = b.IsHole),
                                  (b.IsHole = !f.IsHole),
                                  (f.FirstLeft = b.FirstLeft),
                                  (b.FirstLeft = f),
                                  this.m_UsingPolyTree &&
                                      this.FixupFirstLefts2(b, f))
                                : ((f.IsHole = b.IsHole),
                                  (f.FirstLeft = b.FirstLeft),
                                  this.m_UsingPolyTree &&
                                      this.FixupFirstLefts1(b, f));
                            e = c;
                        }
                        e = e.Next;
                    }
                    c = c.Next;
                } while (c !== b.Pts);
            }
        }
    };
    d.Clipper.Area = function (a) {
        if (!Array.isArray(a)) return 0;
        var b = a.length;
        if (3 > b) return 0;
        for (var c = 0, d = 0, f = b - 1; d < b; ++d)
            (c += (a[f].X + a[d].X) * (a[f].Y - a[d].Y)), (f = d);
        return 0.5 * -c;
    };
    d.Clipper.prototype.Area = function (a) {
        var b = a;
        if (null === a) return 0;
        var c = 0;
        do (c += (a.Prev.Pt.X + a.Pt.X) * (a.Prev.Pt.Y - a.Pt.Y)), (a = a.Next);
        while (a !== b);
        return 0.5 * c;
    };
    d.Clipper.prototype.Area$1 = function (a) {
        return this.Area(a.Pts);
    };
    d.Clipper.SimplifyPolygon = function (a, b) {
        var c = [],
            e = new d.Clipper(0);
        e.StrictlySimple = !0;
        e.AddPath(a, d.PolyType.ptSubject, !0);
        e.Execute(d.ClipType.ctUnion, c, b, b);
        return c;
    };
    d.Clipper.SimplifyPolygons = function (a, b) {
        "undefined" === typeof b && (b = d.PolyFillType.pftEvenOdd);
        var c = [],
            e = new d.Clipper(0);
        e.StrictlySimple = !0;
        e.AddPaths(a, d.PolyType.ptSubject, !0);
        e.Execute(d.ClipType.ctUnion, c, b, b);
        return c;
    };
    d.Clipper.DistanceSqrd = function (a, b) {
        var c = a.X - b.X,
            d = a.Y - b.Y;
        return c * c + d * d;
    };
    d.Clipper.DistanceFromLineSqrd = function (a, b, c) {
        var d = b.Y - c.Y;
        c = c.X - b.X;
        b = d * b.X + c * b.Y;
        b = d * a.X + c * a.Y - b;
        return (b * b) / (d * d + c * c);
    };
    d.Clipper.SlopesNearCollinear = function (a, b, c, e) {
        return Math.abs(a.X - b.X) > Math.abs(a.Y - b.Y)
            ? a.X > b.X === a.X < c.X
                ? d.Clipper.DistanceFromLineSqrd(a, b, c) < e
                : b.X > a.X === b.X < c.X
                ? d.Clipper.DistanceFromLineSqrd(b, a, c) < e
                : d.Clipper.DistanceFromLineSqrd(c, a, b) < e
            : a.Y > b.Y === a.Y < c.Y
            ? d.Clipper.DistanceFromLineSqrd(a, b, c) < e
            : b.Y > a.Y === b.Y < c.Y
            ? d.Clipper.DistanceFromLineSqrd(b, a, c) < e
            : d.Clipper.DistanceFromLineSqrd(c, a, b) < e;
    };
    d.Clipper.PointsAreClose = function (a, b, c) {
        var d = a.X - b.X;
        a = a.Y - b.Y;
        return d * d + a * a <= c;
    };
    d.Clipper.ExcludeOp = function (a) {
        var b = a.Prev;
        b.Next = a.Next;
        a.Next.Prev = b;
        b.Idx = 0;
        return b;
    };
    d.Clipper.CleanPolygon = function (a, b) {
        "undefined" === typeof b && (b = 1.415);
        var c = a.length;
        if (0 === c) return [];
        for (var e = Array(c), f = 0; f < c; ++f) e[f] = new d.OutPt();
        for (f = 0; f < c; ++f)
            (e[f].Pt = a[f]),
                (e[f].Next = e[(f + 1) % c]),
                (e[f].Next.Prev = e[f]),
                (e[f].Idx = 0);
        f = b * b;
        for (e = e[0]; 0 === e.Idx && e.Next !== e.Prev; )
            d.Clipper.PointsAreClose(e.Pt, e.Prev.Pt, f)
                ? ((e = d.Clipper.ExcludeOp(e)), c--)
                : d.Clipper.PointsAreClose(e.Prev.Pt, e.Next.Pt, f)
                ? (d.Clipper.ExcludeOp(e.Next),
                  (e = d.Clipper.ExcludeOp(e)),
                  (c -= 2))
                : d.Clipper.SlopesNearCollinear(e.Prev.Pt, e.Pt, e.Next.Pt, f)
                ? ((e = d.Clipper.ExcludeOp(e)), c--)
                : ((e.Idx = 1), (e = e.Next));
        3 > c && (c = 0);
        var g = Array(c);
        for (f = 0; f < c; ++f) (g[f] = new d.IntPoint1(e.Pt)), (e = e.Next);
        return g;
    };
    d.Clipper.CleanPolygons = function (a, b) {
        for (var c = Array(a.length), e = 0, f = a.length; e < f; e++)
            c[e] = d.Clipper.CleanPolygon(a[e], b);
        return c;
    };
    d.Clipper.Minkowski = function (a, b, c, e) {
        e = e ? 1 : 0;
        var f = a.length,
            g = b.length,
            h = [];
        if (c)
            for (c = 0; c < g; c++) {
                var k = Array(f);
                for (var l = 0, n = a.length, r = a[l]; l < n; l++, r = a[l])
                    k[l] = new d.IntPoint2(b[c].X + r.X, b[c].Y + r.Y);
                h.push(k);
            }
        else
            for (c = 0; c < g; c++) {
                k = Array(f);
                l = 0;
                n = a.length;
                for (r = a[l]; l < n; l++, r = a[l])
                    k[l] = new d.IntPoint2(b[c].X - r.X, b[c].Y - r.Y);
                h.push(k);
            }
        a = [];
        for (c = 0; c < g - 1 + e; c++)
            for (l = 0; l < f; l++)
                (b = []),
                    b.push(h[c % g][l % f]),
                    b.push(h[(c + 1) % g][l % f]),
                    b.push(h[(c + 1) % g][(l + 1) % f]),
                    b.push(h[c % g][(l + 1) % f]),
                    d.Clipper.Orientation(b) || b.reverse(),
                    a.push(b);
        return a;
    };
    d.Clipper.MinkowskiSum = function (a, b, c) {
        if (b[0] instanceof Array) {
            var e = b;
            var f = new d.Paths();
            b = new d.Clipper();
            for (var g = 0; g < e.length; ++g) {
                var h = d.Clipper.Minkowski(a, e[g], !0, c);
                b.AddPaths(h, d.PolyType.ptSubject, !0);
                c &&
                    ((h = d.Clipper.TranslatePath(e[g], a[0])),
                    b.AddPath(h, d.PolyType.ptClip, !0));
            }
            b.Execute(
                d.ClipType.ctUnion,
                f,
                d.PolyFillType.pftNonZero,
                d.PolyFillType.pftNonZero
            );
            return f;
        }
        e = d.Clipper.Minkowski(a, b, !0, c);
        b = new d.Clipper();
        b.AddPaths(e, d.PolyType.ptSubject, !0);
        b.Execute(
            d.ClipType.ctUnion,
            e,
            d.PolyFillType.pftNonZero,
            d.PolyFillType.pftNonZero
        );
        return e;
    };
    d.Clipper.TranslatePath = function (a, b) {
        for (var c = new d.Path(), e = 0; e < a.length; e++)
            c.push(new d.IntPoint2(a[e].X + b.X, a[e].Y + b.Y));
        return c;
    };
    d.Clipper.MinkowskiDiff = function (a, b) {
        var c = d.Clipper.Minkowski(a, b, !1, !0),
            e = new d.Clipper();
        e.AddPaths(c, d.PolyType.ptSubject, !0);
        e.Execute(
            d.ClipType.ctUnion,
            c,
            d.PolyFillType.pftNonZero,
            d.PolyFillType.pftNonZero
        );
        return c;
    };
    d.Clipper.PolyTreeToPaths = function (a) {
        var b = [];
        d.Clipper.AddPolyNodeToPaths(a, d.Clipper.NodeType.ntAny, b);
        return b;
    };
    d.Clipper.AddPolyNodeToPaths = function (a, b, c) {
        var e = !0;
        switch (b) {
            case d.Clipper.NodeType.ntOpen:
                return;
            case d.Clipper.NodeType.ntClosed:
                e = !a.IsOpen;
        }
        0 < a.m_polygon.length && e && c.push(a.m_polygon);
        e = 0;
        a = a.Childs();
        for (var f = a.length, g = a[e]; e < f; e++, g = a[e])
            d.Clipper.AddPolyNodeToPaths(g, b, c);
    };
    d.Clipper.OpenPathsFromPolyTree = function (a) {
        for (var b = new d.Paths(), c = 0, e = a.ChildCount(); c < e; c++)
            a.Childs()[c].IsOpen && b.push(a.Childs()[c].m_polygon);
        return b;
    };
    d.Clipper.ClosedPathsFromPolyTree = function (a) {
        var b = new d.Paths();
        d.Clipper.AddPolyNodeToPaths(a, d.Clipper.NodeType.ntClosed, b);
        return b;
    };
    v(d.Clipper, d.ClipperBase);
    d.Clipper.NodeType = { ntAny: 0, ntOpen: 1, ntClosed: 2 };
    d.ClipperOffset = function (a, b) {
        "undefined" === typeof a && (a = 2);
        "undefined" === typeof b && (b = d.ClipperOffset.def_arc_tolerance);
        this.m_destPolys = new d.Paths();
        this.m_srcPoly = new d.Path();
        this.m_destPoly = new d.Path();
        this.m_normals = [];
        this.m_StepsPerRad =
            this.m_miterLim =
            this.m_cos =
            this.m_sin =
            this.m_sinA =
            this.m_delta =
                0;
        this.m_lowest = new d.IntPoint0();
        this.m_polyNodes = new d.PolyNode();
        this.MiterLimit = a;
        this.ArcTolerance = b;
        this.m_lowest.X = -1;
    };
    d.ClipperOffset.two_pi = 6.28318530717959;
    d.ClipperOffset.def_arc_tolerance = 0.25;
    d.ClipperOffset.prototype.Clear = function () {
        d.Clear(this.m_polyNodes.Childs());
        this.m_lowest.X = -1;
    };
    d.ClipperOffset.Round = d.Clipper.Round;
    d.ClipperOffset.prototype.AddPath = function (a, b, c) {
        var e = a.length - 1;
        if (!(0 > e)) {
            var f = new d.PolyNode();
            f.m_jointype = b;
            f.m_endtype = c;
            if (c === d.EndType.etClosedLine || c === d.EndType.etClosedPolygon)
                for (; 0 < e && d.IntPoint.op_Equality(a[0], a[e]); ) e--;
            f.m_polygon.push(a[0]);
            var g = 0;
            b = 0;
            for (var h = 1; h <= e; h++)
                d.IntPoint.op_Inequality(f.m_polygon[g], a[h]) &&
                    (g++,
                    f.m_polygon.push(a[h]),
                    a[h].Y > f.m_polygon[b].Y ||
                        (a[h].Y === f.m_polygon[b].Y &&
                            a[h].X < f.m_polygon[b].X)) &&
                    (b = g);
            if (
                !(c === d.EndType.etClosedPolygon && 2 > g) &&
                (this.m_polyNodes.AddChild(f), c === d.EndType.etClosedPolygon)
            )
                if (0 > this.m_lowest.X)
                    this.m_lowest = new d.IntPoint2(
                        this.m_polyNodes.ChildCount() - 1,
                        b
                    );
                else if (
                    ((a =
                        this.m_polyNodes.Childs()[this.m_lowest.X].m_polygon[
                            this.m_lowest.Y
                        ]),
                    f.m_polygon[b].Y > a.Y ||
                        (f.m_polygon[b].Y === a.Y && f.m_polygon[b].X < a.X))
                )
                    this.m_lowest = new d.IntPoint2(
                        this.m_polyNodes.ChildCount() - 1,
                        b
                    );
        }
    };
    d.ClipperOffset.prototype.AddPaths = function (a, b, c) {
        for (var d = 0, f = a.length; d < f; d++) this.AddPath(a[d], b, c);
    };
    d.ClipperOffset.prototype.FixOrientations = function () {
        if (
            0 <= this.m_lowest.X &&
            !d.Clipper.Orientation(
                this.m_polyNodes.Childs()[this.m_lowest.X].m_polygon
            )
        )
            for (var a = 0; a < this.m_polyNodes.ChildCount(); a++) {
                var b = this.m_polyNodes.Childs()[a];
                (b.m_endtype === d.EndType.etClosedPolygon ||
                    (b.m_endtype === d.EndType.etClosedLine &&
                        d.Clipper.Orientation(b.m_polygon))) &&
                    b.m_polygon.reverse();
            }
        else
            for (a = 0; a < this.m_polyNodes.ChildCount(); a++)
                (b = this.m_polyNodes.Childs()[a]),
                    b.m_endtype !== d.EndType.etClosedLine ||
                        d.Clipper.Orientation(b.m_polygon) ||
                        b.m_polygon.reverse();
    };
    d.ClipperOffset.GetUnitNormal = function (a, b) {
        var c = b.X - a.X,
            e = b.Y - a.Y;
        if (0 === c && 0 === e) return new d.DoublePoint2(0, 0);
        var f = 1 / Math.sqrt(c * c + e * e);
        return new d.DoublePoint2(e * f, -(c * f));
    };
    d.ClipperOffset.prototype.DoOffset = function (a) {
        var b;
        this.m_destPolys = [];
        this.m_delta = a;
        if (d.ClipperBase.near_zero(a))
            for (var c = 0; c < this.m_polyNodes.ChildCount(); c++) {
                var e = this.m_polyNodes.Childs()[c];
                e.m_endtype === d.EndType.etClosedPolygon &&
                    this.m_destPolys.push(e.m_polygon);
            }
        else {
            this.m_miterLim =
                2 < this.MiterLimit
                    ? 2 / (this.MiterLimit * this.MiterLimit)
                    : 0.5;
            var f =
                3.14159265358979 /
                Math.acos(
                    1 -
                        (0 >= this.ArcTolerance
                            ? d.ClipperOffset.def_arc_tolerance
                            : this.ArcTolerance >
                              Math.abs(a) * d.ClipperOffset.def_arc_tolerance
                            ? Math.abs(a) * d.ClipperOffset.def_arc_tolerance
                            : this.ArcTolerance) /
                            Math.abs(a)
                );
            this.m_sin = Math.sin(d.ClipperOffset.two_pi / f);
            this.m_cos = Math.cos(d.ClipperOffset.two_pi / f);
            this.m_StepsPerRad = f / d.ClipperOffset.two_pi;
            0 > a && (this.m_sin = -this.m_sin);
            for (c = 0; c < this.m_polyNodes.ChildCount(); c++) {
                e = this.m_polyNodes.Childs()[c];
                this.m_srcPoly = e.m_polygon;
                var g = this.m_srcPoly.length;
                if (
                    !(
                        0 === g ||
                        (0 >= a &&
                            (3 > g ||
                                e.m_endtype !== d.EndType.etClosedPolygon))
                    )
                ) {
                    this.m_destPoly = [];
                    if (1 === g)
                        if (e.m_jointype === d.JoinType.jtRound)
                            for (g = 1, e = 0, b = 1; b <= f; b++) {
                                this.m_destPoly.push(
                                    new d.IntPoint2(
                                        d.ClipperOffset.Round(
                                            this.m_srcPoly[0].X + g * a
                                        ),
                                        d.ClipperOffset.Round(
                                            this.m_srcPoly[0].Y + e * a
                                        )
                                    )
                                );
                                var h = g;
                                g = g * this.m_cos - this.m_sin * e;
                                e = h * this.m_sin + e * this.m_cos;
                            }
                        else
                            for (e = g = -1, b = 0; 4 > b; ++b)
                                this.m_destPoly.push(
                                    new d.IntPoint2(
                                        d.ClipperOffset.Round(
                                            this.m_srcPoly[0].X + g * a
                                        ),
                                        d.ClipperOffset.Round(
                                            this.m_srcPoly[0].Y + e * a
                                        )
                                    )
                                ),
                                    0 > g
                                        ? (g = 1)
                                        : 0 > e
                                        ? (e = 1)
                                        : (g = -1);
                    else {
                        for (b = this.m_normals.length = 0; b < g - 1; b++)
                            this.m_normals.push(
                                d.ClipperOffset.GetUnitNormal(
                                    this.m_srcPoly[b],
                                    this.m_srcPoly[b + 1]
                                )
                            );
                        e.m_endtype === d.EndType.etClosedLine ||
                        e.m_endtype === d.EndType.etClosedPolygon
                            ? this.m_normals.push(
                                  d.ClipperOffset.GetUnitNormal(
                                      this.m_srcPoly[g - 1],
                                      this.m_srcPoly[0]
                                  )
                              )
                            : this.m_normals.push(
                                  new d.DoublePoint1(this.m_normals[g - 2])
                              );
                        if (e.m_endtype === d.EndType.etClosedPolygon)
                            for (h = g - 1, b = 0; b < g; b++)
                                h = this.OffsetPoint(b, h, e.m_jointype);
                        else if (e.m_endtype === d.EndType.etClosedLine) {
                            h = g - 1;
                            for (b = 0; b < g; b++)
                                h = this.OffsetPoint(b, h, e.m_jointype);
                            this.m_destPolys.push(this.m_destPoly);
                            this.m_destPoly = [];
                            h = this.m_normals[g - 1];
                            for (b = g - 1; 0 < b; b--)
                                this.m_normals[b] = new d.DoublePoint2(
                                    -this.m_normals[b - 1].X,
                                    -this.m_normals[b - 1].Y
                                );
                            this.m_normals[0] = new d.DoublePoint2(-h.X, -h.Y);
                            h = 0;
                            for (b = g - 1; 0 <= b; b--)
                                h = this.OffsetPoint(b, h, e.m_jointype);
                        } else {
                            h = 0;
                            for (b = 1; b < g - 1; ++b)
                                h = this.OffsetPoint(b, h, e.m_jointype);
                            e.m_endtype === d.EndType.etOpenButt
                                ? ((b = g - 1),
                                  (h = new d.IntPoint2(
                                      d.ClipperOffset.Round(
                                          this.m_srcPoly[b].X +
                                              this.m_normals[b].X * a
                                      ),
                                      d.ClipperOffset.Round(
                                          this.m_srcPoly[b].Y +
                                              this.m_normals[b].Y * a
                                      )
                                  )),
                                  this.m_destPoly.push(h),
                                  (h = new d.IntPoint2(
                                      d.ClipperOffset.Round(
                                          this.m_srcPoly[b].X -
                                              this.m_normals[b].X * a
                                      ),
                                      d.ClipperOffset.Round(
                                          this.m_srcPoly[b].Y -
                                              this.m_normals[b].Y * a
                                      )
                                  )),
                                  this.m_destPoly.push(h))
                                : ((b = g - 1),
                                  (h = g - 2),
                                  (this.m_sinA = 0),
                                  (this.m_normals[b] = new d.DoublePoint2(
                                      -this.m_normals[b].X,
                                      -this.m_normals[b].Y
                                  )),
                                  e.m_endtype === d.EndType.etOpenSquare
                                      ? this.DoSquare(b, h)
                                      : this.DoRound(b, h));
                            for (b = g - 1; 0 < b; b--)
                                this.m_normals[b] = new d.DoublePoint2(
                                    -this.m_normals[b - 1].X,
                                    -this.m_normals[b - 1].Y
                                );
                            this.m_normals[0] = new d.DoublePoint2(
                                -this.m_normals[1].X,
                                -this.m_normals[1].Y
                            );
                            h = g - 1;
                            for (b = h - 1; 0 < b; --b)
                                h = this.OffsetPoint(b, h, e.m_jointype);
                            e.m_endtype === d.EndType.etOpenButt
                                ? ((h = new d.IntPoint2(
                                      d.ClipperOffset.Round(
                                          this.m_srcPoly[0].X -
                                              this.m_normals[0].X * a
                                      ),
                                      d.ClipperOffset.Round(
                                          this.m_srcPoly[0].Y -
                                              this.m_normals[0].Y * a
                                      )
                                  )),
                                  this.m_destPoly.push(h),
                                  (h = new d.IntPoint2(
                                      d.ClipperOffset.Round(
                                          this.m_srcPoly[0].X +
                                              this.m_normals[0].X * a
                                      ),
                                      d.ClipperOffset.Round(
                                          this.m_srcPoly[0].Y +
                                              this.m_normals[0].Y * a
                                      )
                                  )),
                                  this.m_destPoly.push(h))
                                : ((this.m_sinA = 0),
                                  e.m_endtype === d.EndType.etOpenSquare
                                      ? this.DoSquare(0, 1)
                                      : this.DoRound(0, 1));
                        }
                    }
                    this.m_destPolys.push(this.m_destPoly);
                }
            }
        }
    };
    d.ClipperOffset.prototype.Execute = function () {
        var a = arguments;
        if (a[0] instanceof d.PolyTree) {
            var b = a[0];
            var c = a[1];
            b.Clear();
            this.FixOrientations();
            this.DoOffset(c);
            a = new d.Clipper(0);
            a.AddPaths(this.m_destPolys, d.PolyType.ptSubject, !0);
            if (0 < c)
                a.Execute(
                    d.ClipType.ctUnion,
                    b,
                    d.PolyFillType.pftPositive,
                    d.PolyFillType.pftPositive
                );
            else {
                var e = d.Clipper.GetBounds(this.m_destPolys);
                c = new d.Path();
                c.push(new d.IntPoint2(e.left - 10, e.bottom + 10));
                c.push(new d.IntPoint2(e.right + 10, e.bottom + 10));
                c.push(new d.IntPoint2(e.right + 10, e.top - 10));
                c.push(new d.IntPoint2(e.left - 10, e.top - 10));
                a.AddPath(c, d.PolyType.ptSubject, !0);
                a.ReverseSolution = !0;
                a.Execute(
                    d.ClipType.ctUnion,
                    b,
                    d.PolyFillType.pftNegative,
                    d.PolyFillType.pftNegative
                );
                if (1 === b.ChildCount() && 0 < b.Childs()[0].ChildCount())
                    for (
                        a = b.Childs()[0],
                            b.Childs()[0] = a.Childs()[0],
                            b.Childs()[0].m_Parent = b,
                            c = 1;
                        c < a.ChildCount();
                        c++
                    )
                        b.AddChild(a.Childs()[c]);
                else b.Clear();
            }
        } else
            (b = a[0]),
                (c = a[1]),
                d.Clear(b),
                this.FixOrientations(),
                this.DoOffset(c),
                (a = new d.Clipper(0)),
                a.AddPaths(this.m_destPolys, d.PolyType.ptSubject, !0),
                0 < c
                    ? a.Execute(
                          d.ClipType.ctUnion,
                          b,
                          d.PolyFillType.pftPositive,
                          d.PolyFillType.pftPositive
                      )
                    : ((e = d.Clipper.GetBounds(this.m_destPolys)),
                      (c = new d.Path()),
                      c.push(new d.IntPoint2(e.left - 10, e.bottom + 10)),
                      c.push(new d.IntPoint2(e.right + 10, e.bottom + 10)),
                      c.push(new d.IntPoint2(e.right + 10, e.top - 10)),
                      c.push(new d.IntPoint2(e.left - 10, e.top - 10)),
                      a.AddPath(c, d.PolyType.ptSubject, !0),
                      (a.ReverseSolution = !0),
                      a.Execute(
                          d.ClipType.ctUnion,
                          b,
                          d.PolyFillType.pftNegative,
                          d.PolyFillType.pftNegative
                      ),
                      0 < b.length && b.splice(0, 1));
    };
    d.ClipperOffset.prototype.OffsetPoint = function (a, b, c) {
        this.m_sinA =
            this.m_normals[b].X * this.m_normals[a].Y -
            this.m_normals[a].X * this.m_normals[b].Y;
        if (1 > Math.abs(this.m_sinA * this.m_delta)) {
            if (
                0 <
                this.m_normals[b].X * this.m_normals[a].X +
                    this.m_normals[a].Y * this.m_normals[b].Y
            )
                return (
                    this.m_destPoly.push(
                        new d.IntPoint2(
                            d.ClipperOffset.Round(
                                this.m_srcPoly[a].X +
                                    this.m_normals[b].X * this.m_delta
                            ),
                            d.ClipperOffset.Round(
                                this.m_srcPoly[a].Y +
                                    this.m_normals[b].Y * this.m_delta
                            )
                        )
                    ),
                    b
                );
        } else
            1 < this.m_sinA
                ? (this.m_sinA = 1)
                : -1 > this.m_sinA && (this.m_sinA = -1);
        if (0 > this.m_sinA * this.m_delta)
            this.m_destPoly.push(
                new d.IntPoint2(
                    d.ClipperOffset.Round(
                        this.m_srcPoly[a].X + this.m_normals[b].X * this.m_delta
                    ),
                    d.ClipperOffset.Round(
                        this.m_srcPoly[a].Y + this.m_normals[b].Y * this.m_delta
                    )
                )
            ),
                this.m_destPoly.push(new d.IntPoint1(this.m_srcPoly[a])),
                this.m_destPoly.push(
                    new d.IntPoint2(
                        d.ClipperOffset.Round(
                            this.m_srcPoly[a].X +
                                this.m_normals[a].X * this.m_delta
                        ),
                        d.ClipperOffset.Round(
                            this.m_srcPoly[a].Y +
                                this.m_normals[a].Y * this.m_delta
                        )
                    )
                );
        else
            switch (c) {
                case d.JoinType.jtMiter:
                    c =
                        1 +
                        (this.m_normals[a].X * this.m_normals[b].X +
                            this.m_normals[a].Y * this.m_normals[b].Y);
                    c >= this.m_miterLim
                        ? this.DoMiter(a, b, c)
                        : this.DoSquare(a, b);
                    break;
                case d.JoinType.jtSquare:
                    this.DoSquare(a, b);
                    break;
                case d.JoinType.jtRound:
                    this.DoRound(a, b);
            }
        return a;
    };
    d.ClipperOffset.prototype.DoSquare = function (a, b) {
        var c = Math.tan(
            Math.atan2(
                this.m_sinA,
                this.m_normals[b].X * this.m_normals[a].X +
                    this.m_normals[b].Y * this.m_normals[a].Y
            ) / 4
        );
        this.m_destPoly.push(
            new d.IntPoint2(
                d.ClipperOffset.Round(
                    this.m_srcPoly[a].X +
                        this.m_delta *
                            (this.m_normals[b].X - this.m_normals[b].Y * c)
                ),
                d.ClipperOffset.Round(
                    this.m_srcPoly[a].Y +
                        this.m_delta *
                            (this.m_normals[b].Y + this.m_normals[b].X * c)
                )
            )
        );
        this.m_destPoly.push(
            new d.IntPoint2(
                d.ClipperOffset.Round(
                    this.m_srcPoly[a].X +
                        this.m_delta *
                            (this.m_normals[a].X + this.m_normals[a].Y * c)
                ),
                d.ClipperOffset.Round(
                    this.m_srcPoly[a].Y +
                        this.m_delta *
                            (this.m_normals[a].Y - this.m_normals[a].X * c)
                )
            )
        );
    };
    d.ClipperOffset.prototype.DoMiter = function (a, b, c) {
        c = this.m_delta / c;
        this.m_destPoly.push(
            new d.IntPoint2(
                d.ClipperOffset.Round(
                    this.m_srcPoly[a].X +
                        (this.m_normals[b].X + this.m_normals[a].X) * c
                ),
                d.ClipperOffset.Round(
                    this.m_srcPoly[a].Y +
                        (this.m_normals[b].Y + this.m_normals[a].Y) * c
                )
            )
        );
    };
    d.ClipperOffset.prototype.DoRound = function (a, b) {
        for (
            var c = Math.max(
                    d.Cast_Int32(
                        d.ClipperOffset.Round(
                            this.m_StepsPerRad *
                                Math.abs(
                                    Math.atan2(
                                        this.m_sinA,
                                        this.m_normals[b].X *
                                            this.m_normals[a].X +
                                            this.m_normals[b].Y *
                                                this.m_normals[a].Y
                                    )
                                )
                        )
                    ),
                    1
                ),
                e = this.m_normals[b].X,
                f = this.m_normals[b].Y,
                g,
                h = 0;
            h < c;
            ++h
        )
            this.m_destPoly.push(
                new d.IntPoint2(
                    d.ClipperOffset.Round(
                        this.m_srcPoly[a].X + e * this.m_delta
                    ),
                    d.ClipperOffset.Round(
                        this.m_srcPoly[a].Y + f * this.m_delta
                    )
                )
            ),
                (g = e),
                (e = e * this.m_cos - this.m_sin * f),
                (f = g * this.m_sin + f * this.m_cos);
        this.m_destPoly.push(
            new d.IntPoint2(
                d.ClipperOffset.Round(
                    this.m_srcPoly[a].X + this.m_normals[a].X * this.m_delta
                ),
                d.ClipperOffset.Round(
                    this.m_srcPoly[a].Y + this.m_normals[a].Y * this.m_delta
                )
            )
        );
    };
    d.Error = function (a) {
        try {
            throw Error(a);
        } catch (b) {
            alert(b.message);
        }
    };
    d.JS = {};
    d.JS.AreaOfPolygon = function (a, b) {
        b || (b = 1);
        return d.Clipper.Area(a) / (b * b);
    };
    d.JS.AreaOfPolygons = function (a, b) {
        b || (b = 1);
        for (var c = 0, e = 0; e < a.length; e++) c += d.Clipper.Area(a[e]);
        return c / (b * b);
    };
    d.JS.BoundsOfPath = function (a, b) {
        return d.JS.BoundsOfPaths([a], b);
    };
    d.JS.BoundsOfPaths = function (a, b) {
        b || (b = 1);
        var c = d.Clipper.GetBounds(a);
        c.left /= b;
        c.bottom /= b;
        c.right /= b;
        c.top /= b;
        return c;
    };
    d.JS.Clean = function (a, b) {
        if (!(a instanceof Array)) return [];
        var c = a[0] instanceof Array;
        a = d.JS.Clone(a);
        if ("number" !== typeof b || null === b)
            return d.Error("Delta is not a number in Clean()."), a;
        if (0 === a.length || (1 === a.length && 0 === a[0].length) || 0 > b)
            return a;
        c || (a = [a]);
        for (var e = a.length, f, g, h, k, l, n, r, p = [], t = 0; t < e; t++)
            if (((g = a[t]), (f = g.length), 0 !== f))
                if (3 > f) (h = g), p.push(h);
                else {
                    h = g;
                    k = b * b;
                    l = g[0];
                    for (r = n = 1; r < f; r++)
                        (g[r].X - l.X) * (g[r].X - l.X) +
                            (g[r].Y - l.Y) * (g[r].Y - l.Y) <=
                            k || ((h[n] = g[r]), (l = g[r]), n++);
                    l = g[n - 1];
                    (g[0].X - l.X) * (g[0].X - l.X) +
                        (g[0].Y - l.Y) * (g[0].Y - l.Y) <=
                        k && n--;
                    n < f && h.splice(n, f - n);
                    h.length && p.push(h);
                }
        !c && p.length
            ? (p = p[0])
            : c || 0 !== p.length
            ? c && 0 === p.length && (p = [[]])
            : (p = []);
        return p;
    };
    d.JS.Clone = function (a) {
        if (!(a instanceof Array) || 0 === a.length) return [];
        if (1 === a.length && 0 === a[0].length) return [[]];
        var b = a[0] instanceof Array;
        b || (a = [a]);
        var c = a.length,
            d,
            f,
            g = Array(c);
        for (d = 0; d < c; d++) {
            var h = a[d].length;
            var k = Array(h);
            for (f = 0; f < h; f++) k[f] = { X: a[d][f].X, Y: a[d][f].Y };
            g[d] = k;
        }
        b || (g = g[0]);
        return g;
    };
    d.JS.Lighten = function (a, b) {
        if (!(a instanceof Array)) return [];
        if ("number" !== typeof b || null === b)
            return (
                d.Error("Tolerance is not a number in Lighten()."),
                d.JS.Clone(a)
            );
        if (0 === a.length || (1 === a.length && 0 === a[0].length) || 0 > b)
            return d.JS.Clone(a);
        var c = a[0] instanceof Array;
        c || (a = [a]);
        var e,
            f,
            g,
            h = a.length,
            k = b * b,
            l = [];
        for (e = 0; e < h; e++) {
            var n = a[e];
            var r = n.length;
            if (0 !== r) {
                for (g = 0; 1e6 > g; g++) {
                    var p = [];
                    r = n.length;
                    if (n[r - 1].X !== n[0].X || n[r - 1].Y !== n[0].Y) {
                        var t = 1;
                        n.push({ X: n[0].X, Y: n[0].Y });
                        r = n.length;
                    } else t = 0;
                    var u = [];
                    for (f = 0; f < r - 2; f++) {
                        var q = n[f];
                        var v = n[f + 1];
                        var w = n[f + 2];
                        var x = q.X;
                        var y = q.Y;
                        q = w.X - x;
                        var A = w.Y - y;
                        if (0 !== q || 0 !== A) {
                            var z =
                                ((v.X - x) * q + (v.Y - y) * A) /
                                (q * q + A * A);
                            1 < z
                                ? ((x = w.X), (y = w.Y))
                                : 0 < z && ((x += q * z), (y += A * z));
                        }
                        q = v.X - x;
                        A = v.Y - y;
                        w = q * q + A * A;
                        w <= k && ((u[f + 1] = 1), f++);
                    }
                    p.push({ X: n[0].X, Y: n[0].Y });
                    for (f = 1; f < r - 1; f++)
                        u[f] || p.push({ X: n[f].X, Y: n[f].Y });
                    p.push({ X: n[r - 1].X, Y: n[r - 1].Y });
                    t && n.pop();
                    if (u.length) n = p;
                    else break;
                }
                r = p.length;
                p[r - 1].X === p[0].X && p[r - 1].Y === p[0].Y && p.pop();
                2 < p.length && l.push(p);
            }
        }
        c || (l = l[0]);
        "undefined" === typeof l && (l = []);
        return l;
    };
    d.JS.PerimeterOfPath = function (a, b, c) {
        if ("undefined" === typeof a) return 0;
        var d = Math.sqrt,
            f = 0,
            g = a.length;
        if (2 > g) return 0;
        b && ((a[g] = a[0]), g++);
        for (; --g; ) {
            var h = a[g];
            var k = h.X;
            h = h.Y;
            var l = a[g - 1];
            var n = l.X;
            l = l.Y;
            f += d((k - n) * (k - n) + (h - l) * (h - l));
        }
        b && a.pop();
        return f / c;
    };
    d.JS.PerimeterOfPaths = function (a, b, c) {
        c || (c = 1);
        for (var e = 0, f = 0; f < a.length; f++)
            e += d.JS.PerimeterOfPath(a[f], b, c);
        return e;
    };
    d.JS.ScaleDownPath = function (a, b) {
        var c;
        b || (b = 1);
        for (c = a.length; c--; ) {
            var d = a[c];
            d.X /= b;
            d.Y /= b;
        }
    };
    d.JS.ScaleDownPaths = function (a, b) {
        var c, d;
        b || (b = 1);
        for (c = a.length; c--; )
            for (d = a[c].length; d--; ) {
                var f = a[c][d];
                f.X /= b;
                f.Y /= b;
            }
    };
    d.JS.ScaleUpPath = function (a, b) {
        var c,
            d = Math.round;
        b || (b = 1);
        for (c = a.length; c--; ) {
            var f = a[c];
            f.X = d(f.X * b);
            f.Y = d(f.Y * b);
        }
    };
    d.JS.ScaleUpPaths = function (a, b) {
        var c,
            d,
            f = Math.round;
        b || (b = 1);
        for (c = a.length; c--; )
            for (d = a[c].length; d--; ) {
                var g = a[c][d];
                g.X = f(g.X * b);
                g.Y = f(g.Y * b);
            }
    };
    d.ExPolygons = function () {
        return [];
    };
    d.ExPolygon = function () {
        this.holes = this.outer = null;
    };
    d.JS.AddOuterPolyNodeToExPolygons = function (a, b) {
        var c = new d.ExPolygon();
        c.outer = a.Contour();
        var e = a.Childs(),
            f = e.length;
        c.holes = Array(f);
        var g, h;
        for (g = 0; g < f; g++) {
            var k = e[g];
            c.holes[g] = k.Contour();
            var l = 0;
            var n = k.Childs();
            for (h = n.length; l < h; l++)
                (k = n[l]), d.JS.AddOuterPolyNodeToExPolygons(k, b);
        }
        b.push(c);
    };
    d.JS.ExPolygonsToPaths = function (a) {
        var b,
            c,
            e = new d.Paths();
        var f = 0;
        for (b = a.length; f < b; f++) {
            e.push(a[f].outer);
            var g = 0;
            for (c = a[f].holes.length; g < c; g++) e.push(a[f].holes[g]);
        }
        return e;
    };
    d.JS.PolyTreeToExPolygons = function (a) {
        var b = new d.ExPolygons(),
            c;
        var e = 0;
        var f = a.Childs();
        for (c = f.length; e < c; e++)
            (a = f[e]), d.JS.AddOuterPolyNodeToExPolygons(a, b);
        return b;
    };
})();
