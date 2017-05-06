import json
import tornado.websocket
import tornado.gen
from tornado_app.base import BaseHandler, dbClient
import asyncio


class SocketIO(tornado.websocket.WebSocketHandler, BaseHandler):
    """docstring for SocketHandler"""
    clients_all = set()
    clients_group = dict()
    clients_no = dict()
    clients_id_to_no = dict()

    def callback(self, action):
        handler = action + '_handler'
        return getattr(self, handler)

    @staticmethod
    def join_handler(no, group):
        if group not in SocketIO.clients_group:
            SocketIO.clients_group[group] = set()
        SocketIO.clients_group[group].add(SocketIO.clients_no[no]['client'])

        if not isinstance(SocketIO.clients_no[no]['group'], set):
            SocketIO.clients_no[no]['group'] = set()
        SocketIO.clients_no[no]['group'].add(group)

    @staticmethod
    def heartbeat_handler():
        return

    def register_handler(self, no):
        if no not in SocketIO.clients_no.keys():
            SocketIO.clients_no[no] = dict()
            SocketIO.clients_no[no]['client'] = self
            SocketIO.clients_no[no]['group']=set()

    async def client_auto_join_group(self, no):
        if no.startswith('wc'):
            self.join_handler(no, self.get_current_user().decode())
        else:
            cursor = dbClient.Tornado.equipment.find({'no': no})
            doc = await cursor.to_list(None)
            if len(doc) > 0:
                doc = doc[0]
                user = doc['user']
                self.join_handler(no, user)

    def add_equipment_to_user(self, no, user):
        pass

    def post(self):
        action = self.get_argument('action', None)
        if action == 'join':
            user = self.get_argument('user')
            no = self.get_argument('no')
            self.join_handler(no, user)

    @staticmethod
    def leave_group(no, group):
        if no in SocketIO.clients_no.keys():
            if group in SocketIO.clients_no[no]['group']:
                SocketIO.clients_group[group].remove(SocketIO.clients_no[no]['client'])
                SocketIO.clients_no[no]['group'].remove(group)

    @staticmethod
    def leave_all_group(no):
        if no in SocketIO.clients_no.keys():
            for group in SocketIO.clients_no[no]['group']:
                SocketIO.clients_group[group].remove(SocketIO.clients_no[no]['client'])
            SocketIO.clients_no[no]['group'] = set()

    @staticmethod
    def send_to_group(group, message):
        for c in SocketIO.clients_group[group]:
            c.write_message(json.dumps(message))

    @staticmethod
    def send_to_all(message):
        for c in SocketIO.clients_all:
            c.write_message(json.dumps(message))

    def open(self):
        self.write_message(json.dumps({
            'group': 'sys',
            'message': 'Welcome to WebSocket',
        }))
        SocketIO.send_to_all({
            'group': 'sys',
            'message': str(id(self)) + ' has joined',
        })
        SocketIO.clients_all.add(self)

    def on_close(self):
        SocketIO.clients_all.remove(self)
        if str(id(self)) in SocketIO.clients_id_to_no:
            no = SocketIO.clients_id_to_no[str(id(self))]
            self.leave_all_group(no)
            SocketIO.clients_no.pop(no)
        SocketIO.send_to_all({
            'group': 'sys',
            'message': str(id(self)) + ' has left',
        })

    @tornado.gen.coroutine
    def on_message(self, message):
        try:
            d_message = json.loads(message)
            action = d_message['action']

            if action == 'heartbeat':
                self.heartbeat_handler()
                return

            elif action == 'join':
                no = d_message['no']
                group = d_message['group']
                self.join_handler(no, group)
                return

            elif action == 'register':
                if 'no' in d_message:
                    no = d_message['no']
                else:
                    no = 'wc.{}'.format(str(id(self)))
                SocketIO.clients_id_to_no[str(id(self))]=no
                self.register_handler(no)
                yield from self.client_auto_join_group(no)

            elif action == 'push':
                if 'group' not in d_message:
                    d_message['group'] = self.get_current_user().decode()
                msg = d_message['msg']
                SocketIO.send_to_group(
                    d_message['group'],
                    {
                        'message': msg,
                        'group':d_message['group']
                    }
                )

            else:
                SocketIO.send_to_all({
                    'group': 'user',
                    'id': id(self),
                    'message': message,
                })
        except json.decoder.JSONDecodeError:
            self.write_message('bad post message')
            return
        except KeyError:
            return
