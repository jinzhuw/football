
import json
import webapp2
from db.users import User
from webapp2_extras import sessions

class BaseHandler(webapp2.RequestHandler):

    _user = None

    def dispatch(self):
        try:
            super(BaseHandler, self).dispatch()
        finally:
            self.session_store.save_sessions(self.response)

    @webapp2.cached_property
    def session_store(self):
        return sessions.get_store(request=self.request)

    @webapp2.cached_property
    def session(self):
        return self.session_store.get_session()

    @webapp2.cached_property
    def user(self):
        if self._user is None:
            auth_data = self.session.get('auth')
            if auth_data:
                user_id = auth_data.get('user_id')
                if user_id:
                    self._user = User.get_by_id(user_id)
        return self._user 

    def login(self, user):
        self.session['auth'] = {'user_id': user.key().id()}
        self._user = user

    def logout(self):
        self._user = None
        del self.session['auth']

    def json_response(self, j):
        s = json.dumps(j) 
        self.response.headers['Content-Type'] = 'application/json'
        self.response.write(s)


