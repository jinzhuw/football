
import logging
from db import settings, weeks, entries, games
from util import view, handler
import webapp2

class PicksHandler(handler.BaseHandler):
    @handler.user
    def get(self):
        if not self.user:
            self.redirect('/')
            return
        week = weeks.current()
        user_entries = entries.entries_for_user(self.user)
        user_picks = entries.picks_for_user(self.user, week)
        picks = []
        for pick in user_picks.itervalues():
            entry = user_entries[pick.entry_id]
            if entry.activated:
                picks.append((entry.name, entry.key().id(), pick))
        deadline_passed = not weeks.check_deadline(week)
        games_data = []
        if not deadline_passed:
            for g in sorted(games.games_for_week(week), key=lambda g: g.date):
                if g.date.weekday() in [0, 6]:
                    games_data.append(g) 
             
        args = {
            'week': week,
            'picks': sorted(picks),
            'games': games_data,
            'deadline': weeks.deadline(week),
            'deadline_passed': deadline_passed,
        }
        logging.debug(args)
        
        view.render(self, 'picks', args, css=True, js=True)

class PickSetter(handler.BaseHandler):
    @handler.user
    def post(self, entry_id):
        if not self.user:
            self.redirect('/')
            return
        team = int(self.request.body)
        entries.select_team(int(entry_id), weeks.current(), team)

app = webapp2.WSGIApplication([
    webapp2.Route('/picks/<entry_id>', handler=PickSetter),
    ('/picks', PicksHandler),
],
config=settings.app_config(),
debug=settings.debug())

