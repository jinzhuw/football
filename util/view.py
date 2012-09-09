
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
        if user.is_admin:
            navs.extend(admin_pages)
    args['navs'] = navs

    data = template.render(fullpath, args)
    if cache_ttl:
        memcache.set(page, data, cache_ttl)
    handler.response.out.write(data)

def render_json(handler, page, data, cache_ttl=0):
    s = json.dumps(data) 
    handler.response.headers['Content-Type'] = 'application/json'
    handler.response.out.write(s)
    if cache_ttl:
        logging.debug('Caching page %s', page)
        memcache.set(page, s, cache_ttl)

def cache_hit(handler, page):
    data = memcache.get(page)
    if data is not None:
        logging.debug('Using cached data for page %s', page)
        handler.response.out.write(data)
        if hasattr(handler, 'type') and handler.type == 'json':
            handler.response.headers['Content-Type'] = 'application/json'
    return data is not None

def clear_cache(page):
    memcache.delete(page)
