
import time
from db import settings, users, entries, weeks
from util import view, handler, email as mail
from collections import defaultdict
from google.appengine.ext import deferred
import string
import logging
import webapp2

class UsersHandler(handler.BaseHandler):
    @handler.admin
    def get(self):
        sections = dict((c, []) for c in string.uppercase)
        new_users = []
        entries_by_player = defaultdict(list)
        for e in entries.get_all_entries():
            entries_by_player[e.user_id].append(e)
        for user in users.users_by_id().itervalues():
            token = users.make_login_token(user)
            if not user.name:
                new_users.append((user, entries_by_player.get(user.key().id(), []), 0, token))
            else:
                new_entries = 0 
                user_entries = []
                for e in entries_by_player.get(user.key().id(), []):
                    if e.activated:
                        user_entries.append(e)
                    else:
                        new_entries += 1
                sections[user.name[0].upper()].append((user, sorted(user_entries, key=lambda e: e.name), new_entries, token))
        for section in sections.values():
            section.sort(key=lambda x: x[0].name)
        new_users.sort(key=lambda x: x[0].created)
        view.render(self, 'users', {
            'users': sorted(sections.items()),
            'new_users': sorted(new_users, key=lambda x: x[0].email),
        }, css=True, js=True)

class GetEntriesHandler(handler.BaseHandler):
    @handler.admin
    def get(self):
        players = users.users_by_id()
        data = defaultdict(list)
        unknown = []
        for e in entries.get_all_entries():
            if e.user_id not in players:
                #    logging.error('Entry %d, %s is for non existing user %d', e.key().id(), e.name, e.user_id)
                #    self.abort(500)
                unknown.append((e.user_id, e.key().id()))
                continue
            data[players[e.user_id].email].append({
                'name': e.name,
                'alive': e.alive
            })
        buf = ['<table>']
        n = 0
        for name,ents in sorted(data.iteritems()):
            buf.append('<tr><td>%s</td><td>%d</td></tr>' % (name, len(ents)))
            n += len(ents)
        buf.append('</table>')
        buf.append('<br/>------------')
        buf.append('<br/>Total    %d' % n)
        buf.append('<br/><br/>Unknown %s' % unknown)
        self.response.out.write(''.join(buf))

class NewEntriesHandler(handler.BaseHandler):
    @handler.admin
    def post(self, user_id):
        user_id = int(user_id)
        entry = entries.Entry(user_id=user_id)
        entry.put()
        user = users.User.get_by_id(user_id)
        logging.info('Adding new entry for user %d by admin %s', user_id, self.user.name)
        num_entries = entries.unnamed_entries(user_id)
        deferred.defer(mail.email_new_entries, user.email, users.make_login_token(user), num_entries, _queue='email')
        self.response.write(num_entries)

class NewUserHandler(handler.BaseHandler):
    @handler.admin
    def post(self):
        email = self.request.POST.get('email')
        num_entries = int(self.request.POST.get('num_entries') or 1)
        user = users.create(email)
        logging.info('Got user %s', user)
        if not user:
            logging.error('Cannot create user, email already used: %s', email)
            self.abort(409)
        else:
            for i in range(num_entries):
                entry = entries.Entry(user_id=user.key().id())
                entry.put()
            deferred.defer(mail.email_new_user, email, users.make_login_token(user), num_entries, _queue='email')
            self.response.write(users.make_login_token(user))

class ResendActivationHandler(handler.BaseHandler):
    @handler.admin
    def post(self, user_id):
        user_id = int(user_id)
        user = users.User.get_by_id(user_id)
        num_entries = entries.unnamed_entries(user_id)
        deferred.defer(mail.email_new_user, user.email, users.make_login_token(user), num_entries, _queue='email')

def _email_picks_link(user_id, alive_entries, week):
    user = users.User.get_by_id(user_id)        
    # wait for 10 secs so only the last link for buybacks is sent
    time.sleep(5)
    num_alive_entries = entries.Entry.gql('WHERE alive = True AND name != NULL AND user_id = :1', user_id).count()
    if num_alive_entries != len(alive_entries):
        return
    mail.email_picks_link(user, alive_entries, week, False)

def send_picks_email(user_id):
    alive_entries = entries.Entry.gql('WHERE alive = True AND name != NULL AND user_id = :1', user_id)
    if alive_entries.count() == 0:
        logging.info('No active entries for %s', user.name)
        return
    alive_entries = sorted([e.name for e in alive_entries])
    week = weeks.current()
    deferred.defer(_email_picks_link, user_id, alive_entries, week, _queue='email')

class PicksEmailHandler(handler.BaseHandler):
    def post(self, user_id):
        send_picks_email(int(user_id))

class BuybackHandler(handler.BaseHandler):
    @handler.admin
    def post(self, entry_id):
        pick = entries.buyback_entry(int(entry_id))
        if pick is None:
            self.abort(404)
        send_picks_email(pick.user_id)

app = webapp2.WSGIApplication([
    ('/users/newuser', NewUserHandler),
    webapp2.Route('/users/resend-activation/<user_id>', handler=ResendActivationHandler),
    webapp2.Route('/users/entries/<user_id>', handler=NewEntriesHandler),
    webapp2.Route('/users/buyback/<entry_id>', handler=BuybackHandler),
    webapp2.Route('/users/picks-email/<user_id>', handler=PicksEmailHandler),
    ('/users/entries', GetEntriesHandler),
    ('/users', UsersHandler),
], 
config=settings.app_config(),
debug=settings.debug())

