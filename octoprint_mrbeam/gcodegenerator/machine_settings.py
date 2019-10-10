


#def gcode_before_path(intensity = 0):
#	return "\nM3S0\nG4P0\nM03 S"+str(intensity)

def gcode_before_path_color(color = '#000000', intensity = 0, compressor = 100):
	return "\nM100P{p} ;mrbeam_compressor: {p} - gcode_before_path_color\nM3S0\nG4P0\nM03 S{i} ; color: {c}".format(p=compressor, i=intensity, c=color)

def gcode_after_path():
	return "M05"



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
; end of job
M05
M100P0 ; air_pressure: 0 - gcode_footer
G0 X500.000 Y390.000
M09
M02
"""


