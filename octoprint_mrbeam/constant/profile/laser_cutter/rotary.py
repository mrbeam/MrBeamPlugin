# Default profile for the Mr beam laser cutter in default mode and a non-2C series

__all__ = ["profile"]

profile = dict(
    id="rotary",
    grbl=dict(
        settings={
            120: 30, # X Acceleration, mm / sec ^ 2
            121: 30, # Y Acceleration, mm / sec ^ 2
            111: 500, # Y Max rate, mm / min
            110: 500 # X Max rate, mm / min
        },
    ),
)
