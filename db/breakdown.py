
import logging

from google.appengine.ext import db

from db import teams, weeks, settings, games

class Blog(db.Model):
    updated = db.DateTimeProperty(auto_now=True)
    title = db.StringProperty()
    content = db.TextProperty()
    posted = db.BooleanProperty(default=False)

class Comment(db.Model):
    week = db.IntegerProperty(required=True)
    created = db.DateTimeProperty(auto_now_add=True)
    text = db.TextProperty(required=True)
    user = db.StringProperty(required=True)
    user_id = db.IntegerProperty(required=True)

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
    total = 0
    for s in TeamStats.gql('WHERE week = :1', week):
        if s.team == -1:
            no_pick = s.count
        else:
            picks[teams.fullname(s.team)] = s.count
        total += s.count
    return (no_pick, picks, total)

def save_status_counts(week, wins, losses, violations):
    stats = Stats.gql('WHERE week = :1', week).get()
    if not stats:
        stats = Stats(week=week)
    stats.wins = wins
    stats.losses = losses
    stats.violations = violations
    stats.put()

def update_status_counts(week, wins, losses):
    stats = Stats.gql('WHERE week = :1', week).get()
    if not stats:
        stats = Stats(week=week)
    stats.wins += wins
    stats.losses += losses
    stats.put()
    

def get_status_counts(week):
    return Stats.gql('WHERE week = :1', week).get()
        
def get_blog(week):
    return Blog.get_or_insert(str(week))

def save_blog(week, title, content):
    blog = Blog.get_or_insert(str(week))
    blog.title = title
    blog.content = content
    blog.put()
    return blog;

def post_blog(week):
    blog = Blog.get_or_insert(str(week))
    blog.posted = True
    blog.put()

def get_comments(week, count=None, before=None, after=None):
    q = ['WHERE week = %d' % week]
    if before:
        q.append('AND created < %s' % before)
    elif after:
        q.append('AND created > %s' % after)
    q.append('ORDER BY created DESC')
    if count:
        q.append('LIMIT %d' % count)
    return Comment.gql(' '.join(q))

def save_comment(week, user, text):
    c = Comment(week=week, text=text, username=user.name, user_id=user.key().id())
    c.put()
