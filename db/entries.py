
import logging
import base64
import random
import string
import time
from textwrap import dedent

from google.appengine.ext import db
from google.appengine.api import mail

from util import view
from db import teams, weeks, settings

class Entry(db.Model):
    user_id = db.IntegerProperty(required=True)
    name = db.StringProperty()
    alive = db.BooleanProperty(default=True)

    @property
    def activated(self):
        return self.name is not None

class Status(object):
    OPEN, CLOSED, WIN, LOSS, VIOLATION = range(5)

class Pick(db.Model):
    user_id = db.IntegerProperty(required=True)
    entry_id = db.IntegerProperty(required=True)
    week = db.IntegerProperty()
    team = db.IntegerProperty(default=-1)
    status = db.IntegerProperty(default=Status.OPEN, choices=range(5))
    modified = db.DateTimeProperty(auto_now=True) 

    def team_city(self):
        return teams.cityname(self.team)

    def team_shortname(self):
        return teams.shortname(self.team)

def _pick_key(week, entry_id):
    return '%d,%d' % (week, entry_id)

def _create_pick(entry):
    week = weeks.current()
    p = Pick(key_name=_pick_key(week, entry.key().id()), user_id=entry.user_id, entry_id=entry.key().id(), week=week)
    p.put()

def add_entry(user_id):
    entry = Entry(user_id=user_id)
    entry.put()

def name_entry(entry_id, name):
    entry = Entry.get_by_id(entry_id)
    entry.name = name
    entry.put()
    _create_pick(entry)

def buyback_entry(entry_id):
    entry = Entry.get_by_id(entry_id)
    entry.alive = True
    entry.put()
    _create_pick(entry)

def entries_for_user(user):
    entries = {}
    for e in Entry.gql('WHERE user_id = :1', user.key().id()):
        entries[e.key().id()] = e
    return entries

def entry_name_exists(entry_name):
    return Entry.gql('WHERE name = :1', entry_name).count() > 0

def unnamed_entries(user_id):
    return Entry.gql('WHERE user_id = :1 and name = NULL', user_id).count()

def picks_for_user(user, week):
    picks = {}
    for p in Pick.gql('WHERE week = :1 and user_id = :2', week, user.key().id()):
        picks[p.key()] = p
    return picks

def get_all_entries():
    return Entry.all()

def iterpicks(use_cursors=False):
    picks = Pick.gql('ORDER BY week')
    if not use_cursors:
        return picks
    return _iterpicks_with_cursors()

def _iterpicks_with_cursors():
    limit = 100
    picks = Pick.gql('ORDER BY week LIMIT %d' % limit)
    found = limit
    while found == limit:
        found = 0
        for pick in picks.fetch(limit):
            logging.info('Yielding pick for entry %r', pick.entry.name)
            found += 1
            if pick.status == Status.OPEN:
                continue
            yield pick
        logging.info('Finished fetch. Found %d', found)
        picks.with_cursor(picks.cursor())
    logging.info('DONE ITERATING')

def all_picks(week):
    picks = {}
    for p in Pick.gql('WHERE week = :1', week):
        picks[p.entry.key().id()] = p
    return picks

def select_team(entry_id, week, team):
    key = _pick_key(week, entry_id)
    logging.info('Selecting team: pick key = %s, team = %s', key, teams.shortname(team))
    p = Pick.get_by_key_name(key)
    p.team = team
    p.put()

def initialize_picks(week):
    active = Entry.gql('WHERE active = True')
    for e in active:
        p = Pick(key_name=_pick_key(week, e.key().id()), player=e.player, entry=e, week=week)
        p.put()

def count_picks(week):
    picks = Pick.gql('WHERE week = :1', week)   
    stats = defaultdict(int)
    for p in picks:
        stats[p.team] += 1
    nopick = stats.get(-1, 0)
    choices = {}
    for team,count in stats.iteritems():
        if team == -1:
            continue
        choices[teams.longname(team)] = count
    return choices, nopick

