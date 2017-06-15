from websocket import create_connection
import json
import threading
import time
import serial.tools.list_ports
import serial

port_list = serial.tools.list_ports.comports()
port_list = [each.device for each in port_list]
print(port_list)


class SerialClient:
    def __init__(self, config):
        self.port = config['serial_port']

        self.serial1 = serial.Serial(
            # port='com4',
            port='/dev/ttyUSB0',
            baudrate=9600
        )

    def rx(self):
        while 1:
            time.sleep(0.1)
            n = self.serial1.inWaiting()
            if n > 0:
                print(n)
                data = self.serial1.read(n)
                try:
                    print('[{}] -> [{}]'.format(data, data.decode('utf-8')))
                except Exception as e:
                    print('[EXCEPTION], can\'t decode as utf-8')
                    print(data)

    def rx_thread(self):
        t = threading.Thread(name="rx", target=self.rx)
        t.start()

    def run(self):
        print('[Using port]', self.serial1.port)
        self.rx_thread()

    def tx(self, msg):
        if len(msg) > 0:
            print('in sc.tx, msg'.format(msg))
            # 不知道为什么这里要加上\r\n才能正常地返回
            msg += '\r\n'
            msg = msg.encode()
            msg = list(msg)
            msg = [len(msg)] + msg
            data = bytes(msg)
            print(data)
            print(self.serial1.write(data))

class BoClient:
    def __init__(self, config, sc):
        self.config = config
        self.ws = create_connection(config['ws_server'])
        self.no = config['no']
        self.sc = sc

    def rx(self):
        while 1:
            result = json.loads(self.ws.recv())
            print(result)
            if 'message' in result:
                msg=result['message']
                self.sc.tx(msg)

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
        'ws_server': 'ws://zannb.site/chat',
        'no': 'client.bo',
        'serial_port': '/dev/ttyUSB0'
    }
    sc=SerialClient(config)
    bc = BoClient(config,sc)
    bc.run()


