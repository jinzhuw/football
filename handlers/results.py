
from collections import defaultdict
from db import settings, entries, teams
from util import view, handler
import webapp2

class ResultsHandler(handler.BaseHandler):
    def get(self):
        view.render(self, 'results', {}, js=True, css=True)

class Results2011Handler(handler.BaseHandler):
    def get(self):
        view.render(self, 'results', {'static_results': '/js/2011-results.js'}, js=True, css=True)

class ResultsDataHandler(handler.BaseHandler):

    @view.cached(604800)
    def get(self):
        data = defaultdict(list)
        entries_by_id = {}
        for e in entries.get_all_entries():
            entries_by_id[e.key().id()] = e
        current_entry_id = None
        current_entry = None
        current_week = 1
        for pick in entries.iterpicks(True):
            if current_entry_id != pick.entry_id:
                current_entry_id = pick.entry_id
                current_entry = entries_by_id[current_entry_id]
                current_week = 1
            # fill empty weeks with buybacks
            while current_week < pick.week:
                data[current_entry.name].append({'status': 'buyback', 'team': ''})
                current_week += 1
                
            team = teams.shortname(pick.team)
            if pick.status not in (entries.Status.WIN, entries.Status.NONE):
                status = 'violation'
                if pick.status == entries.Status.LOSS:
                    status = 'loss'
                if pick.buyback:
                    status = 'buyback'
                team = {'team': team, 'status': status}
            data[entries_by_id[pick.entry_id].name].append(team)
            current_week += 1
        return view.render_json(self, data)

app = webapp2.WSGIApplication([
    ('/results/data', ResultsDataHandler),
    ('/results/2011', Results2011Handler),
    ('/results', ResultsHandler),
],
config=settings.app_config(),
debug=settings.debug())

