#!/usr/bin/python

import json
import xlwt

normal = xlwt.easyxf('font: name Times New Roman; align: horiz center')
loss = xlwt.easyxf('font: name Times New Roman; pattern: fore_color red, pattern solid; align: horiz center')
violation = xlwt.easyxf('font: name Times New Roman; pattern: fore_color brown, pattern solid; align: horiz center')
buyback = xlwt.easyxf('font: name Times New Roman; pattern: fore_color green, pattern solid; align: horiz center')

wb = xlwt.Workbook()
ws = wb.add_sheet('2011 NFL Suicide Pool')

j = json.load(open('/Users/rjernst/Downloads/results.json', 'r'))
def compare(x, y):
    lx = len(x[1])
    ly = len(y[1])
    if lx == ly:
        return cmp(x[0], y[0])
    return ly - lx

for (i, (player, picks)) in enumerate(sorted(j.iteritems(), cmp=compare)):
    ws.write(i, 0, player, normal)
    for j, p in enumerate(picks):
        t = p
        s = normal
        if isinstance(p, dict):
            t = p['team']
            s = loss
            if p['type'] == 'rule_violation':
                s = violation
            elif p['type'] == 'buyback':
                s = buyback
        ws.write(i, j + 1, t, s)
    
wb.save('nflpool2011.xls')
