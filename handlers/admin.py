
from db import settings, users, entries, weeks, games, breakdown
from util import view, handler, email as mail
from collections import defaultdict
import string
import logging
import webapp2
from google.appengine.ext import deferred

class ClosePicksHandler(handler.BaseHandler):
    def get(self):
        week = weeks.current()
        current_time = weeks.current_time()
        if current_time > weeks.deadline(week):
            closed = entries.close_picks(week)
            if closed > 0:
                view.clear_cache('/results/data')
            counts = entries.get_team_counts(week)
            logging.info('Saving counts: %s', counts)
            breakdown.save_team_counts(week, counts)
            breakdown.save_status_counts(week, 0, 0, entries.num_violations(week))
            self.redirect('/admin')
            return

        past_deadline = []
        for g in games.open_past_deadline(week, current_time):
            past_deadline.append(g.home)
            past_deadline.append(g.visiting)

        closed = entries.close_picks(week, past_deadline)
        if closed > 0:
            view.clear_cache('/results/data')
        self.redirect('/admin')

def ok_to_advance(week):
    return entries.picks_closed(week) and (games.games_complete(week) or settings.debug())

class AdvanceWeekHandler(handler.BaseHandler):
    def get(self):
        week = weeks.current()

        # make sure all the picks are closed
        if not entries.picks_closed(week):
            logging.error('Cannot advance week, all picks are not closed')
            self.abort(409)
            return

        if not games.games_complete(week):
            (results, in_progress) = games.load_scores(week)
            if in_progress > 0 and not settings.debug():
                logging.error('%d games for week %d are still in progress', in_progress, week)
                self.abort(409)
            num_winners, num_losers = entries.set_pick_status(week, results)
            if num_winners > 0 or num_losers > 0:
                view.clear_cache('/results/data')
        # all the games better be complete by now...
        if not games.games_complete(week) and not settings.debug():
            logging.error('Cannot advance week, games are not complete')
            self.abort(409)
        
        counts = entries.get_status_counts(week)
        breakdown.save_status_counts(
            week,
            counts.get(entries.Status.WIN, 0),
            counts.get(entries.Status.LOSS, 0),
            counts.get(entries.Status.VIOLATION, 0)
        )
        games.update_standings()

        alive_entries = entries.deactivate_dead_entries(week)
        weeks.increment()
        entries.create_picks(weeks.current(), alive_entries)

        self.redirect('/admin')

class SendBreakdownHandler(handler.BaseHandler):
    def get(self):
        week = weeks.current()
        (no_pick, picks, total) = breakdown.get_team_counts(week)
        emails = users.get_all_emails()
        deferred.defer(mail.email_breakdown, week, no_pick, picks, emails, _queue='email')
        self.redirect('/admin')
        
class SendPickLinksHandler(handler.BaseHandler):
    def get(self):
        reminder = self.request.GET.get('reminder') == 'true'
        week = weeks.current()
        users_by_id = users.users_by_id()
        alive_entries = entries.alive_entries()
        to_send = defaultdict(list)
        for p in entries.nopicks(week):
            entry = alive_entries[p.entry_id]
            if entry.name:
                to_send[p.user_id].append(entry.name)
        for user_id, user_entries in to_send.iteritems():
            user = users_by_id[user_id]
            deferred.defer(mail.email_picks_link, user, user_entries, week, reminder, _queue='email')
        self.redirect('/admin')

class SendAnalysisHandler(handler.BaseHandler):
    def get(self):
        self.redirect('/admin')

class AdminHandler(handler.BaseHandler):
    def get(self):
        view.render(self, 'admin', {})

class UpdatePowerRanksHandler(handler.BaseHandler):
    def get(self):
        games.update_power_ranks()
        self.redirect('/admin')

class UpdateSpreadsHandler(handler.BaseHandler):
    def get(self):
        games.update_spreads()
        self.redirect('/admin')

class UpdateStandingsHandler(handler.BaseHandler):
    def get(self):
        games.update_standings()
        self.redirect('/admin')

class UpdateRankingsHandler(handler.BaseHandler):
    @handler.admin
    def get(self):
        games.update_rankings()
        self.redirect('/games')

class ResetPicks(handler.BaseHandler):
    def get(self):
        to_save = []
        for p in entries.Pick.gql('WHERE week = :1', weeks.current()):
            if p.status != entries.Status.VIOLATION:
                p.status = 0
                to_save.append(p)
        entries.db.put(to_save)

app = webapp2.WSGIApplication([
    ('/admin/close-picks', ClosePicksHandler),
    ('/admin/advance-week', AdvanceWeekHandler),
    ('/admin/send-breakdown', SendBreakdownHandler),
    ('/admin/send-pick-links', SendPickLinksHandler),
    ('/admin/send-analysis', SendAnalysisHandler),
    ('/admin/reset-picks', ResetPicks),
    ('/admin/update-power-ranks', UpdatePowerRanksHandler),
    ('/admin/update-spreads', UpdateSpreadsHandler),
    ('/admin/update-standings', UpdateStandingsHandler),
    ('/admin/update-rankings', UpdateRankingsHandler),
    ('/admin', AdminHandler),
], 
config=settings.app_config(),
debug=settings.debug())

