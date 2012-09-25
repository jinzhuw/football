
from db import settings, games, weeks, entries, breakdown
from google.appengine.ext import deferred
from util import view, handler
from google.appengine.ext import deferred
import webapp2

class GamesHandler(handler.BaseHandler):
    @handler.admin
    def get(self):
        week = weeks.current()
        current_games = games.games_for_week(week)
        view.render(self, 'games', {
            'week': week,
            'games': sorted(current_games, key=lambda x: x.date),
        }, css=True, js=True)

def load_scores(week):
    (results, in_progress) = games.load_scores(week)
    num_winners, num_losers = entries.set_pick_status(week, results)
    if num_winners > 0 or num_losers > 0:
        view.clear_cache('/results/data')
    breakdown.update_status_counts(week, num_winners, num_losers)
    if in_progress > 0:
        deferred.defer(load_scores, week, _countdown=300)

class LoadScoresHandler(handler.BaseHandler):
    @handler.admin
    def get(self):
        week = weeks.current()
        load_scores(week) 
        self.redirect('/games')

class SetScoreHandler(handler.BaseHandler):
    @handler.admin
    def post(self, game_id):
        home = int(self.request.POST.get('home')) 
        visiting = int(self.request.POST.get('visiting')) 
        game = games.Game.get_by_id(int(game_id))
        winner, loser = games.update(game, home, visiting)
        num_winners, num_losers = entries.set_pick_status(weeks.current(), ([winner], [loser]))
        if num_winners > 0 or num_losers > 0:
            view.clear_cache('/results/data')
        counts = entries.get_status_counts(weeks.current())
        breakdown.save_status_counts(
            weeks.current(),
            counts.get(entries.Status.WIN, 0),
            counts.get(entries.Status.LOSS, 0),
            counts.get(entries.Status.VIOLATION, 0)
        )

class GamesResetHandler(handler.BaseHandler):
    @handler.admin
    def get(self):
        games.reset_for_week(weeks.current())
        self.redirect('/')

app = webapp2.WSGIApplication([
    ('/games/reset', GamesResetHandler),
    ('/games/load-scores', LoadScoresHandler),
    webapp2.Route('/games/<game_id>', handler=SetScoreHandler),
    ('/games', GamesHandler),
],
config=settings.app_config(),
debug=settings.debug())

