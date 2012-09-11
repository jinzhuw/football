
from db import settings, analysis
from util import view, handler
import webapp2

class AnalysisHandler(handler.BaseHandler):
    def get(self):
        view.render(self, 'analysis', {}, js=True)

class StatsHandler(handler.BaseHandler):
    def get(self, week):
        week = int(week)
        (no_pick, picks) = analysis.get_team_counts(week)
        data = {
            'no-pick': no_pick,
            'picks': picks,
        }
        view.render_json(self, self.request.path, data)
        

app = webapp2.WSGIApplication([
    webapp2.Route('/analysis/stats/<week>', StatsHandler),
    ('/analysis', AnalysisHandler),
],
config=settings.app_config(),
debug=settings.debug())

