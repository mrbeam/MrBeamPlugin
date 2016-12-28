import logging
import re
import os
import machine_settings

from biarc import biarc
from point import Point
import numpy

import simplestyle
#import simplepath
import simpletransform
import cubicsuperpath

from svg_util import get_path_d, _add_ns

from lxml import etree



UUCONV = {'in':90.0, 'pt':1.25, 'px':1, 'mm':3.5433070866, 'cm':35.433070866, 'm':3543.3070866,
		  'km':3543307.0866, 'pc':15.0, 'yd':3240 , 'ft':1080}
def unittouu(string):
	'''Returns userunits given a string representation of units in another system'''
	unit = re.compile('(%s)$' % '|'.join(UUCONV.keys()))
	param = re.compile(r'(([-+]?[0-9]+(\.[0-9]*)?|[-+]?\.[0-9]+)([eE][-+]?[0-9]+)?)')

	p = param.match(string)
	u = unit.search(string)
	if p:
		retval = float(p.string[p.start():p.end()])
	else:
		retval = 0.0
	if u:
		try:
			return retval * UUCONV[u.string[u.start():u.end()]]
		except KeyError:
			pass
	return retval

def uutounit(val, unit):
	return val/UUCONV[unit]



class Converter():

	defaults = {
		"directory": None,
		"file": None,
		"svgDPI": 90,
		"noheaders": "false",

		"engrave": False,
		"intensity_white": 0,
		"intensity_black": 500,
		"speed_white": 1500,
		"speed_black": 250,
		"contrast": 1.0,
		"sharpening": 1.0,
		"dithering": False,
		"beam_diameter": 0.2,

		"multicolor": []
	}

	def __init__(self, params, model_path):
		self._logger = logging.getLogger("octoprint.plugins.mrbeam.converter")
		
		# debugging
		self.transform_matrix = {}
		self.transform_matrix_reverse = {}
		self.orientation_points = {}
		
		self.colorParams = {}
		self.options = self.defaults;
		self.setoptions(params)
		self.svg_file = model_path
		self.document=None
		self._logger.info('### Converter Initialized: %s' % self.options)
		
	def setoptions(self, opts):
		# set default values if option is missing
		for key in self.options.keys():
			if key in opts: 
				self.options[key] = opts[key]
				if(key == "multicolor"):
					for paramSet in opts['multicolor']:
						self.colorParams[paramSet['color']] = paramSet
			else:
				self._logger.info("Using default %s = %s" %(key, str(self.options[key])))

	def convert(self, on_progress=None, on_progress_args=None, on_progress_kwargs=None):
		self.parse()

		options = self.options
		options['doc_root'] = self.document.getroot()

		# Get all Gcodetools data from the scene.
		self.calculate_conversion_matrix()
		self.collect_paths()
		
		for p in self.paths :
			#print "path", etree.tostring(p)
			pass

		def report_progress(on_progress, on_progress_args, on_progress_kwargs, done, total):
			if(total == 0):
				total = 1
			
			progress = done / float(total)
			if on_progress is not None:
				if on_progress_args is None:
					on_progress_args = ()
				if on_progress_kwargs is None:
					on_progress_kwargs = dict()

				on_progress_kwargs["_progress"] = progress
				on_progress(*on_progress_args, **on_progress_kwargs)
		

		self._check_dir() 
		gcode = ""
		gcode_outlines = ""
		gcode_fillings = ""
		gcode_images = ""

		self._logger.info("processing %i layers" % len(self.layers))
		# sum up
		itemAmount = 1
		for layer in self.layers :
			if layer in self.paths :
				itemAmount += len(self.paths[layer])
			if layer in self.images:
				itemAmount += len(self.images[layer])
				
		processedItemCount = 0
		report_progress(on_progress, on_progress_args, on_progress_kwargs, processedItemCount, itemAmount)
		for layer in self.layers :
			if layer in self.paths :
				pD = dict()
				for path in self.paths[layer] :
					self._logger.info("path %s, %s, stroke: %s,  'fill: ', %s" % ( layer.get('id'), path.get('id'), path.get('stroke'), path.get('class') ))

					if path.get('stroke') is not None: #todo catch None stroke/fill earlier
						stroke = path.get('stroke')
					elif path.get('fill') is not None:
						stroke = path.get('fill')
					elif path.get('class') is not None:
						stroke = path.get('class')
					else:
						stroke = 'default'
						continue

					if "d" not in path.keys() :
						self._logger.error("Warning: One or more paths don't have 'd' parameter")
						continue
					if stroke not in pD.keys() and stroke != 'default':
						pD[stroke] = []
					d = path.get("d")
					if d != '':
						csp = cubicsuperpath.parsePath(d)
						csp = self._apply_transforms(path, csp)
						pD[stroke] += csp

						processedItemCount += 1
						report_progress(on_progress, on_progress_args, on_progress_kwargs, processedItemCount, itemAmount)

				curvesD = dict() #diction
				for colorKey in pD.keys():
					if colorKey == 'none':
						continue
					curvesD[colorKey] = self._parse_curve(pD[colorKey], layer)

				#pierce_time = self.options['pierce_time']
				layerId = layer.get('id') or '?'
				pathId = path.get('id') or '?'

				#for each color generate GCode
				for colorKey in curvesD.keys():
					settings = self.colorParams.get(colorKey, {'intensity': -1, 'feedrate': -1, 'passes': 0, 'pierce_time': 0})
					gcode_outlines += "; Layer: " + layerId + ", outline of " + pathId + ", stroke: " + colorKey +', '+str(settings)+"\n"
					# gcode_outlines += self.generate_gcode_color(curvesD[colorKey], colorKey, pierce_time)
					curveGCode = self._generate_gcode(curvesD[colorKey], colorKey)
					for p in range(0, int(settings['passes'])):
						gcode_outlines += ";pass %i of %s\n" % (p+1, settings['passes'])
						gcode_outlines += curveGCode


			self._logger.info( 'Infills Setting: %s' % self.options['engrave'])
			if layer in self.images and self.options['engrave']:
				for imgNode in self.images[layer] :
					file_id = imgNode.get('data-serveurl', '')
					x = imgNode.get('x')
					y = imgNode.get('y')						
					if x == None:
						x = "0"
					if y == None:
						y = "0"

					
					# pt units
					x = float(x)
					y = float(y)
					w = float(imgNode.get("width"))
					h = float(imgNode.get("height"))

					_upperLeft = [x, y]
					_lowerRight = [x + w, y + h]
					
					# apply svg transforms
					_mat = self._get_transforms(imgNode)
					simpletransform.applyTransformToPoint(_mat, _upperLeft)
					simpletransform.applyTransformToPoint(_mat, _lowerRight)
					
					### original style with orientation points :( ... TODO
					# mm conversion
					upperLeft = self.transform(_upperLeft,layer, False)
					lowerRight = self.transform(_lowerRight,layer, False)
					
					w = abs(lowerRight[0] - upperLeft[0])
					h = abs(lowerRight[1] - upperLeft[1])

					# contrast = 1.0, sharpening = 1.0, beam_diameter = 0.25, 
					# intensity_black = 1000, intensity_white = 0, speed_black = 30, speed_white = 500, 
					# dithering = True, pierce_time = 500, material = "default"):
					ip = ImageProcessor(contrast = self.options['contrast'], sharpening = self.options['sharpening'], beam_diameter = self.options['beam_diameter'],
					intensity_black = self.options['intensity_black'], intensity_white = self.options['intensity_white'], 
					speed_black = self.options['speed_black'], speed_white = self.options['speed_white'], 
					dithering = self.options['dithering'],
					pierce_time = self.options['pierce_time'], material = "default")
					data = imgNode.get('href')
					if(data is None):
						data = imgNode.get(_add_ns('href', 'xlink'))
						
					gcode = ''
					if(data.startswith("data:")):
						gcode = ip.dataUrl_to_gcode(data, w, h, upperLeft[0], lowerRight[1], file_id)
					elif(data.startswith("http://")):
						gcode = ip.imgurl_to_gcode(data, w, h, upperLeft[0], lowerRight[1], file_id)
					else:
						self._logger.info("Error: unable to parse img data", data)

					gcode_images += gcode
					processedItemCount += 1
					report_progress(on_progress, on_progress_args, on_progress_kwargs, processedItemCount, itemAmount)

		self.export_gcode(gcode_images + "\n\n" + gcode_fillings + "\n\n" + gcode_outlines)


	def collect_paths(self):
		self._logger.info( "collect_paths")
		self.paths = {}
		self.images = {}
		self.layers = [self.document.getroot()]

		def recursive_search(g, layer):
			items = g.getchildren()
			items.reverse()
			if(len(items) > 0):
				self._logger.debug("recursive search: %i - %s"  %(len(items), g.get("id")))
				
			for i in items:
				# TODO layer support
				if i.tag == _add_ns("g",'svg') and i.get(_add_ns('groupmode','inkscape')) == 'layer':
					styles = simplestyle.parseStyle(i.get("style", ''))
					if "display" not in styles or styles["display"] != 'none':
						self.layers += [i]
						recursive_search(i,i)
					else:
						self._logger.info("Skipping hidden layer: '%s'" % i.get('id', "?") 	)

				else:
					# path
					if i.tag == _add_ns('path','svg'):					
						self._handle_node(i, layer)

					# rect, line, polygon, polyline, circle, ellipse
					elif i.tag == _add_ns( 'rect', 'svg' ) or i.tag == 'rect' \
					or i.tag == _add_ns( 'line', 'svg' ) or i.tag == 'line' \
					or i.tag == _add_ns( 'polygon', 'svg' ) or i.tag == 'polygon' \
					or i.tag == _add_ns( 'polyline', 'svg' ) or i.tag == 'polyline' \
					or i.tag == _add_ns( 'ellipse', 'svg' ) or i.tag == 'ellipse' \
					or i.tag == _add_ns( 'circle', 'svg' ) or	i.tag == 'circle':
					
						i.set("d", get_path_d(i))
						self._handle_node(i, layer)

					# image
					elif i.tag == _add_ns('image','svg'):
						x = i.get('x')
						y = i.get('y')						
						if x == None:
							x = "0"
						if y == None:
							y = "0"
					
						self._logger.info("added image " + i.get("width") + 'x' + i.get("height") + "@" + x+","+y)
						self._handle_image(i, layer)
					
					# group
					elif i.tag == _add_ns("g",'svg'):
						recursive_search(i,layer)
				
					else :
						self._logger.debug("ignoring not supported tag: %s \n %s \n\n" % (i.tag, etree.tostring(i)))
					
		recursive_search(self.document.getroot(), self.document.getroot())
		self._logger.info("self.layers: %i" % len(self.layers))
		self._logger.info("self.paths: %i" % len(self.paths))


	def parse(self,file=None):
		try:
			stream = open(self.svg_file,'r')
		except:
			self._logger.error("unable to read %s" % self.svg_file)
		p = etree.XMLParser(huge_tree=True)
		self.document = etree.parse(stream, parser=p)
		stream.close()
		self._logger.info("parsed %s" % self.svg_file)
		
	def _handle_image(self, imgNode, layer):
		self.images[layer] = self.images[layer] + [imgNode] if layer in self.images else [imgNode]
		
	def _handle_node(self, node, layer):
		stroke = self._get_stroke(node)
		fill = self._get_fill(node)
		has_classes = node.get('class', None) is not None # TODO parse styles instead of assuming that the style applies visibility
		visible = has_classes or stroke['visible'] or fill['visible'] or (stroke['color'] == 'unset' and fill['color'] == 'unset')
		processColor = self._process_color(stroke['color'])
		
		if(visible and processColor):
			simpletransform.fuseTransform(node)
			self.paths[layer] = self.paths[layer] + [node] if layer in self.paths else [node]

	def _get_stroke(self, node):
		stroke = {}
		stroke['width'] = 1
		stroke['width_unit'] = "px"
		stroke['color'] = 'unset'
		stroke['opacity'] = 1
		stroke['visible'] = True
		
		#"stroke", "stroke-width", "stroke-opacity", "opacity"
		styles = simplestyle.parseStyle(node.get("style"))
		color = node.get('stroke', None)
		if(color is None):
			if("stroke" in styles):
				color = styles["stroke"]
		
		if(color != None and color != 'none' and color != ''):
			stroke['color'] = color
		
		width = node.get('stroke-width', '')
		if(width is ''):
			if("stroke-width" in styles):
				width = styles["stroke-width"]
		if(width != 'none' and width != ''):
			try:
				strokeWidth = float(re.sub(r'[^\d.]+', '', width))				
				stroke['width'] = strokeWidth
				# todo: unit
			except ValueError:
				pass
				
		stroke_opacity = node.get('stroke-opacity', 1)
		if(stroke_opacity is 1):
			if ("stroke-opacity" in styles):
				try:
					stroke_opacity = float(styles["stroke-opacity"])
				except ValueError:
					pass

		opacity = node.get('opacity', 1)
		if(opacity is 1):
			if ("opacity" in styles):
				try:
					opacity = float(styles["opacity"])
				except ValueError:
					pass
				
		stroke['opacity'] = min(opacity, stroke_opacity)
		stroke['visible'] = stroke['color'] is not None and stroke['opacity'] > 0 and stroke['width'] > 0
		return stroke

	def _get_fill(self, node):
		fill = {}
		fill['color'] = 'unset'
		fill['opacity'] = 1
		fill['visible'] = True
		
		#"fill", "fill-opacity", "opacity"
		styles = simplestyle.parseStyle(node.get("style"))
		color = node.get('fill', None)
		if(color is None):
			if("fill" in styles):
				color = styles["fill"]
		if(color != None and color != 'none' and color != ''):
			fill['color'] = color
				
		fill_opacity = node.get('fill-opacity', 1)
		if(fill_opacity is 1):
			if ("fill-opacity" in styles):
				try:
					fill_opacity = float(styles["fill-opacity"])
				except ValueError:
					pass

		opacity = node.get('opacity', 1)
		if(opacity is 1):
			if ("opacity" in styles):
				try:
					opacity = float(styles["opacity"])
				except ValueError:
					pass

		fill['opacity'] = min(opacity, fill_opacity)
		fill['visible'] = fill['color'] is not None and fill['opacity'] > 0 
		return fill
		
	def _process_color(self, color):
		if(color in self.colorParams.keys()):
			return True
		else:
			self._logger.info("Skipping color: %s " % color)
			return False
		
	def _check_dir(self):
		if self.options['directory'][-1] not in ["/","\\"]:
			if "\\" in self.options['directory'] :
				self.options['directory'] += "\\"
			else :
				self.options['directory'] += "/"
		self._logger.info("Checking directory: '%s'"%self.options['directory'])
		if (os.path.isdir(self.options['directory'])):
			pass
		else: 
			self._logger.error("Directory does not exist! Please specify existing directory at Preferences tab!")
			return False	
		
	def _apply_transforms(self,g,csp):
		trans = self._get_transforms(g)
		if trans != []: #todo can trans be [] anyways?
			self._logger.error("still transforms in the SVG %s" % trans)
			simpletransform.applyTransformToPath(trans, csp)
		return csp

	def _get_transforms(self,g):
		root = self.document.getroot()
		trans = [[1,0,0],[0,1,0]]
		while (g != root):
			if 'transform' in g.keys():
				t = g.get('transform')
				t = simpletransform.parseTransform(t)
				trans = simpletransform.composeTransform(t,trans) if trans != [] else t
				self._logger.debug("Found transform: " % trans)
			g = g.getparent()
		return trans
	
	def _parse_curve(self, p, layer, w = None, f = None):
			c = []
			if len(p)==0 : 
				return []
			p = self._transform_csp(p, layer)
			
			### Sort to reduce Rapid distance	
			k = range(1,len(p))
			keys = [0]
			while len(k)>0:
				end = p[keys[-1]][-1][1]
				dist = None
				for i in range(len(k)):
					start = p[k[i]][0][1]
					dist = max(   ( -( ( end[0]-start[0])**2+(end[1]-start[1])**2 ) ,i)	,   dist )
				keys += [k[dist[1]]]
				del k[dist[1]]
				
			#keys = range(1,len(p)) # debug unsorted.
			for k in keys:
				subpath = p[k]
				c += [ [	[subpath[0][1][0],subpath[0][1][1]]   , 'move', 0, 0] ]
				for i in range(1,len(subpath)):
					sp1 = [  [subpath[i-1][j][0], subpath[i-1][j][1]] for j in range(3)]
					sp2 = [  [subpath[i  ][j][0], subpath[i  ][j][1]] for j in range(3)]
					c += biarc(sp1,sp2,0,0) if w==None else biarc(sp1,sp2,-f(w[k][i-1]),-f(w[k][i]))
				c += [ [ [subpath[-1][1][0],subpath[-1][1][1]]  ,'end',0,0] ]

			#self._logger.debug("Curve: " + str(c))
			return c
		
	def _transform_csp(self, csp_, layer, reverse = False):
		self._logger.debug("_transform_csp %s , %s, %s" % (csp_, layer, reverse))
		csp = [  [ [csp_[i][j][0][:],csp_[i][j][1][:],csp_[i][j][2][:]]  for j in range(len(csp_[i])) ]   for i in range(len(csp_)) ]
		for i in xrange(len(csp)):
			for j in xrange(len(csp[i])): 
				for k in xrange(len(csp[i][j])): 
					csp[i][j][k] = self._transform(csp[i][j][k],layer, reverse)
		return csp
	
	def _transform(self, source_point, layer, reverse=False):
		self._logger.debug('_transform %s,%s,%s ' % (source_point, layer, reverse))
		if layer == None :
			layer = self.document.getroot()
		if layer not in self.transform_matrix:
			for i in range(self.layers.index(layer),-1,-1):
				if self.layers[i] in self.orientation_points : 
					break # i will remain after the loop

			if self.layers[i] not in self.orientation_points :
				self._logger.error("No orientation points for '%s' layer!" % layer)
			elif self.layers[i] in self.transform_matrix :
				self.transform_matrix[layer] = self.transform_matrix[self.layers[i]]
			else:
				orientation_layer = self.layers[i]
				points = self.orientation_points[orientation_layer][0]
				if len(points)==2:
					points += [ [ [(points[1][0][1]-points[0][0][1])+points[0][0][0], -(points[1][0][0]-points[0][0][0])+points[0][0][1]], [-(points[1][1][1]-points[0][1][1])+points[0][1][0], points[1][1][0]-points[0][1][0]+points[0][1][1]] ] ]
				if len(points)==3:
					self._logger.debug("Layer '%s' Orientation points: " % orientation_layer.get(_add_ns('label','inkscape')))
					for point in points:
						self._logger.debug(point)
						
					matrix = numpy.array([
								[points[0][0][0], points[0][0][1], 1, 0, 0, 0, 0, 0, 0],
								[0, 0, 0, points[0][0][0], points[0][0][1], 1, 0, 0, 0],
								[0, 0, 0, 0, 0, 0, points[0][0][0], points[0][0][1], 1],
								[points[1][0][0], points[1][0][1], 1, 0, 0, 0, 0, 0, 0],
								[0, 0, 0, points[1][0][0], points[1][0][1], 1, 0, 0, 0],
								[0, 0, 0, 0, 0, 0, points[1][0][0], points[1][0][1], 1],
								[points[2][0][0], points[2][0][1], 1, 0, 0, 0, 0, 0, 0],
								[0, 0, 0, points[2][0][0], points[2][0][1], 1, 0, 0, 0],
								[0, 0, 0, 0, 0, 0, points[2][0][0], points[2][0][1], 1]
							])

					if numpy.linalg.det(matrix)!=0 :
						m = numpy.linalg.solve(matrix,
							numpy.array(
								[[points[0][1][0]], [points[0][1][1]], [1], [points[1][1][0]], [points[1][1][1]], [1], [points[2][1][0]], [points[2][1][1]], [1]]	
										)
							).tolist()
						self.transform_matrix[layer] = [[m[j*3+i][0] for i in range(3)] for j in range(3)]

					else :
						self._logger.error("Orientation points are wrong! (if there are two orientation points they sould not be the same. If there are three orientation points they should not be in a straight line.)")
				else :
					self._logger.error("Orientation points are wrong! (if there are two orientation points they sould not be the same. If there are three orientation points they should not be in a straight line.)")

			self.transform_matrix_reverse[layer] = numpy.linalg.inv(self.transform_matrix[layer]).tolist()		

			
		x,y = source_point[0], source_point[1]
		if not reverse :
			t = self.transform_matrix[layer]
		else :
			t = self.transform_matrix_reverse[layer]
		return [t[0][0]*x+t[0][1]*y+t[0][2], t[1][0]*x+t[1][1]*y+t[1][2]]

