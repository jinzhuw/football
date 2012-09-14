
import webapp2
import random
import string
import time
from google.appengine.ext import db

class _Settings(db.Model):
    login_key = db.StringProperty(multiline=True)
    session_key = db.StringProperty(multiline=True)
    email_source = db.StringProperty()
    email_enabled = db.BooleanProperty(default=True)
    debug = db.BooleanProperty()
    aws_access_key = db.StringProperty(default='')
    aws_secret_key = db.StringProperty(default='')
    use_google_email = db.BooleanProperty(default=True)
    

_cached_settings = None
_cached_ttl = None

def _random_string(length):
    return str(''.join(random.choice(string.printable) for x in range(length)))

def _load_settings():
    settings = _Settings.get_by_key_name('singleton') 
    if not settings:
        settings = _Settings(key_name='singleton')
        settings.login_key = _random_string(16)
        settings.session_key = _random_string(16)
        settings.email_source = 'Jack Gonzales <jgonzales6@gmail.com>'
        settings.debug = True
        settings.put()
    settings.put()
    return settings

def _cached(real_func):
    def func():
        if not _cached_ttl or time.time() > _cached_ttl:
            global _cached_settings, _cached_ttl
            _cached_ttl = time.time() # + 600 # only lookup settings every 10 minutes
            _cached_settings = _load_settings()
        return real_func()
    return func

@_cached
def login_key():
    return str(_cached_settings.login_key)

@_cached
def app_config():
    cfg = webapp2.Config()
    cfg['webapp2_extras.sessions'] = {'secret_key': str(_cached_settings.session_key)}
    return cfg

@_cached
def email_source():
    return _cached_settings.email_source

@_cached
def email_enabled():
    return _cached_settings.email_enabled

@_cached
def use_google_email():
    return _cached_settings.use_google_email

@_cached
def debug():
    return _cached_settings.debug
    
@_cached
def aws_access_key():
    return str(_cached_settings.aws_access_key)

@_cached
def aws_secret_key():
    return str(_cached_settings.aws_secret_key)
