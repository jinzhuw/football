
from google.appengine.ext import db
from db import teams

class Game(db.Model):
    week = db.IntegerProperty()
    home = db.IntegerProperty()
    away = db.IntegerProperty()
    winner = db.IntegerProperty(default=-1)

def reset():
    for g in Game.all():
        g.delete()

    thursday = []
    f = open('../data/thursday.games', 'r') 
    for line in f:
        thursday.append(line.split())

    schedule = {}
    f = open('../data/schedule.raw', 'r')
    for line in f:
        data = line.split()
        team = data[0]
        for i,opp in enumerate(data[1:]):
            if team in thursday[i]:
                pass # skip thursday games
            week = i + 1
            home = team
            if opp.startswith('@'):
                home = opp[1:]
                opp = team
            if week not in schedule:
                schedule[week] = {}
            schedule[week][home] = opp

    for week in sorted(schedule):
        for home in schedule[week]:
            opp = schedule[week][home]
            if opp == 'BYE':
                continue
            if home == opp:
                raise Exception('home and away are same team %d, week %d' % (home, week))
            g = Game(week=week, home=teams.id(home), away=teams.id(opp))
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


