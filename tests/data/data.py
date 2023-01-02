from mock import ANY

# SLICING TESTS

CONVERT_COMMAND = "convert"
CONVERT_RESPONSE = None

CONVERT_TEST_GCODE_AND_QS = dict(
    CONVERT_DATA={
        u'raster': {u'eng_passes': 1, u'extra_overshoot': False, u'beam_diameter': 0.15, u'speed_white': 1500,
                    u'dithering': False, u'engraving_mode': u'precise', u'intensity_white_user': 0,
                    u'engraving_enabled': False, u'intensity_black_user': 30, u'eng_compressor': 10,
                    u'intensity_white': 0, u'line_distance': 0.15, u'intensity_black': 390, u'pierce_time': 0,
                    u'speed_black': 450}, u'gcodeFilesToAppend': [
            {u'origin': u'local', u'hash': u'5e9dbc016d338d080fe1ecc22530b13999b4314b', u'name': u'Rectangle.gco',
             u'links': [], u'notes': [], u'typePath': [u'machinecode', u'gcode'], u'weight': 1, u'date': 1669995282,
             u'path': u'Rectangle.gco', u'previewId': u'wa_pese', u'type': u'machinecode', u'display': u'Rectangle.gco',
             u'refs': {u'download': u'http://localhost:5003/downloads/files/local/Rectangle.gco',
                       u'resource': u'http://localhost:5003/api/files/local/Rectangle.gco'}, u'size': 1737}],
        u'slicer': u'svgtogcode', u'gcode': u'Rectangle_1more.gco',
        u'design_files': [{u'size': 1737, u'format': u'gcode'},
                          {u'format': u'quickshape', u'design_id': u'qs_tilu', u'dim_x': u'12.6 mm',
                           u'dim_y': u'12.9 mm'}],
        u'material': {u'params_changed': False, u'color': u'8b624a', u'material_name': u'Cardboard, single wave',
                      u'custom': False, u'material_key': u'Cardboard, corrugated single wave', u'thickness_mm': 1.5},
        u'svg': u'<!--COLOR_PARAMS_START[{"color":"#e25303","intensity":1300,"intensity_user":100,"feedrate":200,"pierce_time":0,"passes":2,"progressive":false,"engrave":false,"cut_compressor":100}]COLOR_PARAMS_END-->\n<svg height="1381.8897637795278" version="1.1" width="1771.6535433070867" xmlns="http://www.w3.org/2000/svg" id="compSvg" xmlns:mb="http://www.mr-beam.org/mbns" xmlns:xlink="http://www.w3.org/1999/xlink" viewBox="0 0 500 390" mb:beamOS_version="0+unknown" mb:gc_options="beamOS:0+unknown on 306dc73541aa, gc_nextgen:0.1, enabled:true, precision:0.05, optimize_travel:true, small_paths_first:true, clip_working_area:true, clipRect:0,0,500,390, userAgent:Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/107.0.0.0 Safari/537.36"><defs><filter id="grayscale_filter" mb:id="grayscale_filter">\n\t\t\t\t\t\t\t\t\t\t<feColorMatrix in="SourceGraphic" type="saturate" values="0"/>\n\t\t\t\t\t\t\t\t\t</filter><filter id="gcimage_preview" mb:id="gcimage_preview">\n\t\t\t\t\t\t\t\t\t\t<feComponentTransfer>\n\t\t\t\t\t\t\t\t\t\t\t<feFuncR type="table" tableValues="0.9 1"/>\n\t\t\t\t\t\t\t\t\t\t\t<feFuncG type="table" tableValues="0.3 1"/>\n\t\t\t\t\t\t\t\t\t\t\t<feFuncB type="table" tableValues="0.1 1"/>\n\t\t\t\t\t\t\t\t\t\t</feComponentTransfer>\n\t\t\t\t\t\t\t\t\t</filter><filter id="designHighlight" filterUnits="objectBoundingBox" color-interpolation-filters="sRGB" mb:id="designHighlight">\n\t\t\t\t\t\t\t\t\t\t<feDropShadow stdDeviation="5 5" in="SourceGraphic" dx="0" dy="0" flood-color="#e25303" flood-opacity="1" result="dropShadow"/>\n\t\t\t\t\t\t\t\t\t</filter><filter id="dehighlight" x="0" y="0" mb:id="dehighlight">\n\t\t\t\t\t\t\t\t\t\t\n\t\t\t\t\t\t\t\t\t\t<feColorMatrix type="saturate" values="0.5"/>\n\t\t\t\t\t\t\t\t\t</filter><filter id="scan_text_mode" mb:id="scan_text_mode">\n                                        <feGaussianBlur stdDeviation="0.1"/>\n                                        <feComponentTransfer>\n                                            <feFuncR tableValues="0 0 0 1 1 1 1" type="discrete"/>\n                                            <feFuncG tableValues="0 0 0 1 1 1 1" type="discrete"/>\n                                            <feFuncB tableValues="0 0 0 1 1 1 1" type="discrete"/>\n                                        </feComponentTransfer>\n                                    </filter></defs><g xmlns="http://www.w3.org/2000/svg"><g id="gSlb6o1qtd4i"><g id="gSlb6o1qtd4j" mb:id="qs_tilu-0" mb:origin="qs_tilu" class="userSVG" transform="matrix(0.1264,0,0,0.1294,204.1334,146.0493)"><g class="gridify_original"><g><path fill="#ffffff" stroke="#e25303" d="M50,0L50,0C77.61423749155,0 100,22.385762508450004 100,50L100,50C100,77.61423749155 77.61423749155,100 50,100L50,100C22.385762508450004,100 0,77.61423749155 0,50L0,50C0,22.385762508450004 22.385762508450004,0 50,0z" style="clip-rule: nonzero; fill-opacity: 0; text-decoration: none solid rgb(56, 62, 66); stroke-width: 0.8;" mb:color="#e25303" class="vector_outline" id="pathSlb6o1qtd4m" mb:id="wa_xaqico-0" mb:gc=";_gc_nextgen_svg_id:wa_xaqico-0,node:path,mb:color:#e25303,mb:id:wa_xaqico-0,clip_working_area_clipped:false G0X210.45Y243.95 ;_laseron_ G1X211.70Y243.82 G1X212.91Y243.44 G1X214.01Y242.83 G1X214.96Y242.02 G1X215.73Y241.04 G1X216.31Y239.91 G1X216.66Y238.71 G1X216.77Y237.48 G1X216.65Y236.20 G1X216.28Y234.96 G1X215.68Y233.84 G1X214.89Y232.87 G1X213.93Y232.07 G1X212.82Y231.48 G1X211.65Y231.13 G1X210.45Y231.01 G1X209.20Y231.14 G1X207.99Y231.52 G1X206.90Y232.13 G1X205.95Y232.94 G1X205.17Y233.92 G1X204.59Y235.05 G1X204.25Y236.25 G1X204.13Y237.48 G1X204.25Y238.71 G1X204.59Y239.91 G1X205.17Y241.04 G1X205.95Y242.02 G1X206.90Y242.83 G1X207.99Y243.44 G1X209.20Y243.82 G1X210.45Y243.95 ;_laseroff_" mb:start_x="210.4534" mb:start_y="243.9507" mb:end_x="210.4534" mb:end_y="243.9507" mb:gc_length="40.123371727069696"></path></g></g><g class="gridify_clones"></g></g></g></g></svg>',
        u'vector': [
            {u'passes': 2, u'feedrate': 200, u'progressive': False, u'color': u'#e25303', u'cut_compressor': 100,
             u'intensity_user': 100, u'intensity': 1300, u'engrave': False, u'pierce_time': 0}], u'command': u'convert',
        u'engrave': False, u'job_time_estimation': {u'detailed_list': [
            {u'duration': u'0h 0m', u'bgr': u'#ffffff', u'img': u'/plugin/mrbeam/static/img/img_and_fills2.svg',
             u'label': u'Engraving'},
            {u'duration': u'~ 0h 1m', u'bgr': u'#e25303', u'img': u'/plugin/mrbeam/static/img/line_overlay.svg',
             u'label': u'Path '},
            {u'duration': u'~ 0h 1m', u'bgr': u'#383e42', u'img': u'/plugin/mrbeam/static/img/position_movement.svg',
             u'label': u'Movement'}], u'humanReadable': u'~ 0h 1m', u'val': {u'estimationVariance': 0.07, u'vectors': {
            u'#e25303': {u'duration': {u'hr': u'~ 0h 1m', u'raw': 24.074023036241815,
                                       u'range': {u'max': 33.48696604341237, u'abs': 2.1907360962980054,
                                                  u'val': 31.296229947114362, u'min': 29.105493850816355},
                                       u'val': 31.296229947114362}, u'positioningInMM': 0,
                         u'lengthInMM': 40.123371727069696}}, u'bitmaps': [], u'no_info': 0, u'total': {
            u'raster': {u'hr': u'0h 0m', u'raw': 0, u'range': {u'max': 0, u'abs': 0, u'val': 0, u'min': 0}, u'val': 0},
            u'sum': {u'hr': u'~ 0h 1m', u'raw': 35.48806701723295,
                     u'range': {u'max': 49.36390122097104, u'abs': 3.229414098568199, u'val': 46.13448712240284,
                                u'min': 42.90507302383464}, u'val': 46.13448712240284},
            u'vector': {u'hr': u'~ 0h 1m', u'raw': 24.074023036241815,
                        u'range': {u'max': 33.48696604341237, u'abs': 2.1907360962980054, u'val': 31.296229947114362,
                                   u'min': 29.105493850816355}, u'val': 31.296229947114362},
            u'positioning': {u'hr': u'~ 0h 1m', u'raw': 11.414043980991138,
                             u'range': {u'max': 15.876935177558675, u'abs': 1.0386780022701938,
                                        u'val': 14.838257175288481, u'min': 13.799579173018287},
                             u'val': 14.838257175288481}}, u'estimationCorrection': 1.3}}, u'advanced_settings': False},

    SLICE_KWARGS={'profile': None, 'callback_args': [u'Rectangle_1more.gco', False, False, [
        {u'origin': u'local', u'hash': u'5e9dbc016d338d080fe1ecc22530b13999b4314b', u'links': [],
         u'refs': {u'download': u'http://localhost:5003/downloads/files/local/Rectangle.gco',
                   u'resource': u'http://localhost:5003/api/files/local/Rectangle.gco'}, u'weight': 1,
         u'date': 1669995282, u'path': u'Rectangle.gco', u'previewId': u'wa_pese', u'size': 1737,
         u'name': u'Rectangle.gco', u'notes': [], u'typePath': [u'machinecode', u'gcode'], u'type': u'machinecode',
         u'display': u'Rectangle.gco'}]], 'overrides': {
        'raster': {u'eng_passes': 1, u'extra_overshoot': False, u'speed_white': 1500, u'engraving_mode': u'precise',
                   u'intensity_black_user': 30, u'line_distance': 0.15, u'intensity_black': 390, u'pierce_time': 0,
                   u'speed_black': 450, u'beam_diameter': 0.15, u'dithering': False, u'intensity_white_user': 0,
                   u'engraving_enabled': False, u'intensity_white': 0, u'eng_compressor': 10}, 'vector': [
            {u'passes': 2, u'feedrate': 200, u'intensity': 1300, u'progressive': False, u'intensity_user': 100,
             u'color': u'#e25303', u'pierce_time': 0, u'engrave': False, u'cut_compressor': 100}]}, 'callback': ANY,
                  'printer_profile_id': None, 'position': None},
    SLICE_ARGS=('svgtogcode', 'local', 'local/temp.svg', 'local', u'Rectangle_1more.gco')
)

