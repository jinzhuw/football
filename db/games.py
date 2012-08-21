
import json
import urllib2
from collections import defaultdict

from google.appengine.ext import db

from db import teams

class Game(db.Model):
    week = db.IntegerProperty(required=True)
    home = db.IntegerProperty(required=True)
    visiting = db.IntegerProperty(required=True)
    date = db.DateProperty(required=True)
    home_score = db.IntegerProperty(default=-1)
    visiting_score = db.IntegerProperty(default=-1)
    winner = db.IntegerProperty(default=-1)

def load_schedule():
    schedule = defaultdict(list)
    f = open('data/schedule.txt', 'r')
    week = 0 
    date = None
    for line in f:
        line = line.strip()
        if line.startswith('WEEK'):
            week = int(line.split()[1])
        elif line.startswith('-'):
            date = datetime.strptime(line[1:], '%A, %b. %d')
        elif line:
            t = line.split(' at ')
            visiting = teams.id(t[0])
            home = teams.id(t[1])
            schedule[week].append((date, home, visiting))

    for week,games in sorted(schedule.iteritems()):
        print ''
        print 'Week %d' % week
        for game in games:
            print game[0].strftime('%A,'), teams.shortname(game[1]), 'vs', teams.shortname(game[2])

def reset():
    for g in Game.all():
        g.delete()
    
    for week,games in sorted(schedule.iteritems()):
        for game in games:
            g = Game(week=week, home=game[1], visiting=game[2], date=game[0])
            g.put()

def load_scores(week):
    scores_url = 'http://www.nfl.com/liveupdate/scorestrip/ss.json'
    data = urllib2.urlopen(scores_url)
    j = json.loads(data.read())
    if j['w'] != str(week):
        logging.warning('Could not load scores for week %d, data contains week %s', week, j['w'])

    games = Game.gql('WHERE week = :1 AND winner = -1', week)        
    scores = {}
    for g in j['gms']:
        if 'F' in g['q']:
            scores[g['h']] = (g['hs'], g['as'])
        else:
            logging.debug('Skipping game %s vs %s, game state is %s', g['h'], g['v'], g['q'])

    loaded = False
    for g in games:
        s = scores.get(teams.shortname(g.home))
        if s:
            logging.info('Setting results for game %s (%d) vs %s (%d)',
                         teams.shortname(g.home), s[0],
                         teams.shortname(g.visiting), s[1])
            g.home_score = s[0]
            g.visiting_score = s[1]
            g.winner = g.home if s[0] > s[1] else g.visiting
            g.put() 
            loaded = True

    return loaded 

def update(id, home_score, visiting_score):
    game = Game.get_by_id(id)
    logging.info('Updating status for game %s (%d) vs %s (%d)',
                 teams.shortname(game.home), home_score,
                 teams.shortname(game.visiting), visiting_score)
    game.home_score = home_score
    game.visiting_score = visiting_score
    g.winner = g.home if home_score > visiting_score else g.visiting
    game.put() 

def for_week(week):
    '''
    Return two lists of games, incomplete and complete.

    Each element is a tuple of home and visiting team long names. Additionally,
    the complete games have the winning team as the third element of the tuple.
    The incomplete games have the game id as the third element.
    '''
    incomplete = []
    complete = []
    status = defaultdict(list)
    games = Game.gql('WHERE week = :1', week)        
    for g in games:
        date = g.date.strftime('%A, %B %d')
        home = teams.cityname(g.home)
        visiting = teams.cityname(g.visiting)
        status[date].append({
            'id': g.key().id(),
            'h': teams.cityname(g.home),
            'v': teams.cityname(g.visiting),
            'f': g.winner != -1,
            'hs': g.home_score,
            'vs': g.visiting_score,
        })
            
    return scores

def complete_for_week(week):
    games = Game.gql('WHERE week = :1 AND winner = -1', week)                
    return games.count() == 0

def winners_for_week(week):
    winners = set()
    games = Game.gql('WHERE week = :1', week)
    for game in games:
        winners.add(game.winner)
    return winners

