from __future__ import absolute_import

from octoprint.util import dict_merge
from octoprint_mrbeam.constant.profile.laser_cutter import default, series_2c, rotary, series_2c_rotary

# Default profile for the Mr beam laser cutter in default mode and a non-2C series
default_profile = default.profile

# Default profile for the Mr beam laser cutter in default mode and a 2C series
series_2c_profile = dict_merge(default_profile, series_2c.profile)

# Default profile for the Mr beam laser cutter in rotary mode and a non-2C series
rotary_profile = dict_merge(default_profile, rotary.profile)

# Default profile for the Mr beam laser cutter in rotary mode and a 2C series
series_2c_rotary_profile = dict_merge(default_profile, series_2c_rotary.profile)
