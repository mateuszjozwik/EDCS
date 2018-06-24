"""
    mesgex protocol description

All communications consist of:
"<code> <length of message> <message>"

Even communication with zero-length message has to have a trailing space. Ex:
"600 0 "

^  - start state
|  - steps
<> - possible cases
$  - end state
#  - comment

server - server
- initial handshake between s1 (connecting server) and s2 (server being connected to):
    ^ s1 sends HELLO with its greeting to s2
    | both servers enter CONNECTING state
    <> s2 responds with HELLO_OK_1 with its UUID
        <> s1 responds with HELLO_OK_2 with its UUID
            $ connection between s1 and s2 is established and both servers enter CONNECTED state
        <> s1 responds with REJECT or ERROR
            $ connection was rejected by s1
    <> s2 responds with REJECT or ERROR
        $ connection was rejected by s2

- sharing information about client routing
<ROUTE_CHANGE> <LENGTH> <CLIENT>:<HOP COUNT>;<CLIENT>:<HOP COUNT>;...

client - server
- initial handshake between cc (connecting client) and ss (serving server):
    ^ cc sends HELLO with its name to ss
    | cc and ss enter CONNECTING STATE
    <> ss responds with HELLO_OK_1 with its greeting
        # this path indicates that the name chosen by cc is available
        <> cc responds with HELLO_OK_2
            $ connection is established and cc and ss enter CONNECTED state
        <> cc responds with ERROR
            $ connection was rejected by cc
    <> ss responds with REJECT or ERROR
        # this path indicates that either a name was not specified or it is not available
        $ connection was rejected by ss

To send a message:
Send a packet in the format
<MESSAGE_SEND> <LENGTH> <SENDER NAME>:<RECIPIENT NAME>:<MY MESSAGE>

Message reply:
<MESSAGE_DELIVERED> <LENGTH> <SENDER NAME>:<RECIPIENT NAME>:<MY MESSAGE HASH>
<MESSAGE_FAILED> <LENGTH> <SENDER NAME>:<RECIPIENT NAME>:<MY MESSAGE HASH>

Presence checking:
<PRESENCE CHECK> <LENGTH> <CLIENT NAME>
<PRESENCE RESPONSE> <LENGTH> <CLIENT NAME>:(ONLINE|OFFLINE)


"""


class RequestCodes:
    MESSAGE_SEND = 250

    HELLO = 600

    PING = 888

    ROUTE_CHANGE = 900
    PRESENCE_CHECK = 950


class ResponseCodes:
    HELLO_OK_1 = 200
    HELLO_OK_2 = 201
    MESSAGE_DELIVERED = 260
    ERROR = 500
    REJECT = 503
    MESSAGE_FAILED = 505
    PONG = 889
    PRESENCE_RESPONSE = 951


DefaultMessage = {
    RequestCodes.PING: b'LET\'S PLAY PING PONG',

    ResponseCodes.ERROR: b'ERROR',
    ResponseCodes.REJECT: b'REJECT',
}


class PresenceStatus:
    ONLINE = b'ONLINE'
    OFFLINE = b'OFFLINE'


def list_codes(*args):
    codes = []
    for cls in args:
        codes += [getattr(cls, key) for key in [attr for attr in dir(cls) if not attr.startswith('__')]]
    return tuple(codes)


Codes = list_codes(RequestCodes, ResponseCodes)
