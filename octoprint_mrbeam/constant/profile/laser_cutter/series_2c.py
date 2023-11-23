#!/usr/bin/env python3
from octoprint_mrbeam.enums.device_series import DeviceSeriesEnum

profile = dict(
    id="series_" + DeviceSeriesEnum.C.value,
    model="C",
    legacy=dict(
        job_done_home_position_x=250,
    ),
    volume=dict(
        working_area_shift_x=0.0,
    ),
    grbl=dict(
        settings={
            130: 501.1, # X max travel, mm
        },
    ),
)
