
import json
import lxml.objectify
import lxml.html
import re
import logging
import urllib2
from datetime import datetime, timedelta
from collections import defaultdict

from google.appengine.ext import db

from db import teams, weeks
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
    favorite = db.IntegerProperty(default=-1) 
    spread = db.FloatProperty(default=0.0)

    def tz_date(self):
        d = self.date
        return datetime(d.year, d.month, d.day, d.hour, d.minute, tzinfo=timezone.Pacific)

    def tz_deadline(self):
        d = self.deadline
        return datetime(d.year, d.month, d.day, d.hour, d.minute, tzinfo=timezone.Pacific)

    def complete(self):
        return self.winner != -1 or self.home_score != -1 and self.home_score == self.visiting_score # tie game

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

class TeamRanking(db.Model):
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
    if Game.gql('WHERE week = :1', week).count() == 0:
        load_schedule(week)
        return
 
    games_to_save = []
    for g in Game.gql('WHERE week = :1', week):
        if g.complete():
            g.winner = -1
            g.home_score = -1
            g.visiting_score = -1
            games_to_save.append(g)
    db.put(games_to_save)

def _load_url(url, type):
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
        
    if type == 'xml':
        return lxml.objectify.fromstring(data.read())
    elif type == 'json':
        return json.loads(data.read())
    return data.read() # text

def load_old_scores(week):
    x = _load_url('http://football.myfantasyleague.com/2012/export?TYPE=nflSchedule&W=%d' % week, type='xml')
    scores = {}
    for game in x.matchup:
        visiting_name = teams.shortname(teams.id(game.team[0].get('id')))
        home_name = teams.shortname(teams.id(game.team[1].get('id')))
        visiting_score = int(game.team[0].get('score'))
        home_score = int(game.team[1].get('score'))
        logging.debug('Found score for old game %s vs %s', home_name, visiting_name)
        scores[home_name] = (home_score, visiting_score)

    return scores
    

def load_scores(week):
    j = _load_url('http://www.nfl.com/liveupdate/scorestrip/ss.json', type='json')

    in_progress = 0
    if j['w'] != week:
        scores = load_old_scores(week)
    else:
        scores = {}
        for g in j['gms']:
            if 'F' in g['q']:
                logging.debug('Found score for %s vs %s', g['h'], g['v'])
                scores[g['h']] = (g['hs'], g['vs'])
            elif 'P' != g['q']:
                logging.debug('Game %s v %s in progress, state %s', g['v'], g['h'], g['q'])
                in_progress += 1
            else:
                logging.debug('Skipping game %s vs %s, game state is %s', g['v'], g['h'], g['q'])

    games = Game.gql('WHERE week = :1 AND winner = -1', week)        
    winners = set()
    losers = set()
    for g in games:
        if g.complete():
            continue
        home_team = teams.shortname(g.home)
        s = scores.get(home_team)
        if s:
            logging.info('Setting score for %s (%d) vs %s (%d)',
                         home_team, s[0], teams.shortname(g.visiting), s[1])
            (winner, loser, tie) = update(g, s[0], s[1])
            if tie:
                losers.add(g.home)
                losers.add(g.visiting)
            else:
                winners.add(winner)
                losers.add(loser)

    return ((winners, losers), in_progress)

def _set_rankings(team):
    team_id = teams.shortname(teams.id(team.get('id')))
    rankings = TeamRanking.get_or_insert(team_id)
    rankings.rush_defense_rank = int(team.get('rushDefenseRank')) 
    rankings.rush_offense_rank = int(team.get('rushOffenseRank')) 
    rankings.pass_defense_rank = int(team.get('passDefenseRank')) 
    rankings.pass_offense_rank = int(team.get('passOffenseRank')) 
    rankings.put()

def load_schedule(week, force=False):
    if Game.gql('WHERE week = :1', week).count() > 0 and not force:
        logging.warning('Schedule for week %s is already loaded', week)

    x = _load_url('http://football.myfantasyleague.com/2012/export?TYPE=nflSchedule&W=%d' % week, type='xml')

    if int(x.get('week', 0)) != week:
        logging.warning('Could not load schedule for week %d', week)
        return

    games = []
    for game in x.matchup:
        date = datetime.fromtimestamp(int(game.get('kickoff')))
        date = date.replace(tzinfo=timezone.utc).astimezone(timezone.Pacific).replace(tzinfo=None)
        deadline = datetime(date.year, date.month, date.day, 23, 0) - timedelta(days=1)
        assert game.team[0].get('isHome') == '0'
        visiting = teams.id(game.team[0].get('id'))
        home = teams.id(game.team[1].get('id'))
        g = Game(week=week, home=home, visiting=visiting, date=date, deadline=deadline)
        logging.info('Adding game %s vs %s on %s, deadline %s',
                     teams.shortname(visiting), teams.shortname(home), date, deadline)
        g.put()
        games.append(g)

    return games
        
