from __future__ import absolute_import

from octoprint.util import dict_merge
from . import default, series_2c, rotary

# Default profile for the Mr beam laser cutter in default mode and a non-2C series
default_profile = default.profile
default_profile['id'] = 'default'

# Default profile for the Mr beam laser cutter in default mode and a 2C series
series_2c_profile = dict_merge(default_profile, series_2c.profile)
series_2c_profile['id'] = 'series_2c'

# Default profile for the Mr beam laser cutter in rotary mode and a non-2C series
rotary_profile = dict_merge(default_profile, rotary.profile)
rotary_profile['id'] = 'rotary'

# Default profile for the Mr beam laser cutter in rotary mode and a 2C series
series_2c_rotary_profile = dict_merge(series_2c_profile, rotary.profile)
series_2c_rotary_profile['id'] = 'series_2c_rotary'
