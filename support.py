# Copyright (C) 2010, Thomas Leonard
# See the COPYING file for details, or visit http://0install.net.

import os, time
from zeroinstall import SafeException

def escape_slashes(path):
	return path.replace('/', '#')

def ensure_dirs(path):
	if not os.path.isdir(path):
		os.makedirs(path)
	return path

def format_date(date):
	return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(date))

def get_feed_dir(feed):
	if '#' in feed:
		raise SafeException("Invalid URL '%s'" % feed)
	scheme, rest = feed.split('://', 1)
	domain, rest = rest.split('/', 1)
	assert scheme in ('http', 'https', 'ftp')	# Just to check for mal-formed lines; add more as needed
	for x in [scheme, domain, rest]:
		if not x or x.startswith(','):
			raise SafeException("Invalid URL '%s'" % feed)
	return os.path.join('feeds', scheme, domain, escape_slashes(rest))
