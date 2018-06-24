from threading import Thread
from time import sleep
from socket import socket
from uuid import uuid4
from random import randint

from mesgex.client.client import Client
from mesgex.main import ServerApp
from mesgex.message import create_msg, decipher_msg
from mesgex.constants import RequestCodes, ResponseCodes


def run_thread(*args, **kwargs):
    t = Thread(*args, **kwargs)
    t.start()


def simple_hello_one_server():
    port = randint(20000, 60000)
    server_app = ServerApp(server_listening_addr=('localhost', port))
    t = Thread(target=server_app.run_service, name='Server Thread')
    t.start()
    sleep(0.1)
    my_uuid = str(uuid4())
    with socket() as s:
        s.connect(('localhost', port))
        s.sendall(create_msg(RequestCodes.HELLO))
        data = s.recv(1024)
        code, msg, _ = decipher_msg(data)
        assert code == ResponseCodes.HELLO_OK_1, 'Response code was {}'.format(code)
        print('The other server\'s UUID is {}'.format(msg))
        s.sendall(create_msg(ResponseCodes.HELLO_OK_2, my_uuid))

    server_app.stop_service()

    print('TEST simple_hello_one_server completed.')


def two_server_hello():
    threads = []
    port = randint(20000, 60000)
    print('Chosen port: {}'.format(port))

    s1 = ServerApp(server_listening_addr=('localhost', port),
                   client_listening_addr=('localhost', port+1))
    threads.append(run_thread(target=s1.run_service))

    sleep(0.1)

    s2 = ServerApp(server_listening_addr=('localhost', port+2),
                   client_listening_addr=('localhost', port+3),
                   servers_to_connect_to=(('localhost', port),))
    threads.append(run_thread(target=s2.run_service))

    sleep(1)
    s1.stop_service()
    s2.stop_service()

    print('TEST two_server_hello completed.')


def ping_test():
    threads = []
    port = randint(20000, 60000)
    print('Chosen port: {}'.format(port))

    s1 = ServerApp(server_listening_addr=('localhost', port),
                   client_listening_addr=('localhost', port+1))
    threads.append(run_thread(target=s1.run_service))

    sleep(0.1)

    s2 = ServerApp(server_listening_addr=('localhost', port+2),
                   client_listening_addr=('localhost', port+3),
                   servers_to_connect_to=(('localhost', port),))
    threads.append(run_thread(target=s2.run_service))

    sleep(0.2)

    for server_id, server_connection in s2._server.server_connections.items():
        server_connection.send_ping()

    sleep(0.2)

    s1.stop_service()
    s2.stop_service()

    print('TEST ping_test completed.')


def client_basic_test():
    threads = []
    port = randint(20000, 60000)
    print('Chosen port: {}'.format(port))

    s1 = ServerApp(server_listening_addr=('localhost', port),
                   client_listening_addr=('localhost', port+1))
    threads.append(run_thread(target=s1.run_service))

    sleep(0.2)
    
    cc = Client(server_addr=('localhost', port+1))
    cc.connect('George')
    
    sleep(0.5)
    
    print('Client state: {}'.format(cc.client_connection.state))
    
    s1.stop_service()
    cc.client_connection.close()

    sleep(0.1)
    
    print('TEST client_basic_test completed.')


def two_clients_one_server():
    threads = []
    port = randint(20000, 60000)
    print('Chosen port: {}'.format(port))

    s1 = ServerApp(server_listening_addr=('localhost', port),
                   client_listening_addr=('localhost', port+1))
    threads.append(run_thread(target=s1.run_service))

    sleep(0.2)

    c1 = Client(server_addr=('localhost', port+1))
    c1.connect('George')

    c2 = Client(server_addr=('localhost', port+1))
    c2.connect('James')

    sleep(0.5)

    c2.send_message_to('George', 'Test message for George of the jungle.')

    sleep(0.5)

    s1.stop_service()
    c1.client_connection.close()
    c2.client_connection.close()

    sleep(0.1)

    print('TEST two_clients_one_server completed.')


def three_clients_two_servers():
    threads = []
    port = randint(20000, 60000)
    print('Chosen port: {}'.format(port))

    s1 = ServerApp(server_listening_addr=('localhost', port),
                   client_listening_addr=('localhost', port+1))
    threads.append(run_thread(target=s1.run_service))

    sleep(0.2)

    c1 = Client(server_addr=('localhost', port+1))
    c1.connect('George')

    sleep(0.1)

    s2 = ServerApp(server_listening_addr=('localhost', port+2),
                   client_listening_addr=('localhost', port+3),
                   servers_to_connect_to=(('localhost', port),))
    threads.append(run_thread(target=s2.run_service))

    sleep(0.1)

    c2 = Client(server_addr=('localhost', port+3))
    c2.connect('James')

    sleep(0.1)

    c3 = Client(server_addr=('localhost', port+3))
    c3.connect('Jones')

    sleep(0.2)

    c2.send_message_to('George', 'Test message for George of the jungle.')

    sleep(0.2)

    c1.send_message_to('Jones', 'A little love note to Jones from George.')

    sleep(0.2)

    s1.stop_service()
    s2.stop_service()
    c1.client_connection.close()
    c2.client_connection.close()
    c3.client_connection.close()

    sleep(0.1)

    print('TEST three_clients_two_servers completed.')


def three_clients_two_servers_check_presence():
    threads = []
    port = randint(20000, 60000)
    print('Chosen port: {}'.format(port))

    s1 = ServerApp(server_listening_addr=('localhost', port),
                   client_listening_addr=('localhost', port+1))
    threads.append(run_thread(target=s1.run_service))

    sleep(0.2)

    c1 = Client(server_addr=('localhost', port+1))
    c1.connect('George')

    sleep(0.1)

    s2 = ServerApp(server_listening_addr=('localhost', port+2),
                   client_listening_addr=('localhost', port+3),
                   servers_to_connect_to=(('localhost', port),))
    threads.append(run_thread(target=s2.run_service))

    sleep(0.1)

    c2 = Client(server_addr=('localhost', port+3))
    c2.connect('James')

    sleep(0.1)

    c3 = Client(server_addr=('localhost', port+3))
    c3.connect('Jones')

    sleep(0.2)

    c1.check_presence('Jones')

    sleep(0.2)

    c3.client_connection.close()

    sleep(0.2)

    c1.check_presence('Jones')

    s1.stop_service()
    s2.stop_service()
    c1.client_connection.close()
    c2.client_connection.close()

    sleep(0.1)

    print('TEST three_clients_two_servers_check_presence completed.')


if __name__ == '__main__':
    simple_hello_one_server()
    sleep(0.1)
    two_server_hello()
    sleep(0.1)
    ping_test()
    sleep(0.1)
    client_basic_test()
    sleep(0.1)
    two_clients_one_server()
    sleep(0.1)
    three_clients_two_servers()
    sleep(0.1)
    three_clients_two_servers_check_presence()
