"""
To install the Simple Websocket Server module run:
pip install git+https://github.com/dpallot/simple-websocket-server.git
"""
from socket import socket, SHUT_RDWR
from threading import Thread

from SimpleWebSocketServer import WebSocket


class MesgexWebSocket(WebSocket):
    mesgex_server_addr = None  # address tuple in the form (address, port)
    recv_size = 1024

    def __init__(self, *args, **kwargs):
        try:
            assert isinstance(self.mesgex_server_addr, tuple), 'self.mesgex_server_addr has to be an address tuple.'
            assert len(self.mesgex_server_addr) == 2, 'self.mesgex_server_addr has to contain two elements.'
            assert isinstance(self.mesgex_server_addr[0], str), 'First element of self.mesgex_server_addr has to be ' \
                                                                'an address string.'
            assert isinstance(self.mesgex_server_addr[1], int), 'Second element of self.mesgex_server_addr has to be ' \
                                                                'a port number.'
        except AssertionError as err:
            print(err)
            raise

        super().__init__(*args, **kwargs)

        self.mesgex_server_conn = socket()
        self.mesgex_server_conn.setblocking(True)
        self.mesgex_receive_thread = None

    def mesgex_receive_data(self):
        try:
            while True:
                recv_buf = self.mesgex_server_conn.recv(self.recv_size)
                print('MESGEX message: {}'.format(recv_buf))
                if recv_buf:
                    self.sendMessage(recv_buf.decode('utf-8'))
                else:
                    print('CON: Connection has been closed by remote host.')
                    self.close()
                    break
        except OSError:
            print('CON: OSError: stopping receive thread.')

    def handleMessage(self):
        print('WS message: {}'.format(self.data))
        self.mesgex_server_conn.sendall(self.data.encode('utf-8'))

    def handleConnected(self):
        print(self.address, 'connected')

        self.mesgex_server_conn.connect(self.mesgex_server_addr)

        assert self.mesgex_receive_thread is None, 'This connection is already running.'
        self.mesgex_receive_thread = Thread(target=self.mesgex_receive_data, name='MESGEX Receive Thread')
        self.mesgex_receive_thread.start()

    def handleClose(self):
        print(self.address, 'closed')
        try:
            self.mesgex_server_conn.shutdown(SHUT_RDWR)
        except OSError:
            pass
        self.mesgex_server_conn.close()


