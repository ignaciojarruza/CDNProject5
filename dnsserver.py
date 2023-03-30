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
        with open(file_path) as file:
            lines = file.readlines()
            for line in lines:
                # Only add the line to the replicas list if it contains ".com" and is not an origin server
                self.replicas.append(line.strip('\r\n'))


    def get_url(self, url, ip, ips):
        """
        Sends a request to the specified URL with the given IP address and records the round-trip time.

        Args:
            url (str): The URL to send the request to.
            ip (str): The IP address to include in the request.
            ips (dict): A dictionary to store the round-trip times for each replica server.
        """

        query = "http://" + url + ':' + str(self.port) + "/" + ip
        try:
            rtt = urllib.request.urlopen(query).read()
            ips[float(rtt)] = url
        except urllib.error.URLError:
            # Ignore URLError exceptions (e.g. server is down)
            pass


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
        # Create a thread for each replica server and start them
        for u in self.replicas:
            t = threading.Thread(target=self.get_url, args=(u, ip, ips))
            t.daemon = True
            t.start()
            threads.append(t)
        for t in threads:
            t.join()
        s = min(ips.keys())
        print(ips)
        return ips[s]


class DNSQuery:

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
                index = index+1
                indexend = index+N
                Domain.append(''.join(map(chr, data[index:indexend])))
                index=indexend
                C = unpack("!c", data[index])[0]
            Domain = '.'.join(Domain)
            self.Qclass, self.qtype = unpack("!2H", data[index:index+4])
            self.domain = Domain
            self.todomainlength = index
            print (Domain)


    def checkCdn(self, cdn):
        """
        Sends a request to a given CDN object and retrieves the IP address of the replica server with the shortest
        round-trip time for the current client.

        Args:
            cdn(CDN): A CDN object that contains a list of replica servers.

        Returns:
            str: The IP address of the replica server with the shortest round-trip time for the current client.
        """
        ip = cdn.best_rtt(self.clientIP)
        print(ip)
        return ip


    def respuesta(self, cdn):
        """
        Constructs and returns a response packet for the DNS query.

        Args:
            cdn (CDN): A CDN object that contains a list of replica servers.

        Returns:
            str: A response packet for the DNS query.
        """

        packet = ''
        ip = socket.inet_aton(self.checkCdn(cdn))
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
            packet += ip
        else:
            packet = ''
        return packet
    

    def getip(self, data):
        """
        Retrieves the IP address corresponding to the given domain name from a DNS record file.

        Args:
            data (str): The domain name for which to retrieve the IP address.

        Returns:
        str: The IP address corresponding to the domain name, if found in the DNS record file. An empty string
        otherwise.
        """

        record=open("example.txt",'r').read()
        if data in record:
            for line in record.split('\n'):
                if data == line.split()[0]:
                    return line.split()[-1]
        else:
            return ""


    def handleQuery(udps, data, add, cdn, name):
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
            reply = query.respuesta(cdn)
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
        file = "testme.txt"
        if port == 65535:
            rttPort = 65534
        else:
            rttPort = port + 1
        cdn =  CDN(file,rttPort)
        print ("reaching here")

        while 1:
            try:
                data,add = udps.recvfrom(1024)
                t = threading.Thread(target = handleQuery, args=(udps, data, add, cdn, name))
                t.daemon = True
                t.start()
            except KeyboardInterrupt:
                break

    if __name__ == "__main__":
        if len(sys.argv)!=5:
            print("Error:Incorrect number of Arguments")
        else:
            main(sys.argv)