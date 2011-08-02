# Copyright (C) 2010, Thomas Leonard
# See the COPYING file for details, or visit http://0install.net.

import os, time, codecs
import xml.etree.ElementTree as ET

from zeroinstall.injector.iface_cache import iface_cache
from zeroinstall.injector import gpg, trust, namespaces, model, qdom
from zeroinstall.support import basedir

from support import ensure_dirs, get_feed_dir

def format_date(date):
	return time.strftime("%Y-%m-%d", time.gmtime(date))

# When people change keys, add a mapping so that their new feeds appear under the same user
# TODO: this should be site configuration
aliases = {
		# New key				      Original key
		'617794D7C3DFE0FFF572065C0529FDB71FB13910' : '92429807C9853C0744A68B9AAE07828059A53CC1',
		'6AD4A9C482F1D3F537C0354FC8CC44742B11FF89' : 'FD3208AD535F2B63BCEDB2BFFB013BAB74FFF135',
		'1DFE86921CBA7BCB691DA2434F5A1693E18E1E91' : '0C5C7BC77B70E7BA813478B6FF29FF60ACB8DFE8',
		'2E2B4E59CAC8D874CD2759D34B1095AF2E992B19' : 'C82D382AAB381A54529019D6A0F9B035686C6996',
		'DA9825AECAD089757CDABD8E07133F96CA74D8BA' : '92429807C9853C0744A68B9AAE07828059A53CC1',
		'7722DC5085B903FF176CCAA9695BA303C9839ABC' : '03DC5771716A5A329CA97EA64AB8A8E7613A266F',
		'39AD3DDE2B988623D7F868591C319390658A683A' : 'D30B76E435BD65448F2A57C7B8E1967CBF45481E',
		'4CFBD0B5B7102BF66E9F12AEFBCAE33FC2DE322B' : '92429807C9853C0744A68B9AAE07828059A53CC1',
		'FA2577C515715EEE1261D3B0EFD438E5019F0846' : '7EADC3F1EFE150C371EDE0A15B5CB97421BAA5DC',
}

reverse_aliases = {}	# user ID -> list of their other keys
for new, original in aliases.iteritems():
	if original not in reverse_aliases:
		reverse_aliases[original] = []
	reverse_aliases[original].append(new)

# Feeds with these keys must not be mirrored
test_keys = set()
test_keys.add('5E22F6A13A76F396AC68B5F29B1F5D7F9721DA90')
test_keys.add('2E32123D8BE241A3B6D91E0301685F11607BB2C5')

def make_feed_element(parent, feed, active):
	feed_element = ET.SubElement(parent, 'feed')
	feed_element.attrib['active'] = str(active)
	feed_element.attrib['local-dir'] = get_feed_dir(feed.url).replace('#', '%23')
	feed_element.attrib['url'] = feed.url
	feed_element.attrib['name'] = feed.get_name()
	feed_element.attrib['implementations'] = str(count_impls(feed.url))
	feed_element.attrib['last-modified'] = format_date(feed.last_modified)
	feed_element.attrib['summary'] = feed.summary

def contents(path):
	if not os.path.exists(path):
		return None
	with open(path) as stream:
		return stream.read()

def write_if_changed(xml, path):
	new = path + '.new'
	xml.write(new, encoding='utf-8')
	if contents(path) == contents(new):
		os.unlink(new)
	else:
		os.rename(new, path)
		print "Updated", path

cached_counts = {}
def count_impls(url):
	if url not in cached_counts:
		cached = basedir.load_first_cache(namespaces.config_site, 'interfaces', model.escape(url))
		if cached:
			with open(cached) as stream:
				cached_doc = qdom.parse(stream)
			def count(elem):
				c = 0
				if elem.uri != namespaces.XMLNS_IFACE: return 0
				if elem.name == 'implementation' or elem.name == 'package-implementation':
					c += 1
				else:
					for child in elem.childNodes:
						c += count(child)
				return c
			cached_counts[url] = count(cached_doc)
		else:
			cached_counts[url] = 0
	return cached_counts[url]

class User:
	def __init__(self):
		self.feeds = {}
		self.last_active = None
		self.n_feeds = 0
		self.n_implementations = 0
		self.n_inactive = 0
		self.key = None
	
	def add_feed(self, feed, sig, active):
		assert feed not in self.feeds, feed
		self.feeds[feed] = active
		mtime = sig.get_timestamp()
		if self.last_active is None or self.last_active < mtime:
			self.last_active = mtime
		if active:
			self.n_feeds += 1
			self.n_implementations += count_impls(feed.url)
		else:
			self.n_inactive += 1
	
	def as_xml(self, user_keys):
		root = ET.Element('user')

		name = ET.SubElement(root, 'name')
		name.text = self.key.get_short_name()
		import codecs

		feeds = ET.SubElement(root, 'feeds')

		sorted_feeds = sorted([(feed.get_name().lower(), feed) for feed in self.feeds.keys()])
		for unused, feed in sorted_feeds:
			make_feed_element(feeds, feed, self.feeds[feed])

		stats = ET.SubElement(root, 'stats')
		stats.attrib['feeds'] = str(self.n_feeds)
		stats.attrib['implementations'] = str(self.n_implementations)
		if self.n_inactive:
			stats.attrib['inactive_feeds'] = str(self.n_inactive)
		stats.attrib['karma'] = str(self.get_karma())

		keys = ET.SubElement(root, 'keys')
		for key in user_keys:
			key_elem = ET.SubElement(keys, 'key')
			key_elem.attrib['name'] = key.get_short_name()
			key_elem.attrib['fingerprint'] = key.fingerprint
			key_elem.attrib['keyid'] = key.fingerprint[-16:]

		return ET.ElementTree(root)

	def get_karma(self):
		return 10 * self.n_feeds + self.n_implementations + self.n_inactive

