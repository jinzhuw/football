
from db import settings, games, weeks, entries
from util import view, handler
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
    if entries.set_pick_status(week, results):
        view.clear_cache('/results/data')
    if in_progress > 0:
        deferred.defer(load_scores, week, _countdown=300)

class LoadScoresHandler(handler.BaseHandler):
    @handler.admin
    def get(self):
        week = weeks.current()
        load_scores(week) 
        self.redirect('/games')

class UpdateRankingsHandler(handler.BaseHandler):
    @handler.admin
    def get(self):
        games.update_rankings()
        self.redirect('/games')

class SetScoreHandler(handler.BaseHandler):
    @handler.admin
    def post(self, game_id):
        home = int(self.request.POST.get('home')) 
        visiting = int(self.request.POST.get('visiting')) 
        game = games.Game.get_by_id(int(game_id))
        winner, loser = games.update(game, home, visiting)
        if entries.set_pick_status(weeks.current(), ([winner], [loser])):
            view.clear_cache('/results/data')

class GamesResetHandler(handler.BaseHandler):
    @handler.admin
    def get(self):
        games.reset_for_week(weeks.current())
        self.redirect('/')

app = webapp2.WSGIApplication([
    ('/games/reset', GamesResetHandler),
    ('/games/load-scores', LoadScoresHandler),
    ('/games/update-rankings', UpdateRankingsHandler),
    webapp2.Route('/games/<game_id>', handler=SetScoreHandler),
    ('/games', GamesHandler),
],
config=settings.app_config(),
debug=settings.debug())

