
import json
import lxml.objectify
import logging
import urllib2
from datetime import datetime, timedelta
from collections import defaultdict

from google.appengine.ext import db

from db import teams
from util import timezone

class Game(db.Model):
    week = db.IntegerProperty(required=True)
    home = db.IntegerProperty(required=True)
    visiting = db.IntegerProperty(required=True)
    date = db.DateTimeProperty(required=True)
    deadline = db.DateTimeProperty()
    home_score = db.IntegerProperty(default=-1)
    visiting_score = db.IntegerProperty(default=-1)
    winner = db.IntegerProperty(default=-1)

    def tz_date(self):
        d = self.date
        return datetime(d.year, d.month, d.day, d.hour, d.minute, tzinfo=timezone.Pacific)

    def tz_deadline(self):
        d = self.deadline
        return datetime(d.year, d.month, d.day, d.hour, d.minute, tzinfo=timezone.Pacific)

    def complete(self):
        return self.winner != -1

    def home_fullname(self):
        return teams.fullname(self.home)

    def home_x(self):
        return teams.large_logo_x(self.home)

    def home_y(self):
        return teams.large_logo_y(self.home)

    def visiting_fullname(self):
        return teams.fullname(self.visiting)

    def visiting_x(self):
        return teams.large_logo_x(self.visiting)

    def visiting_y(self):
        return teams.large_logo_y(self.visiting)

class TeamRankingData(db.Model):
    wins = db.IntegerProperty(default=0)
    losses = db.IntegerProperty(default=0)
    power_rank = db.IntegerProperty(default=-1)
    rush_defense_rank = db.IntegerProperty(default=-1)
    rush_offense_rank = db.IntegerProperty(default=-1)
    pass_defense_rank = db.IntegerProperty(default=-1)
    pass_offense_rank = db.IntegerProperty(default=-1)


def read_static_schedule():
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
            try:
                data = line.split(',')
                t = datetime.strptime(data[2].strip(), '%I:%M%p') 
                visiting = teams.id(data[0])
                home = teams.id(data[1].strip())
                dt = datetime(2012, date.month, date.day, t.hour, t.minute)
                schedule[week].append((dt, home, visiting))
            except:
                logging.error('problem on line: %s', line)
                raise

    return schedule

def load_static_schedule():
    for g in Game.all():
        g.delete()
    
    for week,games in read_static_schedule().iteritems():
        for game in games:
            date = game[0]
            deadline = datetime(date.year, date.month, date.day, 23, 0) - timedelta(days=1)
            g = Game(week=week, home=game[1], visiting=game[2], date=date, deadline=deadline)
            g.put()

def reset_for_week(week):
    games_to_save = []
    for g in Game.gql('WHERE week = :1', week):
        if g.winner != -1:
            g.winner = -1
            g.home_score = -1
            g.visiting_score = -1
            games_to_save.append(g)
    db.put(games_to_save)

def _load_url(url, xml):
    data = None
    retries = 3
    while data is None:
        try:
            data = urllib2.urlopen(url)
        except urllib2.URLError:
            logging.exception('Failed to get url %s', url)
            if retries == 0:
                raise
            time.sleep(5)
            retries -= 1
        
    if xml:
        return lxml.objectify.fromstring(data.read())
    else: # json
        return json.loads(data.read())

def load_scores(week):
    j = _load_url('http://www.nfl.com/liveupdate/scorestrip/ss.json', xml=False)

    if j['w'] != week:
        logging.warning('Could not load scores for week %d, data contains week %s', week, j['w'])
        return

    games = Game.gql('WHERE week = :1 AND winner = -1', week)        
    scores = {}
    in_progress = 0
    for g in j['gms']:
        if 'F' in g['q']:
            scores[g['h']] = (g['hs'], g['vs'])
        elif 'P' != g['q']:
            logging.debug('Game %s v %s in progress, state %s', g['v'], g['h'], g['q'])
            in_progress += 1
        else:
            logging.debug('Skipping game %s vs %s, game state is %s', g['v'], g['h'], g['q'])

    winners = set()
    losers = set()
    for g in games:
        if g.winner != -1:
            continue
        s = scores.get(teams.shortname(g.home))
        if s:
            (winner, loser) = update(g, s[0], s[1])
            winners.add(winner)
            losers.add(loser)

    return (winners, losers, in_progress)

