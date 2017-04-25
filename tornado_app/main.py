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


class IndexHandler(tornado.web.RequestHandler):
    def get(self):
        self.render("index.html", log_in_already=False)


class UserHandler(tornado.web.RequestHandler):
    @tornado.gen.coroutine
    def post(self):
        username = self.get_argument("username")
        password = self.get_argument("password")
        db = dbClient.Tornado
        cursor = db.account.find({"username": username})
        try:
            for result in (yield cursor.to_list(length=10)):
                if result['password'] == password:
                    self.redirect("/")
                    return
                else:
                    self.write("log_error.html")
                    return
        except IndexError:
            self.write("log_error.html")
            return


class SignUpHandler(tornado.web.RequestHandler):
    @tornado.gen.coroutine
    def get(self):
        self.render('signup.html')

    def post(self):
        username = self.get_argument("username")
        password1 = self.get_argument("password1")
        password2 = self.get_argument("password2")
        if password1 == password2:
            db=dbClient.Tornado
            db.account.insert({
                'username':username,
                'password':password1
            })
        else:
            self.render()

class LogInHandler(tornado.web.RequestHandler):
    def get(self):
        self.render('login.html')


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

    @classmethod
    def on_response(cls, message):
        cls.render('show_ip.html', rasp_id=message)


class ControlPanelHandler(tornado.web.RequestHandler):
    def get(self):
        self.render("control_panel.html")


class SocketHandler(tornado.websocket.WebSocketHandler):
    """docstring for SocketHandler"""
    clients = set()

    def check_origin(self, origin):
        return True

    @staticmethod
    def send_to_all(message):
        for c in SocketHandler.clients:
            c.write_message(json.dumps(message))

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
    app = tornado.web.Application(
        handlers=[
            (r"/", IndexHandler),
            (r"/index", IndexHandler),
            (r"/control_panel", ControlPanelHandler),
            (r"/chat", SocketHandler),
            (r"/user", UserHandler),
            (r"/myrasp", ShowIPHandler),
            (r'/login', LogInHandler),
            (r'/signup',SignUpHandler)
        ],
        debug=True,
        autoreload=True,
        template_path=os.path.join(os.path.dirname(__file__), "templates"),
        static_path=os.path.join(os.path.dirname(__file__), "static")
    )
    app.listen(9999)
    tornado.ioloop.IOLoop.instance().start()
