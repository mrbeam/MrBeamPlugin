def gcode_before_job(color="#000000", compressor=100):
    gcode = []
    if compressor is not None:
        gcode.append("; gcode_before_job - color: {color}".format(color=color))
        gcode.append("M100P{p} ; mrbeam_compressor: {p}".format(p=compressor))
        gcode.append("G4P0.2")
    else:
        gcode.append("; gcode_before_job - color: {color}".format(color=color))
        gcode.append("; mrbeam_compressor: no compressor")
    gcode.append("\n")
    return "\n".join(gcode)


def gcode_after_job(color="#000000"):
    return ""


def gcode_before_path_color(color="#000000", intensity=0):
    gcode = []
    gcode.append("; gcode_before_path_color")
    gcode.append("M3S0")
    gcode.append("G4P0")
    gcode.append("M03 S{i} ; color: {c}".format(i=intensity, c=color))
    return "\n".join(gcode)


def gcode_after_path():
    return "M3S0"


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
