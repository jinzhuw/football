
from db import settings
from util import view, handler
import webapp2

class RulesHandler(handler.BaseHandler):
    def get(self):
        view.render(self, 'rules', {})

app = webapp2.WSGIApplication([
    ('/rules', RulesHandler),
],
config=settings.APP_CONFIG,
debug=settings.DEBUG)

