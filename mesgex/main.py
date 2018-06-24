from mesgex.server.server import Server


class ServerApp:
    def __init__(self, *args, **kwargs):
        self._server = Server(*args, **kwargs)

    def run_service(self):
        self._server.run_server()

    def stop_service(self):
        self._server.stop_server()
