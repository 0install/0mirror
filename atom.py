# Copyright (C) 2008, Thomas Leonard
# See the COPYING file for details, or visit http://0install.net.

import os, sys
from xml.dom import minidom, Node
from xmltools import nodesEqual

empty_atom_feed_xml = """<?xml version="1.0" encoding="utf-8"?>
<feed xmlns="http://www.w3.org/2005/Atom">
  <title></title>
  <link href=""/>
  <updated></updated>
  <author>
    <name></name>
  </author>
  <id></id>
</feed>
"""

empty_element_xml = """
  <entry>
    <title></title>
    <link href=""/>
    <id></id>
    <updated></updated>
  </entry>
"""

def set_element(doc, path, value):
	assert type(value) in (str, unicode, Node), value
	node = doc
	for element in path.split('/'):
		if element.startswith('@'):
			node.setAttribute(element[1:], value)
			return
		for child in node.childNodes:
			if child.nodeName == element:
				node = child
				break
		else:
			#doc.toxml(sys.stderr)
			raise Exception("Not found: %s (in %s)" % (element, path))
	if not isinstance(value, Node):
		value = doc.createTextNode(value)
	for child in node.childNodes:
		node.removeChild(child)
	node.appendChild(value)

	return node

def remove(doc, path):
	node = doc
	for element in path.split('/'):
		if element.startswith('@'):
			node.removeAttribute(element[1:])
			return
		for child in node.childNodes:
			if child.localName == element:
				node = child
				break
		else:
			raise Exception("Not found: %s (in %s)" % (element, path))
	node.parentNode.removeChild(node)

def is_duplicate(doc, title, summary):
	for entry in doc.documentElement.childNodes:
		if entry.localName != 'entry': continue
		values = {}
		for item in entry.childNodes:
			values[item.localName] = item
		if nodesEqual(values['title'], title) and nodesEqual(values['summary'], summary):
			return True
	return False

class AtomFeed:
	def __init__(self, title, link, updated, author, feed_id = None, source = None):
		def set(path, value): set_element(self.doc, path, value)

		if source is None or not os.path.exists(source):
			self.doc = minidom.parseString(empty_atom_feed_xml)

			set("feed/title", title)
			set("feed/link/@href", link)
			set("feed/author/name", author)
			set("feed/id", feed_id or link)
		else:
			with open(source) as stream:
				self.doc = minidom.parse(stream)

		set("feed/updated", updated)
	
	def save(self, stream):
		self.doc.writexml(stream)
	
	def limit(self, n):
		root = self.doc.documentElement
		while len(root.childNodes) > n:
			for child in root.childNodes:
				if child.localName == 'entry':
					print "removing..."
					root.removeChild(child)
					break
			else:
				print >>sys.stderr, "Can't find an entry to remove!"
				break

	def add_entry(self, title, link, entry_id, updated, summary = None, extra_links = {}):
		entry_doc = minidom.parseString(empty_element_xml)

		def set(path, value): return set_element(entry_doc, path, value)

		title_node = set("entry/title", title)
		set("entry/link/@href", link)
		set("entry/id", entry_id)
		set("entry/updated", updated)
		
		entry_doc.documentElement.appendChild(entry_doc.importNode(summary, deep = True))

		for extra_link in extra_links:
			element = entry_doc.createElement('link')
			element.setAttribute('rel', extra_link)
			element.setAttribute('href', extra_links[extra_link])
			entry_doc.documentElement.appendChild(element)

		entry = self.doc.importNode(entry_doc.documentElement, deep = True)

		if is_duplicate(self.doc, title_node, summary): return

		self.doc.documentElement.appendChild(entry)

if __name__ == '__main__':
	feed = AtomFeed(title = "Example Feed",
			link = "http://example.org/",
			updated = "2003-12-13T18:30:02Z",
			author = "John Doe",
			feed_id = "urn:uuid:60a76c80-d399-11d9-b93C-0003939e0af6")

	summary_xml = """
	<summary type='xhtml'>
	  <div xmlns="http://www.w3.org/1999/xhtml">
	    <a href=""/> - <span/>
	  </div>
	</summary>
	"""

	summary = minidom.parseString(summary_xml)

	feed.add_entry(title = "Atom-Powered Robots Run Amok",
		       link = "http://example.org/2003/12/13/atom03",
		       entry_id = "urn:uuid:1225c695-cfb8-4ebb-aaaa-80da344efa6a",
		       updated = "2003-12-13T18:30:02Z",
		       summary = summary.documentElement)

	summary2 = minidom.parseString(summary_xml)
	feed.add_entry(title = "Atom-Powered Robots Run Amok",
		       link = "http://example.org/2003/12/13/atom03",
		       entry_id = "urn:uuid:1225c695-cfb8-4ebb-aaaa-80da344efa6a",
		       updated = "2003-12-13T18:30:02Z",
		       summary = summary2.documentElement)

	feed.save(sys.stdout)
	print
