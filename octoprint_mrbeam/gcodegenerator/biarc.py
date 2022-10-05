import math
from . import bezmisc
from .point import Point

################################################################################
###
###		Biarc function
###
###		Calculates biarc approximation of cubic super path segment
###		splits segment if needed or approximates it with straight line
###
################################################################################
BIARC_SPLIT_DEPTH = 4
math.pi2 = math.pi * 2
straight_tolerance = 0.0001
straight_distance_tolerance = 0.0001


def biarc(sp1, sp2, z1, z2, depth=0):
    def biarc_split(sp1, sp2, z1, z2, depth):
        if depth < BIARC_SPLIT_DEPTH:
            sp1, sp2, sp3 = csp_split(sp1, sp2)
            l1, l2 = cspseglength(sp1, sp2), cspseglength(sp2, sp3)
            if l1 + l2 == 0:
                zm = z1
            else:
                zm = z1 + (z2 - z1) * l1 / (l1 + l2)
            return biarc(sp1, sp2, z1, zm, depth + 1) + biarc(
                sp2, sp3, zm, z2, depth + 1
            )
        else:
            return [[sp1[1], "line", 0, 0, sp2[1], [z1, z2]]]

    P0, P4 = Point(sp1[1]), Point(sp2[1])
    TS, TE, v = (Point(sp1[2]) - P0), -(Point(sp2[0]) - P4), P0 - P4
    tsa, tea, va = TS.angle(), TE.angle(), v.angle()
    if (
        TE.mag() < straight_distance_tolerance
        and TS.mag() < straight_distance_tolerance
    ):
        # Both tangents are zerro - line straight
        return [[sp1[1], "line", 0, 0, sp2[1], [z1, z2]]]
    if TE.mag() < straight_distance_tolerance:
        TE = -(TS + v).unit()
        r = TS.mag() / v.mag() * 2
    elif TS.mag() < straight_distance_tolerance:
        TS = -(TE + v).unit()
        r = 1 / (TE.mag() / v.mag() * 2)
    else:
        r = TS.mag() / TE.mag()
    TS, TE = TS.unit(), TE.unit()
    tang_are_parallel = (tsa - tea) % math.pi < straight_tolerance or math.pi - (
        tsa - tea
    ) % math.pi < straight_tolerance
    if tang_are_parallel and (
        (
            v.mag() < straight_distance_tolerance
            or TE.mag() < straight_distance_tolerance
            or TS.mag() < straight_distance_tolerance
        )
        or 1 - abs(TS * v / (TS.mag() * v.mag())) < straight_tolerance
    ):
        # Both tangents are parallel and start and end are the same - line straight
        # or one of tangents still smaller then tollerance

        # Both tangents and v are parallel - line straight
        return [[sp1[1], "line", 0, 0, sp2[1], [z1, z2]]]

    c, b, a = v * v, 2 * v * (r * TS + TE), 2 * r * (TS * TE - 1)
    if v.mag() == 0:
        return biarc_split(sp1, sp2, z1, z2, depth)
    asmall, bsmall, csmall = abs(a) < 10**-10, abs(b) < 10**-10, abs(c) < 10**-10
    if asmall and b != 0:
        beta = -c / b
    elif csmall and a != 0:
        beta = -b / a
    elif not asmall:
        discr = b * b - 4 * a * c
        if discr < 0:
            raise ValueError(a, b, c, discr)
        disq = discr**0.5
        beta1 = (-b - disq) / 2 / a
        beta2 = (-b + disq) / 2 / a
        if beta1 * beta2 > 0:
            raise ValueError(a, b, c, disq, beta1, beta2)
        beta = max(beta1, beta2)
    elif asmall and bsmall:
        return biarc_split(sp1, sp2, z1, z2, depth)
    alpha = beta * r
    ab = alpha + beta
    P1 = P0 + alpha * TS
    P3 = P4 - beta * TE
    P2 = (beta / ab) * P1 + (alpha / ab) * P3

    def calculate_arc_params(P0, P1, P2):
        D = (P0 + P2) / 2
        if (D - P1).mag() == 0:
            return None, None
        R = D - ((D - P0).mag() ** 2 / (D - P1).mag()) * (P1 - D).unit()
        p0a, p1a, p2a = (
            (P0 - R).angle() % (2 * math.pi),
            (P1 - R).angle() % (2 * math.pi),
            (P2 - R).angle() % (2 * math.pi),
        )
        alpha = (p2a - p0a) % (2 * math.pi)
        if (p0a < p2a and (p1a < p0a or p2a < p1a)) or (p2a < p1a < p0a):
            alpha = -2 * math.pi + alpha
        if abs(R.x) > 1000000 or abs(R.y) > 1000000 or (R - P0).mag < 0.1:
            return None, None
        else:
            return R, alpha

    R1, a1 = calculate_arc_params(P0, P1, P2)
    R2, a2 = calculate_arc_params(P2, P3, P4)
    if (
        R1 == None
        or R2 == None
        or (R1 - P0).mag() < straight_tolerance
        or (R2 - P2).mag() < straight_tolerance
    ):
        return [[sp1[1], "line", 0, 0, sp2[1], [z1, z2]]]

    d = csp_to_arc_distance(sp1, sp2, [P0, P2, R1, a1], [P2, P4, R2, a2])
    if d > 1 and depth < BIARC_SPLIT_DEPTH:
        return biarc_split(sp1, sp2, z1, z2, depth)
    else:
        if R2.mag() * a2 == 0:
            zm = z2
        else:
            zm = z1 + (z2 - z1) * (abs(R1.mag() * a1)) / (
                abs(R2.mag() * a2) + abs(R1.mag() * a1)
            )
        return [
            [sp1[1], "arc", [R1.x, R1.y], a1, [P2.x, P2.y], [z1, zm]],
            [[P2.x, P2.y], "arc", [R2.x, R2.y], a2, [P4.x, P4.y], [zm, z2]],
        ]


