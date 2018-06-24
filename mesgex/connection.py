from threading import Thread, Lock
from socket import socket, SHUT_RDWR
from typing import Union
from mesgex.message import create_msg, decipher_msg, NeedMoreDataException
from mesgex.constants import RequestCodes, ResponseCodes, DefaultMessage


class ErrorRejectCodeException(Exception):
    pass


class State:
    CONNECTING = 1

    CONNECTED = 10

    CLOSED = 99


class Connection:
    # TODO add checking of connection status through PINGs

    recv_size = 1024

    def __init__(self, conn: socket = None):
        self.conn = conn or socket()
        self.state = None
        self.remote_server_id = None
        self.send_lock = Lock()
        self.last_ping_message = None

        self.recv_buf = b''
        self.recv_thread = None

    @property
    def parent(self):
        raise NotImplementedError

    @parent.setter
    def parent(self, value):
        raise NotImplementedError

    def run(self):
        assert self.recv_thread is None, 'This connection is already running.'
        self.recv_thread = Thread(target=self.receive_data, name='Receive Thread')
        self.recv_thread.start()

    def send_msg(self, code: int, message: Union[str, bytes] = None, blocking=False):
        with self.send_lock:
            try:
                if not blocking:
                    self.conn.setblocking(False)
                self.conn.sendall(create_msg(code, message))
            finally:
                if not blocking:
                    self.conn.setblocking(True)

    def send_ping(self, message: str = DefaultMessage[RequestCodes.PING]):
        self.last_ping_message = message
        self.send_msg(RequestCodes.PING, message)

    def receive_pong(self, message):
        if message != self.last_ping_message:
            print('CON: Received PONG with wrong reply message: {}'.format(message))

    def receive_data(self):
        try:
            while True:
                self.recv_buf += self.conn.recv(self.recv_size)
                if self.recv_buf:
                    try:
                        self.process_message()
                    except NeedMoreDataException:
                        pass
                else:
                    print('CON: Connection has been closed by remote host.')
                    self.close()
                    break
        except OSError:
            print('CON: OSError: stopping receive thread.')
        except ErrorRejectCodeException:
            print('CON: Error code received. Stopping receive thread.')

    def process_message(self):
        assert self.state is not None, 'Processing message with undefined state.'

        code, message, self.recv_buf = decipher_msg(self.recv_buf)

        if code == ResponseCodes.ERROR:
            self.close()
            raise ErrorRejectCodeException('Received ERROR code. Closing connection')
        elif code == ResponseCodes.REJECT:
            self.close()
            raise ErrorRejectCodeException('Received REJECT code. Closing connection')

        if self.state == State.CONNECTED:
            if code == RequestCodes.PING:
                self.send_msg(ResponseCodes.PONG, message)
            elif code == ResponseCodes.PONG:
                self.receive_pong(message)
            elif self.state == State.CONNECTED:
                if code == RequestCodes.MESSAGE_SEND:
                    self.parent.received_message(message)
                elif code == ResponseCodes.MESSAGE_DELIVERED:
                    self.parent.message_delivered(message)

        return code, message

    def accept(self):
        assert self.state is None, 'Invalid server state.'
        self.state = State.CONNECTING

    def reject(self, message=None):
        print('CON: Rejecting connection.')
        self.send_msg(ResponseCodes.REJECT, message)
        self.close()

    def connect(self, addr, message='Nice meeting you.'):
        self.conn.connect(addr)
        self.send_msg(RequestCodes.HELLO, message)
        self.state = State.CONNECTING
        self.run()

    def close(self):
        try:
            self.conn.shutdown(SHUT_RDWR)
        except OSError:
            pass
        self.conn.close()