def _set_rankings(team):
    rankings = TeamRankingData.get_or_insert(team.get('id'))
    rankings.rush_defense_rank = int(team.get('rushDefenseRank')) 
    rankings.rush_offense_rank = int(team.get('rushOffenseRank')) 
    rankings.pass_defense_rank = int(team.get('passDefenseRank')) 
    rankings.pass_offense_rank = int(team.get('passOffenseRank')) 
    rankings.put()

def load_schedule(week):
    if week < 18:
        logging.warning('Cannot load schedule for week %d, which is a static week', week)

    x = _load_url('http://football.myfantasyleague.com/2012/export?TYPE=nflSchedule&W=%d' % week, xml=True)

    if int(x.nflSchedule.get('week', 0)) != week:
        logging.warning('Could not load schedule for week %d', week)
        return

    for game in x.nflSchedule.matchup:
        date = datetime.fromtimestamp(int(game.get('kickoff')))
        deadline = datetime(date.year, date.month, date.day, 23, 0) - timedelta(days=1)
        assert game.team[0].get('isHome') == '0'
        visiting = teams.id(game.team[0].get('id'))
        home = teams.id(game.team[1].get('id'))
        g = Game(week=week, home=home, visiting=visiting, date=date, deadline=deadline)
        g.put()
        
def update_rankings():
    x = _load_url('http://football.myfantasyleague.com/2012/export?TYPE=nflSchedule', xml=True)

    if int(x.nflSchedule.get('week', 0)) != week:
        logging.warning('Could not update rankings for week %d', week)
        return

    for game in x.nflSchedule.matchup:
        for team in game.team:
            _set_rankings(team)

def update(game, home_score, visiting_score):
    logging.info('Updating status for game %s (%d) vs %s (%d)',
                 teams.shortname(game.home), home_score,
                 teams.shortname(game.visiting), visiting_score)
    game.home_score = home_score
    game.visiting_score = visiting_score
    if home_score > visiting_score:
        winner = game.home
        loser = game.visiting
    elif home_score < visiting_score:
        winner = game.visiting
        loser = game.home
    else:
        raise Exception('Tie game (%d - %d, %d - %d)...dont know what to do....' % \
                        game.home, home_score, game.visiting, visiting_score)
        
    game.winner = winner
    game.put() 
    return (winner, loser)

def games_for_week(week):
    """
    Returns a dict of games for a given week, keyed by date. Each game is a dict of:
    id - Game unique id
    h - Home team name
    v - Visiting team name
    f - boolean, True if the game is finished
    hs - Home team score
    vs - Visiting team score
    """
    return Game.gql('WHERE week = :1', week)
    """
    status = defaultdict(list)
    for g in Game.gql('WHERE week = :1', week):
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
            
    return status
    """

def open_past_deadline(week, current_time):
    return Game.gql('WHERE week = :1 AND winner = -1 AND deadline < :2',
                    week, current_time.replace(tzinfo=None))

def results_for_week(week):
    winners = set()
    losers = set()
    for g in Game.gql('WHERE week = :1 AND winner != -1', week):
        winners.add(g.winner)
        if g.winner == g.home:
            losers.add(g.visiting)
        else:
            losers.add(g.home)
    return (winners, losers)

def games_complete(week):
    return Game.gql('WHERE week = :1 AND winner = -1', week).count() == 0

def game_for_team(week, team):
    home = Game.gql('WHERE week = :1 AND home = :2', week, team).get()
    if home:
        return home
    visiting = Game.gql('WHERE week = :1 AND visiting = :2', week, team).get()
    if not visiting:
        logging.error('Could not find game for team %d in week %d', team, week)
    return visiting


