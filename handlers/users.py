
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
                sections[user.name[0]].append((user, user_entries, new_entries, token))
        new_users.sort(key=lambda x: x[0].created)
        view.render(self, 'users', {'users': sorted(sections.items()), 'new_users': new_users}, css=True, js=True)

class GetEntriesHandler(handler.BaseHandler):
    @handler.admin
    def get(self):
        players = users.users_by_id()
        data = defaultdict(list)
        for e in entries.get_all_entries():
            data[players[e.user_id].name].append({
                'name': e.name,
                'status': e.status,
                'enabled': e.enabled
            })
        self.json_response(d)

class NewEntriesHandler(handler.BaseHandler):
    @handler.admin
    def post(self, user_id):
        user_id = int(user_id)
        entry = entries.Entry(user_id=user_id)
        entry.put()
        logging.info('Adding new entry for user %d by admin %s', user_id, self.user.name)
        self.response.write(entries.unnamed_entries(user_id))

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
        

app = webapp2.WSGIApplication([
    ('/users/newuser', NewUserHandler),
    webapp2.Route('/users/entries/<user_id>', handler=NewEntriesHandler),
    ('/users/entries', GetEntriesHandler),
    ('/users', UsersHandler),
], 
config=settings.app_config(),
debug=settings.debug())

