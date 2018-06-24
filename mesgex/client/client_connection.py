from socket import socket
from mesgex.connection import Connection, State
from mesgex.constants import RequestCodes, ResponseCodes
from mesgex.message import format_message_msg


class ClientConnection(Connection):
    def __init__(self, client, conn: socket = None):
        self.client = client
        self.name = None
        super().__init__(conn)

    @property
    def parent(self):
        return self.client

    @parent.setter
    def parent(self, value):
        self.client = value

    def process_message(self):
        code, message = super(ClientConnection, self).process_message()

        if self.state == State.CONNECTING:
            if code == ResponseCodes.HELLO_OK_1:
                print('CCC: Established connection with server.')
                self.state = State.CONNECTED
                self.send_msg(ResponseCodes.HELLO_OK_2)
            elif code == ResponseCodes.HELLO_OK_2:
                print('CCC: Error: Received HELLO_OK_2 from client.')
                self.send_msg(ResponseCodes.ERROR, 'Received HELLO_OK_2 from client.')
                self.close()
            else:
                self.reject()
        elif self.state == State.CONNECTED:
            if code == ResponseCodes.PRESENCE_RESPONSE:
                self.client.presence_response(message)

    def send_message_to(self, recipient: str, message: str):
        assert self.state == State.CONNECTED, 'The client needs to be connected to send a message.'
        self.send_msg(RequestCodes.MESSAGE_SEND, format_message_msg(self.name, recipient, message,
                                                                    RequestCodes.MESSAGE_SEND))

    # noinspection PyMethodOverriding
    def connect(self, addr, name):
        super().connect(addr, name)
        self.name = name

    def send_message_delivered_to(self, sender: bytes, message: bytes):
        assert isinstance(sender, bytes), 'sender must be of type bytes'
        assert isinstance(message, bytes), 'message must be of type bytes'
        self.send_msg(ResponseCodes.MESSAGE_DELIVERED, format_message_msg(self.name, sender, message,
                                                                          ResponseCodes.MESSAGE_DELIVERED))

