
import logging
import base64
import random
import string
import time
from collections import defaultdict
from textwrap import dedent

from google.appengine.ext import db
from google.appengine.api import mail

from util import view
from db import teams, weeks, settings, games

class Entry(db.Model):
    user_id = db.IntegerProperty(required=True)
    name = db.StringProperty()
    alive = db.BooleanProperty(default=True)

    @property
    def activated(self):
        return self.name is not None

class Status(object):
    NONE, WIN, LOSS, VIOLATION = range(4)

class Pick(db.Model):
    user_id = db.IntegerProperty(required=True)
    entry_id = db.IntegerProperty(required=True)
    week = db.IntegerProperty()
    team = db.IntegerProperty(default=-1)
    closed = db.BooleanProperty(default=False)
    status = db.IntegerProperty(default=Status.NONE, choices=range(4))
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
    return p

def create_picks(week, entries):
    new_picks = []
    for (user_id, entry_id) in entries:
        p = Pick(key_name=_pick_key(week, entry_id), user_id=user_id, entry_id=entry_id, week=week)
        new_picks.append(p)
    db.put(new_picks)

def add_entry(user_id):
    entry = Entry(user_id=user_id)
    entry.put()

def name_entry(entry_id, name):
    entry = Entry.get_by_id(entry_id)
    entry.name = name
    entry.put()
    return _create_pick(entry)

def buyback_entry(entry_id):
    entry = Entry.get_by_id(entry_id)
    if not entry:
        return None
    entry.alive = True
    entry.put()
    return _create_pick(entry)

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

def alive_entries():
    entries = {}
    for e in Entry.gql('WHERE alive = True'):
        entries[e.key().id()] = e
    return entries

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

def close_picks(week, teams=None):
    """Close any picks that have the given teams in the given week"""
    if teams is not None:
        logging.info('Closing teams: %s', teams)
        teams_list = ', '.join('%d' % x for x in teams)
        extra = 'team IN (%s)' % teams_list
    else:
        last_week = last_week_picks(week)
        logging.info('Closing all open entries')
        extra = 'closed = False'
    to_save = []
    query = 'WHERE week = %d AND %s' % (week, extra)
    logging.info('Finding picks: %s', query)
    for p in Pick.gql(query):
        p.closed = True
        if teams is None and (p.team == -1 or p.team == last_week.get(p.entry_id)):
            p.status = Status.VIOLATION
        to_save.append(p)
    db.put(to_save)

def picks_closed(week):
    return Pick.gql('WHERE week = :1 AND closed = False', week).count() == 0

def nopicks(week):
    return Pick.gql('WHERE week = :1 AND team = -1', week)

def last_week_picks(week):
    if week == 1:
        return {}
    entries = {}
    for p in db.GqlQuery('SELECT entry_id,team FROM Pick WHERE week = :1 AND status = :2',
                         week - 1, Status.WIN):
        entries[p.entry_id] = p.team 
    return entries

def picks_for_week(week):
    return Pick.gql('WHERE week = :1', week)   

def set_picks_status(week):
    # TODO: only need 1 query and postprocessing for complete/winners
    winners = games.winners_for_week(week)
    picks = []
    winning_entries = set()
    counts = defaultdict(int)
    for p in Pick.gql('WHERE week = :1', week):
        counts[p.team] += 1
        # violations are set when picks are closed
        if p.team not in winners:
            p.status = Status.LOSS
        elif p.status != Status.VIOLATION:
            p.status = Status.WIN
            winning_entries.add(p.entry_id)
        else:
            continue
        picks.append(p)
    db.put(picks)

    entries_to_save = []
    alive_entries = []
    for e in Entry.gql('WHERE alive = True'):
        if e.key().id() not in winning_entries:
            e.alive = False
            entries_to_save.append(e)
        else:
            alive_entries.append((e.user_id, e.key().id()))
    db.put(entries_to_save)

    return (counts, alive_entries)

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

