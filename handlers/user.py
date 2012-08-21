
from db import settings
from util import view, handler
import webapp2

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
            # Returns error message to self.response.write in the BaseHandler.dispatcher
            # Currently no message is attached to the exceptions
            return e

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
        view.render(self, 'user', {})

    def post(self):
        self.response.write('updating a user')

app = webapp2.WSGIApplication([
    ('/user/login', LoginHandler),
    ('/user/logout', LogoutHandler),
    ('/user/settings', UserHandler),
],
config=settings.APP_CONFIG,
debug=settings.DEBUG)

