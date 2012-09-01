
from db import settings, users, entries, weeks
from util import view, handler
from collections import defaultdict
import string
import logging
import webapp2

class UsersHandler(handler.BaseHandler):
    def get(self):
        sections = dict((c, []) for c in string.uppercase)
        unnamed = []
        entries_by_player = defaultdict(list)
        for e in entries.get_all_entries():
            entries_by_player[e.user_id].append(e)
        for user in users.users_by_id().itervalues():
            token = users.make_login_token(user)
            if not user.name:
                unnamed.append((user, entries_by_player.get(user.key().id(), []), token))
            else:
                sections[user.name[0]].append((user, entries_by_player.get(user.key().id(), []), token))
        view.render(self, 'users', {'users': sorted(sections.items()), 'unnamed': unnamed}, css=True)

class GetEntriesHandler(handler.BaseHandler):
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
    def post(self):
        entry = entries.Entry(user_id=user.key().id())
        entry.put()
        self.response.write(entry.key().id())

class NewUserHandler(handler.BaseHandler):
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
            self.redirect('/users')

app = webapp2.WSGIApplication([
    ('/users/newuser', NewUserHandler),
    webapp2.Route('/users/entries/<user_id>', handler=NewEntriesHandler),
    ('/users/entries', GetEntriesHandler),
    ('/users', UsersHandler),
], 
config=settings.APP_CONFIG,
debug=settings.DEBUG)

