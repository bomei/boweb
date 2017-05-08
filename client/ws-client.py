from websocket import create_connection
import json
import threading
import time
from seriel_learn import SerialClient

class BoClient:
    def __init__(self, config, sc:SerialClient):
        self.config = config
        self.ws = create_connection(config['ws_server'])
        self.no = config['no']
        self.sc = sc

    def rx(self):
        while 1:
            result = json.loads(self.ws.recv())
            print('[Receive]', result)
            if 'message' in result:
                print('[message]',result['message'])
                self.sc.tx(result['message'])

    def heartbeat(self):
        while 1:
            time.sleep(5)
            data = {'action': 'heartbeat'}
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
                'group': 'bobo',
                'no': self.no,
                'action': 'push',
                'msg': s
            }
            self.ws.send(json.dumps(data))

    def run(self):
        self.sc.run()
        t_rx = threading.Thread(target=self.rx)
        t_rx.start()
        t_tx = threading.Thread(target=self.tx)
        t_tx.start()
        self.register()
        t_heartbeat = threading.Thread(target=self.heartbeat)
        t_heartbeat.start()


if __name__ == '__main__':
    config = {
        'ws_server': 'ws://192.168.1.105:8888/chat',
        'no': 'client.bobono',
        'serial_port': '/dev/ttyUSB0'
    }
    sc=SerialClient(config)
    bc = BoClient(config,sc)
    bc.run()