def export_users(pairs):
	root = ET.Element('users')
	for karma, user in pairs:
		elem = ET.SubElement(root, "user")
		elem.attrib["name"] = user.key.get_short_name()
		elem.attrib["karma"] = str(karma)
		elem.attrib["uid"] = user.key.fingerprint
	return ET.ElementTree(root)

def export_sites(tuples):
	root = ET.Element('sites')
	for n_feeds, domain, feeds in tuples:
		elem = ET.SubElement(root, "site")
		elem.attrib["name"] = domain
		elem.attrib["feeds"] = str(n_feeds)
		elem.attrib["site-path"] = 'sites/site-%s.html' % domain
	return ET.ElementTree(root)

"""Keep track of some statistics."""
class Stats:
	def __init__(self):
		self.users = {}		# Fingerprint -> User
		self.sites = {}		# Domain -> [Feed]
		self.feeds = []
		self.active = {}	# Feed -> bool
	
	def add_feed(self, feed, active):
		self.active[feed] = active

		metadata = ET.Element('metadata')
		metadata.attrib["active"] = str(active)

		sigs = iface_cache.get_cached_signatures(feed.url)

		for sig in sigs or []:
			if isinstance(sig, gpg.ValidSig):
				fingerprint = aliases.get(sig.fingerprint, sig.fingerprint)
				assert fingerprint not in aliases, fingerprint
				if active:
					assert fingerprint not in test_keys, (fingerprint, feed)
				if fingerprint not in self.users:
					self.users[fingerprint] = User()
				self.users[fingerprint].add_feed(feed, sig, active)

				signer = ET.SubElement(metadata, "signer")
				signer.attrib["user"] = fingerprint
				signer.attrib["date"] = format_date(sig.get_timestamp())
			else:
				signer = ET.SubElement(metadata, "signer")
				signer.attrib["error"] = unicode(sig)

		domain = trust.domain_from_url(feed.url)
		if domain not in self.sites:
			self.sites[domain] = []
		self.sites[domain].append(feed)

		self.feeds.append((feed, metadata))
	
	def write_summary(self, topdir):
		names = []
		keys = gpg.load_keys(self.users.keys() + aliases.keys())
		top_users = []
		for fingerprint, user in self.users.iteritems():
			user.key = keys[fingerprint]
			try:
				# 0launch <= 0.45 doesn't returns names in unicode
				unicode(user.key.name)
			except:
				user.key.name = codecs.decode(user.key.name, 'utf-8')
			names.append((user.key.name, fingerprint))
		for name, fingerprint in sorted(names):
			user = self.users[fingerprint]
			user_dir = ensure_dirs(os.path.join(topdir, 'users', fingerprint))

			user_keys = [fingerprint] + reverse_aliases.get(fingerprint, [])
			user_xml = user.as_xml([keys[k] for k in user_keys])
			write_if_changed(user_xml, os.path.join(user_dir, 'user.xml'))
			top_users.append((user.get_karma(), user))

		users_xml = export_users(reversed(sorted(top_users)))
		write_if_changed(users_xml, os.path.join(topdir, 'top-users.xml'))

		for domain, feeds in self.sites.iteritems():
			site = ET.Element('site')
			site.attrib["name"] = domain
			feeds_elem = ET.SubElement(site, "feeds")
			sorted_feeds = sorted([(feed.get_name().lower(), feed) for feed in feeds])
			for name, feed in sorted_feeds:
				make_feed_element(feeds_elem, feed, self.active[feed])
			site_xml = ET.ElementTree(site)
			write_if_changed(site_xml, os.path.join(topdir, 'sites', 'site-%s.xml' % domain))

		top_sites = [(len(feeds), domain, feeds) for domain, feeds in self.sites.iteritems()]
		sites_xml = export_sites(reversed(sorted(top_sites)))
		write_if_changed(sites_xml, os.path.join(topdir, 'top-sites.xml'))

		for feed, metadata in self.feeds:
			for signer in metadata.findall("signer"):
				if "user" in signer.attrib:
					fingerprint = signer.attrib["user"]
					user = self.users[fingerprint]
					signer.attrib["name"] = user.key.get_short_name()

			metadata_xml = ET.ElementTree(metadata)
			feed_dir = get_feed_dir(feed.url)
			write_if_changed(metadata_xml, os.path.join(topdir, feed_dir, 'metadata.xml'))
