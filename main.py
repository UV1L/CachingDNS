import socket
import threading
import argparse
import cache as c
from cacheparser import CacheParser


parser = argparse.ArgumentParser(description='You started a DNS-script.'
                                             ' Enter a server to use '
                                             'this. Good luck!')
parser.add_argument('-s', '--server', help='This will be your server')
server_name = parser.parse_args().server


def main():
    if server_name is not None:
        server = server_name
    else:
        server = input()
    cache = c.Cache()
    while KeyboardInterrupt:
        try:
            cache.get_cache()
            solve(cache, server)
        except Exception:
            pass


def solve(cache, server):
    while 1:
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.bind(("127.0.0.1", 53))
            data, addr = sock.recvfrom(512)
            if not data:
                break

            parsed_data = CacheParser.parse_from(data)
            cached = cache.read_cache(parsed_data)
            if cached is None:
                returned_data = get_recv(server, data)
                caching_data = CacheParser.parse_from(returned_data)
                cache.cache(caching_data)
            else:
                returned_data = CacheParser.parse_to(parsed_data, cached)

            sock.sendto(returned_data, addr)
        finally:
            sock.close()
            cache.set_cache()


def get_recv(server, data):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(("", 0))
    sock.sendto(data, (server, 53))
    return sock.recvfrom(512)[0]


if __name__ == "__main__":
    main()
