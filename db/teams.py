
_rawnames = (
    ('San Francisco', 'SF',  '49ers'),
    ('Chicago',       'CHI', 'Bears'),
    ('Cincinnati',    'CIN', 'Bengals'),
    ('Buffalo',       'BUF', 'Bills'),
    ('Denver',        'DEN', 'Broncos'),
    ('Cleveland',     'CLE', 'Browns'),
    ('Tampa Bay',     'TB',  'Buccaneers'),
    ('Arizona',       'ARI', 'Cardinals'),
    ('San Diego',     'SD',  'Chargers'),
    ('Kansas City',   'KC',  'Chiefs'),
    ('Indianapolis',  'IND', 'Colts'),
    ('Dallas',        'DAL', 'Cowboys'),
    ('Miami',         'MIA', 'Dolphins'),
    ('Philadelphia',  'PHI', 'Eagles'),
    ('Atlanta',       'ATL', 'Falcons'),
    ('New York',      'NYG', 'Giants'),
    ('New York',      'NYJ', 'Jets'),
    ('Jacksonville',  'JAC', 'Jaguars'),
    ('Detroit',       'DET', 'Lions'),
    ('Green Bay',     'GB',  'Packers'),
    ('Carolina',      'CAR', 'Panthers'),
    ('New England',   'NE',  'Patriots'),
    ('Oakland',       'OAK', 'Raiders'),
    ('St. Louis',     'STL', 'Rams'),
    ('Baltimore',     'BAL', 'Ravens'),
    ('Washington',    'WSH', 'Redskins'),
    ('New Orleans',   'NO',  'Saints'),
    ('Seattle',       'SEA', 'Seahawks'),
    ('Pittsburgh',    'PIT', 'Steelers'),
    ('Houston',       'HOU', 'Texans'),
    ('Tennessee',     'TEN', 'Titans'),
    ('Minnesota',     'MIN', 'Vikings'),
)

def names():
    return [s[0] for s in sorted(_rawnames)]

def cityname(team):
    if team == -1:
        return 'No Pick'
    return _rawnames[team][0]

def shortname(team):
    if team == -1:
        return 'No Pick'
    return _rawnames[team][1]

def fullname(team):
    if team == -1:
        return 'No Pick'
    n = _rawnames[team]
    return '%s %s' % (n[0], n[2])

def mascotname(team):
    if team == -1:
        return 'No Pick'
    return _rawnames[team][2]

def large_logo_x(team):
    return (team * 80) % (8 * 80)

def large_logo_y(team):
    return (team / 8) * 80

_ids = {}
for i,name in enumerate(_rawnames):
    _ids[name[0]] = i
    _ids[name[1]] = i
    _ids[name[2]] = i
    _ids['%s %s' % (name[0], name[2])] = i

def id(name):
    return _ids[name]

