# encoding: utf-8

###########################################################################################################
#
#
#	Reporter Plugin: Blackness
#
#	Read the docs:
#	https://github.com/schriftgestalt/GlyphsSDK/tree/master/Python%20Templates/Reporter
#
#
###########################################################################################################

import copy
import math
import objc
from fontTools.pens.areaPen import AreaPen
from Foundation import *
from GlyphsApp import *
from GlyphsApp.plugins import *


class copyLayer:
	'''A wrapper class to copy a layer, and delete it after some operations.'''

	NEW_LAYER_NAME = '__NEW_TEMP_LAYER'

	@objc.python_method
	def __init__(self, layer: GSLayer):
		self.layer = layer
		self.newLayer = None

	@objc.python_method
	def __enter__(self):
		self.newLayer = GSLayer()
		self.newLayer.name = self.NEW_LAYER_NAME
		self.newLayer.associatedMasterId = self.layer.master.id
		self.layer.parent.layers.append(self.newLayer)
		for shape in self.layer.shapes:
			self.newLayer.shapes.append(copy.deepcopy(shape))
		return self.newLayer

	@objc.python_method
	def __exit__(self, exc_type, exc_val, exc_tb):
		del(self.layer.parent.layers[-1])


class Blackness(ReporterPlugin):

	@objc.python_method
	def settings(self):
		self.menuName = Glyphs.localize({
			'en': u'Blackness',
			'zh': u'灰度',
		})
		# self.generalContextMenus = [{
		# 	'name': Glyphs.localize({
		# 		'en': u'Use Bounding Box',
		# 		'zh': u'使用边界框',
		# 	}),
		# }]

	@objc.python_method
	def foreground(self, layer):
		self.draw(layer)

	@objc.python_method
	def inactiveLayerForeground(self, layer):
		self.draw(layer)

	@objc.python_method
	def draw(self, layer):
		# TODO: bbox condition
		ascender = self.ascender(layer)
		descender = self.descender(layer)
		width = layer.width
		height = ascender - descender
		# Use sqrt to rescale the blackness
		blackness = math.sqrt(self.area(layer) / (width * height))
		# 0 = black, 1 = white
		NSColor.colorWithWhite_alpha_(1 - blackness, 1.0).set()
		NSBezierPath.fillRect_(((0, descender), (width, height)))

	@objc.python_method
	def ascender(self, layer):
		master = layer.master
		ascender = master.ascender
		for param in filter(lambda x: x.name == 'ascender', master.customParameters):
			split = param.value.split(':')
			if len(split) == 1:
				ascender = float(split[0])
			else:
				if split[0].strip() == 'han':
					ascender = float(split[1])
		return ascender

	@objc.python_method
	def descender(self, layer):
		master = layer.master
		descender = master.descender
		for param in filter(lambda x: x.name == 'descender', master.customParameters):
			split = param.value.split(':')
			if len(split) == 1:
				descender = float(split[0])
			else:
				if split[0].strip() == 'han':
					descender = float(split[1])
		return descender

	@objc.python_method
	def area(self, layer: GSLayer) -> float:
		if not layer.shapes:
			return 0.0
		with copyLayer(layer) as newLayer:
			newLayer.decomposeComponents()
			newLayer.removeOverlap()
			pen = AreaPen()
			self.pathsToPen(pen, newLayer.paths)
		return abs(pen.value)

	@objc.python_method
	def pathsToPen(self, pen, paths):
		'''Convert Bezier paths to a Pen. The `pen` will be modified afterwards.'''
		for path in paths:
			if path.closed:
				pen.moveTo(path.nodes[-1].position)
				curve = []
				for node in path.nodes:
					if node.type == LINE:
						pen.lineTo(node.position)
					elif node.type == CURVE:
						curve.append(node.position)
						pen.curveTo(*curve)
						curve.clear()
					elif node.type == OFFCURVE:
						curve.append(node.position)
				pen.endPath()

	@objc.python_method
	def __file__(self):
		return __file__
