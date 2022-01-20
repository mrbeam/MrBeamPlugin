class QuickShapeHelper {
    static getCircle(r) {
        if (isFinite(r) && r > 0) {
            return this.getRect(r, r, 100);
        } else {
            return "";
        }
    }

    static getRect(w, h, r) {
        if (!isFinite(w) || !isFinite(h) || !isFinite(r)) {
            return "";
        }

        if (r <= 0) {
            var d = "M0,0l" + w + ",0 0," + h + " " + -w + ",0 z";
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
                rx = ((r / 50) * Math.min(w, h)) / 2;
                ry = rx;
            } else {
                var rBig = Math.max(w, h) / 2;
                var rSmall = Math.min(w, h) / 2;
                if (w > h) {
                    rx = rSmall + ((r - 50) / 50) * (rBig - rSmall);
                    ry = rSmall;
                } else {
                    ry = rSmall + ((r - 50) / 50) * (rBig - rSmall);
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

            var d =
                "M" +
                a.join(",") +
                "L" +
                b.join(",") +
                "C" +
                c1.join(",") +
                " " +
                c2.join(",") +
                " " +
                c.join(",") +
                "L" +
                d.join(",") +
                "C" +
                e1.join(",") +
                " " +
                e2.join(",") +
                " " +
                e.join(",") +
                "L" +
                f.join(",") +
                "C" +
                g1.join(",") +
                " " +
                g2.join(",") +
                " " +
                g.join(",") +
                "L" +
                h.join(",") +
                "C" +
                a1.join(",") +
                " " +
                a2.join(",") +
                " " +
                a.join(",") +
                "z";
            return d;
        }
    }

    static getStar(r, c, sh) {
        if (!isFinite(r) || !isFinite(c) || !isFinite(sh) || r < 0 || c < 3) {
            return "";
        }
        var points = [];
        var step = (2 * Math.PI) / c;
        var ri = (1 - sh) * r;
        for (var i = 0; i < c; i++) {
            var angle_outer = i * step - Math.PI / 2; // -Math.PI/2 rotates 90deg
            var angle_inner = angle_outer + step / 2;
            var pox = Math.cos(angle_outer) * r;
            var poy = Math.sin(angle_outer) * r;
            var pix = Math.cos(angle_inner) * ri;
            var piy = Math.sin(angle_inner) * ri;
            points.push(pox, poy, pix, piy);
        }
        var d =
            "M" + points[0] + "," + points[1] + "L" + points.join(" ") + "z";
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
        var dx = (w / 5) * 0.89686;
        var dy = (h / 5) * 1.0444;
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

        var out =
            "M" +
            a.join(",") +
            "C" +
            b1.join(",") +
            " " +
            b2.join(",") +
            " " +
            b.join(",") +
            "C" +
            c1.join(",") +
            " " +
            c2.join(",") +
            " " +
            c.join(",") +
            "C" +
            d1.join(",") +
            " " +
            d2.join(",") +
            " " +
            d.join(",") +
            "C" +
            e1.join(",") +
            " " +
            e2.join(",") +
            " " +
            e.join(",") +
            "C" +
            f1.join(",") +
            " " +
            f2.join(",") +
            " " +
            f.join(",") +
            "C" +
            a1.join(",") +
            " " +
            a2.join(",") +
            " " +
            a.join(",") +
            "z";

        /** Debug bezier handles
            out +=
            'M' + a2.join(',') +
            'L' + a.join(',') +
            'L' + b1.join(',') +

            'M' + b2.join(',') +
            'L' + b.join(',') +
            'L' + c1.join(',') +

            'M' + c2.join(',') +
            'L' + c.join(',') +
            'L' + d1.join(',') +

            'M' + d2.join(',') +
            'L' + d.join(',') +
            'L' + e1.join(',') +

            'M' + e2.join(',') +
            'L' + e.join(',') +
            'L' + f1.join(',') +

            'M' + f2.join(',') +
            'L' + f.join(',') +
            'L' + a1.join(',');
            */
        return out;
    }

    static getTextPath(
        cx,
        cy,
        circlePercent,
        textLength,
        counterclockwise = false
    ) {
        if (circlePercent === 0) {
            return `M${cx},${cy}m${-textLength},0h${textLength * 2}`; // half of the line would be enough, but overlength is uncritical on a straight line.
        } else {
            const f = circlePercent / 100.0; // factor, how much of the circle outline is text
            const r = textLength / f / (Math.PI * 2); // resulting radius

            // Text will be aligned in the center of the path (50%), tc = text center
            //
            //   ^    <text center>
            // cy+    ______b______
            //   |   /             \
            //   |  |               |
            //   |  |       |       |
            //   |  |       |r      |
            //   |   \______|______/
            //   |          a
            //   |
            //   0----------+---------------->
            //             cx

            const a = counterclockwise ? [cx, cy - 2 * r] : [cx, cy + 2 * r];
            const b = counterclockwise ? [0, 2 * r] : [0, -2 * r];
            const b2 = [0, -b[1]];

            const sweep = counterclockwise ? 0 : 1;

            // this is for easier debugging
            // const d = `M${a.join(',')}a${r.toFixed(1)} ${r.toFixed(1)} 0 1 ${sweepFlag} ${b.join(',')} a${r.toFixed(1)} ${r.toFixed(1)} 0 1 ${sweepFlag} ${b2[0]+5}, ${b2[1].toFixed(1)}l2,2`;

            // this is for production
            const d = `M${a.join(",")}a${r} ${r} 0 1 ${sweep} ${b.join(
                ","
            )} a${r} ${r} 0 1 ${sweep} ${b2.join(",")}`;

            return d;
        }
    }
}
