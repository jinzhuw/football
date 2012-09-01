
from db import settings, users, entries
from util import view, handler
import webapp2

class HomeHandler(handler.BaseHandler):
    def get(self):
        view.render(self, 'home', {})

class RulesHandler(handler.BaseHandler):
    def get(self):
        view.render(self, 'rules', {})

class PasswordLoginHandler(handler.BaseHandler):
    def get(self):
        view.render(self, 'user', {})

    def post(self):
        email = self.request.POST.get('email')
        password = self.request.POST.get('password')
        user = users.get_user_by_password(email, password)
        if not user:
            self.abort(403)
        self.login(user)
        self.redirect('/picks')

class TokenLoginHandler(handler.BaseHandler):
    def get(self, token):
        user = users.get_user_by_token(token)
        if not user:
            self.abort(403)
        self.login(user)
        if not self.user.name:
            self.redirect('/setup/activation')
        elif entries.has_unnamed_entries(self.user):
            self.redirect('/setup/entries')
        else:
            self.redirect('/picks')

class LogoutHandler(handler.BaseHandler):
    def get(self):
        self.logout()
        self.redirect('/')

app = webapp2.WSGIApplication([
    webapp2.Route('/login/<token>', handler=TokenLoginHandler),
    ('/login', PasswordLoginHandler),
    ('/logout', LogoutHandler),
    ('/rules', RulesHandler),
    ('/', HomeHandler),
],
config=settings.APP_CONFIG,
debug=settings.DEBUG)

