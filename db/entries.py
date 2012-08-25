
import logging
import base64
import random
import string
import time
from textwrap import dedent
from webapp2_extras.appengine.auth.models import User

from google.appengine.ext import db
from google.appengine.api import mail

from util import view
from db import teams, weeks, settings

class Entry(db.Model):
    player_id = db.IntegerProperty(required=True)
    name = db.StringProperty()
    activated = db.BooleanProperty(default=False)
    alive = db.BooleanProperty(default=True)

class Status(object):
    OPEN, CLOSED, WIN, LOSS, VIOLATION = range(5)

class Pick(db.Model):
    player_id = db.IntegerProperty(required=True)
    entry = db.ReferenceProperty(Entry, required=True, collection_name='picks')
    week = db.IntegerProperty()
    team = db.IntegerProperty(default=-1)
    status = db.IntegerProperty(default=Status.OPEN, choices=range(5))
    modified = db.DateTimeProperty(auto_now=True) 

def reset():
    for p in Pick.all():
        p.delete()

    for e in Entry.all():
        e.delete()

def pick_key(week, entry):
    return '%d,%d' % (week, entry.key().id())

def add_entry(player_id):
    entry = Entry(player_id=player_id)
    entry.put()

def name_entry(entry_id, name):
    entry = Entry.get_by_id(entry_id)
    entry.name = name
    entry.activated = True
    entry.put()
    _create_pick(entry)

def buyback_entry(entry_id):
    entry = Entry.get_by_id(entry_id)
    entry.alive = True
    entry.put()
    _create_pick(entry)

def get_entries(player):
    return Entry.gql('WHERE player_id = :1', player.key.id())

def get_all_entries():
    return Entry.all()

def _create_pick(entry):
    week = weeks.current()
    p = Pick(key_name=pick_key(week, entry), player_id=entry.player_id, entry=entry, week=week)
    p.put()

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

def player_picks(player, week):
    picks = {}
    for p in Pick.gql('WHERE week = :1 and player_id = :2 and activated = True', week, player.key.id()):
        picks[p.entry.key().id()] = p
    return picks

def select_team(entry, week, team):
    key = pick_key(entry, week)
    logging.info('Selecting team: pick key = %s, team = %s', key, team)
    p = Pick.get_by_key_name(key)
    p.team = teams.id(team)
    p.put()

def initialize_picks(week):
    active = Entry.gql('WHERE active = TRUE')
    for e in active:
        p = Pick(key_name=pick_key(week, e), player=e.player, entry=e, week=week)
        p.put()

plain_pick = dedent('''
    Hello %(name)s!

    You have the following active entries in Jack's NFL Suicide Pool:
    %(entries)s

    Make your picks for Week %(week)d by clicking the following link:
    %(link)s

    You have until %(deadline)s to save your picks.

    Good luck!
''')
html_pick = view.html_template(plain_pick)

def email_team_picker(player, week):
    if not settings.EMAIL_ENABLED:
        logging.info('email disabled')
        return
    active_entries = Entry.gql('WHERE active = TRUE and player_id = :1', player.key().id())
    if active_entries.count() == 0:
        logging.info('No active entries for %s', player.name)
        return
    handle = encrypt_handle(week, player)
    args = {
        'name': player.name,
        'entries': '\n'.join(e.name for e in active_entries),
        'link': 'http://football.iernst.net/choose?handle=%s' % handle,
        'week': week,
        'deadline': weeks.deadline(week).strftime('%A, %B %d at %I:%M%p'),
    }
    plain = plain_pick % args
    args['deadline'] = '<b>%s</b>' % args['deadline']
    args['entries'] = args['entries'].replace('\n', '<br/>')
    args['link'] = '<a href="%(link)s">%(link)s</a>' % args
    html = html_pick % args

    num_retries = 3
    sleep = 2
    while num_retries > 0:
        try:
            mail.send_mail(
                sender=settings.EMAIL_SOURCE,
                to='%s <%s>' % (player.name, player.email),
                subject='Suicide Pool: Your Picks for Week %d' % week,
                body=plain,
                html=html
            )
            return
        except Exception:
            logging.exception('Failed to send team picker for %r, email = %r, retrying',
                              player.name, player.email) 
        num_retries -= 1
        time.sleep(sleep)
        sleep *= 2

plain_breakdown = dedent('''
    The picks for Week %(week)d are in!

    You can view them at the following link:
    %(link)s
    
    Below is the distribution of picks:
    No Pick - %(nopick)d
    %(picks)s
''')
html_breakdown = view.html_template(plain_breakdown)
def email_breakdown(week):
    if not settings.EMAIL_ENABLED:
        logging.info('Email is disabled, skipping sending breaking')
        return
    picks, nopick = count_picks(week) 
    args = {
        'week': week,
        'link': 'http://football.iernst.net/results',
        'nopick': nopick,
        'picks': '\n'.join('%s - %d' % e for e in sorted(picks.iteritems()))
    }
    plain = plain_breakdown % args
    args['link'] = '<a href="%(link)s">%(link)s</a>' % args
    args['picks'] = args['picks'].replace('\n', '<br/>') 
    html = html_breakdown % args
 
    email_all('Suicide Pool: Week %d Breakdown' % week, plain, html)
   
def email_all(subject, plain, html):
    addresses = []
    for p in Player.all():
        addresses.append(p.email)

    logging.info('Sending breakdown email to %d players', len(addresses))

    mail.send_mail(
        sender=settings.EMAIL_SOURCE,
        to='football@iernst.net',
        bcc=addresses,
        subject=subject,
        body=plain,
        html=html
    )
     

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

from Crypto.Cipher import AES
coder = AES.new(settings.SYMMETRIC_KEY)

def random_string(n):
    return ''.join(random.choice(string.letters + string.digits) for x in range(n))

def encrypt_handle(week, user_id):
    data = '%d,%d,' % (week, user_id)
    pad_len = 16 - len(data) % 16
    data += random_string(pad_len)
    return base64.urlsafe_b64encode(coder.encrypt(data))

def decrypt_handle(data):
    data = data.encode('utf8') # incase we have a unicode string
    d = coder.decrypt(base64.urlsafe_b64decode(data))
    week, user_id, extra = d.split(',', 2)
    return (int(week), user_id)