def biarc_curve_segment_length(seg):
    if seg[1] == "arc":
        return (
            math.sqrt((seg[0][0] - seg[2][0]) ** 2 + (seg[0][1] - seg[2][1]) ** 2)
            * seg[3]
        )
    elif seg[1] == "line":
        return math.sqrt((seg[0][0] - seg[4][0]) ** 2 + (seg[0][1] - seg[4][1]) ** 2)
    else:
        return 0


def biarc_curve_clip_at_l(curve, l, clip_type="strict"):
    # get first subcurve and ceck it's length
    subcurve, subcurve_l, moved = [], 0, False
    for seg in curve:
        if seg[1] == "move" and moved or seg[1] == "end":
            break
        if seg[1] == "move":
            moved = True
        subcurve_l += biarc_curve_segment_length(seg)
        if seg[1] == "arc" or seg[1] == "line":
            subcurve += [seg]

    if subcurve_l < l and clip_type == "strict":
        return []
    lc = 0
    if (subcurve[-1][4][0] - subcurve[0][0][0]) ** 2 + (
        subcurve[-1][4][1] - subcurve[0][0][1]
    ) ** 2 < 10**-7:
        subcurve_closed = True
    i = 0
    reverse = False
    while lc < l:
        seg = subcurve[i]
        if reverse:
            if seg[1] == "line":
                seg = [
                    seg[4],
                    "line",
                    0,
                    0,
                    seg[0],
                    seg[5],
                ]  # Hmmm... Do we have to swap seg[5][0] and seg[5][1] (zstart and zend) or not?
            elif seg[1] == "arc":
                seg = [
                    seg[4],
                    "arc",
                    seg[2],
                    -seg[3],
                    seg[0],
                    seg[5],
                ]  # Hmmm... Do we have to swap seg[5][0] and seg[5][1] (zstart and zend) or not?
        ls = biarc_curve_segment_length(seg)
        if ls != 0:
            if l - lc > ls:
                res += [seg]
            else:
                if seg[1] == "arc":
                    r = math.sqrt(
                        (seg[0][0] - seg[2][0]) ** 2 + (seg[0][1] - seg[2][1]) ** 2
                    )
                    x, y = seg[0][0] - seg[2][0], seg[0][1] - seg[2][1]
                    a = seg[3] / ls * (l - lc)
                    x, y = (
                        x * math.cos(a) - y * math.sin(a),
                        x * math.sin(a) + y * math.cos(a),
                    )
                    x, y = x + seg[2][0], y + seg[2][1]
                    res += [
                        [
                            seg[0],
                            "arc",
                            seg[2],
                            a,
                            [x, y],
                            [seg[5][0], seg[5][1] / ls * (l - lc)],
                        ]
                    ]
                if seg[1] == "line":
                    res += [
                        [
                            seg[0],
                            "line",
                            0,
                            0,
                            [
                                (seg[4][0] - seg[0][0]) / ls * (l - lc),
                                (seg[4][1] - seg[0][1]) / ls * (l - lc),
                            ],
                            [seg[5][0], seg[5][1] / ls * (l - lc)],
                        ]
                    ]
        i += 1
        if i >= len(subcurve) and not subcurve_closed:
            reverse = not reverse
        i = i % len(subcurve)
    return res


