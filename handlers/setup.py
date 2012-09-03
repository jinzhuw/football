
from db import settings, entries, weeks, users
from util import view, handler
import logging
import webapp2
import Crypto

def name_entries(handler):
    for entry_id in handler.request.arguments():
        if not entry_id.startswith('entry_'):
            continue
        name = handler.request.get(entry_id)
        entries.name_entry(int(entry_id[6:]), name)

class UserActivationHandler(handler.BaseHandler):
    @handler.user
    def get(self):
        if self.user.name:
            logging.warning('User %s already activated, redirecting to picks', self.user.name)
            self.redirect('/picks')
            return

        logging.info('Activation requested for email %s', self.user.email)
        user_entries = entries.entries_for_user(self.user).values()
        user_entries.sort(key=lambda e: e.name)
        args = {
            'entries': user_entries,
        }
        logging.info('setup args: %s', args)
        view.render(self, 'setup', args, css=True, js=True)

    @handler.user
    def post(self):
        name = self.request.POST.get('name')
        self.user.name = name
        self.user.put()

        password = self.request.POST.get('password')
        if password:
            users.set_user_password(self.user, password)

        name_entries(self)

        self.redirect('/picks')
        
class UpdateEmailHandler(handler.BaseHandler):
    @handler.user
    def get(self):
        view.render(self, 'setup', {'edit_email': True}, css=True, js=True)

    def post(self):
        # TODO: check format of email
        # TODO: check if email exists
        email = self.request.POST.get('email')
        self.user.email = email
        self.user.put()
        self.redirect('/picks')

class UpdatePasswordHandler(handler.BaseHandler):
    @handler.user
    def get(self):
        edit = 'change' if self.user.password else True
        view.render(self, 'setup', {'edit_password': edit}, css=True, js=True)
        
    def post(self):
        password = self.request.POST.get('password')
        users.set_user_password(self.user, password)
        self.redirect('/picks')

class NameEntriesHandler(handler.BaseHandler):
    @handler.user
    def get(self):
        new_entries = [] 
        old_entries = 0
        for e in entries.entries_for_user(self.user).values():
            if not e.activated:
                new_entries.append(e)
            else:
                old_entries += 1
        if not new_entries:
            self.redirect('/picks')
            return
        args = {
            'new_entries': sorted(new_entries, key=lambda e: e.name),
            'old_entries': old_entries,
        }
        view.render(self, 'setup', args, css=True, js=True)

    def post(self):
        name_entries(self)
        self.redirect('/picks')

class CheckEntryName(handler.BaseHandler):
    @handler.user
    def get(self, entry_name):
        if (entries.entry_name_exists(entry_name)):
            self.abort(409)

app = webapp2.WSGIApplication([
    ('/setup/activation', UserActivationHandler),
    ('/setup/email', UpdateEmailHandler),
    ('/setup/entries', NameEntriesHandler),
    webapp2.Route('/setup/checkentry/<entry_name>', CheckEntryName),
    ('/setup/password', UpdatePasswordHandler),
],
config=settings.app_config(),
debug=settings.debug())

