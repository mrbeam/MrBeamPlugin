


#def gcode_before_path(intensity = 0):
#	return "\nM3S0\nG4P0\nM03 S"+str(intensity)

def gcode_before_path_color(color = '#000000', intensity = '0', air_pressure = '100'):
	return "\n;air_pressure:%s\nM3S0\nG4P0\nM03 S%s;%s" % (air_pressure, intensity, color) 

def gcode_after_path():
	return "M05\n;air_pressure:0"



# TODO remove this or fetch machine settings from settings. (G92 X0 Y0 Z0 looks badly wrong for Mr Beam II machines.)
cooling_fan_speedup_gcode = """
; speedup cooling fan
M3S0
G4P0.5
M5
; end speedup cooling fan
"""

gcode_header = """
$H
G92 X0 Y0 Z0 
G90
M08
"""

# TODO remove this or fetch machine settings from settings.
gcode_footer = """
M05
;air_pressure:%s
G0 X500.000 Y390.000
M09
M02
"""


