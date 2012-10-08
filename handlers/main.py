
from db import settings, users, entries, weeks
from util import view, handler
import webapp2

class HomeHandler(handler.BaseHandler):
    def get(self):
        view.render(self, 'home', {}, css=True)

class RulesHandler(handler.BaseHandler):
    def get(self):
        view.render(self, 'rules', {})

class LoginHandler(handler.BaseHandler):
    def _redirect(self, path, real):
        if real:
            self.redirect(path)
        else:
            view.render_json(self, {'redirect': path})
            
    def _login(self, user, real_redirect):
        if not user:
            self.abort(403)
        self.login(user)
        if not self.user.name:
            self._redirect('/setup/activation', real_redirect)
        elif entries.unnamed_entries(self.user.key().id()) > 0:
            self._redirect('/setup/entries', real_redirect)
        elif not weeks.check_deadline(weeks.current()):
            self._redirect('/breakdown', real_redirect)
        else:
            self._redirect('/picks', real_redirect)

    def get(self, token):
        user = users.get_user_by_token(token)
        self._login(user, True)

    def post(self):
        email = self.request.POST.get('email')
        password = self.request.POST.get('password')
        user = users.get_user_by_password(email, password)
        self._login(user, False)

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

