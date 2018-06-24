from mesgex.client.client_connection import ClientConnection
from mesgex.constants import RequestCodes
from mesgex.message import decipher_message_msg, decipher_presence_response_msg


class Client:
    def __init__(self, server_addr=('localhost', 60606)):
        self.server_addr = server_addr
        self.client_connection = ClientConnection(self)

    def connect(self, name):
        self.client_connection.connect(self.server_addr, name)

    def send_message_to(self, recipient: str, message: str):
        self.client_connection.send_message_to(recipient, message)

    def received_message(self, buffer: bytes):
        sender, recipient, message = decipher_message_msg(buffer)
        print('C: Received message from {}: {}'.format(
            sender.decode('utf-8'),
            message.decode('utf-8'),
        ))
        self.client_connection.send_message_delivered_to(sender, message)

    def message_delivered(self, buffer: bytes):
        sender, recipient, message = decipher_message_msg(buffer)
        print('C: Message to {} delivered.'.format(recipient.decode('utf-8')))

    def check_presence(self, name: str):
        self.client_connection.send_msg(RequestCodes.PRESENCE_CHECK, name)

    def presence_response(self, response: bytes):
        name, presence = decipher_presence_response_msg(response)
        print('{}\'s status is {}'.format(name, presence.decode('utf-8')))

    def close(self):
        self.client_connection.close()