################################################################################
###
###		Generate Gcode
###		Generates Gcode on given curve.
###
###		Curve definition [start point, type = {'arc','line','move','end'}, arc center, arc angle, end point, [zstart, zend]]
###
################################################################################
	def _generate_gcode(self, curve, color='#000000'):
		self._logger.info( "_generate_gcode()")
		settings = self.colorParams.get(color, {'intensity': -1, 'feedrate': -1, 'passes': 0, 'pierce_time': 0})

		def c(c):
			# returns gcode for coordinates/parameters
			c = [c[i] if i < len(c) else None for i in range(6)]  # fills missing coordinates/parameters with none
			if c[5] == 0: c[5] = None
			s = [" X", " Y", " Z", " I", " J", " K"]
			r = ''
			for i in range(6):
				if c[i] != None:
					r += s[i] + ("%.4f" % (round(c[i], 4)))  # truncating leads to invalid GCODE ID33
			return r

		if len(curve) == 0: return ""

		self._logger.debug("Curve: " + str(curve))
		g = ""

		lg = 'G00'
		f = "F%s;%s" % (settings['feedrate'], color)
		for i in range(1, len(curve)):
			#	Creating Gcode for curve between s=curve[i-1] and si=curve[i] start at s[0] end at s[4]=si[0]
			s = curve[i - 1]
			si = curve[i]
			feed = f if lg not in ['G01', 'G02', 'G03'] else ''
			if s[1] == 'move':
				g += "G0" + c(si[0]) + "\n" + machine_settings.gcode_before_path_color(color, settings['intensity']) + "\n"
				pt = int(settings['pierce_time'])
				if pt > 0:
					g += "G4P%.3f\n" % (round(pt / 1000.0, 4))
				lg = 'G00'
			elif s[1] == 'end':
				g += machine_settings.gcode_after_path() + "\n"
				lg = 'G00'
			elif s[1] == 'line':
				if lg == "G00": g += "G01 " + feed + "\n"
				g += "G01 " + c(si[0]) + "\n"
				lg = 'G01'
			elif s[1] == 'arc':
				r = [(s[2][0] - s[0][0]), (s[2][1] - s[0][1])]
				if lg == "G00": g += "G01" + feed + "\n"
				if (r[0] ** 2 + r[1] ** 2) > .1:
					r1, r2 = (Point(s[0]) - Point(s[2])), (Point(si[0]) - Point(s[2]))
					if abs(r1.mag() - r2.mag()) < 0.001:
						g += ("G02" if s[3] < 0 else "G03") + c(
							si[0] + [None, (s[2][0] - s[0][0]), (s[2][1] - s[0][1])]) + "\n"
					else:
						r = (r1.mag() + r2.mag()) / 2
						g += ("G02" if s[3] < 0 else "G03") + c(si[0]) + " R%f" % (r) + "\n"
					lg = 'G02'
				else:
					g += "G01" + c(si[0]) + feed + "\n"
					lg = 'G01'
		if si[1] == 'end':
			g += machine_settings.gcode_after_path() + "\n"
		return g

	def export_gcode(self, gcode) :
		if(self.options['noheaders']):
			self.header = ""
			self.footer = "M05\n"
		else:
			self.header = machine_settings.gcode_header
			self.footer = machine_settings.gcode_footer
			self.header += "G21\n\n"
			
		f = open(self.options['directory'] + self.options['file'], "w")
		f.write(self.header + gcode + self.footer)
		f.close()
		self._logger.info( "wrote file: " + self.options['directory'] + self.options['file'])
		
	def calculate_conversion_matrix(self, layer=None) :
		self._logger.info("entering orientations. layer: %s" % layer)
		if layer == None :
			layer = self.document.getroot()
		if layer in self.orientation_points:
			self._logger.error("Active layer already has orientation points! Remove them or select another layer!")
		
		self._logger.info("entering orientations. layer: %s" % layer)

		# translate == ['0', '-917.7043']
		if layer.get("transform") != None :
			self._logger.error('FOUND TRANSFORM: %s ' % layer.get('transform'))
			translate = layer.get("transform").replace("translate(", "").replace(")", "").split(",")
		else :
			translate = [0,0]

		# doc height in pixels (38 mm == 134.64566px)
		h = self._get_document_height()
		doc_height = unittouu(h)
		viewBoxM = self._get_document_viewbox_matrix()
		viewBoxScale = viewBoxM[1][1] # TODO use both coordinates.
		
		self._logger.info("Document height: %s   viewBoxTransform: %s" % (str(doc_height),  viewBoxM))
			
		points = [[100.,0.,0.],[0.,0.,0.],[0.,100.,0.]]
		orientation_scale = (self.options['svgDPI'] / 25.4) / viewBoxScale # 3.5433070660 @ 90dpi
		points = points[:2]

		self._logger.info("using orientation scale %s, i=%s" % (orientation_scale, points))
		opoints = []
		for i in points :
			# X == Correct!
			# si == x,y coordinate in px
			# si have correct coordinates
			# if layer have any tranform it will be in translate so lets add that
			si = [i[0]*orientation_scale, (i[1]*orientation_scale)+float(translate[1])]
			
			#TODO avoid conversion to cubicsuperpath, calculate p0 and p1 directly
			#point[0] = self._apply_transforms(node,cubicsuperpath.parsePath(node.get("d")))[0][0][1]
			d = 'm %s,%s 2.9375,-6.343750000001 0.8125,1.90625 6.843748640396,-6.84374864039 0,0 0.6875,0.6875 -6.84375,6.84375 1.90625,0.812500000001 z z' % (si[0], -si[1]+doc_height)
			csp = cubicsuperpath.parsePath(d)
			#self._logger.info('### CSP %s' % csp)
			### CSP [[[[0.0, 1413.42519685], [0.0, 1413.42519685], [0.0, 1413.42519685]], [[2.9375, 1407.081446849999], [2.9375, 1407.081446849999], [2.9375, 1407.081446849999]], [[3.75, 1408.987696849999], [3.75, 1408.987696849999], [3.75, 1408.987696849999]], [[10.593748640396, 1402.143948209609], [10.593748640396, 1402.143948209609], [10.593748640396, 1402.143948209609]], [[10.593748640396, 1402.143948209609], [10.593748640396, 1402.143948209609], [10.593748640396, 1402.143948209609]], [[11.281248640396, 1402.831448209609], [11.281248640396, 1402.831448209609], [11.281248640396, 1402.831448209609]], [[4.437498640396001, 1409.675198209609], [4.437498640396001, 1409.675198209609], [4.437498640396001, 1409.675198209609]], [[6.343748640396001, 1410.48769820961], [6.343748640396001, 1410.48769820961], [6.343748640396001, 1410.48769820961]], [[0.0, 1413.42519685], [0.0, 1413.42519685], [0.0, 1413.42519685]], [[0.0, 1413.42519685], [0.0, 1413.42519685], [0.0, 1413.42519685]]]]   
			
			p0 = csp[0][0][1]
			p1 = [i[0],i[1],i[2]]
			point = [p0,p1]
			opoints += [point]
			
		if opoints != None :
			self.orientation_points[layer] = self.orientation_points[layer]+[opoints[:]] if layer in self.orientation_points else [opoints[:]]
			self._logger.info("Generated orientation points in '%s' layer: %s" % (layer.get(_add_ns('label','inkscape')), opoints))
		else :
			self._logger.error("Warning! Found bad orientation points in '%s' layer. Resulting Gcode could be corrupt!") % layer.get(_add_ns('label','inkscape'))

	def _get_document_width(self):
		width = self.document.getroot().get('width')
		if(width == None):
			vbox = self.document.getroot().get('viewBox')
			if(vbox != None ):
				self._logger.info("width property not set in root node, fetching from viewBox attribute")
				parts = vbox.split(' ')
				if(len(parts) == 4):
					width = parts[2]

		if(width == "100%"):
			width = 744.09 # 210mm @ 90dpi
			self._logger.info("Overriding width from 100 percents to %s" % width)

		if(width == None):
			width = 744.09 # 210mm @ 90dpi
			self._logger.info("width not set. Assuming width is %s" % width)
		return str(width)

	def _get_document_height(self):
		height = self.document.getroot().get('height')
		if(height == None):
			self._logger.info("height property not set in root node, fetching from viewBox attribute")
			vbox = self.document.getroot().get('viewBox')
			if(vbox != None ):
				parts = vbox.split(' ')
				if(len(parts) == 4):
					height = parts[3]

		if(height == "100%"):
			height = 1052.3622047 # 297mm @ 90dpi
			self._logger.info("Overriding height from 100 percents to %s" % height)

		if(height == None):
			height = 1052.3622047 # 297mm @ 90dpi
			self._logger.info("Height not set. Assuming height is %s" % height)
		return str(height)

	def _get_document_viewbox_matrix(self):
		vbox = self.document.getroot().get('viewBox')
		if(vbox != None ):
			self._logger.info("Found viewbox attribute", vbox)
			widthPx = unittouu(self._get_document_width())
			heightPx = unittouu(self._get_document_height())
			parts = vbox.split(' ')
			if(len(parts) == 4):
				offsetVBoxX = float(parts[0])
				offsetVBoxY = float(parts[1])
				widthVBox = float(parts[2]) - float(parts[0])
				heightVBox = float(parts[3]) - float(parts[1])

				fx = widthPx / widthVBox
				fy = heightPx / heightVBox
				dx = offsetVBoxX * fx
				dy = offsetVBoxY * fy
				return [[fx,0,0],[0,fy,0], [dx,dy,1]]

		return [[1,0,0],[0,1,0], [0,0,1]]

