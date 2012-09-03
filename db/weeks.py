
from datetime import datetime, timedelta

from google.appengine.ext import db

from db import settings
from util import timezone

class _Week(db.Model):
    current = db.IntegerProperty()

def current():
    week = _Week.get_by_key_name('singleton')
    if not week:
        week = _Week(key_name='singleton', current=1)
    return week.current

def reset():
    for w in _Week.all():
        w.delete()
    w = _Week(key_name='singleton', current=1)
    w.put()

def increment():
    week = _Week.get_by_key_name('singleton')
    week.current += 1
    week.put()

week0 = datetime(2012, 9, 1, 23, 0, tzinfo=timezone.Pacific)
def deadline(week):
    offset = timedelta(weeks=week)
    return week0 + offset

def check_deadline(week):
    now = datetime.now(timezone.Pacific)
    #if settings.NODEADLINE:
    #    return True
    return now < deadline(week)

def results(week):
    # tuesday 8 am
    return deadline(week) + timedelta(days=2, hours=9)
     

