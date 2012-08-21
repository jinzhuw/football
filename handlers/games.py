
from db import settings
from util import view, handler
import webapp2

class GamesHandler(handler.BaseHandler):
    def get(self):
        view.render(self, 'home', {})

app = webapp2.WSGIApplication([
    ('/games', GamesHandler),
],
config=settings.APP_CONFIG,
debug=settings.DEBUG)

