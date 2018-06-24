from socket import socket
from mesgex.constants import RequestCodes, ResponseCodes
from mesgex.connection import Connection, State


DefaultGreeting = """
Hi, nice to meet you. Welcome to the MESGEX chat server.
Feel free to start chatting with anyone!
░░░░░░░░░░░░░░░░░░░░░░░░░░░░░
░░░░░░░░░░░░░▄▄▄▄▄▄▄░░░░░░░░░
░░░░░░░░░▄▀▀▀░░░░░░░▀▄░░░░░░░
░░░░░░░▄▀░░░░░░░░░░░░▀▄░░░░░░
░░░░░░▄▀░░░░░░░░░░▄▀▀▄▀▄░░░░░
░░░░▄▀░░░░░░░░░░▄▀░░██▄▀▄░░░░
░░░▄▀░░▄▀▀▀▄░░░░█░░░▀▀░█▀▄░░░
░░░█░░█▄▄░░░█░░░▀▄░░░░░▐░█░░░
░░▐▌░░█▀▀░░▄▀░░░░░▀▄▄▄▄▀░░█░░
░░▐▌░░█░░░▄▀░░░░░░░░░░░░░░█░░
░░▐▌░░░▀▀▀░░░░░░░░░░░░░░░░▐▌░
░░▐▌░░░░░░░░░░░░░░░▄░░░░░░▐▌░
░░▐▌░░░░░░░░░▄░░░░░█░░░░░░▐▌░
░░░█░░░░░░░░░▀█▄░░▄█░░░░░░▐▌░
░░░▐▌░░░░░░░░░░▀▀▀▀░░░░░░░▐▌░
░░░░█░░░░░░░░░░░░░░░░░░░░░█░░
░░░░▐▌▀▄░░░░░░░░░░░░░░░░░▐▌░░
░░░░░█░░▀░░░░░░░░░░░░░░░░▀░░░
░░░░░░░░░░░░░░░░░░░░░░░░░░░░░
"""


class ClientConnection(Connection):
    def connect(self, addr, message='Nice meeting you.'):
        raise NotImplementedError

    def __init__(self, server, conn: socket = None, greeting=DefaultGreeting):
        self.server = server
        self.greeting = greeting
        self.name = None
        super().__init__(conn)

    @property
    def parent(self):
        return self.server

    @parent.setter
    def parent(self, value):
        self.server = value

    def process_message(self):
        code, message = super(ClientConnection, self).process_message()

        if self.state == State.CONNECTING:
            if code == RequestCodes.HELLO:
                print('SCC: Received client HELLO with name: {}'.format(message))
                self.name = message
                if self.server.check_availability(message):
                    self.send_msg(ResponseCodes.HELLO_OK_1, self.greeting)
                else:
                    self.reject('Name invalid or unavailable.')
            elif code == ResponseCodes.HELLO_OK_1:
                print('SCC: Error: Received HELLO_OK_1 from client.')
                self.send_msg(ResponseCodes.ERROR, 'Received HELLO_OK_1 from client.')
                self.close()
            elif code == ResponseCodes.HELLO_OK_2:
                if self.server.check_availability(self.name):
                    print('SCC: Established connection with client named: {}'.format(self.name))
                    self.state = State.CONNECTED
                    self.server.client_connected(self.name, self)
                else:
                    self.reject()
            else:
                self.reject()
        elif self.state == State.CONNECTED:
            if code == RequestCodes.PRESENCE_CHECK:
                self.server.check_presence(message, self)

    def close(self):
        super().close()
        self.server.client_disconnected(self.name, self)
