class QuickShapeHelper {
	
	static getCircle(r) {
		if (isFinite(r) && r > 0) {
			return this.getRect(r, r, 100);
		} else {
			return "";
		}
	}
	
	static getRect(w, h, r) {
		if (!isFinite(w) ||
				!isFinite(h) ||
				!isFinite(r)
				) {
			return "";
		}

		if (r <= 0) {
			var d = 'M0,0l' + w + ',0 0,' + h + ' ' + (-w) + ',0 z';
			return d;
		} else {
			//     a___________b
			//    /             \
			//   h               c
			//   |               |
			//   g               d
			//    \             /
			//     f___________e

			var rx;
			var ry;
			if (r <= 50) {
				rx = r / 50 * Math.min(w, h) / 2;
				ry = rx;
			} else {
				var rBig = Math.max(w, h) / 2;
				var rSmall = Math.min(w, h) / 2;
				if (w > h) {
					rx = rSmall + (r - 50) / 50 * (rBig - rSmall);
					ry = rSmall;
				} else {
					ry = rSmall + (r - 50) / 50 * (rBig - rSmall);
					rx = rSmall;
				}
			}

			var q = 0.552284749831; // circle approximation with cubic beziers: (4/3)*tan(pi/8) = 0.552284749831

			var a = [rx, 0];
			var b = [w - rx, 0];
			var c = [w, ry];
			var c1 = [b[0] + q * rx, b[1]];
			var c2 = [c[0], c[1] - q * ry];
			var d = [w, h - ry];
			var e = [w - rx, h];
			var e1 = [d[0], d[1] + q * ry];
			var e2 = [e[0] + q * rx, e[1]];
			var f = [rx, h];
			var g = [0, h - ry];
			var g1 = [f[0] - q * rx, f[1]];
			var g2 = [g[0], g[1] + q * ry];
			var h = [0, ry];
			var a1 = [h[0], h[1] - q * ry];
			var a2 = [a[0] - q * rx, a[1]];

			var d = 'M' + a.join(',')
					+ 'L' + b.join(',')
					+ 'C' + c1.join(',')
					+ ' ' + c2.join(',')
					+ ' ' + c.join(',')
					+ 'L' + d.join(',')
					+ 'C' + e1.join(',')
					+ ' ' + e2.join(',')
					+ ' ' + e.join(',')
					+ 'L' + f.join(',')
					+ 'C' + g1.join(',')
					+ ' ' + g2.join(',')
					+ ' ' + g.join(',')
					+ 'L' + h.join(',')
					+ 'C' + a1.join(',')
					+ ' ' + a2.join(',')
					+ ' ' + a.join(',')
					+ 'z';
			return d;

		}
	}
	
	static getStar(r, c, sh) {
		if (!isFinite(r) ||
				!isFinite(c) ||
				!isFinite(sh) ||
				r < 0 ||
				c < 3
				) {
			return "";
		}
		var points = [];
		var step = 2 * Math.PI / c;
		var ri = (1 - sh) * r;
		for (var i = 0; i < c; i++) {
			var angle_outer = i * step;
			var angle_inner = angle_outer + step / 2;
			var pox = Math.cos(angle_outer) * r;
			var poy = Math.sin(angle_outer) * r;
			var pix = Math.cos(angle_inner) * ri;
			var piy = Math.sin(angle_inner) * ri;
			points.push(pox, poy, pix, piy);
		}
		var d = 'M' + points[0] + ',' + points[1] + 'L' + points.join(' ') + 'z';
		return d;
	}

	static getHeart(w, h, lr) {
		if (!isFinite(w) || !isFinite(h) || !isFinite(lr)) {
			return "";
		}
		//         __   __
		//        e  \ /  c
		//       (    d    )
		//        f       b
		//         \     /
		//          \   /
		//            a
		var dx = w / 5 * 0.78;
		var dy = h / 5 * 0.96;
		var q = 0.552284749831; // circle approximation with cubic beziers: (4/3)*tan(pi/8) = 0.552284749831
		var rx = dx;
		var ry = dy;

		var bb = 1.5; // fatter ears
		var earx = 0.4; // longer ears
		var r_comp = Math.max(0, lr) * 0.7;
		var l_comp = Math.min(0, lr) * 0.7;

		var a = [3 * dx, 5 * dy];
		var b = [(5 + r_comp) * dx, 3 * dy];
		var b1 = [a[0] + dx + lr * dx, a[1] - dy];
		var b2 = [b[0] - dx / 2, b[1] + dy / 2];
		var c = [(5 + earx) * dx, (1 - earx) * dy];
		var c1 = [b[0] + q * rx, b[1] - q * ry];
		var c2 = [c[0] + q * rx * bb, c[1] + q * ry * bb];
		var d = [3 * dx, 1 * dy];
		var d1 = [c[0] - q * rx * bb, c[1] - q * ry * bb];
		var d2 = [d[0] + q * rx, d[1] - q * ry];
		var e = [(1 - earx) * dx, (1 - earx) * dy];
		var e1 = [d[0] - q * rx, d[1] - q * ry];
		var e2 = [e[0] + q * rx * bb, e[1] - q * ry * bb];
		var f = [(1 + l_comp) * dx, 3 * dy];
		var f1 = [e[0] - q * rx * bb, e[1] + q * ry * bb];
		var f2 = [f[0] - q * rx, f[1] - q * ry];
		var a1 = [f[0] + dx / 2, f[1] + dy / 2];
		var a2 = [a[0] - dx + lr * dx, a[1] - dy];

		var d = 'M' + a.join(',')
				+ 'C' + b1.join(',')
				+ ' ' + b2.join(',')
				+ ' ' + b.join(',')
				+ 'C' + c1.join(',')
				+ ' ' + c2.join(',')
				+ ' ' + c.join(',')
				+ 'C' + d1.join(',')
				+ ' ' + d2.join(',')
				+ ' ' + d.join(',')
				+ 'C' + e1.join(',')
				+ ' ' + e2.join(',')
				+ ' ' + e.join(',')
				+ 'C' + f1.join(',')
				+ ' ' + f2.join(',')
				+ ' ' + f.join(',')
				+ 'C' + a1.join(',')
				+ ' ' + a2.join(',')
				+ ' ' + a.join(',')

//				// Debug bezier handles
//				+'M' + a.join(',')
//				+ 'L' + b1.join(',')
//				+ 'M' + a.join(',')
//				+ 'L' + a2.join(',')
//
//				+ 'M' + c.join(',')
//				+ 'L' + d1.join(',')
//				+ 'M' + d.join(',')
//				+ 'L' + d2.join(',')
//
//				+ 'M' + e1.join(',')
//				+ 'L' + e.join(',')
//				+ 'L' + e2.join(',')
//
//				+ 'M' + f1.join(',')
//				+ 'L' + f.join(',')
//				+ 'L' + f2.join(',')
				+'z';
		return d;
	}
};
