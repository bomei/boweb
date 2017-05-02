import os

import tornado
import tornado.web
import tornado.gen
import tornado.websocket
import tornado.ioloop
import tornado.template
import motor
import json
from tornado.httpclient import AsyncHTTPClient

# conn = pymongo.MongoClient(host='zannb.site', port=27017)
dbClient = motor.motor_tornado.MotorClient('zannb.site', 27017)


class BaseHandler(tornado.web.RequestHandler):
    def get_current_user(self):
        return self.get_secure_cookie('username')

    def get_current_xsrf(self):
        return self.get_secure_cookie('_xsrf')


class IndexHandler(BaseHandler):
    def get(self):
        log_in_already = False
        if self.get_secure_cookie('username'):
            log_in_already = True
        self.render("index.html", log_in_already=log_in_already)


class UserHandler(BaseHandler):
    pass


class EquipmentHandler(BaseHandler):
    @tornado.web.authenticated
    async def post(self):
        db = dbClient.Tornado
        action = self.get_argument('action', None)
        if action is not None:
            user = self.get_secure_cookie('username').decode()
            if action == 'add':
                no = self.get_argument('no')
                r = await self.add_new_to_user(no, user)
                if r == 'success':
                    self.write('add {} to {} success'.format(no, user))
                elif r == 'used':
                    self.write('{} has been activated'.format(no))

            elif action == 'query':
                kind = self.get_argument('kind')
                cursor = db[user].find({'kind': kind})
                doc = await cursor.to_list(None)
                if len(doc) > 0:
                    for each in doc:
                        each.pop('_id')
                    self.write(json.dumps(doc))
                else:
                    self.write('No')

            elif action == 'drop_all':
                db[user].drop()
                db.equipment.remove({'user': user})

    async def add_new_to_user(self, no, user):
        user = user if isinstance(user, str) else user.decode()
        db = dbClient.Tornado
        cursor = db.equipment.find({'no': no})
        doc = await cursor.to_list(None)
        if len(doc) == 0:
            db.equipment.insert({
                'no': no,
                'user': user,
                'kind': no.split('.')[0]
            })
            db[user].insert({
                'no': no,
                'symbol': 'equipments',
                'kind': no.split('.')[0]
            })
            post_data = {
                'action': 'add',
                'user': user,
                'no': no,
                '_xsrf':self.get_current_xsrf()
            }
            import urllib.parse, requests

            body = urllib.parse.urlencode(post_data)
            AsyncHTTPClient().fetch('http://localhost:9999/chat', method='POST', body=body)
            return 'success'
        else:
            return 'used'

    def on_chat_response(self):
        pass


class SignUpHandler(BaseHandler):
    def get(self):
        self.render('signup.html', username_used=False)

    async def post(self):
        username = self.get_argument("username")
        password1 = self.get_argument("password1")
        password2 = self.get_argument("password2")
        cursor = dbClient.Tornado.account.find({'username': username})
        doc = await cursor.to_list(None)
        if len(doc) == 0:
            db = dbClient.Tornado
            db.account.insert({
                'username': username,
                'password': password1
            })
            self.redirect('/')
        else:
            self.render('signup.html', username_used=True)


class LogInHandler(BaseHandler):
    def get(self):
        self.render('login.html')

    async def post(self):
        username = self.get_argument("username")
        password = self.get_argument("password")
        db = dbClient.Tornado
        cursor = db.account.find({"username": username})
        try:
            for result in (await cursor.to_list(length=10)):
                if result['password'] == password:
                    self.set_secure_cookie('username', username)
                    self.redirect("/")
                    return
                else:
                    self.write("log_error.html")
                    return
        except IndexError:
            self.write("log_error.html")
            return


class LogOutHandler(BaseHandler):
    def get(self):
        self.clear_cookie('username')
        self.redirect('/')
        if self.get_argument('logout', None):
            self.clear_cookie('username')
            self.redirect('/')


class ShowIPHandler(tornado.websocket.WebSocketHandler):
    def get(self):
        try:
            ip_m = '0.0.0.0'
            if len(ip_m) > 0:
                self.render('show_ip.html', rasp_id=ip_m)
        except tornado.web.MissingArgumentError:
            SocketHandler.send_to_all({
                'require_ip': True
            })


