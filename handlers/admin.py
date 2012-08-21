
from db import settings, users, entries
from util import view, handler
from collections import defaultdict
import string
import logging
import webapp2

class AdminHandler(handler.BaseHandler):
    def get(self):
        # TODO: add list of users to admin view
        # TODO: ajax to view/edit user, same urls as user settings page
        sections = dict((c, []) for c in string.uppercase)
        entries_by_player = defaultdict(list)
        for e in entries.get_all_entries():
            entries_by_player[e.player_id].append(e)
        for user in users.get_users():
            sections[user.name[0]].append((user, entries_by_player.get(user.key.id(), [])))
        view.render(self, 'admin', {'users': sections.items()})

class GetEntriesHandler(handler.BaseHandler):
    def get(self):
        players = {}
        for user in users.get_users():
            players[user.key.id()] = user.name
        d = defaultdict(list)
        for e in entries.get_all_entries():
            d[players[e.player_id]].append({
                'name': e.name,
                'status': e.status,
                'enabled': e.enabled
            })
        self.json_response(d)

class NewUserHandler(handler.BaseHandler):
    def post(self):
        name = self.request.POST.get('name')
        email = self.request.POST.get('email')
        users.create_user(self, name, email, 1)

app = webapp2.WSGIApplication([
    ('/admin/newuser', NewUserHandler),
    ('/admin/entries', GetEntriesHandler),
    ('/admin', AdminHandler),
], 
config=settings.APP_CONFIG,
debug=settings.DEBUG)

