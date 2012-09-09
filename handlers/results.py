
from collections import defaultdict
from db import settings, entries, teams
from util import view, handler
import webapp2

class ResultsHandler(handler.BaseHandler):
    def get(self):
        force = self.request.get('force')
        if not force and view.cache_hit(self, 'results'):
            return
        view.render(self, 'results', {}, js=True, css=True, cache_ttl=604800)

class ResultsDataHandler(handler.BaseHandler):
    type = 'json'

    def get(self):
        force = self.request.get('force')
        if not force and view.cache_hit(self, 'results/data'):
            return
        data = defaultdict(list)
        entries_by_id = {}
        for e in entries.get_all_entries():
            entries_by_id[e.key().id()] = e.name
        for pick in entries.iterpicks():
            # todo: add status logic
            team = teams.shortname(pick.team)
            if pick.status not in (entries.Status.WIN, entries.Status.NONE):
                status = 'violation'
                if pick.status == entries.Status.LOSS:
                    status = 'loss'
                team = {'team': team, 'status': status}
            data[entries_by_id[pick.entry_id]].append(team)
        view.render_json(self, 'results/data', data, cache_ttl=604800)

app = webapp2.WSGIApplication([
    ('/results/data', ResultsDataHandler),
    ('/results', ResultsHandler),
],
config=settings.app_config(),
debug=settings.debug())

