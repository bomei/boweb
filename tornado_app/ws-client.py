"""

Usage:
    wsclient.py <ip> <port> <dir>

"""
from docopt import docopt
from websocket import create_connection
import json
import threading


def rec():
    while 1:
        result = json.loads(ws.recv())
        print('[Receive]', result)


if __name__ == '__main__':
    arguments = docopt(__doc__)
    address = 'ws://{}:{}/{}'.format(
        arguments['<ip>'],
        arguments['<port>'],
        arguments['<dir>']
    )
    ws = create_connection(address)
    t = threading.Thread(target=rec)
    t.start()
    # print('sending hello')
    ws.send('hello')
    while 1:
        s = input()
        ws.send(s)
