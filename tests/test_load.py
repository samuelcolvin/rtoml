from datetime import date, datetime, time, timedelta, timezone

import pytest

import rtoml


@pytest.mark.parametrize(
    'input_toml,output_obj',
    [
        ('"" = "bar"', {'': 'bar'}),
        ('foo = "bar"', {'foo': 'bar'}),
        ('ports = [ 8001, 8001, 8002 ]', {'ports': [8001, 8001, 8002]}),
        ('x = 1979-05-27T07:32:00', {'x': datetime(1979, 5, 27, 7, 32)}),
        ('x = 1979-05-27T07:32:00.123', {'x': datetime(1979, 5, 27, 7, 32, 0, 123000)}),
        ('x = 1979-05-27T07:32:00.123000', {'x': datetime(1979, 5, 27, 7, 32, 0, 123000)}),
        ('x = 1979-05-27T07:32:00.000123', {'x': datetime(1979, 5, 27, 7, 32, 0, 123)}),
        ('x = 1979-05-27T07:32:00Z', {'x': datetime(1979, 5, 27, 7, 32, tzinfo=timezone.utc)}),
        ('x = 1979-05-27T07:32:00-08:00', {'x': datetime(1979, 5, 27, 7, 32, tzinfo=timezone(timedelta(hours=-8)))}),
        ('x = 1979-05-27T07:32:00+08:00', {'x': datetime(1979, 5, 27, 7, 32, tzinfo=timezone(timedelta(hours=8)))}),
        (
            'x = 1979-05-27T07:32:00+08:15',
            {'x': datetime(1979, 5, 27, 7, 32, tzinfo=timezone(timedelta(hours=8, minutes=15)))},
        ),
        (
            'x = 1979-05-27T00:32:00.123-07:00',
            {'x': datetime(1979, 5, 27, 0, 32, 0, 123000, tzinfo=timezone(timedelta(hours=-7)))},
        ),
        ('x = 1979-05-27 07:32:00', {'x': datetime(1979, 5, 27, 7, 32)}),
        ('x = 1979-05-27T00:32:00.999999', {'x': datetime(1979, 5, 27, 0, 32, 0, 999999)}),
        ('x = 1987-01-28', {'x': date(1987, 1, 28)}),
        ('x = 12:34:56', {'x': time(12, 34, 56)}),
        ('foo.bar = "thing"', {'foo': {'bar': 'thing'}}),
        (
            '''
foo.bar = """
thing"""
''',
            {'foo': {'bar': 'thing'}},
        ),
        (
            '''
foo.bar = """
thing
"""
''',
            {'foo': {'bar': 'thing\n'}},
        ),
        (
            '''
foo.bar = """
thing

more"""
''',
            {'foo': {'bar': 'thing\n\nmore'}},
        ),
        (
            """
# This is a TOML document. (from https://github.com/toml-lang/toml)

title = "TOML Example"

[owner]
name = "Tom Preston-Werner"
dob = 1979-05-27T07:32:00-08:00 # First class dates

[database]
server = "192.168.1.1"
ports = [ 8001, 8001, 8002 ]
connection_max = 5000
enabled = true

[servers]

  # Indentation (tabs and/or spaces) is allowed but not required
  [servers.alpha]
  ip = "10.0.0.1"
  dc = "eqdc10"

  [servers.beta]
  ip = "10.0.0.2"
  dc = "eqdc10"

[clients]
data = [ ["gamma", "delta"], [1, 2] ]

# Line breaks are OK when inside arrays
hosts = [
  "alpha",
  "omega"
]
""",
            {
                'clients': {'data': [['gamma', 'delta'], [1, 2]], 'hosts': ['alpha', 'omega']},
                'database': {
                    'connection_max': 5000,
                    'enabled': True,
                    'ports': [8001, 8001, 8002],
                    'server': '192.168.1.1',
                },
                'owner': {
                    'dob': datetime(1979, 5, 27, 7, 32, tzinfo=timezone(timedelta(hours=-8))),
                    'name': 'Tom Preston-Werner',
                },
                'servers': {'alpha': {'dc': 'eqdc10', 'ip': '10.0.0.1'}, 'beta': {'dc': 'eqdc10', 'ip': '10.0.0.2'}},
                'title': 'TOML Example',
            },
        ),
        (
            """
[[fruit]]
  name = "apple"

  [fruit.physical]  # subtable
    color = "red"
    shape = "round"

  [[fruit.variety]]  # nested array of tables
    name = "red delicious"

  [[fruit.variety]]
    name = "granny smith"

[[fruit]]
  name = "banana"

  [[fruit.variety]]
    name = "plantain"
""",
            {
                'fruit': [
                    {
                        'name': 'apple',
                        'physical': {'color': 'red', 'shape': 'round'},
                        'variety': [{'name': 'red delicious'}, {'name': 'granny smith'}],
                    },
                    {'name': 'banana', 'variety': [{'name': 'plantain'}]},
                ]
            },
        ),
        ("""[ j . "ʞ" . 'l' ]""", {'j': {'ʞ': {'l': {}}}}),
    ],
)
def test_load(input_toml, output_obj):
    assert rtoml.load(input_toml) == output_obj


