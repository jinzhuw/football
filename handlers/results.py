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

import settings, util
from db import players, teams
from view import render, cache_hit

class DisplayResults(webapp.RequestHandler):

    def get(self):
        force = self.request.get('force')
        if not force and cache_hit(self, 'results'):
            return
        weeks = 10
        entries_by_week = {}
        eliminated_by_week = {}
        entries = {}
        for pick in players.iterpicks():
            if pick.status == players.Status.OPEN:
                continue
            util.increment(entries_by_week, pick.week)
            team = teams.shortname(pick.team)
            if pick.status == players.Status.LOSS or pick.status == players.Status.VIOLATION:
                util.increment(eliminated_by_week, pick.week)
            e = entries.get(pick.entry.key().id())
            if e is None:
                e = (pick.entry, [])
                entries[pick.entry.key().id()] = e

            # fill in weeks that no pick exists
            last_week = 1 if len(e[1]) == 0 else (e[1][-1][2] + 1)
            while last_week <= pick.week - 1:
                e[1].append(('', 'none', last_week))
                last_week += 1
            
            type = ''
            if pick.status == players.Status.VIOLATION:
                type = 'violation'
            elif pick.status == players.Status.LOSS:
                type = 'loss' 
            e[1].append([team, type, pick.week])

        active = []
        inactive = []
        for entry,picks in entries.itervalues():
            l = inactive
            if entry.active:
                l = active
            l.append((entry.name, picks))
        active = sorted(active)
        inactive = sorted(inactive, key=lambda x: '%d,%s' % (100 - len(x[1]), x[0]))
        args = {
            'active': active, 
            'inactive': inactive,
            'entries_by_week': sorted(entries_by_week.items()),
            'eliminated_by_week': sorted(eliminated_by_week.items()),
        }
        render(self, 'results', args, cache_ttl=604800) 

def main():
    application = webapp.WSGIApplication([('/results', DisplayResults)],
                                         debug=settings.DEBUG)
    wsgiref.handlers.CGIHandler().run(application)


if __name__ == '__main__':
  main()
