import random
from mesgex.main import ServerApp


if __name__ == '__main__':
    server_app = ServerApp(client_listening_addr=('localhost', 60009))
    server_app.run_service()
