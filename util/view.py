
import os
import logging
import json

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

def render(handler, page, args, css=False, js=False): 
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
        if user.is_admin:
            navs.extend(admin_pages)
    args['navs'] = navs

    data = template.render(fullpath, args)
    handler.response.out.write(data)
    return data

def render_json(handler, data):
    s = json.dumps(data) 
    handler.response.headers['Content-Type'] = 'application/json'
    handler.response.out.write(s)
    return s

class cached:
    def __init__(self, ttl):
        self.ttl = ttl

    def __call__(self, f):
        def func(handler, *args, **kwargs):
            force = handler.request.get('force')
            if not force and _cache_hit(handler, handler.request.path):
                return
            logging.debug('Caching page %s', handler.request.path)
            data = f(handler, *args, **kwargs)
            memcache.set(handler.request.path, data, self.ttl)
        return func

def _cache_hit(handler, key):
    data = memcache.get(key)
    if data is not None:
        logging.debug('Using cached data for page %s', key)
        handler.response.out.write(data)
        if hasattr(handler, 'type') and handler.type == 'json':
            handler.response.headers['Content-Type'] = 'application/json'
    return data is not None

def clear_cache(page):
    memcache.delete(page)
