
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


####################################################
# Manage creating and modifying entries and picks
####################################################

def add_entry(user_id):
    entry = Entry(user_id=user_id)
    entry.put()

def _create_pick(entry, week, save=True):
    p = Pick(key_name=_pick_key(week, entry.key().id()), user_id=entry.user_id, entry_id=entry.key().id(), week=week)
    if save:
        p.put()
    return p

def name_entry(entry_id, name):
    entry = Entry.get_by_id(entry_id)
    entry.name = name
    entry.put()
    return _create_pick(entry, weeks.current())

def buyback_entry(entry_id):
    entry = Entry.get_by_id(entry_id)
    if not entry:
        return None
    entry.alive = True
    entry.put()
    return _create_pick(entry, weeks.current())

def create_picks(week, entries):
    new_picks = []
    for e in entries:
        new_picks.append(_create_pick(e, week, False))
    db.put(new_picks)

def select_team(entry_id, week, team):
    key = _pick_key(week, entry_id)
    logging.info('Selecting team: pick key = %s, team = %s', key, teams.shortname(team))
    p = Pick.get_by_key_name(key)
    p.team = team
    p.put()


####################################################
# Finding entries and picks
####################################################

def entries_for_user(user):
    entries = {}
    for e in Entry.gql('WHERE user_id = :1', user.key().id()):
        entries[e.key().id()] = e
    return entries

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
    if use_cursors:
        return _iterpicks_with_cursors()
    else:
        return Pick.gql('WHERE closed = True ORDER BY entry_id')

def _iterpicks_with_cursors():
    limit = 100
    picks = Pick.gql('ORDER BY entry_id LIMIT %d' % limit)
    found = limit
    while found == limit:
        found = 0
        for pick in picks.fetch(limit):
            found += 1
            if not pick.closed:
                continue
            yield pick
        logging.info('Finished fetch. Found %d', found)
        picks.with_cursor(picks.cursor())

def all_picks(week):
    picks = {}
    for p in Pick.gql('WHERE week = :1', week):
        picks[p.entry.key().id()] = p
    return picks

####################################################
# Checking entries
####################################################

def entry_name_exists(entry_name):
    return Entry.gql('WHERE name = :1', entry_name).count() > 0

def has_unnamed_entries(user_id):
    return Entry.gql('WHERE user_id = :1 and name = NULL', user_id).count() > 0

def picks_closed(week):
    return Pick.gql('WHERE week = :1 AND closed = False', week).count() == 0

def picks_status_set(week):
    return Pick.gql('WHERE week = :1 AND status = :2', week, Status.NONE).count() == 0

####################################################
# Weekly entry/pick management
####################################################

def close_picks(week, teams=None):
    """Close any picks that have the given teams in the given week"""
    query = ['WHERE week = %d AND closed = False' % week]
    last_week = last_week_picks(week)
    if teams is not None:
        if len(teams) == 0:
            logging.info('No teams to close')
            return 0
        logging.info('Closing teams: %s', teams)
        teams_list = ', '.join('%d' % x for x in teams)
        query.append('AND team IN (%s)' % teams_list)
    else:
        logging.info('Closing all open entries')
    to_save = []
    query = ' '.join(query)
    logging.info('Finding picks: %s', query)
    num_closed = 0
    for p in Pick.gql(query):
        num_closed += 1
        p.closed = True
        if p.team == last_week.get(p.entry_id) or teams is None and p.team == -1:
            p.status = Status.VIOLATION
        to_save.append(p)
    db.put(to_save)
    return num_closed

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

def get_team_counts(week):
    counts = defaultdict(int)
    for p in Pick.gql('WHERE week = :1', week):
        counts[p.team] += 1
    return counts

def get_status_counts(week):
    counts = defaultdict(int)
    for p in Pick.gql('WHERE week = :1', week):
        counts[p.status] += 1
    return counts
    

def set_pick_status(week, game_results=None):
    query = ['WHERE week = %d AND status != %d' % (week, Status.VIOLATION)]
    if game_results is None:
        winners, losers = games.results_for_week(week)
    else:
        winners, losers = game_results
        if len(winners) < 15:
            # if there are a lot of games being handled, look at all picks for the week
            winners_list = ', '.join('%d' % x for x in winners)
            losers_list = ', '.join('%d' % x for x in losers)
            query.append('AND team IN (%s, %s)' % (winners_list, losers_list))
    query = ' '.join(query)
    
    logging.info('Setting pick status: query = %s', query)
    picks = []
    for p in Pick.gql(query):
        logging.info('Looking at pick %d, team %d', p.key().id(), p.team)
        if p.team in winners:
            p.status = Status.WIN
        elif p.team in losers:
            p.status = Status.LOSS
        else:
            logging.info('Skipping...')
            continue
        picks.append(p)
    db.put(picks)
    return len(picks) != 0

def deactivate_dead_entries(week):
    picks = {}
    for p in db.GqlQuery('SELECT entry_id,status FROM Pick WHERE week = :1', week):
        picks[p.entry_id] = p.status
    
    entries_to_save = []
    alive_entries = []
    for e in Entry.gql('WHERE alive = True'):
        status = picks[e.key().id()]
        if status != Status.WIN:
            e.alive = False
            entries_to_save.append(e)
        else:
            alive_entries.append(e)
    db.put(entries_to_save)

    return alive_entries

