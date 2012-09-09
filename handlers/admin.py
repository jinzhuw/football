
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
            entries.close_picks(week)
            counts = entries.get_pick_counts(week)
            logging.info('Saving counts: %s', counts)
            analysis.save_counts(week, counts)
            self.redirect('/admin')
            return

        past_deadline = []
        for g in games.open_past_deadline(week, current_time):
            past_deadline.append(g.home)
            past_deadline.append(g.visiting)

        entries.close_picks(week, past_deadline)
        self.redirect('/admin')

def ok_to_advance(week):
    return entries.picks_closed(week)# and games.games_complete(week)

class AdvanceWeekHandler(handler.BaseHandler):
    def get(self):
        week = weeks.current()
        if not ok_to_advance(week):
            self.abort(409)
            return

        alive_entries = entries.set_picks_status(week)

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

