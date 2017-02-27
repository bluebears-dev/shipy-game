# *-* coding: utf-8 *-*
# Author: pgorski42
# Date: 28.12.16

import atexit
import socket
import sys
import time


class Server:

    def __init__(self, port = 7777):
        self.address = (socket.gethostname(), port)
        self.socket = socket.socket()
        self.socket.bind(self.address)
        print('\nServer bound on: %s' % socket.gethostbyname(socket.gethostname()))
        print('-----------------------------------------------------------------')
        self.players = []
        self.index = 1
        self.ships = []
        self.coords = None

    def listen(self):
        self.socket.listen()
        client = self.socket.accept()
        print(client[1])
        msg = client[0].recv(20480).decode()
        query = msg.rsplit(sep = '|')

        if query[0] == 'ships':
            print('Received ships: %s' % query[1])
            self.ships.append(query[1])
            client[0].send(str(len(self.ships) % 2).encode())
        elif query[0] == 'coords':
            if not self.coords:
                print('Received coords: %s' % query[1])
                self.coords = query[1]
            client[0].send(str(self.coords).encode())
        elif query[0] == 'get_coords':
            print('Sending coords: %s' % self.coords)
            client[0].send(str(self.coords).encode())
            self.coords = None
        elif query[0] == 'get_player':
            print('Requested player name')
            print(len(self.players))
            if len(self.players) - 1 >= int(query[1]):
                client[0].send(self.players[int(query[1])].encode())
                print(self.players[int(query[1])])
            else:
                client[0].send(str(None).encode())
        elif query[0] == 'get_ships':
            print('Requested ships')
            if len(self.ships) - 1 >= int(query[1]):
                client[0].send(self.ships[int(query[1])].encode())
            else:
                client[0].send(str(None).encode())
        elif query[0] == 'player':
            print('Received player name: %s' % query[1])
            self.players.append(query[1])
            client[0].send(str(len(self.players) % 2).encode())
        elif query[0] == 'clear':
            print('Clearing data')
            self.ships = []
            self.players = []
            self.index = 1
            self.coords = None
        elif query[0] == 'test':
            print('Connection accepted')
        print('-----------------------------------------------------------------')

    def close(self):
        if self.socket:
            self.socket.close()

try:
    s = Server()
except OSError:
    print('Cannot start')
    s = None
    start_time = time.time()
    while not s:
        try:
            s = Server()
        except OSError:
            if (time.time() - start_time) > 1.0:
                print('|', end='')
                sys.stdout.flush()
                start_time = time.time()
            s = None

atexit.register(lambda: (s.close(), print('Terminating server...')))
while True:
    s.listen()
