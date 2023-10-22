# Default profile for the Mr beam laser cutter in default mode and a non-2C series

__all__ = ["profile"]

profile = dict(
    id="profile_3",
    grbl=dict(
        settings={
            110: 500.000,  # x max rate, mm/min
            111: 500.000,  # y max rate, mm/min
            112: 500.000,  # z max rate, mm/min
        },
    ),
)
