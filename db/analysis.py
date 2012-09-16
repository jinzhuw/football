
import logging

from google.appengine.ext import db

from db import teams, weeks, settings, games

class Analysis(db.Model):
    week = db.IntegerProperty(required=True)
    updated = db.DateTimeProperty(auto_now=True)
    text = db.TextProperty()
    posted = db.BooleanProperty(default=False)

class AnalysisComment(db.Model):
    week = db.IntegerProperty(required=True)
    created = db.DateTimeProperty(auto_now_add=True)
    text = db.TextProperty(required=True)
    user = db.StringProperty(required=True)

class Stats(db.Model):
    week = db.IntegerProperty(required=True)
    wins = db.IntegerProperty(default=0)
    losses = db.IntegerProperty(default=0)
    violations = db.IntegerProperty(default=0)

class TeamStats(db.Model):
    week = db.IntegerProperty(required=True)
    team = db.IntegerProperty(required=True)
    count = db.IntegerProperty(required=True)

def save_team_counts(week, team_counts):
    # wipe out any old numbers
    to_delete = [s for s in TeamStats.gql('WHERE week = :1', week)]
    if to_delete:
        db.delete(to_delete)
    to_put = []
    for team,count in team_counts.iteritems():
        to_put.append(TeamStats(week=week, team=team, count=count))
    db.put(to_put)

def get_team_counts(week):
    picks = {}
    no_pick = 0 
    for s in TeamStats.gql('WHERE week = :1', week):
        if s.team == -1:
            no_pick = s.count
        else:
            picks[teams.fullname(s.team)] = s.count
    return (no_pick, picks)

def save_status_counts(week, wins, losses, violations):
    stats = Stats.gql('WHERE week = :1', week).get() 
    if stats is None:
        stats = Stats(week=week)
    stats.wins = wins
    stats.losses = losses
    stats.violations = violations
    stats.put()
        
