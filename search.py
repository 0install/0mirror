#!/usr/bin/env python
#
# This is a stand-alone tool for querying the search index that 0mirror
# builds when mirroring feeds.
#
# Copyright (C) 2011, Anders F Bjorklund
# Copyright (C) 2013, Thomas Leonard
# See the COPYING file for details, or visit http://0install.net.
#
# This version for 0mirror is based on original code for 0install:
# http://thread.gmane.org/gmane.comp.file-systems.zero-install.devel/3847

from whoosh.index import open_dir
from whoosh.qparser import MultifieldParser

from xml.sax.saxutils import escape, quoteattr

import os, sys

indexpath = os.path.expanduser("./search-index/")

index = open_dir(indexpath)
searcher = index.searcher()

fields = ["name", "summary", "description"]
parser = MultifieldParser(fields, schema=index.schema)

args = sys.argv[1:]
query = parser.parse(unicode(' '.join(args)))

results = searcher.search(query)
max_score = results and max([result.score for result in results]) or 0.0

print '<?xml version="1.0" ?>'
print "<results>"
for result in results:
	uri = result["uri"]
	name = result["name"]
	summary = "summary" in result and result["summary"] or ""
	category = "category" in result and result["category"] or None

	s = 100.0 * result.score / max_score

	print "  <result uri=%s name=%s score='%d'>" % (quoteattr(uri), quoteattr(name), s)
	print "    <summary>%s</summary>" % escape(summary)
	if category:
		print "    <category>%s</category>" % escape(category)
	print "  </result>"
print "</results>"
