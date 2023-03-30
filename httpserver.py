import argparse
import socketserver
import http.server
from http.server import BaseHTTPRequestHandler
import requests

class HTTPReplicaRequestHandler(BaseHTTPRequestHandler):
    """HTTPReplicaRequestHandler subclasses BaseHTTPRequestHandler to serve
    resources that are on the desired origin."""
    def do_GET(self):
        """Overrides GET requests to add origin cdn functionality."""
        #Send GET Request to server here
        path = self.path
        url = 'http://{origin}:8080'.format(origin=self.origin)
        url += path
        file = requests.get(url)

        #TODO: add /grading/breacon check and return 204

        #Send file response to client here
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        self.wfile.write(file.content)
    
def argumentParser():
    """Parses command line arguments."""
    #TODO: add http/https check
    #TODO: add origin check for Project 5
    parser = argparse.ArgumentParser(description="Project 5 Replica Server Implementation...")
    parser.add_argument('-p', '--port', type=int, help='port HTTP server will bind to')
    parser.add_argument('-o', '--origin', help='origin server of CDN')
    return parser.parse_args()

#2014X
#PORT = 20140


if __name__ == '__main__':
    args = argumentParser()
    PORT = args.port
    ORIGIN = args.origin

    Handler = HTTPReplicaRequestHandler
    Handler.origin = ORIGIN
    

    with socketserver.TCPServer(("", PORT), Handler) as httpd:
        httpd.serve_forever()


#Resources
#1. https://docs.python.org/3/library/http.server.html#http.server.BaseHTTPRequestHandler
#2. https://docs.python.org/3/library/http.server.html