
from db import settings, users, entries
from util import view, handler
import webapp2

class HomeHandler(handler.BaseHandler):
    def get(self):
        view.render(self, 'home', {})

class RulesHandler(handler.BaseHandler):
    def get(self):
        view.render(self, 'rules', {})

class LoginHandler(handler.BaseHandler):
    def _login(self, user):
        if not user:
            self.abort(403)
        self.login(user)
        if not self.user.name:
            self.redirect('/setup/activation')
        elif entries.unnamed_entries(self.user.key().id()) > 0:
            self.redirect('/setup/entries')
        else:
            self.redirect('/picks')

    def get(self, token):
        user = users.get_user_by_token(token)
        self._login(user)

    def post(self):
        email = self.request.POST.get('email')
        password = self.request.POST.get('password')
        user = users.get_user_by_password(email, password)
        self._login(user)

class LogoutHandler(handler.BaseHandler):
    def get(self):
        self.logout()
        self.redirect('/')

app = webapp2.WSGIApplication([
    webapp2.Route('/login/<token>', LoginHandler),
    ('/login', LoginHandler),
    ('/logout', LogoutHandler),
    ('/rules', RulesHandler),
    ('/', HomeHandler),
],
config=settings.app_config(),
debug=settings.debug())

