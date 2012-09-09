
from db import settings, games, weeks
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
            'css': 'games',
            'js': 'games'
        })

class LoadScoresHandler(handler.BaseHandler):
    @handler.admin
    def get(self):
        week = weeks.current()
        games.load_scores(week)
        self.redirect('/games')

class SetScoreHandler(handler.BaseHandler):
    @handler.admin
    def post(self, game_id):
        home = int(self.request.POST.get('home')) 
        visiting = int(self.request.POST.get('visiting')) 
        games.update(int(game_id), home, visiting)

class GamesResetHandler(handler.BaseHandler):
    @handler.admin
    def get(self):
        games.reset()
        self.redirect('/')

app = webapp2.WSGIApplication([
    ('/games/reset', GamesResetHandler),
    ('/games/load-scores', LoadScoresHandler),
    webapp2.Route('/games/<game_id>', handler=SetScoreHandler),
    ('/games', GamesHandler),
],
config=settings.app_config(),
debug=settings.debug())

