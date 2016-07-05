# To change this license header, choose License Headers in Project Properties.
# To change this template file, choose Tools | Templates
# and open the template in the editor.


def gcode_before_path(intensity = 0):
	return "\nM03 S"+str(intensity)

def gcode_after_path():
	return "M03 S0\n"

gcode_header = """
$H
G92 X0 Y0 Z0
G90
M08
"""

gcode_footer = """
M05
G0 X0.000 Y0.000
M09
M02
"""


