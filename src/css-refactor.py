#!/usr/bin/env python
# -*- coding:utf-8 -*-

"""
first, merge the contents of identical selectors
then, merge any 2+ sub-properties into their common parent
--oocss
	# Ref: https://github.com/stubbornella/oocss/wiki
	identify declarations that would benefit from object-oriented css:
		1. Separate structure from skin
		2. Separate container and content
"""

import sys
from itertools import chain
from collections import defaultdict
from optparse import OptionParser

import parse as cssparse
from parse import Rule, Sels, Decls, Decl, Ident


def flatten(l): return list(chain.from_iterable(l))

class Inherit_(Ident):
	def __init__(self):
		super(self.__class__, self).__init__('inherit')

class Auto_(Ident):
	def __init__(self):
		super(self.__class__, self).__init__('auto')

class Normal_(Ident):
	def __init__(self):
		super(self.__class__, self).__init__('normal')

Inherit = Inherit_()
Auto = Auto_()
Normal = Normal_()

class Background:
	def __init__(self): pass

class Border:
	def __init__(self): pass

class Box:
	"""Box parent properties require exactly 4 child values"""
	def __init__(self, property_):
		self.property = property_

class Font:
	def __init__(self): pass

class ListStyle:
	def __init__(self): pass

PROPERTIES = {
	# NOTE: default values, anywhere, may be omitted if they are the default

	'background'		: (False, Background(),
		[
			'background-color',
			'background-image',
			'background-repeat',
			'background-attachment',
			'background-position',
		]),
	'background-color'	: (False, None, []),
	'background-image'	: (False, None, []),
	'background-repeat'	: (False, None, []),
	'background-attachment'	: (False, None, []),

	'border'		: (False, Border(),
		[
			'border-width',
			'border-style',
			'border-color',
		]),
	'border-width'		: (False, Box('border-width'),
		[
			'border-top-width',
			'border-right-width',
			'border-bottom-width',
			'border-left-width',
		]),
	'border-top-width'	: (False, None, []),
	'border-right-width'	: (False, None, []),
	'border-bottom-width'	: (False, None, []),
	'border-left-width'	: (False, None, []),
	'border-style'		: (False, Box('border-style'),
		[
			'border-top-style',
			'border-right-style',
			'border-bottom-style',
			'border-left-style',
		]),
	'border-top-style'	: (False, None, []),
	'border-right-style' 	: (False, None, []),
	'border-bottom-style'	: (False, None, []),
	'border-left-style'	: (False, None, []),
	'border-color' 		: (False, Box('border-color'),
		[
			'border-top-color',
			'border-right-color',
			'border-bottom-color',
			'border-left-color',
		]),
	'border-top-color'	: (False, None, []),
	'border-right-color'	: (False, None, []),
	'border-bottom-color'	: (False, None, []),
	'border-left-color'	: (False, None, []),

	'font'			: (True, Font(),
		[
			'font-style',
			'font-variant',
			'font-weight',
			'font-size',
			'line-height',
			'font-family',
		]),
	'font-style'		: (True, Normal,  []),
	'font-variant'		: (True, Normal,  []),
	'font-weight'		: (True, Normal,  []),
	'font-size'		: (True, Inherit, []),
	'line-height'		: (True, Inherit, []),
	'font-family'		: (True, Inherit, []),

	'margin'		: (False, Box('margin'),
		[
			'margin-top',
			'margin-right',
			'margin-bottom',
			'margin-left',
		]),
	'margin-top'		: (False, Auto, []),
	'margin-right'		: (False, Auto, []),
	'margin-bottom'		: (False, Auto, []),
	'margin-left'		: (False, Auto, []),

	'padding'		: (False, Box('padding'),
		[
			'padding-top',
			'padding-right',
			'padding-bottom',
			'padding-left',
		]),
	'padding-top'		: (False, Auto, []),
	'padding-right'		: (False, Auto, []),
	'padding-bottom'	: (False, Auto, []),
	'padding-left'		: (False, Auto, []),

	'list-style'		: (True, ListStyle(),
		[
			'list-style-type',
			'list-style-position',
			'list-style-image',
		]),
	'list-style-type'	: (True, Inherit, []),
	'list-style-position'	: (True, Inherit, []),
	'list-style-image'	: (True, Inherit, []),

}

# reverse lookup
PARENT = dict(flatten([[(child, prop) for child in children] for
		prop,(inherited,default,children) in PROPERTIES.items()]))

