
from db import settings
from util import view, handler
import webapp2

class HomeHandler(handler.BaseHandler):
    def get(self):
        view.render(self, 'home', {})

app = webapp2.WSGIApplication([
    ('/', HomeHandler),
],
config=settings.APP_CONFIG,
debug=settings.DEBUG)