def update_rankings():
    x = _load_url('http://football.myfantasyleague.com/2012/export?TYPE=nflSchedule', type='xml')

    for game in x.matchup:
        for team in game.team:
            _set_rankings(team)

def team_rankings():
    return TeamRanking.all()

def _extract_team_power_rank(row):
    rank_elem = row.find_class('pr-rank')
    if not rank_elem:
        return (None, None) # extra element at bottom of table for explanation is not a rank
    rank = int(rank_elem[0].text_content())
    team_name = [x[0] for x in row.iterlinks()][1].text_content()
    return (teams.id(team_name), rank)

def update_power_ranks():
    t = _load_url('http://espn.go.com/nfl/powerrankings', type='text')
    x = lxml.html.document_fromstring(t)
    logging.info('Updating power ranks')
    rankings = []
    for row in x.find_class('oddrow'):
        rankings.append(_extract_team_power_rank(row))
    for row in x.find_class('evenrow'):
        rankings.append(_extract_team_power_rank(row))
    changed_rankings = []
    for team_id,rank in rankings:
        if team_id is None: continue
        logging.info('Looking up team %s', team_id)
        ranking = TeamRanking.get_by_key_name(teams.shortname(team_id))
        ranking.power_rank = rank
        changed_rankings.append(ranking)
    db.put(changed_rankings)

def _update_team_standings(standings, team, winner):
    ndx = 0 if team == winner else 1
    standings[team][ndx] += 1

def update_standings():
    standings = defaultdict(lambda: [0, 0])
    for g in Game.all():
        if g.winner == -1: continue
        _update_team_standings(standings, g.home, g.winner)
        _update_team_standings(standings, g.visiting, g.winner)
    changed_rankings = []
    for team_id, (wins, losses) in standings.iteritems():
        ranking = TeamRanking.get_by_key_name(teams.shortname(team_id))
        ranking.wins = wins
        ranking.losses = losses
        changed_rankings.append(ranking)
    db.put(changed_rankings)

def _find_spread(team, data):
    spread_re = team + " <a href=[^>]+>(\-?\d+\.\d)"
    return float(re.search(spread_re, str(data)).group(1))

_team_re = re.compile('\S+ (\S+) @ \S+ (\S+)')
def update_spreads():
    week = weeks.current()
    changed_games = []
    x = _load_url('http://www.sportsbook.ag/rss/live-nfl-football.rss', type='xml')
    for game in x.channel.item:
        team_names = _team_re.search(str(game.title)).group(1, 2)
        visiting_spread = _find_spread(team_names[0], game.description)
        home_spread = _find_spread(team_names[1], game.description)
        g = Game.gql('WHERE week = :1 AND home = :2 AND visiting = :3',
                     week, teams.id(team_names[1]), teams.id(team_names[0])).get()
        if not g:
            continue
        if visiting_spread > 0:
            g.favorite = g.home
        elif home_spread > 0:
            g.favorite = g.visiting
        g.spread = abs(home_spread)
        changed_games.append(g)
        logging.info('%s vs %s, Favorite: %s, spread %f', 
                     teams.shortname(g.visiting), teams.shortname(g.home),
                     teams.shortname(g.favorite), g.spread)
    db.put(changed_games)

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
        game.put() # save scores
        return (None, None, True)
        
    game.winner = winner
    game.put() 
    return (winner, loser, False)

def games_for_week(week):
    games = Game.gql('WHERE week = :1', week)
    if games.count() == 0:
        return load_schedule(week)
    return games

def open_past_deadline(week, current_time):
    return Game.gql('WHERE week = :1 AND winner = -1 AND deadline < :2',
                    week, current_time.replace(tzinfo=None))

def results_for_week(week):
    winners = set()
    losers = set()
    for g in Game.gql('WHERE week = :1', week):
        if not g.complete(): continue
        if g.home_score == g.visiting_score:
            losers.add(g.home)
            losers.add(g.visiting)
            continue

        winners.add(g.winner)
        if g.winner == g.home:
            losers.add(g.visiting)
        else:
            losers.add(g.home)
    return (winners, losers)

def games_complete(week):
    return Game.gql('WHERE week = :1 AND home_score = -1 AND visiting_score = -1', week).count() == 0

def game_for_team(week, team):
    if team == -1:
        return None
    home = Game.gql('WHERE week = :1 AND home = :2', week, team).get()
    if home:
        return home
    visiting = Game.gql('WHERE week = :1 AND visiting = :2', week, team).get()
    if not visiting:
        logging.error('Could not find game for team %d in week %d', team, week)
    return visiting


