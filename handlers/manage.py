#!/usr/bin/env python
#
# Copyright 2007 Google Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and 
# limitations under the License.
#

import os
import sys
import logging
import wsgiref.handlers

from google.appengine.ext import webapp
from google.appengine.api import taskqueue
from google.appengine.api import users

import settings
from db import players, weeks, games
from view import render, clear_cache

def secure(method):
    def check_security(self):
        user = users.get_current_user()
        if user:
            logging.info('security check: email = %s', user.email())
        if user and user.email() in settings.ADMINS:
            method(self)
        else:
            self.redirect('/')
    return check_security

class PlayersManager(webapp.RequestHandler):

    @secure
    def get(self):
        ps = players.Player.gql('ORDER BY name')
        args = {'players': ps}

        player_id = self.request.get('id')
        if player_id:
            player = players.Player.get_by_id(int(player_id))
            args['player'] = player
            args['week'] = weeks.current()
            args['handle'] = players.encrypt_handle(weeks.current(), player)
            
        render(self, 'players', args)

class GamesManager(webapp.RequestHandler):

    @secure
    def get(self):
        week = weeks.current()
        incomplete, complete = games.for_week(week)
        args = {
            'complete_games': sorted(complete), 
            'open_games': sorted(incomplete), 
            'week': week
        }
        render(self, 'games', args)

    @secure
    def post(self):
        for a in self.request.arguments():
            if not a.startswith('game.'):
                continue
            games.complete(int(a[5:]), self.request.get(a))
        
        # is the week complete?
        week = weeks.current()
        if games.games_are_complete(week):
            logging.info('completing week %d', week)
            winners = games.winners_for_week(week)
            last_week = {}
            if week > 1:
                last_week = players.all_picks(week - 1)

            last_week_ok = lambda l,p: not l or l.team != p.team or l.status == players.Status.LOSS
            entries = set()
            picks = players.Pick.gql('WHERE week = :1', week)
            for pick in picks:
                entry_id = pick.entry.key().id()
                entries.add(entry_id)
                if pick.team == -1 or not last_week_ok(last_week.get(entry_id), pick):
                    pick.status = players.Status.VIOLATION
                elif pick.team not in winners:
                    pick.status = players.Status.LOSS
                else:
                    pick.status = players.Status.WIN
                pick.put()

                if pick.status != players.Status.WIN:
                    pick.entry.active = False
                    pick.entry.put()
            
            weeks.increment()        
            players.initialize_picks(weeks.current())

            # schedule weekly email with results
            eta = weeks.results(week)
            logging.info('Emailing results at %s', eta.strftime('%c'))
            taskqueue.add(url='/manage/email/team_picker', method='GET', eta=eta)
            
        clear_cache('results')
        self.redirect('/manage/games')

class AddPlayer(webapp.RequestHandler):

    @secure
    def post(self):
        name = self.request.get('player.name') 
        email = self.request.get('player.email')
        id = players.add_player(name, email)

        self.redirect('/manage/players?id=%d' % id)

class AddEntry(webapp.RequestHandler):

    @secure
    def post(self):
        id = self.request.get('player.id')
        name = self.request.get('entry.name') 
        player = players.add_entry(int(id), name)
        clear_cache('results')

        handle = players.encrypt_handle(weeks.current(), player)
        taskqueue.add(url='/manage/email/team_picker?handle=%s' % handle,
                      method='GET')
        
        self.redirect('/manage/players?id=%s' % id)

class RebuyEntry(webapp.RequestHandler):

    @secure
    def get(self):
        id = int(self.request.get('entry.id'))
        entry = players.rebuy_entry(id)
        clear_cache('results')
        
        self.redirect('/manage/players?id=%d' % entry.player.key().id())

class QuickAdd(webapp.RequestHandler):
    def get(self):
        name = self.request.get('player')
        email = self.request.get('email')
        player_id = players.add_player(name, email)        
        
        num = 0
        while True:
            ename = self.request.get('entry%d' % num)            
            if not ename:
                break
            players.add_entry(player_id, ename)
            num += 1
        
class QuickPick(webapp.RequestHandler):
    def get(self):
        team = self.request.get('team')
        entryname = self.request.get('entry') 
        entry = players.Entry.gql('WHERE name = :1', entryname).get()
        if not entry:
            logging.info('Unknown entry %r', entryname)
            self.error(400)
            return
        week = weeks.current()
        players.select_team(entry, week, team)

class InitDb(webapp.RequestHandler):

    @secure
    def get(self):
        weeks.reset()
        games.reset()
        players.reset()

        self.redirect('/manage/players')

class EmailTeamPicker(webapp.RequestHandler):

    def get(self):
        queue = self.request.get('queue')
        if queue:
            taskqueue.add(url='/manage/email/team_picker', method='GET')
            return
        handle = self.request.get('handle')
        if handle:
            week, player = players.decrypt_handle(handle)
            players.email_team_picker(player, week) 
        else:
            week = weeks.current()
            for player in players.Player.all():
                players.email_team_picker(player, week)

class EmailBreakdown(webapp.RequestHandler):

    def get(self):
        close = self.request.get('close')
        week = weeks.current()
        if close == 'true':
            picks = players.all_picks(weeks.current())
            for p in picks.itervalues():
                p.status = players.Status.CLOSED
                if p.team == -1:
                    # no pick
                    p.status = players.Status.VIOLATION
                    p.entry.active = False
                    p.entry.put()
                p.put()
            clear_cache('results')
        players.email_breakdown(week)
            
def main():
    application = webapp.WSGIApplication([('/manage/players', PlayersManager),
                                        ('/manage/games', GamesManager),
                                        #('/manage/quick_add', QuickAdd),
                                        #('/manage/quick_pick', QuickPick),
                                        ('/manage/init', InitDb),
                                        ('/manage/add_player', AddPlayer),
                                        ('/manage/rebuy', RebuyEntry),
                                        ('/manage/email/team_picker', EmailTeamPicker),
                                        ('/manage/email/breakdown', EmailBreakdown),
                                        ('/manage/add_entry', AddEntry)],
                                       debug=settings.DEBUG)
    wsgiref.handlers.CGIHandler().run(application)


if __name__ == '__main__':
    main()
