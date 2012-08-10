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
import logging
import wsgiref.handlers

from google.appengine.ext import webapp
from google.appengine.ext import db
from google.appengine.api import memcache

import settings
from db import players, teams, weeks
from view import render, is_admin

class ChooseTeams(webapp.RequestHandler):
    """
    send email - tuesday, 8am
    deadline - saturday midnight
    """

    def get(self):
        handle = self.request.get('handle')
        force = self.request.get('force') == 'true'
        admin = is_admin()
        edit = self.request.get('edit') == 'true'
        week, player = players.decrypt_handle(handle)

        entries = []
        chosen = players.player_picks(player, week)
        for e in player.entries:
            if e.key().id() not in chosen and e.active:
                entries.append(e)

        args = {
            'player': player, 
            'week': week, 
            'teams': teams.names(),
            'entries': sorted(entries, key=lambda e: e.name), 
            'chosen': [(p.entry, teams.longname(p.team)) \
                       for p in sorted(chosen.itervalues(), key=lambda p: p.entry.name)], 
            'expired': not (force and admin or weeks.check_deadline(week)), 
            'edit': edit,
            'handle': handle
        }
        render(self, 'choose', args)

    def post(self):
        handle = self.request.get('handle')
        week, player = players.decrypt_handle(handle)
        if not (is_admin() or weeks.check_deadline(week)):
            logging.info('Deadline passed for %s, week %d', player.name, week)
            self.redirect('/choose?handle=%s' % handle)
            return

        logging.info('player = %s, week = %d', player.name, week)
        for e in player.entries:
            teamname = self.request.get(str(e.key().id()))
            if not teamname:
                continue
            logging.info('Entry %s picked team %s', e.name, teamname)
            players.select_team(e, week, teamname)
    
        self.redirect('/choose?handle=%s' % handle)

def main():
    application = webapp.WSGIApplication([('/choose', ChooseTeams)],
                                         debug=settings.DEBUG)
    wsgiref.handlers.CGIHandler().run(application)


if __name__ == '__main__':
  main()
