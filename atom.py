from xml.dom import minidom

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
    <summary></summary>
  </entry>
"""

def set_element(doc, path, value):
	node = doc
	for element in path.split('/'):
		if element.startswith('@'):
			node.setAttribute(element[1:], value)
			return
		for child in node.childNodes:
			if child.localName == element:
				node = child
				break
		else:
			raise Exception("Not found: %s (in %s)" % (element, path))
	node.appendChild(doc.createTextNode(value))

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

class AtomFeed:
	def __init__(self, title, link, updated, author, feed_id = None):
		self.doc = minidom.parseString(empty_atom_feed_xml)

		def set(path, value): set_element(self.doc, path, value)

		set("feed/title", title)
		set("feed/link/@href", link)
		set("feed/updated", updated)
		set("feed/author/name", author)
		set("feed/id", feed_id or link)
	
	def save(self, stream):
		self.doc.writexml(stream)

	def add_entry(self, title, link, entry_id, updated, summary = None):
		entry_doc = minidom.parseString(empty_element_xml)

		def set(path, value): set_element(entry_doc, path, value)

		set("entry/title", title)
		set("entry/link/@href", link)
		set("entry/id", entry_id)
		set("entry/updated", updated)
		
		if summary:
			set("entry/summary", summary)
		else:
			remove(entry_doc, "entry/summary")

		entry = self.doc.importNode(entry_doc.documentElement, deep = True)
		self.doc.documentElement.appendChild(entry)

if __name__ == '__main__':
	feed = AtomFeed(title = "Example Feed",
			link = "http://example.org/",
			updated = "2003-12-13T18:30:02Z",
			author = "John Doe",
			feed_id = "urn:uuid:60a76c80-d399-11d9-b93C-0003939e0af6")

	feed.add_entry(title = "Atom-Powered Robots Run Amok",
		       link = "http://example.org/2003/12/13/atom03",
		       entry_id = "urn:uuid:1225c695-cfb8-4ebb-aaaa-80da344efa6a",
		       updated = "2003-12-13T18:30:02Z",
		       summary = "Some text.")

	import sys
	feed.save(sys.stdout)
	print
