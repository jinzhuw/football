
from db import settings, users, entries, weeks
from util import view, handler
from collections import defaultdict
import string
import logging
import webapp2

class AdminHandler(handler.BaseHandler):
    def get(self):
        view.render(self, 'admin', {})


app = webapp2.WSGIApplication([
    ('/admin', AdminHandler),
], 
config=settings.APP_CONFIG,
debug=settings.DEBUG)

