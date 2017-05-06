from websocket import create_connection
import json
import threading
import time


class BoClient:
    def __init__(self, config):
        self.config = config
        self.ws = create_connection(config['ws_server'])
        self.no = config['no']

    def rx(self):
        while 1:
            result = json.loads(self.ws.recv())
            print('[Receive]', result)

    def heartbeat(self):
        while 1:
            time.sleep(5)
            data = {'heartbeat': True}
            data = json.dumps(data)
            self.ws.send(data)

    def register(self):
        msg = {
            'no': self.no,
            'action': 'register',
        }
        msg = json.dumps(msg)
        self.ws.send(msg)

    def tx(self):
        while 1:
            s = input()
            data = {
                'group': 'ass',
                'no': self.no,
                'action': 'push',
                'msg': s
            }
            self.ws.send(json.dumps(data))

    def run(self):
        t_rx = threading.Thread(target=self.rx)
        t_rx.start()
        t_tx=threading.Thread(target=self.tx)
        t_tx.start()
        self.register()


if __name__ == '__main__':
    config = {
        'ws_server': 'ws://localhost:9999/chat',
        'no': 'client.bo'
    }
    bc = BoClient(config)
    bc.run()
