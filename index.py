# Copyright (C) 2011, Anders F Bjorklund
# Copyright (C) 2013, Thomas Leonard
# See the COPYING file for details, or visit http://0install.net.
#
# This version for 0mirror is based on original code for 0install:
# http://thread.gmane.org/gmane.comp.file-systems.zero-install.devel/3847

import os
import logging

from whoosh.index import create_in, open_dir
from whoosh import fields
from whoosh.analysis import StemmingAnalyzer

from zeroinstall.injector.namespaces import XMLNS_IFACE

sa = StemmingAnalyzer()
schema = fields.Schema(
		uri		= fields.ID(unique=True, stored=True),
		name		= fields.TEXT(stored=True,field_boost=10.0),
		summary		= fields.TEXT(stored=True, field_boost=5.0),
		description	= fields.TEXT(analyzer=sa),
		category	= fields.KEYWORD(stored=True),
		homepage	= fields.STORED
	)

class Indexer:
	def __init__(self, config, index_dir):
		self.config = config
		self.index_dir = index_dir

		if not os.path.exists(index_dir):
			os.makedirs(index_dir)
			index = create_in(index_dir, schema)
		else:
			index = open_dir(index_dir)

		self.writer = index.writer()

	def update(self, url):
		feed = self.config.iface_cache.get_feed(url)
		if not feed:
			logging.warning("%s not cached", url)
			return

		if feed.feed_for:
			self.writer.delete_by_term('uri', unicode(url))
			return		# Skip sub-feeds

		name = feed.get_name()
		summary = feed.summary
		description = feed.description
		category = None
		for meta in feed.get_metadata(XMLNS_IFACE, 'category'):
			category = meta.content
			break
		homepage = None
		for meta in feed.get_metadata(XMLNS_IFACE, 'homepage'):
			homepage = meta.content
			break

		print "Indexing", url
		self.writer.update_document(uri=unicode(url), name=unicode(name),
				       summary=unicode(summary), description=unicode(description),
				       category=category, homepage=homepage)

		#print "%-32s\"%s\"" % ("%s (%s)" % (name, category), summary)

	def commit(self):
		self.writer.commit()
