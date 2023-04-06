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