# Default profile for the Mr beam laser cutter in default mode and a non-2C series

__all__ = ["profile"]

profile = dict(
    id="rotary",
    volume=dict(
            depth=390.0,
            width=500.0,
            after_homing_shift_y=-80.0, # After homing shift in Y direction
            after_homing_shift_rate=500, # After homing feed rate mm / min
        ),
    grbl=dict(
        settings={
            120: 30, # X Acceleration, mm / sec ^ 2
            121: 30, # Y Acceleration, mm / sec ^ 2
            111: 500, # Y Max rate, mm / min
            110: 500 # X Max rate, mm / min
        },
    ),
)
