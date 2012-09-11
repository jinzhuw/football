
from db import settings, users, entries, weeks, games, analysis
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
            analysis.save_team_counts(week, counts)
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
            results = games.load_scores(week)
            if entries.set_pick_status(week, results):
                view.clear_cache('/results/data')
        # all the games better be complete by now...
        if not games.games_complete(week) and not settings.debug():
            logging.error('Cannot advance week, games are not complete')
            self.abort(409)
        
        counts = entries.get_status_counts(week)
        analysis.save_status_counts(
            week,
            counts.get(entries.Status.WIN, 0),
            counts.get(entries.Status.LOSS, 0),
            counts.get(entries.Status.VIOLATION, 0)
        )

        alive_entries = entries.deactivate_dead_entries(week)
        weeks.increment()
        entries.create_picks(weeks.current(), alive_entries)

        self.redirect('/admin')

class SendBreakdownHandler(handler.BaseHandler):
    def get(self):
        week = weeks.current()
        (no_pick, picks) = analysis.get_counts(week)
        emails = users.get_all_emails()
        deferred.defer(mail.email_breakdown, week, no_pick, picks, emails, _queue='email')
        self.redirect('/admin')

class SendSinglePickLinksHandler(handler.BaseHandler):
    def post(self, user_id):
        user_id = int(user_id)
        alive_entries = entries.Entry.gql('WHERE alive = True and user_id = :1', user_id)
        if alive_entries.count() == 0:
            logging.info('No active entries for %s', user.name)
            return
        week = weeks.current()
        user = users.User.get_by_id(user_id)        
        deferred.defer(mail.email_picks_link, user, alive_entries, week, False, _queue='email')
        
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

app = webapp2.WSGIApplication([
    ('/admin/close-picks', ClosePicksHandler),
    ('/admin/advance-week', AdvanceWeekHandler),
    ('/admin/send-breakdown', SendBreakdownHandler),
    webapp2.Route('/admin/send-pick-links/<user_id>', SendSinglePickLinksHandler),
    ('/admin/send-pick-links', SendPickLinksHandler),
    ('/admin/send-analysis', SendAnalysisHandler),
    ('/admin', AdminHandler),
], 
config=settings.app_config(),
debug=settings.debug())