class ControlPanelHandler(BaseHandler):
    @tornado.web.authenticated
    def get(self):
        self.render("control_panel.html")


class SocketHandler(tornado.websocket.WebSocketHandler, BaseHandler):
    """docstring for SocketHandler"""
    clients_all = set()
    clients_group = dict()
    clients_no = dict()

    def add_to_group(self,group):
        if group not in SocketHandler.clients_group:
            SocketHandler.clients_group[group]=set()
        SocketHandler.clients_group[group].add(self)

    async def client_refresh(self, no=None):
        if no is not None:
            cursor = dbClient.Tornado.equipment.find({'no': no})
            doc = await cursor.to_list(None)
            if len(doc) > 0:
                doc = doc[0]
                user=doc['user']
                if user not in SocketHandler.clients_group:
                    SocketHandler.clients_group[user]=set()
                SocketHandler.clients_group[user].add(self)
                return

    def post(self):
        action = self.get_argument('action', None)
        if action is not None:
            user = self.get_argument('user')
            no = self.get_argument('no')

            if action == 'add':
                if user not in SocketHandler.clients_group:
                    SocketHandler.clients_group[user] = set()
                if no in SocketHandler.clients_no:
                    SocketHandler.clients_group[user].add(SocketHandler.clients_no[no])

    def check_origin(self, origin):
        return True

    @staticmethod
    def send_to_group(group, message):
        for c in SocketHandler.clients_group[group]:
            c.write_message(message)

    @staticmethod
    def send_to_all(message):
        for c in SocketHandler.clients_all:
            c.write_message(json.dumps(message))

    def register(self, newer):
        pass

    def open(self):
        self.write_message(json.dumps({
            'group': 'sys',
            'message': 'Welcome to WebSocket',
        }))
        SocketHandler.send_to_all({
            'group': 'sys',
            'message': str(id(self)) + ' has joined',
        })
        SocketHandler.clients_all.add(self)

    def on_close(self):
        SocketHandler.clients_all.remove(self)
        SocketHandler.send_to_all({
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
                data = d_message['data']
                self.join_handler(data)
                return

            elif action == 'register':
                if 'no' in d_message:
                    no = d_message['no']
                    if no not in SocketHandler.clients_no:
                        SocketHandler.clients_no[no] = self
                    yield self.client_refresh(no)
                else:
                    user=self.get_current_user().decode()
                    self.add_to_group(user)
                    return

            elif action == 'push':
                if 'group' not in d_message:
                    d_message['group']=self.get_current_user().decode()
                msg=d_message['data']['msg']
                SocketHandler.send_to_group(d_message['group'],json.dumps(d_message))

            else:
                SocketHandler.send_to_all({
                    'group': 'user',
                    'id': id(self),
                    'message': message,
                })
        except json.decoder.JSONDecodeError:
            self.write_message('bad post message')
            return
        except KeyError:
            return

    def heartbeat_handler(self):
        pass

    def join_handler(self, data):
        if 'direction_group' in data:
            direction_group = data['direction_group']
            if direction_group in SocketHandler.clients_group:
                if self not in SocketHandler.clients_group[direction_group]:
                    SocketHandler.clients_group[direction_group].add(self)


if __name__ == '__main__':
    settings = {
        "template_path": os.path.join(os.path.dirname(__file__), "templates"),
        'static_path': os.path.join(os.path.dirname(__file__), "static"),
        "cookie_secret": "bobo=",
        "xsrf_cookies": False,
        "login_url": "/login",
        'debug': True,
        'autoreload': True
    }

    app = tornado.web.Application(
        handlers=[
            (r"/", IndexHandler),
            (r"/index", IndexHandler),
            (r"/control_panel", ControlPanelHandler),
            (r"/chat", SocketHandler),
            (r"/user", UserHandler),
            (r"/myrasp", ShowIPHandler),
            (r'/login', LogInHandler),
            (r'/logout', LogOutHandler),
            (r'/signup', SignUpHandler),
            (r'/equipment', EquipmentHandler)
        ],
        **settings
    )
    app.listen(9999)
    tornado.ioloop.IOLoop.instance().start()
