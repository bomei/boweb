import serial.tools.list_ports
import serial
import time
from threading import Thread
import traceback

port_list = serial.tools.list_ports.comports()
port_list = [each.device for each in port_list]
print(port_list)


class SerialClient:
    def __init__(self, config):
        self.port = config['serial_port']

        self.serial1 = serial.Serial(
            # port='com4',
            port=self.port,
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
        t = Thread(name="rx", target=self.rx)
        t.start()

    def run(self):
        print('[Using port]', self.serial1.port)
        self.rx_thread()

    def tx(self, msg):
        if len(msg) > 0:
            # 不知道为什么这里要加上\r\n才能正常地返回
            msg += '\r\n'
            msg = msg.encode()
            msg = list(msg)
            msg = [len(msg)] + msg
            data = bytes(msg)
            print(data)
            print(self.serial1.write(data))



