from __future__ import absolute_import, division, print_function

import motor
import tornado.web

dbClient = motor.motor_tornado.MotorClient('zannb.site', 27017)


class BaseHandler(tornado.web.RequestHandler):
    def get_current_user(self):
        return self.get_secure_cookie('username')

    def get_current_xsrf(self):
        return self.get_secure_cookie('_xsrf')

    @staticmethod
    async def db_login(c, db, username, pwd):
        await c[db].authenticate(username, pwd)

