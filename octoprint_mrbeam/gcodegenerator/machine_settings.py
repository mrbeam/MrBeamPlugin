


def gcode_before_path(intensity = 0):
	return "\nM3S0\nG4P0\nM03 S"+str(intensity)

def gcode_before_path_color(color = '#000000', intensity = '0'):
	return "\nM3S0\nG4P0\nM03 S%s;%s" % (intensity, color) 

def gcode_after_path():
	return "M05"

# TODO remove this or fetch machine settings from settings. (G92 X0 Y0 Z0 looks badly wrong for Mr Beam II machines.)
gcode_header = """
$H
G92 X0 Y0 Z0 
G90
M08
"""

# TODO remove this or fetch machine settings from settings.
gcode_footer = """
M05
G0 X500.000 Y390.000
M09
M02
"""


