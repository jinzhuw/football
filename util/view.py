
import os
import logging

from google.appengine.ext.webapp import template
from google.appengine.api import memcache, users

from db import settings

pages = (
    ('Home', '/'),
    ('Rules', '/rules'),
    ('Results', '/results'),
)
user_pages = (
    ('Picks', '/picks'),
)
admin_pages = (
    ('Users', '/users'),
    ('Games', '/games'),
    ('Admin', '/admin'),
)

def render(handler, page, args, cache_ttl=0, css=False, js=False): 
    fullpath = os.path.join(os.path.dirname(__file__), '../templates/%s.html' % page)

    if css:
        args['css'] = page
    if js:
        args['js'] = page

    args['active_nav'] = handler.request.path

    user = handler.user
    args['user'] = handler.user
    navs = list(pages)
    if user:
        navs.extend(user_pages)
        #if user.is_admin:
    navs.extend(admin_pages)
    args['navs'] = navs

    data = template.render(fullpath, args)
    if cache_ttl:
        memcache.set(page, data, cache_ttl)
    handler.response.out.write(data)

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
