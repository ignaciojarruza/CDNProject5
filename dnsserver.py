<<<<<<< HEAD
import socket
from struct import *
import threading
import urllib.request
import urllib.error
import sys

class CDN:

    def __init__(self, file_path ,port):
        """
        Initializes a CDN object with the list of replica servers specified in the given file
        and the port on which the CDN will run.

        Args:
            file_path (str): The path to the file containing the list of replica servers.
            port (int): The port on which the CDN will run.
        """
        self.replicas = []
        self.port = int(port)
        with open(file_path) as file_path:
            lines = file_path.readlines()
            for line in lines:
                # Only add the line to the replicas list if it contains ".com" and is not an origin server
                if ".com" in line and "Origin" not in line:
                    self.replicas.append(socket.gethostbyname(line.strip('\r\n')))
            

    def get_url(self, url, ip, ips):
        """
        Sends a request to the specified URL with the given IP address and records the round-trip time.

        Args:
            url (str): The URL to send the request to.
            ip (str): The IP address to include in the request.
            ips (dict): A dictionary to store the round-trip times for each replica server.
        """
    
        query = "http://" + ip + ":" + str(self.port) + "/" + self.clientIP
        rtt = urllib.request.urlopen(query).read()
        ips[float(rtt)] = ip


    def best_rtt(self, ip):
        """
        Sends a request to each replica server with the given IP address and returns the URL of the server
        that had the shortest round-trip time.

        Args:
            ip (str): The IP address to include in the request.

        Returns:
            str: The URL of the replica server with the shortest round-trip time.
        """
        threads = []
        ips = {}
        for u in self.replicas:
            t = threading.Thread(target=self.get_url, args=(u, ips))
            t.daemon = True
            t.start()
            threads.append(t)
        for t in threads:
            t.join()
        s = min(ips.keys())
        return ips[s]


class DNSQuery:
    """
    Represents a DNS query object.
    """

    def __init__(self, data, addr):
        """
        Initializes a new DNSQuery object.

        Args:
            data (bytes): The DNS query data.
            addr (tuple): The client address.
        """
        self.data = data
        self.clientIP = str(addr[0])
        print (addr[0])
        # unpack query header
        id, misc, qdcount, ancount, nscount, arcount = unpack('!6H', data[:12])
        self.isquery= (misc & 0x8000) == 0
        if self.isquery:
            index = 12
            C = unpack("!c", data[index])[0]
            Domain = []
            while C != b'\x00':
                N = ord(C)
                index = index + 1
                indexend = index + N
                Domain.append(''.join(map(chr, data[index:indexend])))
                index = indexend
                C = unpack("!c", data[index])[0]
            Domain = '.'.join(Domain)
            self.Qclass, self.qtype = unpack("!2H", data[index:index +4])
            self.domain = Domain
            self.todomainlength = index
            print (Domain)


    def check_cdn(self, cdn):
        """
        Sends a request to a given CDN object and retrieves the IP address of the replica server with the shortest
        round-trip time for the current client.

        Args:
            cdn (CDN): A CDN object that contains a list of replica servers.

        Returns:
            str: The IP address of the replica server with the shortest round-trip time for the current client.
        """
        ip = cdn.best_rtt(self.clientIP)
        print(ip)
        return ip


    def generate_resp_packet(self, cdn):
        """
        Constructs and returns a response packet for the DNS query.

        Args:
            cdn (CDN): A CDN object that contains a list of replica servers.

        Returns:
            str: A response packet for the DNS query.
        """

        packet = ''
        ip = socket.inet_aton(self.check_cdn(cdn))
        print(ip, len(ip))
        if len(ip) > 0:
            packet += self.data[:2] + "\x81\x80"
            packet += self.data[4:6] + self.data[4:6] + '\x00\x00\x00\x00'
            packet += self.data[12:self.todomainlength+5]                     
            packet += '\xc0\x0c'                                           
            packet += '\x00\x01'               
            packet += '\x00\x01'                                 
            packet += '\x00\x00\x00\x0F'  
            packet += '\x00\x04'                                        
            #packet+= pack('!H',len(ip))
            packet += ip
        else:
            packet = ''
        return packet
    

    def get_ip(self, data):
        """
        Retrieves the IP address corresponding to the given domain name from a DNS record file.

        Args:
            data (str): The domain name for which to retrieve the IP address.

        Returns:
            str: The IP address corresponding to the domain name, if found in the DNS record file. An empty string
            otherwise.
        """

        record = open("example.txt",'r').read()
        if data in record:
            for line in record.split('\n'):
                if data == line.split()[0]:
                    return line.split()[-1]
        else:
            return ""


