# Copyright (C) 2010, Thomas Leonard
# See the COPYING file for details, or visit http://0install.net.

import os, time
import xml.etree.ElementTree as ET

from zeroinstall.injector.iface_cache import iface_cache
from zeroinstall.injector import gpg

def format_date(date):
	return time.strftime("%Y-%m-%d", time.gmtime(date))

# When people change keys, add a mapping so that their new feeds appear under the same user
aliases = {
		# New key				      Original key
		'617794D7C3DFE0FFF572065C0529FDB71FB13910' : '92429807C9853C0744A68B9AAE07828059A53CC1',
		'6AD4A9C482F1D3F537C0354FC8CC44742B11FF89' : 'FD3208AD535F2B63BCEDB2BFFB013BAB74FFF135',
		'1DFE86921CBA7BCB691DA2434F5A1693E18E1E91' : '0C5C7BC77B70E7BA813478B6FF29FF60ACB8DFE8',
		'2E2B4E59CAC8D874CD2759D34B1095AF2E992B19' : 'C82D382AAB381A54529019D6A0F9B035686C6996',
		'DA9825AECAD089757CDABD8E07133F96CA74D8BA' : '92429807C9853C0744A68B9AAE07828059A53CC1',
}

# Feeds with these keys must not be mirrored
test_keys = set()
test_keys.add('5E22F6A13A76F396AC68B5F29B1F5D7F9721DA90')
test_keys.add('2E32123D8BE241A3B6D91E0301685F11607BB2C5')

def ensure_dir(path):
	if not os.path.isdir(path):
		os.mkdir(path)
	return path

class User:
	def __init__(self):
		self.feeds = set()
		self.last_active = None
		self.n_feeds = 0
		self.n_implementations = 0
		self.key = None
	
	def add_feed(self, feed, sig):
		assert feed not in self.feeds, feed
		self.feeds.add(feed)
		mtime = sig.get_timestamp()
		if self.last_active is None or self.last_active < mtime:
			self.last_active = mtime
		self.n_feeds += 1
		self.n_implementations += len(feed.implementations)
	
	def as_xml(self):
		root = ET.Element('user')

		name = ET.SubElement(root, 'name')
		name.text = self.key.get_short_name()

		feeds = ET.SubElement(root, 'feeds')

		sorted_feeds = sorted([(feed.get_name(), feed) for feed in self.feeds])
		for name, feed in sorted_feeds:
			feed_element = ET.SubElement(feeds, 'feed')
			feed_element.attrib['url'] = feed.url
			feed_element.attrib['name'] = name
			feed_element.attrib['implementations'] = str(len(feed.implementations))
			feed_element.attrib['last-modified'] = format_date(feed.last_modified)
			feed_element.attrib['summary'] = feed.summary

		stats = ET.SubElement(root, 'stats')
		stats.attrib['feeds'] = str(self.n_feeds)
		stats.attrib['implementations'] = str(self.n_implementations)
		stats.attrib['karma'] = str(self.get_karma())

		return ET.ElementTree(root)

	def get_karma(self):
		return 10 * self.n_feeds + self.n_implementations

"""Keep track of some statistics."""
class Stats:
	def __init__(self):
		self.users = {}		# Fingerprint -> User
	
	def add_feed(self, feed):
		sigs = iface_cache.get_cached_signatures(feed.url)
		if not sigs:
			return

		for sig in sigs:
			fingerprint = aliases.get(sig.fingerprint, sig.fingerprint)
			assert fingerprint not in aliases, fingerprint
			assert fingerprint not in test_keys, (fingerprint, feed)
			if fingerprint not in self.users:
				self.users[fingerprint] = User()
			self.users[fingerprint].add_feed(feed, sig)
	
	def write_summary(self, topdir):
		names = []
		keys = gpg.load_keys(self.users.keys())
		for fingerprint, user in self.users.iteritems():
			user.key = keys[fingerprint]
			names.append((user.key.name, fingerprint))
		for name, fingerprint in sorted(names):
			user = self.users[fingerprint]
			print '%s (%s feeds and %s implementations)' % (name, user.n_feeds, user.n_implementations)
			user_dir = ensure_dir(os.path.join(topdir, 'users', fingerprint))
			user_xml = user.as_xml()
			user_xml.write(os.path.join(user_dir, 'user.xml'))