###	Distance calculattion from point to arc
def point_to_arc_distance(p, arc):
    P0, P2, c, a = arc
    dist = None
    p = Point(p)
    r = (P0 - c).mag()
    if r > 0:
        i = c + (p - c).unit() * r
        alpha = (i - c).angle() - (P0 - c).angle()
        if a * alpha < 0:
            if alpha > 0:
                alpha = alpha - math.pi2
            else:
                alpha = math.pi2 + alpha
        if between(alpha, 0, a) or min(abs(alpha), abs(alpha - a)) < straight_tolerance:
            return (p - i).mag(), [i.x, i.y]
        else:
            d1, d2 = (p - P0).mag(), (p - P2).mag()
            if d1 < d2:
                return (d1, [P0.x, P0.y])
            else:
                return (d2, [P2.x, P2.y])


def csp_to_arc_distance(
    sp1, sp2, arc1, arc2, tolerance=0.01
):  # arc = [start,end,center,alpha]
    n, i = 10, 0
    d, d1, dl = (0, (0, 0)), (0, (0, 0)), 0
    while i < 1 or (abs(d1[0] - dl[0]) > tolerance and i < 4):
        i += 1
        dl = d1 * 1
        for j in range(n + 1):
            t = float(j) / n
            p = csp_at_t(sp1, sp2, t)
            d = min(point_to_arc_distance(p, arc1), point_to_arc_distance(p, arc2))
            d1 = max(d1, d)
        n = n * 2
    return d1[0]


def csp_at_t(sp1, sp2, t):
    ax, bx, cx, dx = sp1[1][0], sp1[2][0], sp2[0][0], sp2[1][0]
    ay, by, cy, dy = sp1[1][1], sp1[2][1], sp2[0][1], sp2[1][1]

    x1, y1 = ax + (bx - ax) * t, ay + (by - ay) * t
    x2, y2 = bx + (cx - bx) * t, by + (cy - by) * t
    x3, y3 = cx + (dx - cx) * t, cy + (dy - cy) * t

    x4, y4 = x1 + (x2 - x1) * t, y1 + (y2 - y1) * t
    x5, y5 = x2 + (x3 - x2) * t, y2 + (y3 - y2) * t

    x, y = x4 + (x5 - x4) * t, y4 + (y5 - y4) * t
    return [x, y]


def csp_split(sp1, sp2, t=0.5):
    [x1, y1], [x2, y2], [x3, y3], [x4, y4] = sp1[1], sp1[2], sp2[0], sp2[1]
    x12 = x1 + (x2 - x1) * t
    y12 = y1 + (y2 - y1) * t
    x23 = x2 + (x3 - x2) * t
    y23 = y2 + (y3 - y2) * t
    x34 = x3 + (x4 - x3) * t
    y34 = y3 + (y4 - y3) * t
    x1223 = x12 + (x23 - x12) * t
    y1223 = y12 + (y23 - y12) * t
    x2334 = x23 + (x34 - x23) * t
    y2334 = y23 + (y34 - y23) * t
    x = x1223 + (x2334 - x1223) * t
    y = y1223 + (y2334 - y1223) * t
    return (
        [sp1[0], sp1[1], [x12, y12]],
        [[x1223, y1223], [x, y], [x2334, y2334]],
        [[x34, y34], sp2[1], sp2[2]],
    )


def cspseglength(sp1, sp2, tolerance=0.001):
    bez = (sp1[1][:], sp1[2][:], sp2[0][:], sp2[1][:])
    return bezmisc.bezierlength(bez, tolerance)


def between(c, x, y):
    return (x - straight_tolerance <= c <= y + straight_tolerance) or (
        y - straight_tolerance <= c <= x + straight_tolerance
    )
