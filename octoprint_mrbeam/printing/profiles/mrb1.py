#!/usr/bin/env python3

# Old default dictionary for Mr Beam I

# we tried to switch to more up-to-date default profiles...
# but then more than just one profile had the same name as the default one
#    and that confused the whole system.... :-(

__all__ = ["profile"]

profile = dict(
    id="_mrbeam_junior",
    name="Mr Beam",
    model="Junior",
    volume=dict(
        width=217,
        depth=298,
        height=0,
        origin_offset_x=1.1,
        origin_offset_y=1.1,
    ),
    zAxis=False,
    focus=False,
    glasses=True,
    axes=dict(
        x=dict(speed=5000, inverted=False),
        y=dict(speed=5000, inverted=False),
        z=dict(speed=1000, inverted=False),
    ),
    start_method=None,
    grbl=dict(
        resetOnConnect=False,
    ),
)
