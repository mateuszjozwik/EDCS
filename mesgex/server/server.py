from threading import Lock, Thread
from socket import socket, SHUT_RDWR, SOL_SOCKET, SO_REUSEADDR
from typing import Dict

from mesgex.connection import Connection
from mesgex.constants import RequestCodes, ResponseCodes, PresenceStatus
from mesgex.message import decipher_message_msg, format_route_msg, decipher_route_msg, format_presence_response_msg, \
    format_message_msg
from mesgex.server.server_connection import ServerConnection
from mesgex.server.client_connection import ClientConnection
from uuid import uuid4


class Route:
    def __init__(self, hop_count=0, connection=None):
        self.connection = connection
        self.hop_count = hop_count

    def update(self, hop_count, connection):
        self.connection = connection
        self.hop_count = hop_count


class RouteNotFoundException(Exception):
    pass


class Server:
    client_routing = ...  # type: Dict[bytes, Route]

    def __init__(self, servers_to_connect_to: list = None, max_servers: int = 5,
                 server_listening_addr=('127.0.0.1', 60606),
                 client_listening_addr=('127.0.0.1', 60607)):
        self.max_servers = max_servers

        self.server_id = str(uuid4())
        self.server_connections = {}
        self.new_servers = []
        self.new_server_lock = Lock()
        self.server_listening_addr = server_listening_addr
        self.server_listening_thread = None
        self.server_listening_sock = None

        self.new_clients = []
        self.client_routing = {}
        self.client_routing_lock = Lock()
        self.client_connections = {}
        self.new_client_lock = Lock()
        self.client_listening_addr = client_listening_addr
        self.client_listening_thread = None
        self.client_listening_sock = None

        self.connecting_thread = None
        if servers_to_connect_to:
            self.connecting_thread = Thread(target=self.connect_to_servers, args=(servers_to_connect_to,),
                                            name='Connecting Thread')
            self.connecting_thread.start()

    def server_run_listening(self):
        self.server_listening_sock = socket()
        self.server_listening_sock.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
        self.server_listening_sock.bind(self.server_listening_addr)
        self.server_listening_sock.listen(5)
        while True:
            try:
                conn, addr = self.server_listening_sock.accept()
            except OSError:
                print('S: Stopping listening for new server connections.')
                break
                # raise
            sc = ServerConnection(self, conn)
            accept = True

            with self.new_server_lock:
                if len(self.server_connections) + len(self.new_servers) < self.max_servers:
                    self.new_servers.append(sc)
                else:
                    accept = False

            if accept:
                sc.accept()
            else:
                sc.reject()

            sc.run()

    def client_run_listening(self):
        self.client_listening_sock = socket()
        self.client_listening_sock.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
        self.client_listening_sock.bind(self.client_listening_addr)
        self.client_listening_sock.listen(5)
        while True:
            try:
                conn, addr = self.client_listening_sock.accept()
            except OSError:
                print('S: Stopping listening for new client connections.')
                break
            with self.new_client_lock:
                cc = ClientConnection(self, conn)
                self.new_clients.append(cc)
            cc.accept()
            cc.run()

    def route_msg_received(self, connection, msg):
        routes = decipher_route_msg(msg)
        for client, hop_count in routes:
            self.route_change(client, hop_count, connection)

    def route_change(self, client_name: bytes, hop_count: int, connection: Connection):
        tell_the_others = False
        with self.client_routing_lock:
            if client_name in self.client_routing:
                route = self.client_routing[client_name]
                if hop_count == 0 and route.connection is connection:
                    del self.client_routing[client_name]
                    tell_the_others = True
                elif hop_count < route.hop_count:
                    route.update(hop_count, connection)
                    tell_the_others = True
            else:
                if hop_count > 0:
                    self.client_routing[client_name] = Route(hop_count, connection)
                    tell_the_others = True
        if tell_the_others:
            with self.new_server_lock:
                new_hop_count = hop_count+1 if hop_count != 0 else 0
                for server_id, server_connection in filter(lambda item: item[1] is not connection,
                                                           self.server_connections.items()):
                    server_connection.send_msg(RequestCodes.ROUTE_CHANGE,
                                               format_route_msg([(client_name, new_hop_count)]))

    def run_server(self):
        self.server_listening_thread = Thread(target=self.server_run_listening, name='Listening Thread')
        self.server_listening_thread.start()

        self.client_listening_thread = Thread(target=self.client_run_listening, name='Listening Thread')
        self.client_listening_thread.start()

    def stop_server(self):
        with self.new_server_lock:
            for server_id, server in self.server_connections.items():
                try:
                    server.conn.shutdown(SHUT_RDWR)
                except OSError:
                    pass
                server.conn.close()
        self.server_listening_sock.shutdown(SHUT_RDWR)
        self.server_listening_sock.close()

        self.client_listening_sock.shutdown(SHUT_RDWR)
        self.client_listening_sock.close()

    def client_connected(self, name: bytes, client_connection: ClientConnection):
        with self.new_client_lock:
            self.new_clients.remove(client_connection)
            self.client_connections[name] = client_connection
        self.route_change(name, 1, client_connection)

    def client_disconnected(self, name: str, client_connection: ClientConnection):
        with self.new_client_lock:
            if client_connection in self.new_clients:
                self.new_clients.remove(client_connection)
            else:
                del self.client_connections[name]
        self.route_change(name, 0, client_connection)

    def tell_all_routes(self, connection):
        with self.client_routing_lock:
            routes = [(client, route.hop_count + 1) for client, route in self.client_routing.items()]
        connection.send_msg(RequestCodes.ROUTE_CHANGE, format_route_msg(routes))

    def server_connection_established(self, server_id: str, server_connection: ServerConnection):
        accept = False
        with self.new_server_lock:
            if len(self.server_connections) < self.max_servers:
                self.server_connections[server_id] = server_connection
                self.new_servers.remove(server_connection)
                accept = True
            else:
                server_connection.reject()
        return accept

    def server_connection_closed(self, server_id: str, server_connection: ServerConnection):
        with self.new_server_lock:
            if server_id:
                del self.server_connections[server_id]
            else:
                self.new_servers.remove(server_connection)

    def connect_to_servers(self, servers):
        for server in servers:
            sc = ServerConnection(self, socket())
            with self.new_server_lock:
                if len(self.server_connections) < self.max_servers:
                    sc.connect(server)
                    self.new_servers.append(sc)
                else:
                    break

    def check_availability(self, name):
        if name \
                and b':' not in name \
                and b';' not in name \
                and name not in self.client_routing:
            return True
        else:
            return False

    def received_message(self, buffer: bytes, connection: Connection):
        """Forward message to client or server."""
        sender, recipient, message = decipher_message_msg(buffer)
        try:
            self.get_connection_for_client(recipient).send_msg(RequestCodes.MESSAGE_SEND, buffer)
        except RouteNotFoundException:
            print('S: Route to {} not found.'.format(recipient.decode('utf-8')))
            connection.send_msg(ResponseCodes.MESSAGE_FAILED,
                                format_message_msg(sender, recipient, message, ResponseCodes.MESSAGE_FAILED))

    def message_delivered(self, buffer: bytes):
        sender, recipient, message_hash = decipher_message_msg(buffer)
        print('S: Message to {} delivered. Hash: {}'.format(recipient.decode('utf-8'), message_hash.decode('utf-8')))
        try:
            self.get_connection_for_client(sender).send_msg(ResponseCodes.MESSAGE_DELIVERED, buffer)
        except RouteNotFoundException:
            print('S: No one to deliver message delivered message.')

    def message_failed(self, buffer: bytes):
        sender, recipient, message_hash = decipher_message_msg(buffer)
        print('S: Message to {} failed. Hash: {}'.format(recipient.decode('utf-8'), message_hash.decode('utf-8')))
        try:
            self.get_connection_for_client(sender).send_msg(ResponseCodes.MESSAGE_DELIVERED, buffer)
        except RouteNotFoundException:
            print('S: No one to deliver message delivered message.')

    def get_connection_for_client(self, client: bytes) -> Connection:
        if client in self.client_connections:
            return self.client_connections[client]
        elif client in self.client_routing:
            return self.client_routing[client].connection
        else:
            raise RouteNotFoundException

    def check_presence(self, name, connection):
        if name in self.client_connections or name in self.client_routing:
            connection.send_msg(ResponseCodes.PRESENCE_RESPONSE,
                                format_presence_response_msg(name, PresenceStatus.ONLINE))
        else:
            connection.send_msg(ResponseCodes.PRESENCE_RESPONSE,
                                format_presence_response_msg(name, PresenceStatus.OFFLINE))
