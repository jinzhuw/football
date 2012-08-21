
import json
import webapp2
from webapp2_extras import auth
from webapp2_extras import sessions
from webapp2_extras.auth import InvalidAuthIdError
from webapp2_extras.auth import InvalidPasswordError
from webapp2_extras.appengine.auth.models import User

class BaseHandler(webapp2.RequestHandler):
    """
    BaseHandler for all requests

    Holds the auth and session properties so they are reachable for all requests
    """
    def dispatch(self):
        """
        Save the sessions for preservation across requests
        """
        try:
            super(BaseHandler, self).dispatch()
        finally:
            self.session_store.save_sessions(self.response)

    @webapp2.cached_property
    def auth(self):
        return auth.get_auth()

    @webapp2.cached_property
    def session_store(self):
        return sessions.get_store(request=self.request)

    @webapp2.cached_property
    def auth_config(self):
        """Dict to hold urls for login/logout"""
        return {
            'login_url': '/user/login',
            'logout_url': '/user/logout'
        }

    @webapp2.cached_property
    def user(self):
        auth_data = self.auth.get_user_by_session()
        if auth_data is None:
            return None
        user_id = auth_data.get('user_id')
        if user_id is None:
            return None
        return User.get_by_id(user_id)

    def json_response(self, j):
        s = json.dumps(j) 
        self.response.headers['Content-Type'] = 'application/json'
        self.response.write(s)


