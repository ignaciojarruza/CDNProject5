# CDN Project 5

# High Level Approach: DNS Server
The DNS Server implementation creates a server that runs indefinitely and responds to DNS A queries for the domain passed in through the command line.

First, it listens through a UDP port for any DNS requests made to the specified port. If the server receives a dig query, for example, each request is then checked for validity.

If the request is not an A DNS request or is not for the domain passed in at startup (in this case it would be cs5700.example.com), then the request is ignored and the server does not react.

If a valid DNS query was made to the server, then the server will dynamically select one of the http replicas based on overall RTT. The ip of the replica with the lowest RTT to the DNS server is the ip that is returned to the DNS A query. We specifically made our measurements be dependent on RTT in order to get a semi-accurate measurement of network congestion for each of the servers and select the one which in theory will result in the fastest response to the client.

We tested utilizing third party APIs for geographical information but did not pursue that as a potential avenue for dynamic selection. We found that the increased overhead and third party reliance led to some situations where the RTT was entirely dependent on this lookup, which we did not feel was appropriate for the project. If we had more time to thoroughly test this dynamic selection, then it definitely would be a path to take in an attempt to optimize the download speed. I'm curious to see how other group implementations stack up to a regular "in vivo" check of which server responds quickest to the initial ping. One of the reasons we also decided against it was the discussion about third party APIs limiting the amount of times it can be utilized in a period of time. Through initial testing of the dns server, this limit was hit on our end and times dropped significantly.

One limitation I can forsee from our implementation is that we are pinging servers from only the CDN server location. These RTT might not be an accurate representation of the network congestivity/architecture of where the client made their request. Although we saw the geoIP dynamic selection to be a possible solution for this, for the reasons we mentioned above we decided not to 

# High Level Approach: HTTP Server
The HTTP Server implementation utilizes a subclass of a basic HTTP handler that responds to GET requests by first fetching the content from the origin cdn server with a GET request. For the milestone, this is a direct GET request without any consideration of caching, which will be added for the final project submission.
We extended the functionality of the HTTP Server to support caching through the use of mysql.
[Explain a little more in detail here]

The GET request to the origin server is done via overloading the do_GET() method of the BaseHTTPRequestHandler and utilizes the requests library for the sending/receiving HTTP requests.

The HTTP Server utilizes a TCPServer socketserver that is set to serve forever with the innate serve_forever() method.
Testing for the http servers involved sending hundreds of GET requests in sequence to one server at a time and making sure that all requests were met.
The resources, documentation for http.server and BaseHTTPRequestHandler

# Work Distribution

HTTPServer: Ignacio Arruza
DNSServer: Ignacio Arruza
Testing DNS and HTTP servers: Ignacio
DNSServer Dynamic Replica HTTP IP selection: Sukanya Nag
run/stop/deploy CDN Scripts: Sukanya Nag
Caching Functionality: Sukanya Nag

