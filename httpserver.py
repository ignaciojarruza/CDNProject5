import socketserver
import http.server
from http.server import BaseHTTPRequestHandler

class HTTPReplicaRequestHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_headers('Content-type', 'text/html')
        self.end_headers()
        self.wfile.write(b'Custom Behavior added here.')

#2014X
PORT = 20140
Handler = HTTPReplicaRequestHandler

with socketserver.TCPServer(("", PORT), Handler) as httpd:
    print("serving at port", PORT)
    httpd.serve_forever()


#Resources
#1. https://docs.python.org/3/library/http.server.html#http.server.BaseHTTPRequestHandler
#2. https://docs.python.org/3/library/http.server.html