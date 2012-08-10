
_rawnames = (
    ('San Fransisco', 'SF'),
    ('Chicago',       'CHI'),
    ('Cincinnati',    'CIN'),
    ('Buffalo',       'BUF'),
    ('Denver',        'DEN'),
    ('Clevland',      'CLE'),
    ('Tampa Bay',     'TB'),
    ('Arizona',       'ARI'),
    ('San Diego',     'SD'),
    ('Kansas City',   'KC'),
    ('Indianapolis',  'IND'),
    ('Dallas',        'DAL'),
    ('Miami',         'MIA'),
    ('Philadelphia',  'PHI'),
    ('Atlanta',       'ATL'),
    ('NY Giants',     'NYG'),
    ('NY Jets',       'NYJ'),
    ('Jacksonville',  'JAC'),
    ('Detroit',       'DET'),
    ('Green Bay',     'GB'),
    ('Carolina',      'CAR'),
    ('New England',   'NE'),
    ('Oakland',       'OAK'),
    ('St. Louis',     'STL'),
    ('Baltimore',     'BAL'),
    ('Washington',    'WSH'),
    ('New Orleans',   'NO'),
    ('Seattle',       'SEA'),
    ('Pittsburgh',    'PIT'),
    ('Houston',       'HOU'),
    ('Tennessee',     'TEN'),
    ('Minnesota',     'MIN'),
)

def names():
    return [s[0] for s in sorted(_rawnames)]

def longname(team):
    if team == -1:
        return 'No Pick'
    return _rawnames[team][0]

def shortname(team):
    if team == -1:
        return 'No Pick'
    return _rawnames[team][1]

_ids = {}
for i,name in enumerate(_rawnames):
    _ids[name[0]] = i
    _ids[name[1]] = i

def id(name):
    return _ids[name]

