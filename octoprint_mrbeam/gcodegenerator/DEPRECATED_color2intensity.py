# To change this license header, choose License Headers in Project Properties.
# To change this template file, choose Tools | Templates
# and open the template in the editor.

__author__="teja"
__date__ ="$Dec 11, 2014 9:46:51 PM$"

import webcolors

def color2intensity(colorString, minIntensity=0, maxIntensity=1000):
	if colorString == "" or colorString == "none": 
		return minIntensity
	else:
		rgb = webcolors.hex_to_rgb(colorString)
		gray = 0.2989 * rgb[0] + 0.5870 * rgb[1] + 0.1140 * rgb[2]
		intensity = (1-gray/255) * (maxIntensity-minIntensity) + minIntensity
		return intensity


if __name__ == "__main__":
    print "Hello World"
