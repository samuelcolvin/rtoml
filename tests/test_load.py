from datetime import date, datetime, time, timedelta, timezone
from importlib.machinery import SourceFileLoader
from pathlib import Path

import pytest

import rtoml


@pytest.mark.parametrize(
    'input_toml,output_obj',
    [
        ('foo = "bar"', {'foo': 'bar'}),
        ('ports = [ 8001, 8001, 8002 ]', {'ports': [8001, 8001, 8002]}),
        ('x = 1979-05-27T07:32:00', {'x': datetime(1979, 5, 27, 7, 32)}),
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


def test_load_path(tmp_path):
    p = tmp_path / 'test.toml'
    p.write_text('foo = "bar"')
    assert rtoml.load(p) == {'foo': 'bar'}


def test_load_file(tmp_path):
    p = tmp_path / 'test.toml'
    p.write_text('foo = "bar"')
    with p.open() as f:
        assert rtoml.load(f) == {'foo': 'bar'}


def test_invalid_type():
    with pytest.raises(TypeError, match="invalid toml input, must be str not <class 'bytes'>"):
        rtoml.load(b'foobar')


def test_invalid_toml():
    with pytest.raises(rtoml.TomlParsingError, match='invalid number at line 1 column 5'):
        rtoml.load('x = y')


def test_version():
    assert isinstance(rtoml.VERSION, str)


def test_example():
    module = SourceFileLoader('example', str(Path(__file__).parent / '../example.py')).load_module()
    # check it looks about right
    assert isinstance(module.obj, dict)
    assert module.obj['title'] == 'TOML Example'


# waiting for https://github.com/alexcrichton/toml-rs/issues/357 to be released
@pytest.mark.xfail
def test_mixed_array():
    assert rtoml.loads('x = [1.1, 2, 3.3]') == {'x': [1.1, 2, 3.3]}


# https://github.com/alexcrichton/toml-rs/issues/367
@pytest.mark.xfail
def test_subtable():
    s = """\
[fruit]
apple.color = "red"
apple.taste.sweet = true

[fruit.apple.texture]  # you can add sub-tables
smooth = true
"""
    assert rtoml.loads(s) == ...
