
from db import settings, weeks, entries
from util import view, handler
import webapp2

class PicksHandler(handler.BaseHandler):
    def get(self):
        args = {
            #'week': weeks.current()
        }
        args['chosen'] = entries.player_picks(self.user, 1)
        
        view.render(self, 'picks', args)

app = webapp2.WSGIApplication([
    ('/picks', PicksHandler),
],
config=settings.APP_CONFIG,
debug=settings.DEBUG)

