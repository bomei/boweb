import os.path

import tornado.httpserver
import tornado.web
import tornado.ioloop
import tornado.options
import tornado.httpclient
import tornado.websocket
import pymongo
import json

conn = pymongo.MongoClient(host='zannb.site', port=27017)


class IndexHandler(tornado.web.RequestHandler):
    def get(self):
        self.render("index.html")


class UserHandler(tornado.web.RequestHandler):
    def post(self):
        username = self.get_argument("username")
        password = self.get_argument("password")
        db = conn.Tornado
        result = db.account.find({"username": username})
        try:
            if result[0]['password'] == password:
                self.redirect("/")
                return
            else:
                self.render("log_error.html")
                return
        except IndexError:
            self.render("log_error.html")
            return


class SocketHandler(tornado.websocket.WebSocketHandler):
    """docstring for SocketHandler"""
    clients = set()

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
        SocketHandler.send_to_all({
            'type': 'user',
            'id': id(self),
            'message': message,
        })

        # #MAIN


if __name__ == '__main__':
    app = tornado.web.Application(
        handlers=[
            (r"/", IndexHandler),
            (r"/chat", SocketHandler),
            (r"/user", UserHandler)
        ],
        debug=True,
        autoreload=True,
        template_path=os.path.join(os.path.dirname(__file__), "templates"),
        static_path=os.path.join(os.path.dirname(__file__), "static")
    )
    app.listen(12345)
    tornado.ioloop.IOLoop.instance().start()
