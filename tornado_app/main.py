from __future__ import absolute_import, division, print_function

#
import os
# import sys
#
# d=os.getcwd()
# sys.path.append(d)

import tornado
import tornado.web
import tornado.gen
import tornado.websocket
import tornado.ioloop
import tornado.template

import json
from tornado.httpclient import AsyncHTTPClient

from base import BaseHandler, dbClient
from socket_io import SocketIO


# conn = pymongo.MongoClient(host='zannb.site', port=27017)


class IndexHandler(BaseHandler):
    def get(self):
        log_in_already = False
        if self.get_secure_cookie('username'):
            log_in_already = True
        username = self.get_current_user()
        self.render("index.html", log_in_already=log_in_already, username=username)


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
                '_xsrf': self.get_current_xsrf()
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
        self.render("control_panel.html", username=self.get_current_user())


class SocketHandler(SocketIO):
    """docstring for SocketHandler"""

    def check_origin(self, origin):
        return True if origin is not None else False


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
