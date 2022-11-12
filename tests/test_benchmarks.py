import sys
from datetime import date, datetime, time, timedelta, timezone
from pathlib import Path

import pytest
from dirty_equals import HasRepr

import rtoml

data_toml_path = Path('tests/data.toml')

pytestmark = pytest.mark.skipif(sys.version_info < (3, 8), reason='requires python3.8 or higher')


def test_data():
    data = rtoml.load(data_toml_path)
    assert data == {
        'title': 'TOML Example',
        'owner': {
            'name': 'Tom Preston-Werner',
            'dob': datetime(1979, 5, 27, 7, 32, tzinfo=timezone(timedelta(hours=-8))),
        },
        'database': {'server': '192.168.1.1', 'ports': [8001, 8001, 8002], 'connection_max': 5000, 'enabled': True},
        'servers': {'alpha': {'ip': '10.0.0.1', 'dc': 'eqdc10'}, 'beta': {'ip': '10.0.0.2', 'dc': 'eqdc10'}},
        'clients': {
            'data': [['gamma', 'delta'], [1, 2]],
            'hosts': ['alpha', 'omega'],
            'apple': {'type': 'fruit', 'skin': 'thin', 'color': 'red'},
            'orange': {'type': 'fruit', 'skin': 'thick', 'color': 'orange'},
        },
        'strings': {
            'str0': 'Roses are red\nViolets are blue',
            'str1': 'The quick brown fox jumps over the lazy dog.',
            'str2': 'The quick brown fox jumps over the lazy dog.',
            'str3': 'The quick brown fox jumps over the lazy dog.',
            'str4': 'Here are two quotation marks: "". Simple enough.',
            'str5': 'Here are three quotation marks: """.',
            'str6': 'Here are fifteen quotation marks: """"""""""""""".',
            'winpath': 'C:\\Users\\nodejs\\templates',
            'winpath2': '\\\\ServerX\\admin$\\system32\\',
            'quoted': 'Tom "Dubs" Preston-Werner',
            'regex': '<\\i\\c*\\s*>',
            'regex2': "I [dw]on't need \\d{2} apples",
            'lines': 'The first newline is\ntrimmed in raw strings.\n   All other whitespace\n   is preserved.\n',
            'quot15': 'Here are fifteen quotation marks: """""""""""""""',
            'apos15': "Here are fifteen apostrophes: '''''''''''''''",
        },
        'numbers': {
            'int1': 99,
            'int2': 42,
            'int3': 0,
            'int4': -17,
            'int5': 1000,
            'int6': 5349221,
            'int7': 12345,
            'hex1': 3735928559,
            'hex2': 3735928559,
            'hex3': 3735928559,
            'oct1': 342391,
            'oct2': 493,
            'bin1': 214,
            'flt1': 1.0,
            'flt2': 3.1415,
            'flt3': -0.01,
            'flt4': 5e22,
            'flt5': 1000000.0,
            'flt6': -0.02,
            'flt7': 6.626e-34,
            'sf1': HasRepr('inf'),
            'sf2': HasRepr('inf'),
            'sf3': HasRepr('-inf'),
            'sf4': HasRepr('nan'),
            'sf5': HasRepr('nan'),
            'sf6': HasRepr('nan'),
            'bool1': True,
            'bool2': False,
        },
        'dates': {
            'odt1': datetime(1979, 5, 27, 7, 32, tzinfo=timezone.utc),
            'odt2': datetime(1979, 5, 27, 0, 32, tzinfo=timezone(timedelta(hours=-7))),
            'odt3': datetime(1979, 5, 27, 0, 32, 0, 999999, tzinfo=timezone(timedelta(hours=-7))),
            'ldt1': datetime(1979, 5, 27, 7, 32),
            'ldt2': datetime(1979, 5, 27, 0, 32, 0, 999999),
            'ld1': date(1979, 5, 27),
            'lt1': time(7, 32),
            'lt2': time(0, 32, 0, 999999),
        },
        'lists': {
            'integers': [1, 2, 3],
            'colors': ['red', 'yellow', 'green'],
            'nested_array_of_int': [[1, 2], [3, 4, 5]],
            'nested_mixed_array': [[1, 2], ['a', 'b', 'c']],
            'integers2': [1, 2, 3],
            'integers3': [1, 2],
        },
        'tables': {
            'table-1': {'key1': 'some string', 'key2': 123},
            'table-2': {'key1': 'another string', 'key2': 456},
            'dog': {'tater.man': {'type': {'name': 'pug'}}},
            'x': {'y': {'z': {'w': {}}}},
            'product': {'type': {'name': 'Nail'}},
        },
        'fruit': {
            'apple': {'color': 'red', 'taste': {'sweet': True}},
            'tables': {
                'name': {'first': 'Tom', 'last': 'Preston-Werner'},
                'point': {'x': 1, 'y': 2},
                'animal': {'type': {'name': 'pug'}},
            },
            'variety': [
                {
                    'name': 'plantain',
                    'points': [{'x': 1, 'y': 2, 'z': 3}, {'x': 7, 'y': 8, 'z': 9}, {'x': 2, 'y': 4, 'z': 8}],
                }
            ],
        },
        'products': [{'name': 'Hammer', 'sku': 738594937}, {}, {'name': 'Nail', 'sku': 284758393, 'color': 'gray'}],
        'spoons': [
            {
                'name': 'apple',
                'physical': {'color': 'red', 'shape': 'round'},
                'variety': [{'name': 'red delicious'}, {'name': 'granny smith'}],
            },
            {'name': 'banana'},
        ],
    }


@pytest.mark.benchmark(group='load-data.toml')
def test_loads_data_toml(benchmark):
    data_toml_str = data_toml_path.read_text()
    benchmark(rtoml.loads, data_toml_str)


@pytest.mark.benchmark(group='load-data.toml')
def test_load_data_toml(benchmark):
    benchmark(rtoml.load, data_toml_path)


@pytest.mark.benchmark(group='load-dict')
def test_load_big_dict(benchmark):
    d = {str(i): i for i in range(1000)}
    toml_str = rtoml.dumps(d)
    benchmark(rtoml.loads, toml_str)


@pytest.mark.benchmark(group='dumps-data.toml')
def test_dump_data_toml(benchmark):
    data = rtoml.load(data_toml_path)
    # benchmark(rtoml.loads, data_toml_bytes, name='loads-bytes')
    benchmark(rtoml.dumps, data)


@pytest.mark.benchmark(group='dumps-simple')
def test_dump_simple(benchmark):
    data = {
        'fruit': ['apple', 'orange', 'banana', None, True, False, 123, 123.456, 1e-10, 1e10],
        'tables': {'name': 'Tom', 'point': {'x': 1, 'y': 2}},
        'datetime': datetime(1979, 5, 27, 7, 32, tzinfo=timezone.utc),
        'tuples': [(i + 1, i + 2, i + 3) for i in range(10)],
        'many': [{str(i): i + j for i in range(100)} for j in range(100)],
    }

    # benchmark(rtoml.loads, data_toml_bytes, name='loads-bytes')
    benchmark(rtoml.dumps, data)
