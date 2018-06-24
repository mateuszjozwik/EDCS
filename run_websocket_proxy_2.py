import random

from SimpleWebSocketServer import SimpleWebSocketServer
from mesgex.websocket import MesgexWebSocket


class WS1(MesgexWebSocket):
    mesgex_server_addr = ('localhost', 60009)

if __name__ == '__main__':
    """
// To connect through JS (assuming port = 60266) use this:
port = 60266

ws1 = new WebSocket('ws://localhost:' + port);
ws1.onmessage = function(ev){console.log('George received: ' + ev.data)};
setTimeout(function(){ ws1.send('600 6 George') }, 100);
setTimeout(function(){ ws1.send('201 0 ') }, 300);

ws2 = new WebSocket('ws://localhost:' + port);
ws2.onmessage = function(ev){console.log('James received: ' + ev.data)};
setTimeout(function(){ ws2.send('600 5 James') }, 500);
setTimeout(function(){ ws2.send('201 0 ') }, 600);

setTimeout(function(){ ws2.send('250 51 James:George:Test message for George of the jungle.') }, 1000);
// George's confirmation of receiving James' message is still missing.
    """

    port = random.randint(10000, 65000)
    server2 = SimpleWebSocketServer('', 64215, WS1)
    print('Running server2 on port {}.'.format(64215))
    server2.serveforever()

