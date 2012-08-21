
from db import settings, entries
from util import view, handler
import logging
import webapp2
from webapp2_extras.appengine.auth.models import User

def create_user(handler, name, email, num_entries):
    user = handler.auth.store.user_model.create_user(email, password_raw='hello')
    # Passing password_raw=password so password will be hashed
    # Returns a tuple, where first value is BOOL. If True ok, If False no new user is created
    if not user[0]: #user is a tuple
        logging.error(user[1])
        handler.abort(500)
    else:
        # User is created, let's try redirecting to login page
        user = user[1]
        try:
            user.name = name
            user.email = email
            user.is_admin = False # set admins manually in datastore
            user.put()
            for i in range(num_entries):
                entries.add_entry(user.key.id())
            # TODO: create entries, without name, use status to identify unnamed entries
            handler.redirect('/admin', abort=True)
        except (AttributeError, KeyError), e:
            logging.error(e)
            handler.abort(403)

def edit_user(email, name=None, password=None, new_email=None):
    # get user from db
    # set each param (special for email and password?)
    pass

def name_entry(handler, entry, entry_name): 
    # get entry from db
    # set name
    # make active
    pass

def get_users():
    return User.gql('ORDER BY name')

def add_entry_to_user(handler, email, num_entries):
    pass
