
import logging
import time
from db import settings, weeks, entries, games, teams
from util import view, handler
import webapp2

class PicksHandler(handler.BaseHandler):
    @handler.user
    def get(self):
        week = weeks.current()
        user_entries = entries.entries_for_user(self.user)
        user_picks = entries.picks_for_user(self.user, week)
        picks = []
        for pick in user_picks.itervalues():
            entry = user_entries[pick.entry_id]
            if entry.activated:
                picks.append((entry.name, entry.key().id(), pick))
             
        args = {
            'week': week,
            'picks': sorted(picks),
            'current_time': time.mktime(weeks.current_time().timetuple()),
            'deadline': weeks.deadline(week),
            'deadline_passed': not weeks.check_deadline(week),
        }
        logging.debug(args)
        
        view.render(self, 'picks', args, css=True, js=True)

class PicksDataHandler(handler.BaseHandler):
    @handler.user
    @view.cached(86400)
    def get(self):
        week = weeks.current()
        data = []
        for g in games.games_for_week(week):
            data.append({
                'date_str': g.date.strftime('%A, %b. %d'),
                'time_str': g.date.strftime('%I:%M %p').lstrip('0'),
                'datetime': time.mktime(g.tz_date().timetuple()),
                'deadline': time.mktime(g.tz_deadline().timetuple()),
                'home_team': {
                    'short': teams.shortname(g.home),
                    'city': teams.cityname(g.home),
                    'mascot': teams.mascotname(g.home),
                    'id': g.home,
                    'logo_x': g.home_x(),
                    'logo_y': g.home_y(),
                },
                'visiting_team': {
                    'short': teams.shortname(g.visiting),
                    'city': teams.cityname(g.visiting),
                    'mascot': teams.mascotname(g.visiting),
                    'id': g.visiting,
                    'logo_x': g.visiting_x(),
                    'logo_y': g.visiting_y(),
                }
            })
        view.render_json(self, data)

class PickSetter(handler.BaseHandler):
    def get(self, entry_id):
        self.redirect('/login/%s' % entry_id) # this is really the login token

    @handler.user
    def post(self, entry_id):
        team = int(self.request.POST.get('team'))
        week = weeks.current()
        game = games.game_for_team(week, team)
        current_time = weeks.current_time()
        if current_time < weeks.deadline(week) and \
           current_time < game.tz_deadline():
            entries.select_team(int(entry_id), weeks.current(), team)
        else:
            logging.warning('Attempt to set pick after deadline, user %s, team %s',
                            self.user.name, teams.shortname(team))
            self.abort(403)

app = webapp2.WSGIApplication([
    ('/picks/data', PicksDataHandler),
    webapp2.Route('/picks/<entry_id>', handler=PickSetter),
    ('/picks', PicksHandler),
],
config=settings.app_config(),
debug=settings.debug())