def test_load_str():
    assert rtoml.load('foo = "bar"') == {'foo': 'bar'}


@pytest.mark.parametrize(
    'input_toml,output_obj',
    [
        ('foo = "bar"', {'foo': 'bar'}),
        ('emoji = "😷"', {'emoji': '😷'}),
        ('polish = "Witaj świecie"', {'polish': 'Witaj świecie'}),
    ],
)
def test_load_path(tmp_path, input_toml, output_obj):
    p = tmp_path / 'test.toml'
    p.write_text(input_toml, encoding='UTF-8')
    assert rtoml.load(p) == output_obj


def test_load_file(tmp_path):
    p = tmp_path / 'test.toml'
    p.write_text('foo = "bar"')
    with p.open() as f:
        assert rtoml.load(f) == {'foo': 'bar'}


def test_invalid_type():
    with pytest.raises(TypeError, match="invalid toml input, must be str not <class 'bytes'>"):
        rtoml.load(b'foobar')


def test_datetime_tz_neg():
    d: datetime = rtoml.load('date = 1979-05-27T07:32:00.999999-08:00')['date']
    assert d == datetime(1979, 5, 27, 7, 32, 0, 999999, tzinfo=timezone(timedelta(seconds=-28800)))
    assert d.tzinfo.tzname(datetime.now()) == 'UTC-08:00'


def test_datetime_tz_pos():
    d: datetime = rtoml.load('date = 1979-05-27T07:32:00+05:15')['date']
    assert d == datetime(1979, 5, 27, 7, 32, tzinfo=timezone(timedelta(seconds=18900)))
    assert d.tzinfo.tzname(datetime.now()) == 'UTC+05:15'


def test_datetime_tz_utc():
    d: datetime = rtoml.load('date = 1979-05-27T07:32:00Z')['date']
    assert d == datetime(1979, 5, 27, 7, 32, tzinfo=timezone.utc)
    assert d.tzinfo.tzname(datetime.now()) == 'UTC'


def test_datetime_invalid():
    with pytest.raises(rtoml.TomlParsingError, match='day is out of range for month'):
        rtoml.load('date = 1979-02-30T07:32:00')


def test_invalid_toml():
    m = r'^invalid TOML value, did you mean to use a quoted string\? at line 1 column 5$'
    with pytest.raises(rtoml.TomlParsingError, match=m):
        rtoml.load('x = y')


def test_mixed_array():
    assert rtoml.loads('x = [1.1, 2, 3.3]') == {'x': [1.1, 2, 3.3]}
    assert rtoml.loads('x = [1, ["Arrays are not integers."]]') == {'x': [1, ['Arrays are not integers.']]}
    assert rtoml.loads('x = ["hi", 42]') == {'x': ['hi', 42]}


def test_subtable():
    """
    This is slightly incorrect, but matches normal TOML parsing.

    See https://github.com/alexcrichton/toml-rs/issues/367
    """
    s = """\
[fruit]
apple.color = "red"
apple.taste.sweet = true

[fruit.apple.texture]  # you can add sub-tables
smooth = true
"""
    with pytest.raises(rtoml.TomlParsingError, match='duplicate key: `apple` for key `fruit` at line 5 column 1'):
        rtoml.loads(s)


def test_none_value():
    assert rtoml.loads('x = "null"') == {'x': 'null'}
    assert rtoml.loads('x = "null"', none_value='null') == {'x': None}
    assert rtoml.loads('x = "null"', none_value='') == {'x': 'null'}
    assert rtoml.loads('x = ""', none_value='') == {'x': None}

    # Reproducible with the same none_value repr
    s = {'x': None}
    assert rtoml.dumps(s, none_value='py:None') == 'x = "py:None"\n'
    assert rtoml.loads('x = "py:None"\n', none_value='py:None') == s
