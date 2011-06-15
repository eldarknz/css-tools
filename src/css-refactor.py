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
from optparse import OptionParser

import parse as cssparse

def decl_find_duplicate_properties(doc):
	"""
	not so easy; there are browser hacks out there that require this. be smarter.
	"""
	for r in doc.rules:
		decls = r.decls.decl
		d = dict([(x.property, x.values) for x in decls])
		if len(d) != len(decls):
			yield (r, len(decls) - len(d))

def selectors_merge_identical(doc):
	"""
	"""
	for r in doc.rules:
		for sel in r.sels.sel:
			print sel
			print r.decls

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
print doc.rules

cssparse.Format.canonical()

selectors_merge_identical(doc)

"""
rules_with_dupes = list(decl_find_duplicate_properties(doc))
if rules_with_dupes:
	print '/* !!! Duplicate decl properties !!! */'
	for r, dupecnt in rules_with_dupes:
		print r.format()
"""