def properties_merge(parent, decl):
	"""given a parent property string and a list of child decls,
	generate the equivalent combined Decl for the parent"""
	global PROPERTIES
	if len(decl) < 2:
		return None # don't bother merging < 2 children
	inherited, merger, children = PROPERTIES[parent]
	prop = dict((d.propertylow, d) for d in decl)
	vals = []
	for c in children:
		if c in prop:
			v = prop[c].values
			vals.extend(v)
		else:
			inherit, default, _ = PROPERTIES[c]
			if inherit:
				pass # value can be omitted
			elif default:
				vals.append(default)
			else:
				# if the value is not present, does not inherit...
				# and has no automatic default we cannot produce an
				# equivalent parent Decl, bail
				return None
	if len(vals) == 4 and isinstance(merger, Box):
		# "If one or more of the values are not present, the value for a missing side is taken
		# from the opposite side that is present. If only one value is listed, it applies to all sides."
		# Ref: http://www.blooberry.com/indexdot/css/properties/padding/padding.htm
		#print '%s == %s: %s' % (vals[0], vals[1], vals[0] == vals[1])
		if vals[0] == vals[1] and vals[0] == vals[2] and vals[0] == vals[3]:
			# in the box model you've got four sides; if 4 identical child values exist
			# then it must be border/padding/margin and we can reduce to 1
			vals = vals[:1]
		elif vals[1] == vals[3]:
			# if the left and right values are equal we can omit the right side
			vals = vals[:3]
	if not vals:
		return None # couldn't merge
	return Decl(parent, vals)

def decls_property_combine(block):
	# merge decl based on property parents
	prop = defaultdict(list)
	parents = defaultdict(list)
	for decl in block.decl:
		prop[decl.property].append(decl)
		if decl.property in PARENT:
			parent = PARENT[decl.property]
			if parent:
				parents[parent].append(decl)
	if len(prop) != len(block.decl):
		# 1+ duplicate properties, go no further
		return block
	# now go by parents...
	for parent, decls in parents.iteritems():
		if parent in prop:
			# parent exists in the decl also; skip it for now
			continue
		merged = properties_merge(parent, decls)
		if merged:
			# remove merged children from prop
			for d in decls:
				del prop[d.property]
			# add new parent
			prop[merged.property].append(merged)
			#print 'decls_property_combine merged:', merged.format(), merged
	block.decl = [v[0] for v in prop.values()]
	#print 'decls_property_combine block:', block
	return block 

def decls_find_duplicate_properties(doc):
	"""
	not so easy; there are browser hacks out there that require this. be smarter.
	"""
	for r in doc.rules:
		decls = r.decls.decl
		d = dict([(x.property, x.values) for x in decls])
		if len(d) != len(decls):
			yield (r, len(decls) - len(d))

def selectors_merge(doc):
	"""
	for each unique selector:
		merge all specified decls
	this allows us to perform intra-decl operations
	"""
	sel_decls = {}
	for r in doc.rules:
		for sel in r.sels.sel:
			try:
				sel_decls[sel] += r.decls
			except KeyError:
				sel_decls[sel] = r.decls
	return sel_decls

op = OptionParser()
(Opts, Args) = op.parse_args()

if Args:
	filename = Args[0]
	# TODO: add support for URLs
	f = open(filename, 'r')
	contents = f.read()
	f.close()
else:
	filename = '-'
	contents = sys.stdin.read()

doc = cssparse.CSSDoc.parse(contents)
#print doc.rules

cssparse.Format.canonical()

# merge all properies associated with each selector
sels_merged = selectors_merge(doc)

# merge child properties into parents
foo = []
for sel, decls in sels_merged.items():
	dcomb = decls_property_combine(decls)
	foo.append((sel, dcomb))
	#print sel.format(), dcomb.format()

# merge selectors having identical decls
# TODO: would be better if we identified subsets of decls that were longer than their selector name,
# then merged those, breaking decls up
#foo = sorted(
identical_decls = defaultdict(list)
#print foo
for s, d in foo:
	identical_decls[d].append(s)
for d, s in identical_decls.items():
	#print s, d
	r = Rule(Sels(s), d)
	print r.format()

"""
rules_with_dupes = list(decl_find_duplicate_properties(doc))
if rules_with_dupes:
	print '/* !!! Duplicate decl properties !!! */'
	for r, dupecnt in rules_with_dupes:
		print r.format()
"""

