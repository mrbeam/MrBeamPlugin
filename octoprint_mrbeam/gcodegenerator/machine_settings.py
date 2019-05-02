# To change this license header, choose License Headers in Project Properties.
# To change this template file, choose Tools | Templates
# and open the template in the editor.


def gcode_before_path(intensity = 0):
	return "\nM03 S"+str(intensity)

def gcode_before_path_color(color = '#000000', intensity = '0'):
	return "\nM03 S%s;%s" % (intensity, color) 

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

gcode_footer = """
M05
G0 X500.000 Y400.000
M09
M02
"""


