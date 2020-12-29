import pytest
import logging


def compare_dimensions(bbox, exp):
    #    exp = {
    #        "y": 27.573705673217773,
    #        "x": 5.796566963195801,
    #        "w": 149.99998474121094,
    #        "h": 149.99998474121094,
    #    }

    mx = abs(bbox[u"x"] - exp["x"]) < 0.0001
    my = abs(bbox[u"y"] - exp["y"]) < 0.0001
    mw = abs(bbox[u"w"] - exp["w"]) < 0.0001
    mh = abs(bbox[u"h"] - exp["h"]) < 0.0001
    if mx and my and mw and mh:
        return (True, "")
    else:
        msg = "Dimensions do not match:"
        if not mx:
            msg += " X-Pos: {} != {}".format(bbox[u"x"], exp["x"])
        if not my:
            msg += " Y-Pos: {} != {}".format(bbox[u"y"], exp["y"])
        if not mw:
            msg += " Width: {} != {}".format(bbox[u"w"], exp["w"])
        if not mh:
            msg += " Height: {} != {}".format(bbox[u"h"], exp["h"])
        return False, msg
