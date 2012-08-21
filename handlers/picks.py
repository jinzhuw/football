
from db import settings
from util import view, handler
import webapp2

class PicksHandler(handler.BaseHandler):
    def get(self):
        view.render(self, 'picks', {})

app = webapp2.WSGIApplication([
    ('/picks', PicksHandler),
],
config=settings.APP_CONFIG,
debug=settings.DEBUG)

