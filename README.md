# CDN Project 5
# High Level Approach: HTTP Server
The HTTP Server implementation utilizes a subclass of a basic HTTP handler that responds to GET requests by first fetching the content from the origin cdn server with a GET request. For the milestone, this is a direct GET request without any consideration of caching, which will be added for the final project submission.

This GET request to the origin server is done via overloading the do_GET() method of the BaseHTTPRequestHandler and utilizes the requests library for the sending/receiving HTTP requests.

The HTTP Server utilizes a TCPServer socketserver that is set to serve forever with the innate serve_forever() method.

The resources, documentation for http.server and BaseHTTPRequestHandler

# Work Distribution

HTTPServer: Ignacio Arruza