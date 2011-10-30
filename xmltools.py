# Copyright (C) 2011, Thomas Leonard
# See the COPYING file for details, or visit http://0install.net.

from xml.dom import Node

def childNodes(parent, namespaceURI = None, localName = None):
	for x in parent.childNodes:
		if x.nodeType != Node.ELEMENT_NODE: continue
		if namespaceURI is not None and x.namespaceURI != namespaceURI: continue

		if localName is None or x.localName == localName:
			yield x

def nodesEqual(a, b):
	assert a.nodeType == Node.ELEMENT_NODE
	assert b.nodeType == Node.ELEMENT_NODE

	if a.namespaceURI != b.namespaceURI:
		return False

	if a.nodeName != b.nodeName:
		return False
	
	a_attrs = set(["%s %s" % (name, value) for name, value in a.attributes.itemsNS()])
	b_attrs = set(["%s %s" % (name, value) for name, value in b.attributes.itemsNS()])

	if a_attrs != b_attrs:
		#print "%s != %s" % (a_attrs, b_attrs)
		return False
	
	a_children = list(childNodes(a))
	b_children = list(childNodes(b))

	if len(a_children) != len(b_children):
		return False
	
	for a_child, b_child in zip(a_children, b_children):
		if not nodesEqual(a_child, b_child):
			return False
	
	return True
