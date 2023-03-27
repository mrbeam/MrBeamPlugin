;Generated from temp.svg 50a214f821b33c29205074152c3b09f1419bca5d
; gc_nexgen gc_options: beamOS:0.13.0a1.post11.dev0+gc565d0fa on 8302c3e12fe3, gc_nextgen:0.1, enabled:true, precision:0.05, optimize_travel:true, small_paths_first:true, clip_working_area:true, clipRect:0,0,500,390, userAgent:Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) HeadlessChrome/111.0.5563.66 Safari/537.36
; created:2023-03-24 09:47:17
; laser params: {u'#e25303': {u'passes': 2, u'feedrate': 200, u'progressive': False, u'color': u'#e25303', u'intensity': 1300, u'intensity_user': 100, u'cut_compressor': 100, 'mpr': 13.0, 'svgDPI': 90, u'engrave': False, u'pierce_time': 0, 'laserhead_model_id': None}}

; speedup cooling fan
M3S0
G4P0.5
M5
; end speedup cooling fan

; gcode_before_job - color: #e25303
M100P100 ; mrbeam_compressor: 100
G4P0.2

; Layer:compSvg, outline of:pathSlfmcyaal1r, stroke:#e25303, {u'passes': 2, u'feedrate': 200, u'progressive': False, u'color': u'#e25303', u'intensity': 1300, u'intensity_user': 100, u'cut_compressor': 100, 'mpr': 13.0, 'svgDPI': 90, u'engrave': False, u'pierce_time': 0, 'laserhead_model_id': None}
; pass:1/2
;_gc_nextgen_svg_id:wa_maryki-0,node:path,mb:color:#e25303,mb:id:wa_maryki-0,clip_working_area_clipped:false
G0X9.87Y377.32
F200;#e25303
; gcode_before_path_color
M3S0
G4P0
M03 S1300 ; color: #e25303

G1X41.50Y355.04
M05

; pass:2/2
;_gc_nextgen_svg_id:wa_maryki-0,node:path,mb:color:#e25303,mb:id:wa_maryki-0,clip_working_area_clipped:false
G0X9.87Y377.32
F200;#e25303
; gcode_before_path_color
M3S0
G4P0
M03 S1300 ; color: #e25303

G1X41.50Y355.04
M05

; end of job
M05
M100P0 ; mrbeam_compressor off
