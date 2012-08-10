
from google.appengine.dist import use_library
use_library('django', '1.2')

import os
import logging

from google.appengine.ext.webapp import template
from google.appengine.api import memcache
from google.appengine.api import users

import settings

def render(handler, page, args, cache_ttl=0): 
    fullpath = os.path.join(os.path.dirname(__file__), 'templates/%s.html' % page)

    args['css'] = page
    args['page'] = handler.request.path

    user = users.get_current_user()
    if user and user.email() in settings.ADMINS:
        args['user'] = user
        args['logout'] = users.create_logout_url('/')

    data = template.render(fullpath, args)
    if cache_ttl:
        memcache.set(page, data, cache_ttl)
    handler.response.out.write(data)
    return data

def is_admin():
    user = users.get_current_user()
    return user and user.email() in settings.ADMINS

def cache_hit(handler, page):
    data = memcache.get(page)
    if data is not None:
        handler.response.out.write(data)
    return data is not None

def clear_cache(page):
    memcache.delete(page)
