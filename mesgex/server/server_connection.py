from socket import socket
from mesgex.constants import RequestCodes, ResponseCodes
from mesgex.connection import Connection, State


class ServerConnection(Connection):
    def __init__(self, server, conn: socket = None):
        self.server = server
        super().__init__(conn)

    @property
    def parent(self):
        return self.server

    @parent.setter
    def parent(self, value):
        self.server = value

    def process_message(self):
        code, message = super(ServerConnection, self).process_message()

        if self.state == State.CONNECTING:
            if code == RequestCodes.HELLO:
                print('SC: Received HELLO with message: {}'.format(message))
                self.send_msg(ResponseCodes.HELLO_OK_1, self.server.server_id)
            elif code == ResponseCodes.HELLO_OK_1:
                print('SC: Established connection with server identified as: {}'.format(message))
                self.state = State.CONNECTED
                self.remote_server_id = message
                if self.server.server_connection_established(self.remote_server_id, self):
                    self.send_msg(ResponseCodes.HELLO_OK_2, self.server.server_id)
                    self.server.tell_all_routes(self)
                else:
                    self.reject()
            elif code == ResponseCodes.HELLO_OK_2:
                print('SC: Established connection with server identified as: {}'.format(message))
                self.state = State.CONNECTED
                self.remote_server_id = message
                if not self.server.server_connection_established(self.remote_server_id, self):
                    self.reject()
                else:
                    self.server.tell_all_routes(self)
            else:
                self.reject()
        elif self.state == State.CONNECTED:
            if code == RequestCodes.ROUTE_CHANGE:
                self.server.route_msg_received(self, message)

    def close(self):
        super(ServerConnection, self).close()
        self.server.server_connection_closed(self.remote_server_id, self)
