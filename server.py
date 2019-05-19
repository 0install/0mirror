#!/usr/bin/python2

import codecs
import search
import BaseHTTPServer
import urlparse
import sys

assert len(sys.argv) == 2, "Usage: server.py index-dir"
index_path = sys.argv[1]

PORT = 8000

class Handler(BaseHTTPServer.BaseHTTPRequestHandler):
    def do_GET(self):
        parts = self.path.split('?',1)
        if len(parts) < 2:
            self.send_error(400, "Missing query")
            return
        q = urlparse.parse_qs(parts[1])
        q = q.get("q")
        if q is None:
            self.send_error(400, "Missing q parameter")
            return
        self.send_response(200)
        self.send_header("Content-Type", "text/xml")
        self.end_headers()
        writer = codecs.getwriter('utf-8')(self.wfile)
        searcher = search.Searcher(index_path)
        searcher.query(q[0].decode('utf-8'), writer)
        writer.flush()

print "Serving on port %d" % PORT
httpd = BaseHTTPServer.HTTPServer(('', PORT), Handler)
httpd.serve_forever()
