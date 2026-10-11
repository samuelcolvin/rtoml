import math
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
    m = r'^invalid date, expected day between 01 and 28 at line 1 column 8$'
    with pytest.raises(rtoml.TomlParsingError, match=m):
        rtoml.load('date = 1979-02-30T07:32:00')


def test_invalid_toml():
    m = r'^string values must be quoted, expected literal string at line 1 column 5$'
    with pytest.raises(rtoml.TomlParsingError, match=m):
        rtoml.load('x = y')


def test_mixed_array():
    assert rtoml.loads('x = [1.1, 2, 3.3]') == {'x': [1.1, 2, 3.3]}
    assert rtoml.loads('x = [1, ["Arrays are not integers."]]') == {'x': [1, ['Arrays are not integers.']]}
    assert rtoml.loads('x = ["hi", 42]') == {'x': ['hi', 42]}


def test_subtable():
    """
    Example from the spec, a [table] header may define a sub-table within a table defined via dotted keys.

    toml-rs 0.5 rejected this, see https://github.com/alexcrichton/toml-rs/issues/367
    """
    s = """\
[fruit]
apple.color = "red"
apple.taste.sweet = true

[fruit.apple.texture]  # you can add sub-tables
smooth = true
"""
    assert rtoml.loads(s) == {
        'fruit': {'apple': {'color': 'red', 'taste': {'sweet': True}, 'texture': {'smooth': True}}}
    }


def test_none_value():
    assert rtoml.loads('x = "null"') == {'x': 'null'}
    assert rtoml.loads('x = "null"', none_value='null') == {'x': None}
    assert rtoml.loads('x = "null"', none_value='') == {'x': 'null'}
    assert rtoml.loads('x = ""', none_value='') == {'x': None}

    # Reproducible with the same none_value repr
    s = {'x': None}
    assert rtoml.dumps(s, none_value='py:None') == 'x = "py:None"\n'
    assert rtoml.loads('x = "py:None"\n', none_value='py:None') == s


@pytest.mark.parametrize(
    'input_toml,output_obj',
    [
        ('a = -1_000\nb = 0xff\nc = 0o17\nd = 0b101\ne = +7', {'a': -1000, 'b': 255, 'c': 15, 'd': 5, 'e': 7}),
        ('a = 1e3\nb = -0.5\nc = 6.626e-34\nd = +1.0', {'a': 1000.0, 'b': -0.5, 'c': 6.626e-34, 'd': 1.0}),
        ('a = inf\nb = -inf\nc = +inf', {'a': math.inf, 'b': -math.inf, 'c': math.inf}),
        ('a = true\nb = false', {'a': True, 'b': False}),
        ('', {}),
        ('# just a comment', {}),
        ('[a]', {'a': {}}),
        ('a = {x = 1, y = {z = 2}}', {'a': {'x': 1, 'y': {'z': 2}}}),
        ('a = {}', {'a': {}}),
        ("a = 'C:\\path'\nb = '''\nmulti\n'''", {'a': 'C:\\path', 'b': 'multi\n'}),
        (r'a = "\t\n\u00e9\U0001F637\\"', {'a': '\t\né😷\\'}),
        ('a = 12:34:56.123456', {'a': time(12, 34, 56, 123456)}),
        ('a = 12:34:56.1', {'a': time(12, 34, 56, 100000)}),
        # nanoseconds are truncated to microseconds
        ('a = 1979-05-27T07:32:00.123456789', {'a': datetime(1979, 5, 27, 7, 32, 0, 123456)}),
        ('a = 1979-05-27T07:32:00.000000001', {'a': datetime(1979, 5, 27, 7, 32)}),
        ('a = []', {'a': []}),
        ('a = [[1, 2], []]', {'a': [[1, 2], []]}),
        # integers beyond 64 bits are accepted up to the i128 range
        ('a = 9223372036854775808\nb = -9223372036854775809', {'a': 2**63, 'b': -(2**63) - 1}),
        ('a = 170141183460469231731687303715884105727', {'a': 2**127 - 1}),
    ],
)
def test_load_more(input_toml, output_obj):
    assert rtoml.loads(input_toml) == output_obj


def test_load_nan():
    loaded = rtoml.loads('a = nan\nb = -nan')
    assert math.isnan(loaded['a'])
    assert math.isnan(loaded['b'])


@pytest.mark.parametrize(
    'input_toml,error',
    [
        ('a = 340282366920938463463374607431768211456', '^integer number overflowed at line 1 column 5$'),
        ('a = 1\na = 2', '^duplicate key at line 2 column 1$'),
        ('[a]\n[a]', '^duplicate key at line 2 column 2$'),
        ('a = {x = 1, x = 2}', '^duplicate key at line 1 column 13$'),
        ('a = "unterminated', '^invalid basic string, expected `"` at line 1 column 18$'),
        ('a = 1979-02-30', '^invalid date, expected day between 01 and 28 at line 1 column 5$'),
        ('a = 25:00:00', '^invalid time, expected hour between 00 and 23 at line 1 column 5$'),
        # errors on later lines report the right position, columns count characters not bytes
        ('a = 1\n\n  b = €', 'at line 3 column 7$'),
        ('a = "€€" \n b = c', 'at line 2 column 6$'),
    ],
)
def test_load_errors(input_toml, error):
    with pytest.raises(rtoml.TomlParsingError, match=error):
        rtoml.loads(input_toml)


def test_load_error_is_value_error():
    with pytest.raises(ValueError):
        rtoml.loads('x = y')


def test_none_value_nested():
    toml = """\
a = ["n", 1, "n"]
[b]
c = "n"
[[d]]
e = "n"
"""
    assert rtoml.loads(toml, none_value='n') == {'a': [None, 1, None], 'b': {'c': None}, 'd': [{'e': None}]}
    # keys are never affected
    assert rtoml.loads('n = 1', none_value='n') == {'n': 1}


def test_tzinfo():
    d: datetime = rtoml.load('date = 1979-05-27T07:32:00-08:00')['date']
    assert repr(d.tzinfo) == 'TzInfo(UTC-08:00)'
    assert str(d.tzinfo) == 'UTC-08:00'
    assert d.tzinfo.dst(d) is None
    assert d.tzinfo.utcoffset(d) == timedelta(hours=-8)
    assert d.utcoffset() == timedelta(hours=-8)

    utc: datetime = rtoml.load('date = 1979-05-27T07:32:00Z')['date']
    assert repr(utc.tzinfo) == 'TzInfo(UTC)'
    assert utc.tzinfo.utcoffset(utc) == timedelta(0)


@pytest.mark.parametrize(
    'input_toml,output_obj',
    [
        ('a = 1979-05-27T07:32', {'a': datetime(1979, 5, 27, 7, 32)}),
        ('a = 07:32', {'a': time(7, 32)}),
        ('a = {\n  x = 1,\n  y = 2,\n}', {'a': {'x': 1, 'y': 2}}),
        (r'a = "\x41\x42"', {'a': 'AB'}),
    ],
)
def test_toml_1_1(input_toml, output_obj):
    """
    Features from TOML 1.1, seconds are optional, inline tables may span lines and have a trailing comma,
    and hex escapes (backslash x) are allowed in strings.
    """
    assert rtoml.loads(input_toml) == output_obj
