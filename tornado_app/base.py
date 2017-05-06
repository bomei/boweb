import tornado.web
import motor

dbClient = motor.motor_tornado.MotorClient('zannb.site', 27017)

class BaseHandler(tornado.web.RequestHandler):
    def get_current_user(self):
        return self.get_secure_cookie('username')

    def get_current_xsrf(self):
        return self.get_secure_cookie('_xsrf')
