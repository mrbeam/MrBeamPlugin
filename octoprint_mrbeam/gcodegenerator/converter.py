import logging
#import sys
#import copy
import re
import os
from biarc import biarc
import machine_settings

import simplestyle
import simplepath
import simpletransform
import cubicsuperpath


from lxml import etree
#logging.basicConfig
#logging.shutdown()
#reload(logging)

#a dictionary of all of the xmlns prefixes in a standard inkscape doc
NSS = {
u'sodipodi' :u'http://sodipodi.sourceforge.net/DTD/sodipodi-0.dtd',
u'cc'	   :u'http://creativecommons.org/ns#',
u'ccOLD'	:u'http://web.resource.org/cc/',
u'svg'	  :u'http://www.w3.org/2000/svg',
u'dc'	   :u'http://purl.org/dc/elements/1.1/',
u'rdf'	  :u'http://www.w3.org/1999/02/22-rdf-syntax-ns#',
u'inkscape' :u'http://www.inkscape.org/namespaces/inkscape',
u'xlink'	:u'http://www.w3.org/1999/xlink',
u'xml'	  :u'http://www.w3.org/XML/1998/namespace'
}

def addNS(tag, ns=None):
	val = tag
	if ns!=None and len(ns)>0 and NSS.has_key(ns) and len(tag)>0 and tag[0]!='{':
		val = "{%s}%s" % (NSS[ns], tag)
	return val