def handle_query(udps, data, add, cdn, name):
    """
    Handles a DNS query by constructing a response and sending it to the client.
        
    Args:
        udps (socket.socket): The UDP socket used for sending the response.
        data (str): The DNS query data.
        add (tuple): The address of the client making the query.
        cdn (CDN): The CDN instance used for querying replica servers.
        name (str): The domain name to be handled.

    """
    query = DNSQuery(data, add)
    if query.domain == name:
        reply = query.generate_resp_packet(cdn)
        if len(reply) > 0:
            udps.sendto(reply, add)


def main(args):
    """
    Main function to start the DNS server.

    Args:
        args (list): List of command-line arguments.

    """

    port = 0
    name = ""
    if args[1] == '-p':
        port = int(args[2])
    elif args[3] == '-p':
        port = int(args[4])
    if args[1] == '-n':
        name = args[2]
    elif args[3] == '-n':
        name = args[4]

    udps = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    udps.bind(("", port))

    file="testme.txt"
    if port == 20140:
        rttPort = 20139
    else:
        rttPort = port + 1
    cdn =  CDN(file, rttPort)

    print ("reaching here")

    while 1:
        try:
            data,add = udps.recvfrom(1024)
            t = threading.Thread(target = handle_query, args=(udps, data, add, cdn, name))
            t.daemon = True
            t.start()
        except KeyboardInterrupt:
            break
    udps.close()

if __name__ == "__main__":
        if len(sys.argv)!=5:
            print("Error : Incorrect number of arguments")
        else:
            main(sys.argv)
=======
#!/usr/bin/env python3

