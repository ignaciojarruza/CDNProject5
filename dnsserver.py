import socket
from struct import *
import threading
import urllib.request
import urllib.error
import sys

class CDN:

    def __init__(self, replica ,port):
        """
        Initializes a CDN object with a replica server and port number.

        Args:
        - replica (str): IP address and port number of the replica server
        - port (int): port number to be used for communication
        """

        self.replica = replica
        self.port = int(port)


    def get_url(self, url, ip):
        """
        Sends a request to the specified URL with the given IP address and returns the round-trip time (RTT) of the request.

        Args:
        - url (str): URL of the endpoint to be queried
        - ip (str): IP address to be used in the request

        Returns:
        - rtt (float): Round-trip time of the request in seconds, or None if an error occurs.
        """

        query = "http://" + url + ':' + str(self.port) + "/" + ip
        try:
            rtt = urllib.request.urlopen(query).read()
            return float(rtt)
        except urllib.error.URLError:
            # Ignore URLError exceptions (e.g. server is down)
            pass


    def best_rtt(self, ip):
        """
        Returns the IP address of the replica server with the lowest RTT for the given IP address.

        Args:
        - ip (str): IP address to be used in the request

        Returns:
        - replica_ip (str): IP address of the replica server with the lowest RTT, or None if an error occurs.
        """
        rtt = self.get_url(self.replica, ip)
        return self.replica if rtt is None else self.replica.split(':')[0]


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
                indexend = index+N
                Domain.append(''.join(map(chr, data[index:indexend])))
                index = indexend
                C = unpack("!c", data[index])[0]
            Domain = '.'.join(Domain)
            self.Qclass, self.qtype = unpack("!2H", data[index:index +4])
            self.domain = Domain
            self.todomainlength = index
            print (Domain)


    def generate_resp_packet(self, cdn):
        """
        Constructs and returns a response packet for the DNS query.

        Args:
            cdn (CDN): A CDN object that contains a list of replica servers.

        Returns:
            str: A response packet for the DNS query.
        """

        packet = ''
        ip = cdn.best_rtt(self.clientIP)
        print(ip)
        if ip > 0:
            packet += self.data[:2] + "\x81\x80"
            packet += self.data[4:6] + self.data[4:6] + '\x00\x00\x00\x00'  
            packet += self.data[12:self.todomainlength + 5]
            packet += '\xc0\x0c'
            packet += '\x00\x01'                                    
            packet += '\x00\x01'                                    
            packet += '\x00\x00\x00\x0F'                                  
            packet += '\x00\x04'                                          
            packet += socket.inet_aton(ip)
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

    replica = "cdn-dns.5700.network:8080"
    cdn = CDN(replica, port + 1)
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