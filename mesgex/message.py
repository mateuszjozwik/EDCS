from mesgex.constants import Codes, DefaultMessage, RequestCodes, ResponseCodes, PresenceStatus
from typing import Union
import hashlib


def create_msg(code: int, message: Union[str, bytes] = None) -> bytes:
    if message is not None:
        assert isinstance(message, (str, bytes)), 'Message must be a string or bytes object.'
        if isinstance(message, str):
            message = message.encode('utf-8')
    else:
        message = DefaultMessage.get(code, b'')
    return b'%d %d %s' % (code, len(message), message)


def decipher_msg(buffer: bytes) -> (int, bytes, bytes):
    components = buffer.split(b' ', 2)

    if len(components) < 3:
        raise NeedMoreDataException

    assert len(components[0]) == 3, 'Wrong length of code.'

    try:
        code = int(components[0])
    except ValueError:
        raise NeedMoreDataException

    try:
        msg_len = int(components[1])
    except ValueError:
        raise NeedMoreDataException

    msg = components[2]

    if len(msg) < msg_len:
        raise NeedMoreDataException

    if code not in Codes:
        raise BadCodeException('Received code: {}'.format(code))

    return code, msg[:msg_len], msg[msg_len:]


def format_message_msg(sender, recipient, msg, code):
    assert isinstance(sender, (str, bytes)), 'Sender must be a string or bytes object.'
    assert isinstance(recipient, (str, bytes)), 'Recipient must be a string or bytes object.'
    assert isinstance(msg, (str, bytes)), 'Message must be a string or bytes object.'
    if isinstance(sender, str):
        sender = sender.encode('utf-8')
    if isinstance(recipient, str):
        recipient = recipient.encode('utf-8')
    if isinstance(msg, str):
        msg = msg.encode('utf-8')
    if code == RequestCodes.MESSAGE_SEND:
        return b'%s:%s:%s' % (sender, recipient, msg)
    elif code in (ResponseCodes.MESSAGE_DELIVERED, ResponseCodes.MESSAGE_FAILED):
        return b'%s:%s:%s' % (sender, recipient, hashlib.md5(msg).hexdigest().encode('utf-8'))


def decipher_message_msg(buffer: bytes) -> (bytes, bytes, bytes):
    """This function returns data in the format (sender, recipient, message/hash)"""
    assert isinstance(buffer, bytes), 'buffer must be a bytes object.'
    msg_split = buffer.split(b':', 2)
    assert len(msg_split) == 3, 'Wrong format of message to send: {}'.format(buffer)
    return msg_split


def format_route_msg(routes):
    msg = b''
    for client, hop_count in routes:
        msg += b'%s:%d;' % (client, hop_count)
    return msg


def decipher_route_msg(buffer: bytes):
    split_buffer = buffer.split(b';')
    routes = []
    for route in split_buffer:
        if route:
            client, hop_count = route.split(b':')
            routes.append((client, int(hop_count)))
    return routes


def format_presence_response_msg(name: bytes, presence: bytes):
    return b'%s:%s' % (name, presence)


def decipher_presence_response_msg(buffer: bytes):
    name, presence = buffer.split(b':')
    if presence in (PresenceStatus.ONLINE, PresenceStatus.OFFLINE):
        return name.decode('utf-8'), presence
    else:
        raise InvalidPresenceException


class InvalidPresenceException(Exception):
    pass


class BadCodeException(Exception):
    pass


class NeedMoreDataException(Exception):
    pass
