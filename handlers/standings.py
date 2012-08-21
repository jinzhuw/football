
from db import settings
from util import view, handler
import webapp2

class StandingsHandler(handler.BaseHandler):
    def get(self):
        view.render(self, 'standings', {})

app = webapp2.WSGIApplication([
    ('/standings', StandingsHandler),
],
config=settings.APP_CONFIG,
debug=settings.DEBUG)

