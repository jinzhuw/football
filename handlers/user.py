
from db import settings, entries, weeks
from util import view, handler
from webapp2_extras.auth import InvalidAuthIdError
from webapp2_extras.auth import InvalidPasswordError
from webapp2_extras.appengine.auth.models import User
import logging
import webapp2
import Crypto

class LoginHandler(handler.BaseHandler):
    def get(self):
        view.render(self, 'user', {})

    def post(self):
        """
        username: Get the username from POST dict
        password: Get the password from POST dict
        """
        username = self.request.POST.get('username')
        password = self.request.POST.get('password')
        # Try to login user with password
        # Raises InvalidAuthIdError if user is not found
        # Raises InvalidPasswordError if provided password doesn't match with specified user
        try:
            self.auth.get_user_by_password(username, password)
            self.redirect('/picks')
        except (InvalidAuthIdError, InvalidPasswordError), e:
            logging.error('Login error: %s', e)
            self.redirect('/')

class TokenLoginHandler(handler.BaseHandler):
    def get(self, handle):
        try:
            week, user_id = entries.decrypt_handle(handle)
            if week != weeks.current():
                self.redirect('/')
            token = User.create_auth_token(user_id)
            logging.info('token = %s', token)
            self.auth.get_user_by_password(user_id, 'hello')            
            self.auth.get_user_by_token(user_id, token)            
            logging.info('logged in user by token = %s', self.user)
            self.redirect('/picks')
        except (InvalidAuthIdError, InvalidPasswordError), e:
            logging.error('Token login error: %s', e)
            self.redirect('/')

class LogoutHandler(handler.BaseHandler):
    def get(self):
        self.auth.unset_session()
        # User is logged out, let's try redirecting to login page
        try:
            self.redirect(self.auth_config['login_url'])
        except (AttributeError, KeyError), e:
            return "User is logged out"

class UserHandler(handler.BaseHandler):
    def get(self):
        args = {
            'new_entries': [],
            'entries': []
        }
        for e in entries.get_entries(self.user):
            if e.activated:
                args['entries'].append(e)
            else:
                args['new_entries'].append(e)
        args['entries'].sort(key=lambda e: e.name)
        args['num_new_entries'] = len(args['new_entries'])
        view.render(self, 'user', args)

class NameHandler(handler.BaseHandler):
    def post(self):
        name = self.request.get('name')
        self.user.name = name
        self.user.put()

class EmailHandler(handler.BaseHandler):
    def post(self):
        email = self.request.get('email')
        self.user.email = email
        self.user.put()

class EntriesHandler(handler.BaseHandler):
    def post(self):
        for entry_id in self.request.arguments():
            if not entry_id.startswith('entry_'):
                continue
            name = self.request.get(entry_id)
            entry_id = entry_id[6:]
            if not name.strip():
                name = self.request.get('default_' + entry_id)
            entries.name_entry(int(entry_id), name)
        self.redirect('/user/settings')

app = webapp2.WSGIApplication([
    webapp2.Route('/user/login/<handle>', handler=TokenLoginHandler),
    ('/user/login', LoginHandler),
    ('/user/logout', LogoutHandler),
    ('/user/settings', UserHandler),
    ('/user/name', NameHandler),
    ('/user/email', EmailHandler),
    ('/user/entries', EntriesHandler),
],
config=settings.APP_CONFIG,
debug=settings.DEBUG)

