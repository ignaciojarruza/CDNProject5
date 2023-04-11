#!/usr/bin/env python3

import argparse
import socket
import dnslib

class DNSServer():
    def __init__(self, port, name):
        self.port = port
        self.name = name
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.socket.bind(port, name)
    
    def readDNSRequest(self, request):
        message = dnslib.DNSRecord.parse(request)
        domainRequested = str(message.q.qname)
        ip = self.socket.gethostbyname(domainRequested)
        return ip

    def serve_forever(self):
        while True:
            data, address = self.socket.recvfrom(1024)
            ipDomain = self.readDNSRequest(data)

        #return "Serving forever."
    
        

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
    args = argumentParser()
    PORT = args.port
    NAME = args.name

    dns = DNSServer(PORT, NAME)

#Resources:
#1. https://pythontic.com/modules/socket/gethostbyname
#2. https://pypi.org/project/dnslib/
#3. https://stackoverflow.com/questions/16977588/reading-dns-packets-in-python



