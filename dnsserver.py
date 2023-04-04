#!/usr/bin/env python3

import argparse
class DNSServer():
    #TODO: add handling DNS requests

    def serve_forever():
       #while True:
        return "Serving forever."

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
