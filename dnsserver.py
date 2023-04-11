#!/usr/bin/env python3

import argparse
import socket
import dnslib

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
        print("ip of host: {ip}".format(ip=self.hostIP))

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
    
    def replicaIP(self, request):
        #TODO: dynamically return IP
        return '54.169.255.101'
    
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
            if self.isDNSRequestValid(request) == False:
                continue

            #Craft and send response
            replicaIP = self.replicaIP(request)
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



