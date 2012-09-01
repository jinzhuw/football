
from db import settings, games, weeks
from util import view, handler
import webapp2

class GamesHandler(handler.BaseHandler):
    def get(self):
        week = weeks.current()
        current_games = games.games_for_week(week)
        view.render(self, 'games', {
            'week': week,
            'games': current_games,
            'css': 'games',
            'js': 'games'
        })

class SetScoreHandler(handler.BaseHandler):
    def post(self, game_id):
        home = int(self.request.POST.get('home')) 
        visiting = int(self.request.POST.get('visiting')) 
        games.update(int(game_id), home, visiting)

class GamesResetHandler(handler.BaseHandler):
    def get(self):
        games.reset()
        self.redirect('/')

app = webapp2.WSGIApplication([
    webapp2.Route('/games/<game_id>', handler=SetScoreHandler),
    ('/games/reset', GamesResetHandler),
    ('/games', GamesHandler),
],
config=settings.APP_CONFIG,
debug=settings.DEBUG)