CONVERT_TEST_QS = dict(
    CONVERT_DATA={u'raster': {u'eng_passes': 1, u'extra_overshoot': False, u'beam_diameter': 0.15, u'speed_white': 1500,
                              u'dithering': False, u'engraving_mode': u'precise', u'intensity_white_user': 0,
                              u'engraving_enabled': False, u'intensity_black_user': 30, u'eng_compressor': 10,
                              u'intensity_white': 0, u'line_distance': 0.15, u'intensity_black': 390, u'pierce_time': 0,
                              u'speed_black': 450}, u'gcodeFilesToAppend': [], u'slicer': u'svgtogcode',
                  u'gcode': u'Rectangle.gco', u'design_files': [
            {u'format': u'quickshape', u'design_id': u'qs_faja', u'dim_x': u'45.1 mm', u'dim_y': u'22.6 mm'}],
                  u'material': {u'params_changed': False, u'color': u'8b624a',
                                u'material_name': u'Cardboard, single wave', u'custom': False,
                                u'material_key': u'Cardboard, corrugated single wave', u'thickness_mm': 1.5},
                  u'svg': u'<!--COLOR_PARAMS_START[{"color":"#e25303","intensity":1300,"intensity_user":100,"feedrate":200,"pierce_time":0,"passes":2,"progressive":false,"engrave":false,"cut_compressor":100}]COLOR_PARAMS_END-->\n<svg height="1381.8897637795278" version="1.1" width="1771.6535433070867" xmlns="http://www.w3.org/2000/svg" id="compSvg" xmlns:mb="http://www.mr-beam.org/mbns" xmlns:xlink="http://www.w3.org/1999/xlink" viewBox="0 0 500 390" mb:beamOS_version="0+unknown" mb:gc_options="beamOS:0+unknown on f9835a8f03e1, gc_nextgen:0.1, enabled:true, precision:0.05, optimize_travel:true, small_paths_first:true, clip_working_area:true, clipRect:0,0,500,390, userAgent:Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/107.0.0.0 Safari/537.36"><defs><filter id="grayscale_filter" mb:id="grayscale_filter">\n\t\t\t\t\t\t\t\t\t\t<feColorMatrix in="SourceGraphic" type="saturate" values="0"/>\n\t\t\t\t\t\t\t\t\t</filter><filter id="gcimage_preview" mb:id="gcimage_preview">\n\t\t\t\t\t\t\t\t\t\t<feComponentTransfer>\n\t\t\t\t\t\t\t\t\t\t\t<feFuncR type="table" tableValues="0.9 1"/>\n\t\t\t\t\t\t\t\t\t\t\t<feFuncG type="table" tableValues="0.3 1"/>\n\t\t\t\t\t\t\t\t\t\t\t<feFuncB type="table" tableValues="0.1 1"/>\n\t\t\t\t\t\t\t\t\t\t</feComponentTransfer>\n\t\t\t\t\t\t\t\t\t</filter><filter id="designHighlight" filterUnits="objectBoundingBox" color-interpolation-filters="sRGB" mb:id="designHighlight">\n\t\t\t\t\t\t\t\t\t\t<feDropShadow stdDeviation="5 5" in="SourceGraphic" dx="0" dy="0" flood-color="#e25303" flood-opacity="1" result="dropShadow"/>\n\t\t\t\t\t\t\t\t\t</filter><filter id="dehighlight" x="0" y="0" mb:id="dehighlight">\n\t\t\t\t\t\t\t\t\t\t\n\t\t\t\t\t\t\t\t\t\t<feColorMatrix type="saturate" values="0.5"/>\n\t\t\t\t\t\t\t\t\t</filter><filter id="scan_text_mode" mb:id="scan_text_mode">\n                                        <feGaussianBlur stdDeviation="0.1"/>\n                                        <feComponentTransfer>\n                                            <feFuncR tableValues="0 0 0 1 1 1 1" type="discrete"/>\n                                            <feFuncG tableValues="0 0 0 1 1 1 1" type="discrete"/>\n                                            <feFuncB tableValues="0 0 0 1 1 1 1" type="discrete"/>\n                                        </feComponentTransfer>\n                                    </filter></defs><g xmlns="http://www.w3.org/2000/svg"><g id="gSlbavm8361m"><g id="gSlbavm8361n" mb:id="qs_faja-0" mb:origin="qs_faja" class="userSVG" transform="matrix(0.4511,0,0,0.4511,222.1382,158.4891)"><g class="gridify_original"><g><path fill="#ffffff" stroke="#e25303" d="M0,0l100,0 0,50 -100,0 z" style="clip-rule: nonzero; fill-opacity: 0; text-decoration: none solid rgb(56, 62, 66); stroke-width: 0.8;" mb:color="#e25303" class="vector_outline" id="pathSlbavm8361q" mb:id="wa_tupopo-0" mb:gc=";_gc_nextgen_svg_id:wa_tupopo-0,node:path,mb:color:#e25303,mb:id:wa_tupopo-0,clip_working_area_clipped:false G0X222.14Y231.51 ;_laseron_ G1X267.25Y231.51 G1X267.25Y208.96 G1X222.14Y208.96 G1X222.14Y231.51 ;_laseroff_" mb:start_x="222.1382" mb:start_y="231.5109" mb:end_x="222.1382" mb:end_y="231.5109" mb:gc_length="135.32999999999998"></path></g></g><g class="gridify_clones"></g></g></g></g></svg>',
                  u'vector': [{u'passes': 2, u'feedrate': 200, u'progressive': False, u'color': u'#e25303',
                               u'cut_compressor': 100, u'intensity_user': 100, u'intensity': 1300, u'engrave': False,
                               u'pierce_time': 0}], u'command': u'convert', u'engrave': False, u'job_time_estimation': {
            u'detailed_list': [
                {u'duration': u'0h 0m', u'bgr': u'#ffffff', u'img': u'/plugin/mrbeam/static/img/img_and_fills2.svg',
                 u'label': u'Engraving'},
                {u'duration': u'~ 0h 2m', u'bgr': u'#e25303', u'img': u'/plugin/mrbeam/static/img/line_overlay.svg',
                 u'label': u'Path '}, {u'duration': u'~ 0h 1m', u'bgr': u'#383e42',
                                       u'img': u'/plugin/mrbeam/static/img/position_movement.svg',
                                       u'label': u'Movement'}], u'humanReadable': u'~ 0h 2m',
            u'val': {u'estimationVariance': 0.07, u'vectors': {u'#e25303': {
                u'duration': {u'hr': u'~ 0h 2m', u'raw': 81.198,
                              u'range': {u'max': 95.570046, u'abs': 6.252246000000001, u'val': 89.3178,
                                         u'min': 83.065554}, u'val': 89.3178}, u'positioningInMM': 0,
                u'lengthInMM': 135.32999999999998}}, u'bitmaps': [], u'no_info': 0, u'total': {
                u'raster': {u'hr': u'0h 0m', u'raw': 0, u'range': {u'max': 0, u'abs': 0, u'val': 0, u'min': 0},
                            u'val': 0}, u'sum': {u'hr': u'~ 0h 2m', u'raw': 92.61204398099113,
                                                 u'range': {u'max': 109.00437576562658, u'abs': 7.131127386536319,
                                                            u'val': 101.87324837909026, u'min': 94.74212099255394},
                                                 u'val': 101.87324837909026},
                u'vector': {u'hr': u'~ 0h 2m', u'raw': 81.198,
                            u'range': {u'max': 95.570046, u'abs': 6.252246000000001, u'val': 89.3178,
                                       u'min': 83.065554}, u'val': 89.3178},
                u'positioning': {u'hr': u'~ 0h 1m', u'raw': 11.414043980991138,
                                 u'range': {u'max': 13.434329765626572, u'abs': 0.8788813865363178,
                                            u'val': 12.555448379090253, u'min': 11.676566992553933},
                                 u'val': 12.555448379090253}}, u'estimationCorrection': 1.1}},
                  u'advanced_settings': False},
    SLICE_KWARGS={'callback': ANY,
                  'callback_args': [u'Rectangle.gco', False, False, []],
                  'overrides': {'raster': {u'beam_diameter': 0.15,
                                           u'dithering': False,
                                           u'eng_compressor': 10,
                                           u'eng_passes': 1,
                                           u'engraving_enabled': False,
                                           u'engraving_mode': u'precise',
                                           u'extra_overshoot': False,
                                           u'intensity_black': 390,
                                           u'intensity_black_user': 30,
                                           u'intensity_white': 0,
                                           u'intensity_white_user': 0,
                                           u'line_distance': 0.15,
                                           u'pierce_time': 0,
                                           u'speed_black': 450,
                                           u'speed_white': 1500},
                                'vector': [{u'color': u'#e25303',
                                            u'cut_compressor': 100,
                                            u'engrave': False,
                                            u'feedrate': 200,
                                            u'intensity': 1300,
                                            u'intensity_user': 100,
                                            u'passes': 2,
                                            u'pierce_time': 0,
                                            u'progressive': False}]},
                  'position': None,
                  'printer_profile_id': None,
                  'profile': None},
    SLICE_ARGS=('svgtogcode', 'local', 'local/temp.svg', 'local', u'Rectangle.gco'),
)
