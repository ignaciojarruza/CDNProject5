# CDN Project 5

# High Level Approach: DNS Server
The DNS Server implementation creates a server that runs indefinitely and responds to DNS A queries for the domain passed in through the command line.

First, it listens through a UDP port for any DNS requests made to the specified port. If the server receives a dig query, for example, each request is then checked for validity.

If the request is not an A DNS request or is not for the domain passed in at startup (in this case it would be cs5700.example.com), then the request is ignored and the server does not react.

If a valid DNS query was made to the server, then the server will dynamically select one of the http replicas based on overall RTT. For our implementation of dynamically selecting a replica ip address we devised two methods: (1) using geolite2 to acquire longitude and latitude coordinates in order to choose the closest replica server to the client and (2) lowest RTT from the DNS to the replicas.

The purpose of having two is that we were worried that geolite2 can cause issues when put under loads in the thousands of requests. I tried looking up online how many requests in theory should be handled without issues but could not find a difinitive answer. Although there are no limits to requests per second like other libraries, it is mentioned that repeated requests in the range of thousands can sometimes result in either slower times or blocking of IP addresses.

In an attempt to error-proof this situation, we introduced a try-except that if triggered will use the RTT algorithm instead of the Geo location algorithm. The performance of the geo location is better, but we introduced RTT as a safety net in the event that thorough testing causes issues in the future like the IP of the DNS being blocked from the service because too many requests were being sent.



# High Level Approach: HTTP Server
The HTTP Server implementation utilizes a subclass of a basic HTTP handler that responds to GET requests by first fetching the content from the origin cdn server with a GET request. For the milestone, this is a direct GET request without any consideration of caching, which will be added for the final project submission.
We extended the functionality of the HTTP Server to support caching through the use of mysql.
[Explain a little more in detail here]

The GET request to the origin server is done via overloading the do_GET() method of the BaseHTTPRequestHandler and utilizes the requests library for the sending/receiving HTTP requests.

The HTTP Server utilizes a TCPServer socketserver that is set to serve forever with the innate serve_forever() method.
Testing for the http servers involved sending hundreds of GET requests in sequence to one server at a time and making sure that all requests were met.
The resources, documentation for http.server and BaseHTTPRequestHandler

# Design Decisions
Some of the design decisions we took in order to finalize this project include:
(1) Having two methods of dynamically selecting IP in the case that one fails. We recognized that there were some cases that could be out of our control when introducing the geolite2 module. For example, an IP could not be located in the database or our access is slowed because of too many subsequent requests. To combat this, we use the RTT algorithm as a backup to any geolite2 errors that can show up in the process.
We added geo location after testing the performance of the RTT and realizing that there was room for improvement.
(2) Overloading the HTTP Handler in the replica servers in order to add custom behavior when receiving GET requests. This allowed us to introduce caching functionality within GET requests.
(3) Caching through [add more detail here]

# Challenges Faced
We had numerous challenges throughout implementation, the most notable ones were:
(1) RTT did not perform as well as we hoped. This was mostly due to the inherent bias that geographic location has in network congestion and network latency. We solved this by introducing the alternative geo location IP algorithm.
(2) Our scripts needed a little bit of tweaking to get the correct modules downloaded while deploying.
(3) We faced an issue in getting the DNS server to correctly receive DNS A requests and had to reimplement the dns server from scratch. This is why we could not hand in the milestone in time.
(4) Geopy distance calculations were resulting in errors sometimes because they utilize a (latitude, longitude) point schema while I was using (longitude, latitude)

# Work Distribution
HTTPServer: Ignacio Arruza
DNSServer: Ignacio Arruza
Testing DNS and HTTP servers: Ignacio
DNSServer RTT IP selection: Sukanya Nag
DNSServer Geo location IP selection: Ignacio Arruza
run/stop/deploy CDN Scripts: Sukanya Nag
Caching Functionality: Sukanya Nag

