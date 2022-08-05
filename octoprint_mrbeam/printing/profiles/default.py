# Default config for the Mr beam laser cutter

__all__ = ["profile"]

profile = dict(
    id="_default",
    name="MrBeam2",
    model="X",
    axes=dict(
        x=dict(inverted=False, speed=5000, overshoot=1, homing_direction_positive=True),
        y=dict(inverted=False, speed=5000, overshoot=0, homing_direction_positive=True),
        z=dict(inverted=False, speed=1000, overshoot=0, homing_direction_positive=True),
    ),
    # False if we need to show focus tab
    focus=True,
    # if True, Mr Beam shows warning to put on safety glasses (MrBeamI)
    glasses=False,
    # if set to onebutton, MR Beam 2 One Button to start laser is activated.
    start_method="onebutton",
    laser=dict(
        max_temperature=55.0,   # deprecated, moved to iobeam.laserhead_handler in SW-1077
        hysteresis_temperature=48.0,
        cooling_duration=25,  # if set to positive values: enables time based cooling resuming rather that per hysteresis_temperature
        intensity_factor=13,  # to get from 100% intesity to GCODE-intensity of 1300
        intensity_limit=1300,  # Limits intensity of ALL incomming G-Code commands (a correction factor is multiplied on top of this)
        intensity_upper_bound=1500,  # Limits intensity of ALL G-Code commands even with correction factor to this upper bound
        max_correction_factor=1.15,  # max value of the correction factor
    ),
    dust=dict(extraction_limit=0.70, auto_mode_time=60),
    volume=dict(
        # Grbl values $130 (x max travel) and $131 (y max travel) need to be set to:
        # x | $130 (x max travel):  width + (2 * working_area_shift_x) + origin_offset_x
        # y | $131 (y max travel):  depth + (2 * working_area_shift_y) + origin_offset_y
        # While origin_offset_x = origin_offset_x = $27 (homing pull-off) + 0.1 !!
        #
        # Example: D-Series
        #   has an working_area_shift_x of 7.0, so we have to add it left and right of working_area.
        #   However, left working_area_shift_x is in negative coordinates.
        #   So $130 (x max travel) will be 515.1, reaching
        #       from -7.0: 0 - 7.0(working_area_shift_x)
        #       till 508.1: 500(width) + 7.0(working_area_shift_x) + 1.1(origin_offset_x)
        depth=390.0,
        height=0.0,
        origin_offset_x=1.1,
        origin_offset_y=1.1,
        width=500.0,
        working_area_shift_x=7.0,
        working_area_shift_y=0.0,
    ),
    grbl=dict(
        resetOnConnect=True,
        # legacy ?
        homing_debounce=1,
        # GRBL auto update configuration
        auto_update_file=None,
        auto_update_version=None,
        # versions=['0.9g_22270fa', '0.9g_20180223_61638c5'],
        # GRBL settings that will get synced to GRBL
        settings_count=33,
        settings={
            0: 10,  # step idle delay must be 255
            1: 255,  # step idle delay, msec
            2: 0,  # step port invert mask:00000000
            3: 2,  # dir port invert mask:00000010
            4: 0,  # step enable invert, bool
            5: 0,  # limit pins invert, bool
            6: 0,  # probe pin invert, bool
            10: 31,  # status report mask:00011111
            11: 0.020,  # junction deviation, mm
            12: 0.002,  # arc tolerance, mm
            13: 0,  # report inches, bool
            14: 1,  # auto start, bool
            20: 1,  # soft limits, bool
            21: 0,  # hard limits, bool
            22: 1,  # homing cycle, bool
            23: 0,  # homing dir invert mask:00000000
            24: 25.000,  # homing feed, mm/min
            25: 2000.000,  # homing seek, mm/min
            26: 100,  # homing debounce, msec
            27: 1.000,  # homing pull-off, mm
            40: 1,  # turn Laser mode on, bool
            100: 100.000,  # x, step/mm
            101: 100.000,  # y, step/mm
            102: 100.000,  # z, step/mm
            110: 5000.000,  # x max rate, mm/min
            111: 5000.000,  # y max rate, mm/min
            112: 5000.000,  # z max rate, mm/min
            120: 700.000,  # x accel, mm/sec^2
            121: 700.000,  # y accel, mm/sec^2
            122: 100.000,  # z accel, mm/sec^2
            130: 515.100,  # x max travel, mm       # !! C-Series: 501.1
            131: 391.100,  # y max travel, mm
            132: 40.000,  # z max travel, mm
        },
    ),
    zAxis=False,
)
