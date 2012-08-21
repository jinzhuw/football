
from google.appengine.dist import use_library
#use_library('django', '1.2')

import os
import logging

from google.appengine.ext.webapp import template
from google.appengine.api import memcache, users

from db import settings

pages = (
    ('Home', '/'),
    ('Rules', '/rules'),
    ('Standings', '/standings'),
)
user_pages = (
    ('Picks', '/picks'),
    ('Settings', '/user/settings'),
)
admin_pages = (
    ('Games', '/games'),
    ('Admin', '/admin'),
)

def render(handler, page, args, cache_ttl=0): 
    fullpath = os.path.join(os.path.dirname(__file__), '../templates/%s.html' % page)

    args['active_nav'] = handler.request.path

    user = handler.user
    args['user'] = handler.user
    left_navs = list(pages)
    right_navs = list()
    if user:
        right_navs.extend(user_pages)
        #if user.is_admin:
    left_navs.extend(admin_pages)
    args['left_navs'] = left_navs
    args['right_navs'] = right_navs

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

def html_template(tmpl):
    html = ['<html><body>']
    for line in tmpl.split('\n\n'):
        line = line.strip()
        html.append('<p>%s</p>' % line.replace('\n', '<br/>\n'))
    html.append('</body></html>')
    return '\n'.join(html)
