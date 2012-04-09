#!/usr/bin/env python

import contextlib
import re
import urllib
import sys
import urllib2
import os

from xml.dom.minidom import parseString

out_dir = sys.argv[1]

def fetch(uri):
    with contextlib.closing(urllib2.urlopen(uri)) as uh:
        return uh.read()


root_uri = 'http://s3.amazonaws.com/ec2-downloads/'
print("Getting data from %s" % (root_uri))

doc = parseString(fetch(root_uri))
keys = doc.getElementsByTagName("Key")
real_keys = list()
for k in keys:
    for tmp in k.childNodes:
        if tmp.nodeValue:
            real_keys.append(tmp.nodeValue)

real_keys.sort()
real_keys = set(real_keys)

wsdl_keys = set()
for k in real_keys:
    if re.match(r"^(\d+)-(\d+)-(\d+)\.ec2\.wsdl$", k, re.I):
        wsdl_keys.add(k)

for k in wsdl_keys:
    uri = root_uri + urllib.quote(k)
    print("Fetching from %s" % (uri))
    try:
        contents = fetch(uri)
        fn = os.path.join(out_dir, k)
        with open(fn, "w") as fh:
            fh.write(contents)
            print("Wrote to %s - %s bytes" % (fn, len(contents)))
    except urllib2.HTTPError as e:
        print("Failed downloading from %s due to %s" % (uri, e))
