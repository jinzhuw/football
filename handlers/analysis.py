
from db import settings
from util import view, handler
import webapp2

class AnalysisHandler(handler.BaseHandler):
    def get(self):
        view.render(self, 'analysis', {}, js=True, css=True)

app = webapp2.WSGIApplication([
    ('/analysis', AnalysisHandler),
],
config=settings.app_config(),
debug=settings.debug())

