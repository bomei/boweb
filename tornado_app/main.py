import os

import tornado
import tornado.web
import tornado.gen
import tornado.websocket
import tornado.ioloop
import tornado.template
import motor
import json

# conn = pymongo.MongoClient(host='zannb.site', port=27017)
dbClient = motor.motor_tornado.MotorClient('zannb.site', 27017)


class BaseHandler(tornado.web.RequestHandler):
    def get_current_user(self):
        return self.get_secure_cookie('username')


class IndexHandler(BaseHandler):
    def get(self):
        log_in_already=False
        if self.get_secure_cookie('username'):
            log_in_already=True
        self.render("index.html", log_in_already=log_in_already)


class UserHandler(BaseHandler):
    pass


class SignUpHandler(BaseHandler):
    @tornado.gen.coroutine
    def get(self):
        self.render('signup.html')

    def post(self):
        username = self.get_argument("username")
        password1 = self.get_argument("password1")
        password2 = self.get_argument("password2")
        if password1 == password2:
            db = dbClient.Tornado
            db.account.insert({
                'username': username,
                'password': password1
            })
        else:
            self.render()


class LogInHandler(BaseHandler):
    def get(self):
        self.render('login.html')

    @tornado.gen.coroutine
    def post(self):
        username = self.get_argument("username")
        password = self.get_argument("password")
        db = dbClient.Tornado
        cursor = db.account.find({"username": username})
        try:
            for result in (yield cursor.to_list(length=10)):
                if result['password'] == password:
                    self.set_secure_cookie('username',username)
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


class SocketHandler(tornado.websocket.WebSocketHandler):
    """docstring for SocketHandler"""
    clients = dict()

    def check_origin(self, origin):
        return True

    @staticmethod
    def send_to_all(message):
        for k,v in SocketHandler.clients.items():
            for c in v:
                c.write_message(json.dumps(message))

    def register(self, newer):
        pass


    def open(self):
        self.write_message(json.dumps({
            'type': 'sys',
            'message': 'Welcome to WebSocket',
        }))
        SocketHandler.send_to_all({
            'type': 'sys',
            'message': str(id(self)) + ' has joined',
        })
        SocketHandler.clients.add(self)

    def on_close(self):
        SocketHandler.clients.remove(self)
        SocketHandler.send_to_all({
            'type': 'sys',
            'message': str(id(self)) + ' has left',
        })

    def on_message(self, message):
        try:
            d_message = json.loads(message)
        except json.decoder.JSONDecodeError:
            d_message = message
        if 'heartbeat' in d_message:
            return
        if 'send_ip' in d_message:
            self.redirect('/myrasp?ip_message=' + message)
            return
        SocketHandler.send_to_all({
            'type': 'user',
            'id': id(self),
            'message': message,
        })

        # #MAIN


# class TemplatesHandler(tornado.web.RequestHandler):
#     def get(self):
#         self.render()

if __name__ == '__main__':
    settings = {
        "template_path": os.path.join(os.path.dirname(__file__), "templates"),
        'static_path': os.path.join(os.path.dirname(__file__), "static"),
        "cookie_secret": "bobo=",
        "xsrf_cookies": True,
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
            (r'/signup', SignUpHandler)
        ],
        **settings
    )
    app.listen(9999)
    tornado.ioloop.IOLoop.instance().start()
