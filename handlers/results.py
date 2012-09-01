
from db import settings
from util import view, handler
import webapp2

class ResultsHandler(handler.BaseHandler):
    def get(self):
        view.render(self, 'results', {}, js=True, css=True)

app = webapp2.WSGIApplication([
    ('/results', ResultsHandler),
],
config=settings.APP_CONFIG,
debug=settings.DEBUG)

