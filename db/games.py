
from collections import defaultdict
#from google.appengine.ext import db
from db import teams

class Game(db.Model):
    week = db.IntegerProperty(required=True)
    home = db.IntegerProperty(required=True)
    away = db.IntegerProperty(required=True)
    date = db.DateProperty(required=True)
    home_score = db.IntegerProperty()
    away_score = db.IntegerProperty()
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
            away = teams.id(t[0])
            home = teams.id(t[1])
            schedule[week].append((date, home, away))

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
            g = Game(week=week, home=game[1], away=game[2], date=game[0])
            g.put()

def for_week(week):
    '''
    Return two lists of games, incomplete and complete.

    Each element is a tuple of home and away team long names. Additionally,
    the complete games have the winning team as the third element of the tuple.
    The incomplete games have the game id as the third element.
    '''
    incomplete = []
    complete = []
    games = Game.gql('WHERE week = :1', week)        
    for g in games:
        home = teams.longname(g.home)
        away = teams.longname(g.away)
        if g.winner == -1:
            incomplete.append((home, away, g.key().id()))
        else:
            complete.append((home, away, teams.longname(g.winner)))
    return incomplete, complete

def complete(id, winner):
    game = Game.get_by_id(id)
    game.winner = teams.id(winner)
    game.put() 

def games_are_complete(week):
    games = Game.gql('WHERE week = :1 AND winner = -1', week)                
    return games.count() == 0

def winners_for_week(week):
    winners = set()
    games = Game.gql('WHERE week = :1', week)
    for game in games:
        winners.add(game.winner)
    return winners

