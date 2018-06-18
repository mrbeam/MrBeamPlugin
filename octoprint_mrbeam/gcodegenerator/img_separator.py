# coding=utf-8
#!/usr/bin/env python

"""
img_separator.py
bitmap separation for speed optimized raster processing

Copyright (C) 2018 Mr Beam Lasers GmbH
Author: Teja Philipp, teja@mr-beam.org

"""
import optparse
import logging
from PIL import Image
import cv2
import numpy as np
import os.path

(cvMajor, cvMinor) = cv2.__version__.split('.')[:2]
isCV2 = cvMajor == "2"

class ImageSeparator():

	def __init__( self):
		self.log = logging.getLogger(self.__class__.__name__)

	def separate(self, img, threshold=255, callback=None):
		"""
		Separates img (a Pillow Image object) according to some magic into a list of img objects. 
		Afterwards all parts merged togehter are equal to the input image.
		Supports so far only Grayscale images (mode 'L')
		Arguments:
		img -- a Pillow Image object
		
		Keyword arguments:
		threshold -- all pixels brighter than this threshold are used for separation
		callback -- instead of waiting for the list to return, a callback(img, iteration) can be used to save memory
		"""
		(width, height) = img.size
		
		x_limit = [0] * height # [0, 0, 0, .... ]
		iteration = 0
		parts = []
		while(True):
			(x_limit, separation) = self._separate_partial(img, start_list=x_limit, threshold=threshold)
			if(separation == None):
				return parts
			
			if(callback != None):
				callback(separation, iteration)
			else:
				parts.append({'i': separation, 'x': 0, 'y':0})
				
			all_done = all(l >= width for l in x_limit)
			if(all_done):
				return parts
			iteration += 1
			
	def separate_contours(self, img, threshold=255, callback=None):
		w,h = img.size
		monochrome = np.array(img, dtype=np.uint8) # should be grayscale already
		maxValue = 255
		th, filtered = cv2.threshold(monochrome, threshold-1, maxValue, cv2.THRESH_BINARY);
		#cv2.imwrite("/tmp/separate_contours_1_threshold.png", filtered)
		if(isCV2):
			contours, hierarchy = cv2.findContours(filtered.copy(), cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)
		else:
			i, contours, hierarchy = cv2.findContours(filtered, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)

		parts = [] # array of dicts {'i': imgdata, 'x': x_offset, 'y': y_offset}
		maxArea = (w-1)*(h-1)
		for i in range(len(contours)):
			area = cv2.contourArea(contours[i])
			if(area < maxArea):
				# get bbox
				cnt_x,cnt_y,cnt_w,cnt_h = cv2.boundingRect(contours[i])
				
				# create mask
				mask = cv2.bitwise_not(np.zeros((h, w), np.uint8))
				cv2.drawContours(mask, contours, i, (0), -1) 
				#cv2.imwrite("/tmp/separate_contours_2_mask_"+str(i)+".png", mask)

				# apply mask to original image
				separation_cv = cv2.bitwise_or(monochrome, mask)
				
				cropped = separation_cv[cnt_y:cnt_y+cnt_h, cnt_x:cnt_x+cnt_w]
				separation = Image.fromarray(np.uint8(cropped))

				data = {'i': separation, 'x': cnt_x, 'y':h-(cnt_y+cnt_h)} # x, y are marking lower left of the contour in pixels with origin 0,0 at bottom left
				# collect results
				if(callback != None):
					callback(data, i)
				else:
					parts.append(data)
			
		return parts
	
	def _separate_partial(self, img, start_list, threshold=255):

		(width, height) = img.size
		pxArray = img.load()
		
		# iterate line by line
		tmp = None	
		for row in range(0, height):
			x = self._find_first_gap_in_row(pxArray, width, height, start_list[row], row, threshold=threshold)
			if(x < width):
				if(tmp == None): # new separated image
					tmp = Image.new("L", (width, height), "white")
				box = (start_list[row], row, x, row+1)
				region = img.crop(box)
				tmp.paste(region, box)
										
			start_list[row] = x
		return (start_list, tmp)


	def _find_first_gap_in_row(self, pxArray, w, h, x, y, threshold=255):
		skip = True # assume white pixel at the beginning
		
		for i in range(x, w):
			px = pxArray[i, y]
				
			brightness = px	
			if(brightness < threshold): # "rising edge" -> colored pixel
				skip = False

			if(skip == False):
				if(brightness >= threshold): # "falling edge" -> white pixel again
					return i
		
		return w


if __name__ == "__main__":
	opts = optparse.OptionParser(usage="usage: %prog [options] <imagefile>")
	opts.add_option("-t",   "--threshold", type="int", default="255", help="intensity for white (skipped) pixels, default 255", dest="threshold")
	
	(options, args) = opts.parse_args()
	path = args[0]
	filename, _ = os.path.splitext(path)
	output_name = filename + "_"

	sepp = ImageSeparator()

	img = Image.open(path)
	img = img.convert('L')
	
	def write_to_file_callback(part, iteration):
		print part
		if(part != None):
			part.save(output_name + "{:0>3}".format(iteration) + ".png", "PNG")

	#sepp.separate(img, callback=write_to_file_callback)
	sepp.separate_contours(img, callback=write_to_file_callback)

