"""

Usage:
    wsclient.py <ip> <port> <dir>

"""
from docopt import docopt
from websocket import create_connection
import json
import threading
import time


def rec():
    while 1:
        result = json.loads(ws.recv())
        print('[Receive]', result)


def heartbeat(ws):
    while 1:
        time.sleep(5)
        data = {'heartbeat': True}
        data = json.dumps(data)
        ws.send(data)


if __name__ == '__main__':
    arguments = docopt(__doc__)
    address = 'ws://{}:{}/{}'.format(
        arguments['<ip>'],
        arguments['<port>'],
        arguments['<dir>']
    )
    ws = create_connection('ws://127.0.0.1:9999/chat')
    t = threading.Thread(target=rec)
    t.start()
    heartbeat_t = threading.Thread(target=heartbeat, args=(ws,))
    heartbeat_t.start()
    # print('sending hello')
    ws.send('hello')
    while 1:
        s = input()
        ws.send(s)
