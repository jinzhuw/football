
import os
import logging
import random
import string
import base64

from Crypto.Hash import SHA
from Crypto.Cipher import AES 
from google.appengine.ext import db
from db import settings

class User(db.Model):
    name = db.StringProperty()
    email = db.EmailProperty(required=True)
    is_admin = db.BooleanProperty(default=False)
    password = db.StringProperty(multiline=True)
    salt = db.StringProperty(multiline=True)
    password_reset = db.BooleanProperty(default=False)
    created = db.DateTimeProperty(auto_now_add=True)
    updated = db.DateTimeProperty(auto_now=True)

def create(email):
    email = email.lower()
    existing = User.gql('WHERE email = :1', email)
    if existing.count() != 0:
        logging.error('Email %s already exists', email)
        return None
    user = User(email=email)
    user.put()
    return user

def users_by_id():
    users = {}
    for user in User.all():
        users[user.key().id()] = user
    return users

def _hash_password(salt, password):
    h = SHA.new(salt or '') 
    h.update(password)
    return h.hexdigest()

def get_user_by_password(email, password):
    email = email.lower()
    user = [u for u in User.gql('WHERE email = :1', email)]
    if not user:
        logging.error('Bad login: unknown email %s', email)
        return None
    user = user[0]
    if user.password != _hash_password(user.salt, password):
        logging.error('Bad login: Incorrect password for user %s', email)
        return None
    return user

def set_user_password(user, password):
    user.salt = db.ByteString(os.urandom(16).encode('base_64'))
    user.password = _hash_password(user.salt, password)
    user.put()

token_coder = AES.new(settings.login_key())
def make_login_token(user):
    data = '%s,' % user.key().id()
    pad_len = 32 - len(data) % 32
    data += ''.join(random.choice(string.letters + string.digits) for x in range(pad_len))
    return base64.urlsafe_b64encode(token_coder.encrypt(data))

def get_user_by_token(token):
    token = token.encode('utf8') # incase we have a unicode string
    data = token_coder.decrypt(base64.urlsafe_b64decode(token))
    user_id, extra = data.split(',', 2)
    user = User.get_by_id(int(user_id))
    if not user:
        logging.error('Bad login: invalid token, user_id = %s', user_id)
    return user

