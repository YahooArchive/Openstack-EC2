#!/usr/bin/env python

import sys
from StringIO import StringIO

# Easy to use like:
#
# for fn in `ls data/wsdls/`; do echo "$fn -> $fn.xsd" ; python tools/wsdls-to-xsds.py data/wsdls/$fn > data/xsds/$fn.xsd; done

from xml.dom.minidom import parseString
from xml.dom.minidom import getDOMImplementation


def clean_nodes(node):
    remove_list = list()
    for child in node.childNodes:
        if child.nodeType == c.TEXT_NODE:
            if c.nodeValue == None or not c.nodeValue.strip():
                remove_list.append(child)
        elif child.hasChildNodes():
            clean_nodes(child)
    for n in remove_list:
        node.removeChild(n)


def read(fn):
    with open(fn, 'r') as fh:
        return fh.read()


fn = sys.argv[1]
dom = parseString(read(fn))
ndom = getDOMImplementation().createDocument(None, None, None)

xs_schema = None
root_name = 'types'
xs_name = 'xs:schema'
for node in dom.getElementsByTagName(root_name):
    for c in node.childNodes:
        if c.nodeType in [c.COMMENT_NODE, c.TEXT_NODE]:
            pass
        else:
            if c.nodeName == xs_name and c.nodeType == c.ELEMENT_NODE:
                xs_schema = c
                break

if not xs_schema:
    raise Exception("Could not find %r node under %r" % (xs_name, root_name))

ndom.appendChild(ndom.importNode(xs_schema, True))

# Sometimes these are missing...
needed_ns = [(u'xmlns:xs', u'http://www.w3.org/2001/XMLSchema'),
                (u'xmlns:xsi', u'http://www.w3.org/2001/XMLSchema-instance')]
xs = ndom.documentElement
for attr, val in needed_ns:
    if not xs.hasAttribute(attr):
        xs.setAttribute(attr, val)

# Remove these attributes
remove_attrs = []
for attr in remove_attrs:
    if xs.hasAttribute(attr):
        xs.removeAttribute(attr)

clean_nodes(xs)
print(ndom.toprettyxml(encoding='UTF-8', indent=(" " * 4)))
