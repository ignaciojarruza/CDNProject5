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