import argparse
import socket
import dnslib
import time
import geoip2.database
from geopy.distance import geodesic
class DNSServer():

    def __init__(self, port, name):
        '''
        DNSServer constructor. Initializes object and creates UDP Socket for communcation.
        Parameters:
            port: port to bind CDN server
            name: CDN-specific name that your server translates to an IP
        '''
        self.port = port
        self.name = name
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.hostIP = socket.gethostbyname(socket.gethostname())
        self.socket.bind((self.hostIP, port))

        #Save Replica IPs and long/lat values for faster lookups
        self.replicaIPs = {}
        self.replicaLongLats = {}
        replica_domains = ['cdn-http1.5700.network', 'cdn-http2.5700.network', 'cdn-http3.5700.network',
                           'cdn-http4.5700.network', 'cdn-http5.5700.network', 'cdn-http6.5700.network', 
                           'cdn-http7.5700.network']
        for replica in replica_domains:
            self.replicaIPs[replica] = socket.gethostbyname(replica)
            for replica in self.replicaIPs:
                self.geoReader = geoip2.database.Reader('GeoLite2-City.mmdb')
                geoData = self.geoReader.city(self.replicaIPs[replica])
                self.replicaLongLats[replica] = (geoData.location.longitude, geoData.location.latitude)          

    def isDNSRequestValid(self, request):
        '''
        Checks the validity of the DNS request.
        Validity is defined as (1) having domain requested be the same as the DNS instantiation domain
        and (2) being a request of type A.
        Parameters:
            request: DNS request
        Returns:
            valid: boolean value for validity of DNS request
        '''
        #Domain Name Check
        message = dnslib.DNSRecord.parse(request)
        domainRequested = str(message.q.qname)
        valid = True
        if domainRequested != "{name}.".format(name=self.name):
            valid = False

        #Query Type Check
        if message.q.qtype != dnslib.QTYPE.A:
            valid = False
        
        return valid
    
    def bestReplicaGeo(self, address):
        #Find longitude and latitude for client IP
        geoData = self.geoReader.city(address[0])

        #TODO: Compare distances and pick closest replica server
        closestIP = None
        closestDistance = float('inf')
        for replica in self.replicaIPs:
            httpReplicaCoordinates = self.replicaLongLats[replica]
            clientCoordinates = (geoData.location.longitude, geoData.location.latitude)
            distance = geodesic(httpReplicaCoordinates, clientCoordinates).km
            if distance and distance < closestDistance:
                closestDistance = distance
                closestIP = replica
        return closestIP


        

        return
    
    def bestReplicaRTT(self, request):
        """
        Determines the IP address of the replica server with the lowest Round Trip Time (RTT).
        This method resolves the domain names of the available replica servers, pings each server,
        and selects the one with the lowest RTT. If a server is unreachable or its domain cannot
        be resolved, it is skipped.

        Parameters:
            request: DNS request

        Returns:
            str: IP address of the replica server with the lowest RTT, or None if none of the servers can be reached
        """

        replica_domains = ['cdn-http1.5700.network', 'cdn-http2.5700.network', 'cdn-http3.5700.network',
                           'cdn-http4.5700.network', 'cdn-http5.5700.network', 'cdn-http6.5700.network', 
                           'cdn-http7.5700.network']

        best_ip = None
        best_rtt = float('inf')

        # Resolve the domain names to their corresponding IP addresses
        for domain in replica_domains:
            try:
                addrinfo = socket.getaddrinfo(domain, None, family=socket.AF_INET, type=socket.SOCK_STREAM)
                ip = addrinfo[0][4][0]
            except socket.gaierror:
                continue            

            # Measure the RTT by sending TCP SYN packets
            start_time = time.time()
            try:
                tcp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                tcp_socket.settimeout(1)
                tcp_socket.connect((ip, 20140))
                tcp_socket.close()
                rtt = (time.time() - start_time) * 1000

                if rtt and rtt < best_rtt:
                    best_rtt = rtt
                    best_ip = ip
            except (socket.timeout, socket.error):
                continue

        return best_ip
    
    def sendDNSResponse(self, request, address, replicaIP):
        '''
        Sends appropriate DNS response to client.
        Parameters:
            request: DNS Request that client sent
            address: Address of client in (ip, port) tuple
            replicaIP: IP of replica http server to redirect client
        '''
        parsedRequest = dnslib.DNSRecord.parse(request)
        response = parsedRequest.reply()
        response.add_answer(dnslib.RR(rname=address[0], ttl=45, rdata=dnslib.A(replicaIP)))
        self.socket.sendto(response.pack(), address)

    def serve_forever(self):
        """
        Runs the DNS server indefinitely. DNS server will listen
        for DNS queries and only respond when conditions are appropriate.
        Only responds for A type queries and when domain requested is the same as the DNS
        server creation name passed through the command line.
        """
        while True:
            request, address = self.socket.recvfrom(1024)
            print(f"Received request from {address}: {request}")
            if self.isDNSRequestValid(request) == False:
                continue

            #Craft and send response
            #replicaIP = self.bestReplicaRTT(request)
            replicaIP = self.bestReplicaGeo(address)
            self.sendDNSResponse(request, address, replicaIP)

def argumentParser():
    '''
    Parses command line arguments.
    Supports:
        -p PORT: port to bind CDN server
        -n NAME: CDN-specific name that your server translates to an IP
    '''
    parser = argparse.ArgumentParser(description='Project 5 DNS Server Implementation...')
    parser.add_argument('-p', '--port', type=int, help='port DNS server will bind to')
    parser.add_argument('-n', '--name', help='name that you server translates to IP')
    return parser.parse_args()

#2014X sukanyanag group supported ports
if __name__ == '__main__':
    '''
    Main method. Handles Command Line Arguments and creates/runs DNS object.
    '''
    args = argumentParser()
    PORT = args.port
    NAME = args.name

    dns = DNSServer(PORT, NAME)
    dns.serve_forever()

#Resources:
#1. https://pythontic.com/modules/socket/gethostbyname
#2. https://pypi.org/project/dnslib/
#3. https://stackoverflow.com/questions/16977588/reading-dns-packets-in-python
#4. https://geoip2.readthedocs.io/en/latest/
#5. https://www.youtube.com/watch?v=ccvMfdlArbI




>>>>>>> 84631f308e17a27a0a6b7cf51af1ccf5600d9cf4
