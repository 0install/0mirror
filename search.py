# Tool for querying the search index that 0mirror builds when mirroring feeds.
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

class Searcher:
	def __init__(self, index_dir):
		index = open_dir(index_dir)
		self.searcher = index.searcher()

		fields = ["baseuri", "name", "summary", "description"]
		self.parser = MultifieldParser(fields, schema=index.schema)

	def query(self, query_string, out):
		"""out should take unicode and encode it as necessary"""
		query = self.parser.parse(unicode(query_string))
		results = self.searcher.search(query)
		max_score = results and max([result.score for result in results]) or 0.0

		out.write('<?xml version="1.0" ?>')
		out.write("<results>")
		for result in results:
			uri = result["uri"]
			name = result["name"]
			summary = result.get("summary", "")
			category = result.get("category", None)

			s = 100.0 * result.score / max_score

			out.write("<result uri=%s name=%s score='%d'>" % (quoteattr(uri), quoteattr(name), s))
			out.write("<summary>%s</summary>" % escape(summary))
			if category:
				out.write("<category>%s</category>" % escape(category))
			out.write("</result>")
		out.write("</results>")