class Converter():


	defaults = {
		"directory": None,
		"file": None,
		"svgDPI": 90,
		"noheaders": "false",
#		"engraving_laser_speed": 300,
#		"laser_intensity": 500,
#		"pierce_time": 0,

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
		#logging.shutdown()
		#reload(logging)
		#self.transform_matrix = {}
		#self.transform_matrix_reverse = {}

		
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

		#self.effect(on_progress, on_progress_args, on_progress_kwargs)
		options = self.options
		options['doc_root'] = self.document.getroot()

		# Get all Gcodetools data from the scene.
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
		
#		def get_boundaries(points):
#			minx,miny,maxx,maxy=None,None,None,None
#			out=[[],[],[],[]]
#			for p in points:
#				if minx==p[0]:
#					out[0]+=[p]
#				if minx==None or p[0]<minx: 
#					minx=p[0]
#					out[0]=[p]
#
#				if miny==p[1]:
#					out[1]+=[p]
#				if miny==None or p[1]<miny: 
#					miny=p[1]
#					out[1]=[p]
#
#				if maxx==p[0]:
#					out[2]+=[p]
#				if maxx==None or p[0]>maxx: 
#					maxx=p[0]
#					out[2]=[p]
#
#				if maxy==p[1]:
#					out[3]+=[p]
#				if maxy==None or p[1]>maxy: 
#					maxy=p[1]
#					out[3]=[p]
#			return out


#		def remove_duplicates(points):
#			i=0		
#			out=[]
#			for p in points:
#				for j in xrange(i,len(points)):
#					if p==points[j]: points[j]=[None,None]	
#				if p!=[None,None]: out+=[p]
#			i+=1
#			return(out)
	
	
#		def get_way_len(points):
#			l=0
#			for i in xrange(1,len(points)):
#				l+=math.sqrt((points[i][0]-points[i-1][0])**2 + (points[i][1]-points[i-1][1])**2)
#			return l

	
#		def sort_dxfpoints(points):
#			points=remove_duplicates(points)
#
#			ways=[
#					# l=0, d=1, r=2, u=3
#			 [3,0], # ul
#			 [3,2], # ur
#			 [1,0], # dl
#			 [1,2], # dr
#			 [0,3], # lu
#			 [0,1], # ld
#			 [2,3], # ru
#			 [2,1], # rd
#			]
#
#			minimal_way=[]
#			minimal_len=None
#			minimal_way_type=None
#			for w in ways:
#				tpoints=points[:]
#				cw=[]
#				for j in xrange(0,len(points)):
#					p=get_boundaries(get_boundaries(tpoints)[w[0]])[w[1]]
#					tpoints.remove(p[0])
#					cw+=p
#				curlen = get_way_len(cw)
#				if minimal_len==None or curlen < minimal_len: 
#					minimal_len=curlen
#					minimal_way=cw
#					minimal_way_type=w
#			
#			return minimal_way


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
						data = imgNode.get(inkex.addNS('href', 'xlink'))
						
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
				self._logger.info("recursive search: %i - %s"  %(len(items), g.get("id")))
			for i in items:
				if i.tag == addNS("g",'svg') and i.get(addNS('groupmode','inkscape')) == 'layer':
					styles = simplestyle.parseStyle(i.get("style", ''))
					if "display" not in styles or styles["display"] != 'none':
						self.layers += [i]
						recursive_search(i,i)
					else:
						self._logger.info("Skipping hidden layer: '%s'" % i.get('id', "?") 	)
				else:
					# path
					if i.tag == addNS('path','svg'):					
						self._handle_node(i, layer)

					# rect
					elif i.tag == addNS( 'rect', 'svg' ) or i.tag == 'rect':

						# Manually transform
						#
						#    <rect x="X" y="Y" width="W" height="H"/>
						# into
						#    <path d="MX,Y lW,0 l0,H l-W,0 z"/>
						#
						# I.e., explicitly draw three sides of the rectangle and the
						# fourth side implicitly

						# Create a path with the outline of the rectangle
						x = float( i.get( 'x','0' ) )
						y = float( i.get( 'y','0' ) )
						if ( not x ) or ( not y ):
							pass
						w = float( i.get( 'width', '0' ) )
						h = float( i.get( 'height', '0' ) )
						a = []
						a.append( ['M ', [x, y]] )
						a.append( [' l ', [w, 0]] )
						a.append( [' l ', [0, h]] )
						a.append( [' l ', [-w, 0]] )
						a.append( [' Z', []] )
						d = simplepath.formatPath( a )
						i.set("d", d)
						
						self._handle_node(i, layer)
						
					# line
					elif i.tag == addNS( 'line', 'svg' ) or i.tag == 'line':

						# Convert
						#
						#   <line x1="X1" y1="Y1" x2="X2" y2="Y2/>
						# to
						#   <path d="MX1,Y1 LX2,Y2"/>

						x1 = float( i.get( 'x1' ) )
						y1 = float( i.get( 'y1' ) )
						x2 = float( i.get( 'x2' ) )
						y2 = float( i.get( 'y2' ) )
						if ( not x1 ) or ( not y1 ) or ( not x2 ) or ( not y2 ):
							pass
						a = []
						a.append( ['M ', [x1, y1]] )
						a.append( [' L ', [x2, y2]] )
						d = simplepath.formatPath( a )
						i.set("d",d)
						
						self._handle_node(i, layer)

					# polygon
					elif i.tag == addNS( 'polygon', 'svg' ) or i.tag == 'polygon' \
					or i.tag == addNS( 'polyline', 'svg' ) or i.tag == 'polyline':
						# Convert
						#
						#  <polygon points="x1,y1 x2,y2 x3,y3 [...]"/>
						#  <polyline points="x1,y1 x2,y2 x3,y3 [...]"/>
						# to
						#   <path d="Mx1,y1 Lx2,y2 Lx3,y3 [...] Z"/>
						#
						# Note: we ignore polygons with no points

						pl = i.get( 'points', '' ).strip()
						if pl == '':
							pass

						pa = pl.split()
						d = "".join( ["M " + pa[j] if j == 0 else " L " + pa[j] for j in range( 0, len( pa ) )] )
						d += " Z"
						i.set("d", d)

						self._handle_node(i, layer)
					
					# circle / ellipse
					elif i.tag == addNS( 'ellipse', 'svg' ) or \
						i.tag == 'ellipse' or \
						i.tag == addNS( 'circle', 'svg' ) or \
						i.tag == 'circle':

							# Convert circles and ellipses to a path with two 180 degree arcs.
							# In general (an ellipse), we convert
							#
							#   <ellipse rx="RX" ry="RY" cx="X" cy="Y"/>
							# to
							#   <path d="MX1,CY A RX,RY 0 1 0 X2,CY A RX,RY 0 1 0 X1,CY"/>
							#
							# where
							#   X1 = CX - RX
							#   X2 = CX + RX
							#
							# Note: ellipses or circles with a radius attribute of value 0 are ignored

							if i.tag == addNS( 'ellipse', 'svg' ) or i.tag == 'ellipse':
								rx = float( i.get( 'rx', '0' ) )
								ry = float( i.get( 'ry', '0' ) )
							else:
								rx = float( i.get( 'r', '0' ) )
								ry = rx
							if rx == 0 or ry == 0:
								pass

							cx = float( i.get( 'cx', '0' ) )
							cy = float( i.get( 'cy', '0' ) )
							x1 = cx - rx
							x2 = cx + rx
							d = 'M %f,%f ' % ( x1, cy ) + \
								'A %f,%f ' % ( rx, ry ) + \
								'0 1 0 %f,%f ' % ( x2, cy ) + \
								'A %f,%f ' % ( rx, ry ) + \
								'0 1 0 %f,%f' % ( x1, cy )
							i.set("d", d)
							
							self._handle_node(i, layer)

					# image
					elif i.tag == addNS('image','svg'):
						x = i.get('x')
						y = i.get('y')						
						if x == None:
							x = "0"
						if y == None:
							y = "0"
					
						self._logger.info("added image " + i.get("width") + 'x' + i.get("height") + "@" + x+","+y)
						self._handle_image(i, layer)
						
					
					# group
					elif i.tag == addNS("g",'svg'):
						recursive_search(i,layer)
				
					else :
						self._logger.info("ignoring not supported tag %s" % i.tag)
						self._logger.debug("ignoring not supported tag: %s \n %s \n\n" % (i.tag, etree.tostring(i)))
					
		recursive_search(self.document.getroot(), self.document.getroot())
		self._logger.info("self.layers: %i" % len(self.layers))
		self._logger.info("self.paths: %i" % len(self.paths))




	def parse(self,file=None):
		self._logger.info("### parsing %s" % self.svg_file)
		try:
			stream = open(self.svg_file,'r')
		except:
			self._logger.error("unable to read %s" % self.svg_file)
		self._logger.info("### opened %s" % self.svg_file)
		p = etree.XMLParser(huge_tree=True)
		self._logger.info("### lxml instance %s" % self.svg_file)
		#p.useGlobalPythonLog()
		self._logger.info("### lxml logging %s" % self.svg_file)
		self.document = etree.parse(stream, parser=p)
		#self.original_document = copy.deepcopy(self.document)
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
#					l1 = biarc(sp1,sp2,0,0) if w==None else biarc(sp1,sp2,-f(w[k][i-1]),-f(w[k][i]))
#					self._logger.debug((-f(w[k][i-1]),-f(w[k][i]), [i1[5] for i1 in l1]) )
				c += [ [ [subpath[-1][1][0],subpath[-1][1][1]]  ,'end',0,0] ]

			#self._logger.debug("Curve: " + str(c))
			return c
		
	def _transform_csp(self, csp_, layer, reverse = False):
		self._logger.debug("_transform_csp %s , %s, %s" % (csp_, layer, reverse))
		csp = [  [ [csp_[i][j][0][:],csp_[i][j][1][:],csp_[i][j][2][:]]  for j in range(len(csp_[i])) ]   for i in range(len(csp_)) ]
#		for i in xrange(len(csp)):
#			for j in xrange(len(csp[i])): 
#				for k in xrange(len(csp[i][j])): 
#					csp[i][j][k] = self._transform(csp[i][j][k],layer, reverse)
		return csp
	
	def _transform(self, source_point, layer, reverse=False):
		if layer == None :
			layer = self.document.getroot()
		if layer not in self.transform_matrix:
			for i in range(self.layers.index(layer),-1,-1):
				#if self.layers[i] in self.orientation_points : 
				#	break

				self._logger.debug(str(self.layers))
				self._logger.debug(str("I: " + str(i)))
				self._logger.debug("Transform: " + str(self.layers[i]))
#				if self.layers[i] not in self.orientation_points :
#					self._logger.error("Orientation points for '%s' layer have not been found! Please add orientation points using Orientation tab!") % layer.get(inkex.addNS('label','inkscape'))
#				elif self.layers[i] in self.transform_matrix :
#					self.transform_matrix[layer] = self.transform_matrix[self.layers[i]]
#				else :
#					orientation_layer = self.layers[i]
#					if len(self.orientation_points[orientation_layer])>1 : 
#						self._logger.error("There are more than one orientation point groups in '%s' layer") % orientation_layer.get(inkex.addNS('label','inkscape'))
#					points = self.orientation_points[orientation_layer][0]
#					if len(points)==2:
#						points += [ [ [(points[1][0][1]-points[0][0][1])+points[0][0][0], -(points[1][0][0]-points[0][0][0])+points[0][0][1]], [-(points[1][1][1]-points[0][1][1])+points[0][1][0], points[1][1][0]-points[0][1][0]+points[0][1][1]] ] ]
#					if len(points)==3:
#						self._logger.debug("Layer '%s' Orientation points: " % orientation_layer.get(inkex.addNS('label','inkscape')))
#						for point in points:
#							self._logger.debug(point)
#						#	Zcoordinates definition taken from Orientatnion point 1 and 2 
#						#self.Zcoordinates[layer] = [max(points[0][1][2],points[1][1][2]), min(points[0][1][2],points[1][1][2])]
#						matrix = numpy.array([
#									[points[0][0][0], points[0][0][1], 1, 0, 0, 0, 0, 0, 0],
#									[0, 0, 0, points[0][0][0], points[0][0][1], 1, 0, 0, 0],
#									[0, 0, 0, 0, 0, 0, points[0][0][0], points[0][0][1], 1],
#									[points[1][0][0], points[1][0][1], 1, 0, 0, 0, 0, 0, 0],
#									[0, 0, 0, points[1][0][0], points[1][0][1], 1, 0, 0, 0],
#									[0, 0, 0, 0, 0, 0, points[1][0][0], points[1][0][1], 1],
#									[points[2][0][0], points[2][0][1], 1, 0, 0, 0, 0, 0, 0],
#									[0, 0, 0, points[2][0][0], points[2][0][1], 1, 0, 0, 0],
#									[0, 0, 0, 0, 0, 0, points[2][0][0], points[2][0][1], 1]
#								])
#
#						if numpy.linalg.det(matrix)!=0 :
#							m = numpy.linalg.solve(matrix,
#								numpy.array(
#									[[points[0][1][0]], [points[0][1][1]], [1], [points[1][1][0]], [points[1][1][1]], [1], [points[2][1][0]], [points[2][1][1]], [1]]	
#											)
#								).tolist()
#							self.transform_matrix[layer] = [[m[j*3+i][0] for i in range(3)] for j in range(3)]
#
#						else :
#							self._logger.error("Orientation points are wrong! (if there are two orientation points they sould not be the same. If there are three orientation points they should not be in a straight line.)")
#					else :
#						self._logger.error("Orientation points are wrong! (if there are two orientation points they sould not be the same. If there are three orientation points they should not be in a straight line.)")

			#	self.transform_matrix_reverse[layer] = numpy.linalg.inv(self.transform_matrix[layer]).tolist()		
				self._logger.debug("\n Layer '%s' transformation matrixes:" % layer.get(addNS('label','inkscape')) )
				self._logger.debug(self.transform_matrix)
				self._logger.debug(self.transform_matrix_reverse)
				#self._logger.debug("scalematrix", self.transform_matrix)
				#self._logger.debug("revmatrix", self.transform_matrix_reverse)

			
		x,y = source_point[0], source_point[1]
#		if not reverse :
#			t = self.transform_matrix[layer]
#		else :
#			t = self.transform_matrix_reverse[layer]
#		return [t[0][0]*x+t[0][1]*y+t[0][2], t[1][0]*x+t[1][1]*y+t[1][2]]
		return [x, y]

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
		f = "F%s;%s" % (settings['intensity'], color)
		for i in range(1, len(curve)):
			#	Creating Gcode for curve between s=curve[i-1] and si=curve[i] start at s[0] end at s[4]=si[0]
			s = curve[i - 1]
			si = curve[i]
			feed = f if lg not in ['G01', 'G02', 'G03'] else ''
			if s[1] == 'move':
				g += "G0" + c(si[0]) + "\n" + machine_settings.gcode_before_path_color(color) + "\n"
				if settings['pierce_time'] > 0:
					pt = int(settings['pierce_time'])
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
					r1, r2 = (P(s[0]) - P(s[2])), (P(si[0]) - P(s[2]))
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