#!/usr/bin/env python3

import argparse
import socketserver
import http.server
from http.server import BaseHTTPRequestHandler
import requests
import sqlite3
import zlib
import os
import sys
import urllib.request

MB_20 = 18 * 1024 * 1024

class Cache:
    """
    Cache class for managing cached content.
    
    Attributes:
        connection (sqlite3.Connection): Connection to the SQLite database.
        handler (sqlite3.Cursor): Cursor for executing SQLite commands.
    """

    def __init__(self):
        """
        Initializes a new Cache instance by setting up the SQLite database.
        """

        self.connection = sqlite3.connect("cache.db", check_same_thread=False)
        self.handler = self.connection.cursor()
        self.handler.execute('''CREATE TABLE IF NOT EXISTS CACHE (Path TEXT, Content BLOB, Frequency INT, Size INT);''')

    def hit(self, data):
        """
        Checks if the given data is a cache hit.

        Args:
            data: The data to check for a cache hit.

        Returns:
            bool: True if the data is a cache hit, False otherwise.
        """

        return data is not None

    def get_data(self, path):
        """
        Retrieves the cached content for the given path, if available.

        Args:
            path (str): The path for which to retrieve cached content.

        Returns:
            bytes: The cached content, or None if not found.
        """

        self.handler.execute("SELECT * FROM Cache WHERE Path = :Path", {"Path": path})
        data = self.handler.fetchone()
        if self.hit(data):
            content = zlib.decompress(data[1])
            frequency = data[2]
            frequency += 1
            self.handler.execute("UPDATE Cache SET Frequency =:Frequency WHERE Path=:Path",
                                 {"Frequency": frequency, "Path": path})
            self.connection.commit()
            return content

        return None

    def close(self):
        """
        Closes the SQLite connection and commits any changes.
        """

        self.connection.commit()
        self.connection.close()

    def get_cache_size(self):
        """
        Retrieves the current size of the cache.

        Returns:
            int: The size of the cache in bytes.
        """

        cache_stat = os.stat('cache.db')
        cache_size = cache_stat.st_size
        return cache_size

    def over_size(self, data):
        """
        Checks if adding the given data to the cache would exceed the maximum cache size.

        Args:
            data: The data to check.

        Returns:
            bool: True if adding the data would exceed the maximum cache size, False otherwise.
        """

        cache_size = self.get_cache_size()
        return cache_size + sys.getsizeof(data) > MB_20

    def insert_data(self, path, data):
        """
        Inserts the given data into the cache.

        Args:
            path (str): The path associated with the data.
            data (bytes): The data to insert into the cache.
        """

        compressed_data = zlib.compress(data)
        size = sys.getsizeof(compressed_data)
        frequency = 1
        if self.over_size(compressed_data):
            self.evict(sys.getsizeof(compressed_data))

        self.handler.execute("INSERT INTO Cache(Path,Content,Frequency,Size)VALUES(?,?,?,?)",
                             (path, compressed_data, frequency, size))
        self.connection.commit()

    def evict(self, file_size):
        """
        Evicts the least frequently accessed items from the cache until there is enough space for the new file.

        Args:
            file_size (int): The size of the new file to be added to the cache.
        """

        cache_size = self.get_cache_size()
        while cache_size + file_size >= MB_20:
            self.handler.execute(
                "DELETE FROM Cache WHERE Path = (SELECT Path FROM Cache WHERE Frequency = (SELECT MIN(Frequency) FROM Cache))")
            self.connection.commit()
            self.handler.execute("VACUUM")
            cache_size = self.get_cache_size()


class HTTPReplicaRequestHandler(BaseHTTPRequestHandler):
    """
    HTTPReplicaRequestHandler subclasses BaseHTTPRequestHandler to serve
    resources that are on the desired origin. Sends a 404 if origin is not Project 5 orgin cdn.
    """

    cache = None
    origin = None

    def do_GET(self):
        """
        Handles GET requests by fetching the requested content from either the local cache or the origin server.
        Handles /grading/beacon by responding with 204.
        For other paths, it first checks if the content is available in the local cache. If it is, the content
        is returned from the cache. If the content is not found in the cache, it fetches the content from the origin
        server, adds it to the cache, and returns it to the client.
        """

        """
        #Send GET Request to origin
        path = self.path
        url = 'http://{origin}:8080'.format(origin=self.origin)
        url += path
        file = requests.get(url)
        """

        #/grading/beacon check
        #TODO: make get request to origin server and see result, might just return that instead of custom 204 response
        if self.path == '/grading/beacon':
            self.send_response(204)
            self.end_headers()
            return
        
        # Check if content is in the cache
        html = self.cache.get_data(self.path)

        if html is None:
            url = 'http://{origin}:8080'.format(origin=self.origin)
            url += self.path
            file = requests.get(url)
            html = file.content
            self.cache.insert_data(self.path, html)

        """
        #Send Client Response; Caching Functionality needs to be added after milestone
        self.send_response(file.status_code)
        #self.send_header(file.headers)
        self.end_headers()
        self.wfile.write(file.content)
        """
        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.end_headers()
        self.wfile.write(html)
    
def argumentParser():
    """
    Parses command line arguments.
    Supports:
        -p PORT: port to bind http server
        -o ORIGIN: CDN origin where content is fetched
    """
    #TODO: add http/https check
    parser = argparse.ArgumentParser(description="Project 5 Replica Server Implementation...")
    parser.add_argument('-p', '--port', type=int, help='port HTTP server will bind to')
    parser.add_argument('-o', '--origin', help='origin server of CDN')
    return parser.parse_args()

#2014X group: sukanyanag alloted ports
if __name__ == '__main__':
    args = argumentParser()
    PORT = args.port
    ORIGIN = args.origin

    Handler = HTTPReplicaRequestHandler
    Handler.origin = ORIGIN
    Handler.cache = Cache()
    
    with socketserver.TCPServer(("", PORT), Handler) as httpd:
        httpd.serve_forever()


#Resources
#1. https://docs.python.org/3/library/http.server.html#http.server.BaseHTTPRequestHandler
#2. https://docs.python.org/3/library/http.server.html