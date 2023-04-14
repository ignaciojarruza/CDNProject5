# CDN Project 5

# Running the Scripts
We tested our architecture by running the three scripts in this manner:
./deployCDN -p 20140 -o cs5700cdnorigin.ccs.neu.edu:8080 -n cs5700cdn.example.com -u sukanyanag -i ~/.ssh/id_ed25519.pub
./runCDN -p 20140 -o cs5700cdnorigin.ccs.neu.edu:8080 -n cs5700cdn.example.com -u sukanyanag -i ~/.ssh/id_ed25519.pub
./stopCDN -p 20140 -o cs5700cdnorigin.ccs.neu.edu -n cs5700cdn.example.com -u sukanyanag -i ~/.ssh/id_ed25519.pub


# High Level Approach: DNS Server
The DNS Server implementation creates a server that runs indefinitely and responds to DNS A queries for the domain passed in through the command line.

First, it listens through a UDP port for any DNS requests made to the specified port. If the server receives a dig query, for example, each request is then checked for validity.

If the request is not an A DNS request or is not for the domain passed in at startup (in this case it would be cs5700.example.com), then the request is ignored and the server does not react.

If a valid DNS query was made to the server, then the server will dynamically select one of the http replicas based on overall RTT. For our implementation of dynamically selecting a replica ip address we devised two methods: (1) using geolite2 to acquire longitude and latitude coordinates in order to choose the closest replica server to the client and (2) lowest RTT from the DNS to the replicas.

The purpose of having two is that we were worried that geolite2 can cause issues when put under loads in the thousands of requests. I tried looking up online how many requests in theory should be handled without issues but could not find a difinitive answer. Although there are no limits to requests per second like other libraries, it is mentioned that repeated requests in the range of thousands can sometimes result in either slower times or blocking of IP addresses.

In an attempt to error-proof this situation, we introduced a try-except that if triggered will use the RTT algorithm instead of the Geo location algorithm. The performance of the geo location is better, but we introduced RTT as a safety net in the event that thorough testing causes issues in the future like the IP of the DNS being blocked from the service because too many requests were being sent. I also saved previous client IPs and the mappings to their closest replica server such that the geo IP API isn't overused unnecesarily and reduces overall API calls.



# High Level Approach: HTTP Server
The HTTP Server implementation utilizes a subclass of a basic HTTP handler that responds to GET requests by first fetching the content from the origin cdn server with a GET request. For the milestone, this is a direct GET request without any consideration of caching, which will be added for the final project submission.
We extended the functionality of the HTTP Server to support caching through the use of a dictionary that holds key value pairs of the form: <path, (file, frequency)>. This caching strategy utilzies a lambda function to order the dictionary before removing the 3 least frequently accessed files once data reaches the 20MB limit. If a request is contained in the dictionary then no request is sent to the origin and performance is more efficient. This rolling frequency caching strategy favors files that are accessed more frequently.


The GET request to the origin server is done via overloading the do_GET() method of the BaseHTTPRequestHandler and utilizes the requests library for the sending/receiving HTTP requests.

The HTTP Server utilizes a TCPServer socketserver that is set to serve forever with the innate serve_forever() method.
Testing for the http servers involved sending hundreds of GET requests in sequence to one server at a time and making sure that all requests were met.
The resources, documentation for http.server and BaseHTTPRequestHandler

# Design Decisions
Some of the design decisions we took in order to finalize this project include:
(1) Having two methods of dynamically selecting IP in the case that one fails. We recognized that there were some cases that could be out of our control when introducing the geolite2 module. For example, an IP could not be located in the database or our access is slowed because of too many subsequent requests. To combat this, we use the RTT algorithm as a backup to any geolite2 errors that can show up in the process.
We added geo location after testing the performance of the RTT and realizing that there was room for improvement.
(2) Overloading the HTTP Handler in the replica servers in order to add custom behavior when receiving GET requests. This allowed us to introduce caching functionality within GET requests.
(3) We implemented caching through the use of a dictionary that holds <path, (file, frequency)> and is emptied based on cache hit frequency. Since We wanted to maintain a total 20MB disk space, we made sure to keep the cache size to 17MB to accomodate the other files and make sure we never exceed this limit. In order to do this, we remove the last 3 least frequently accessed file paths. 

