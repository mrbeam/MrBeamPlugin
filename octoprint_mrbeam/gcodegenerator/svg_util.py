from . import simplepath
import re

# a dictionary of all of the xmlns prefixes in a standard inkscape doc
NSS = {
    "sodipodi": "http://sodipodi.sourceforge.net/DTD/sodipodi-0.dtd",
    "cc": "http://creativecommons.org/ns#",
    "ccOLD": "http://web.resource.org/cc/",
    "svg": "http://www.w3.org/2000/svg",
    "dc": "http://purl.org/dc/elements/1.1/",
    "rdf": "http://www.w3.org/1999/02/22-rdf-syntax-ns#",
    "inkscape": "http://www.inkscape.org/namespaces/inkscape",
    "xlink": "http://www.w3.org/1999/xlink",
    "xml": "http://www.w3.org/XML/1998/namespace",
    "mb": "http://www.mr-beam.org/mbns",
}


def _add_ns(tag, ns=None):
    val = tag
    if ns != None and len(ns) > 0 and ns in NSS and len(tag) > 0 and tag[0] != "{":
        val = "{%s}%s" % (NSS[ns], tag)
    return val


# eats an lxml.etree node and returns a path
def get_path_d(node):
    if node.tag == _add_ns("rect", "svg") or node.tag == "rect":
        # Manually transform
        #
        #    <rect x="X" y="Y" width="W" height="H"/>
        # into
        #    <path d="MX,Y lW,0 l0,H l-W,0 z"/>
        #
        # I.e., explicitly draw three sides of the rectangle and the
        # fourth side implicitly

        # Create a path with the outline of the rectangle
        x = float(node.get("x", "0"))
        y = float(node.get("y", "0"))
        if (not x) or (not y):
            pass
        w = float(node.get("width", "0"))
        h = float(node.get("height", "0"))
        a = []
        a.append(["M ", [x, y]])
        a.append([" l ", [w, 0]])
        a.append([" l ", [0, h]])
        a.append([" l ", [-w, 0]])
        a.append([" Z", []])
        d = simplepath.formatPath(a)
        return d

    # line
    elif node.tag == _add_ns("line", "svg") or node.tag == "line":

        # Convert
        #
        #   <line x1="X1" y1="Y1" x2="X2" y2="Y2/>
        # to
        #   <path d="MX1,Y1 LX2,Y2"/>

        x1 = float(node.get("x1"))
        y1 = float(node.get("y1"))
        x2 = float(node.get("x2"))
        y2 = float(node.get("y2"))
        if (not x1) or (not y1) or (not x2) or (not y2):
            pass
        a = []
        a.append(["M ", [x1, y1]])
        a.append([" L ", [x2, y2]])
        d = simplepath.formatPath(a)
        return d

        self._handle_node(i, layer)

    # polygon
    elif (
        node.tag == _add_ns("polygon", "svg")
        or node.tag == "polygon"
        or node.tag == _add_ns("polyline", "svg")
        or node.tag == "polyline"
    ):
        # Convert
        #
        #  <polygon points="x1,y1 x2,y2 x3,y3 [...]"/>
        #  <polyline points="x1,y1 x2,y2 x3,y3 [...]"/>
        # to
        #   <path d="Mx1,y1 Lx2,y2 Lx3,y3 [...] Z"/>
        #
        # Note: we ignore polygons with no points

        pl = node.get("points", "").strip()
        if pl == "":
            pass

        pa = pl.split()
        d = "".join(
            ["M " + pa[j] if j == 0 else " L " + pa[j] for j in range(0, len(pa))]
        )
        d += " Z"
        return d

    # circle / ellipse
    elif (
        node.tag == _add_ns("ellipse", "svg")
        or node.tag == "ellipse"
        or node.tag == _add_ns("circle", "svg")
        or node.tag == "circle"
    ):

        # Convert circles and ellipses to a path with two 180 degree arcs.
        # In general (an ellipse), we convert
        #
        #   <ellipse rx="RX" ry="RY" cx="X" cy="Y"/>
        # to
        #   <path d="MX1,CY A RX,RY 0 1 0 X2,CY A RX,RY 0 1 0 X1,CY"/>
        #
        # where
        #   X1 = CX - RX
        #   X2 = CX + RX
        #
        # Note: ellipses or circles with a radius attribute of value 0 are ignored

        if node.tag == _add_ns("ellipse", "svg") or node.tag == "ellipse":
            rx = float(node.get("rx", "0"))
            ry = float(node.get("ry", "0"))
        else:
            rx = float(node.get("r", "0"))
            ry = rx
        if rx == 0 or ry == 0:
            pass

        cx = float(node.get("cx", "0"))
        cy = float(node.get("cy", "0"))
        x1 = cx - rx
        x2 = cx + rx
        d = (
            "M %f,%f " % (x1, cy)
            + "A %f,%f " % (rx, ry)
            + "0 1 0 %f,%f " % (x2, cy)
            + "A %f,%f " % (rx, ry)
            + "0 1 0 %f,%f" % (x1, cy)
        )
        return d


UUCONV = {
    "in": 90.0,
    "pt": 1.25,
    "px": 1,
    "mm": 3.5433070866,
    "cm": 35.433070866,
    "m": 3543.3070866,
    "km": 3543307.0866,
    "pc": 15.0,
    "yd": 3240,
    "ft": 1080,
}


def unittouu(string):
    """Returns userunits given a string representation of units in another
    system."""
    unit = re.compile("(%s)$" % "|".join(UUCONV.keys()))
    param = re.compile(r"(([-+]?[0-9]+(\.[0-9]*)?|[-+]?\.[0-9]+)([eE][-+]?[0-9]+)?)")

    p = param.match(string)
    u = unit.search(string)
    if p:
        retval = float(p.string[p.start() : p.end()])
    else:
        retval = 0.0
    if u:
        try:
            return retval * UUCONV[u.string[u.start() : u.end()]]
        except KeyError:
            pass
    return retval


def uutounit(val, unit):
    return val / UUCONV[unit]
