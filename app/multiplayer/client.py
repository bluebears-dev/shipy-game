# *-* coding: utf-8 *-*
# Author: pgorski42
# Date: 29.12.16


import socket


class Client:

    def __init__(self, address = ('127.0.0.1', 7777)):
        self.server_address = address
        self.message = None
        self.socket = socket.socket()

    def establish_connection(self):
        self.socket.close()
        self.socket = socket.socket()
        self.socket.connect(self.server_address)

    def request(self, query, data = ''):
        self.establish_connection()
        self.socket.send((str(query) + '|' + str(data)).encode())
        self.message = self.socket.recv(20480)
        if self.message:
            self.message = self.message.decode()
        return self.message