# Challenges Faced
We had numerous challenges throughout implementation, the most notable ones were:
(1) RTT did not perform as well as we hoped. This was mostly due to the inherent bias that geographic location has in network congestion and network latency. We solved this by introducing the alternative geo location IP algorithm.
(2) Our scripts needed a little bit of tweaking to get the correct modules downloaded while deploying.
(3) We faced an issue in getting the DNS server to correctly receive DNS A requests and had to reimplement the dns server from scratch. This is why we could not hand in the milestone in time.
(4) Geopy distance calculations were resulting in errors sometimes because they utilize a (latitude, longitude) point schema while I was using (longitude, latitude).
(5) We implemented the cache using sqlite3 at the beginning of our implementation and found issues with the st_size variable and utilizing ('VACUUM') to recaculate this value. The issue we encountered was that in order to call .('VACUUM') you need to have at least twice the size of the database being executed. This resulted in us needing to cut the size of the database by half to accomodate this feature, and ultimately still found issues with Disk I/O errors. We fixed this by implementing the design choice mentioned above by utilizing a dictionary and removing the least frequently accessed files once the size exceeded the 20MB.

# Testing
We tested our DNS by running dig requests to the IP of the dnsserver. The requests were in the format of: dig @198.74.61.103 -p 20140 cs5700cdn.example.com 
We tested our geo location algorithm and our RTT algorithms by checking the CDN status page and looking at the latency values for the DNS. In this way we found out that our RTT had some inherent bias towards the closest replica server to the DNS and implemented the geo algorithm.

We tested our HTTP replica servers and their caching functionality by creating a new python script that would randomly chose a file path hosted in an index.html that had all the urls listed in the origin. This script utilized the requests library to send thousands of consecutive requests. This specific method is how we tested the caching functionality and to also make sure that our system scales with a large volume of requests. We would also test our individual http replicas by issuing wget requests in the format: wget <ipReplica>:<port>/<path>
so for example: wget 50.116.39.110:20140/Lizzo

Through the use of both the CDN status page and time wget requests we were able to figure out which of our two algorithms worked fastest and gave the better performance. We also utilized numerous time wget requests to optimize things like returning the 204 without sending an http request to origin, which replica returned fastest for specific situations, etc. 

I think most of testing involved trying to optimize all the functionality that we introduced and seeing how the sequence of code can change performance in wget requests and using a "dumb" client that sent a large volume of http requests to a replica and calculating latency between each iteration.

# If We Had More Time
If we had more time, we would have definitely spent more time trying to improve the replica server ip allocation. By comapring all the group's latency values it is clear that some groups achieve better performance than just returning the closest replica to the client. I suspect that there must be a combination of RTT and geo location and it is where I would have spent more time if I had it. I also would test if compressing data in some way in the caching algorithm would affect performance.
In conclusion, the areas where we would have spent more time to implement more features for better performance would be in the dynamic ip selection and in caching.

# Work Distribution
HTTPServer: Ignacio Arruza
DNSServer: Ignacio Arruza
Testing DNS and HTTP servers: Ignacio Arruza
DNSServer RTT IP selection: Sukanya Nag
DNSServer Geo location IP selection: Ignacio Arruza
run/stop/deploy CDN Scripts: Sukanya Nag
Caching Functionality: Ignacio Arruza & Sukanya Nag

# DNS Resources
1. https://pythontic.com/modules/socket/gethostbyname
2. https://pypi.org/project/dnslib/
3. https://stackoverflow.com/questions/16977588/reading-dns-packets-in-python
4. https://geoip2.readthedocs.io/en/latest/
5. https://www.youtube.com/watch?v=ccvMfdlArbI
6. https://www.section.io/engineering-education/using-geopy-to-calculate-the-distance-between-two-points/
7. https://pypi.org/project/geoip2/
8. https://stackoverflow.com/questions/50953375/longitude-formatting-scale-for-calculating-distance-with-geopy
9. https://geopy.readthedocs.io/en/v1/#geopy.point.Point

# HTTP Resources
1. https://docs.python.org/3/library/http.server.html#http.server.BaseHTTPRequestHandler
2. https://docs.python.org/3/library/http.server.html
3. https://nedbatchelder.com/blog/202002/sysgetsizeof_is_not_what_you_want.html

