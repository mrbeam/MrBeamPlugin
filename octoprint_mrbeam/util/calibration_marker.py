class CalibrationMarker:

    SVG = """<?xml version="1.0" encoding="UTF-8" standalone="no"?>
<svg xmlns:svg="http://www.w3.org/2000/svg" xmlns="http://www.w3.org/2000/svg" id="calibration_markers-0" viewBox="%(xmin)s %(ymin)s %(xmax)s %(ymax)s" height="%(ymax)smm" width="%(xmax)smm">
	<path id="NE" d="M%(xmax)s %(ymax)sl-20,0 5,-5 -10,-10 10,-10 10,10 5,-5 z" style="stroke:#000000; stroke-width:1px; fill:none;" />
	<path id="NW" d="M%(xmin)s %(ymax)sl20,0 -5,-5 10,-10 -10,-10 -10,10 -5,-5 z" style="stroke:#000000; stroke-width:1px; fill:none;" />
	<path id="SW" d="M%(xmin)s %(ymin)sl20,0 -5,5 10,10 -10,10 -10,-10 -5,5 z" style="stroke:#000000; stroke-width:1px; fill:none;" />
	<path id="SE" d="M%(xmax)s %(ymin)sl-20,0 5,5 -10,10 10,10 10,-10 5,5 z" style="stroke:#000000; stroke-width:1px; fill:none;" />
</svg>"""

    GCODE = """
; Generated from calibration_marker.py
; laser params: {u'feedrate': %(feedrate)s, u'intensity': %(intensity)s}

; speedup cooling fan
M3S0
G4P0.5
M5
; end speedup cooling fan

; gcode_before_job - color: #000000
; mrbeam_compressor: no compressor

; marker top right
G90
G0X%(xmax)sY%(ymax)s
G91
F%(feedrate)s
M3S0
G4P0
M3S%(intensity)s

G1X-20Y0
G1X5Y-5
G1X-10Y-10
G1X10Y-10
G1X10Y10
G1X5Y-5
G1X0Y20
M5

; marker top left
G90
G0X%(xmin)sY%(ymax)s
G91
F%(feedrate)s
M3S0
G4P0
M3S%(intensity)s

G1X20Y0
G1X-5Y-5
G1X10Y-10
G1X-10Y-10
G1X-10Y10
G1X-5Y-5
G1X0Y20
M5

; marker bottom left
G90
G0X%(xmin)sY%(ymin)s
G91
F%(feedrate)s
M3S0
G4P0
M3S%(intensity)s

G1X20Y0
G1X-5Y5
G1X10Y10
G1X-10Y10
G1X-10Y-10
G1X-5Y5
G1X0Y-20
M5

; marker bottom right
G90
G0X%(xmax)sY%(ymin)s
G91
F%(feedrate)s
M3S0
G4P0
M3S%(intensity)s

G1X-20Y0
G1X5Y5
G1X-10Y10
G1X10Y10
G1X10Y-10
G1X5Y5
G1X0Y-20
M5

; end of job
G90
M5
"""

    def __init__(self, workingAreaWidthMM, workingAreaHeightMM):
        self.xmin = 0
        self.xmax = workingAreaWidthMM
        self.ymin = 0
        self.ymax = workingAreaHeightMM

    def getSvg(self):
        return self.SVG % {
            "xmin": self.xmin,
            "xmax": self.xmax,
            "ymin": self.ymin,
            "ymax": self.ymax,
        }

    def getGCode(self, intensity, feedrate):
        return self.GCODE % {
            "xmin": self.xmin,
            "xmax": self.xmax,
            "ymin": self.ymin,
            "ymax": self.ymax,
            "intensity": intensity,
            "feedrate": feedrate,
        }
