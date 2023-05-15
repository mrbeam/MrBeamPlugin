;Generated from temp.svg b2bdde2b8fdd7bd411358224c9c8597a0d75558b
; gc_nexgen gc_options: beamOS:0.13.0.post0.post13.dev0+g2cbcae78 on 061d2e3c274c, gc_nextgen:0.1, enabled:true, precision:0.05, optimize_travel:true, small_paths_first:true, clip_working_area:true, clipRect:0,0,500,390, userAgent:Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) HeadlessChrome/113.0.5672.92 Safari/537.36
; created:2023-05-14 19:12:44
; laser params: {u'#e25303': {u'passes': 2, u'feedrate': 200, u'progressive': False, u'color': u'#e25303', u'intensity': 1300, u'intensity_user': 100, u'cut_compressor': 100, 'mpr': 13.0, 'svgDPI': 90, u'engrave': False, u'pierce_time': 0}}

; speedup cooling fan
M3S0
G4P0.5
M5
; end speedup cooling fan

; gcode_before_job - color: #e25303
M100P100 ; mrbeam_compressor: 100
G4P0.2

; Layer:compSvg, outline of:pathSlhnsm5of1r, stroke:#e25303, {u'passes': 2, u'feedrate': 200, u'progressive': False, u'color': u'#e25303', u'intensity': 1300, u'intensity_user': 100, u'cut_compressor': 100, 'mpr': 13.0, 'svgDPI': 90, u'engrave': False, u'pierce_time': 0}
; pass:1/2
;_gc_nextgen_svg_id:wa_juwixu-0,node:path,mb:color:#e25303,mb:id:wa_juwixu-0,clip_working_area_clipped:false
G0X11.75Y377.22
F200;#e25303
; gcode_before_path_color
M3S0
G4P0
M03 S1300 ; color: #e25303

G1X43.40Y354.94
M05

; pass:2/2
;_gc_nextgen_svg_id:wa_juwixu-0,node:path,mb:color:#e25303,mb:id:wa_juwixu-0,clip_working_area_clipped:false
G0X11.75Y377.22
F200;#e25303
; gcode_before_path_color
M3S0
G4P0
M03 S1300 ; color: #e25303

G1X43.40Y354.94
M05

; end of job
M05
M100P0 ; mrbeam_compressor off
