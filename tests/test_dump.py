import math
from collections import OrderedDict
from datetime import date, datetime, time, timedelta, timezone, tzinfo
from zoneinfo import ZoneInfo

import pytest

import rtoml


@pytest.mark.parametrize(
    'input_obj,output_toml',
    [
        ({'text': '\nfoo\nbar\n'}, 'text = """\n\nfoo\nbar\n"""\n'),
        ({'foo': 'bar'}, 'foo = "bar"\n'),
        (None, '"!NONE"'),
        ([1, 2, 3], '[1, 2, 3]'),
        ([1, 2, None], '[1, 2, "!NONE"]'),
        (datetime(1979, 5, 27, 7, 32), '1979-05-27T07:32:00'),
        (datetime(1979, 5, 27, 7, 32, tzinfo=timezone.utc), '1979-05-27T07:32:00Z'),
        (date(2022, 12, 31), '2022-12-31'),
        (time(12, 00, 59, 23456), '12:00:59.023456'),
        ({'x': datetime(1979, 5, 27, 7, 32)}, 'x = 1979-05-27T07:32:00\n'),
        # order changed to avoid https://github.com/alexcrichton/toml-rs/issues/142
        ({'x': {'a': 1}, 'y': 4}, 'y = 4\n\n[x]\na = 1\n'),
        ({'x': 1, 'y': None}, 'x = 1\ny = "!NONE"\n'),
        ((1, 2, 3), '[1, 2, 3]'),
        ((1, 2, None), '[1, 2, "!NONE"]'),
        ({'emoji': '😷'}, 'emoji = "😷"\n'),
        ({'bytes': b'123'}, 'bytes = [49, 50, 51]\n'),  # TODO: should this be a string of "123"
        ({'polish': 'Witaj świecie'}, 'polish = "Witaj świecie"\n'),
    ],
)
def test_dumps(input_obj, output_toml):
    assert rtoml.dumps(input_obj, none_value='!NONE') == output_toml


@pytest.mark.parametrize(
    'input_obj,output_toml',
    [
        ([1, 2, None], '[1, 2]'),
        ((1, 2, None), '[1, 2]'),
        # TOML has no null, so a top-level None can only become a string
        (None, '"null"'),
    ],
)
def test_dumps_no_none(input_obj, output_toml):
    assert rtoml.dumps(input_obj, none_value=None) == output_toml


@pytest.mark.parametrize(
    'input_obj,output_toml',
    [
        ({'text': '\nfoo\nbar\n'}, 'text = """\n\nfoo\nbar\n"""\n'),
        ({'foo': 'bar'}, 'foo = "bar"\n'),
        ({'a': [1, 2, 3]}, 'a = [\n    1,\n    2,\n    3,\n]\n'),
        # a bare top-level value is not a TOML document, so pretty has no effect
        ([1, 2, 3], '[1, 2, 3]'),
        ((1, 2, 3), '[1, 2, 3]'),
    ],
)
def test_dumps_pretty(input_obj, output_toml):
    assert rtoml.dumps(input_obj, pretty=True) == output_toml


@pytest.mark.parametrize(
    'input_obj,output_toml,size',
    [
        ({'foo': 'bar'}, 'foo = "bar"\n', 12),
        ({'emoji': '😷'}, 'emoji = "😷"\n', 12),
        ({'polish': 'Witaj świecie'}, 'polish = "Witaj świecie"\n', 25),
    ],
)
def test_dump_path(tmp_path, input_obj, output_toml, size):
    p = tmp_path / 'test.toml'
    assert rtoml.dump(input_obj, p) == size
    assert p.read_text(encoding='UTF-8') == output_toml


def test_dump_file(tmp_path):
    p = tmp_path / 'test.toml'
    with p.open('w') as f:
        assert rtoml.dump({'foo': 'bar'}, f) == 12
    assert p.read_text() == 'foo = "bar"\n'


def test_varied_list():
    assert rtoml.dumps({'test': [1, '2']}) == 'test = [1, "2"]\n'


@pytest.mark.parametrize(
    'input_obj, none_value, output_toml',
    [
        ({'test': None}, 'null', 'test = "null"\n'),
        ({'test': None}, 'foo', 'test = "foo"\n'),
        ({'test': None}, None, ''),
        ({None: 'test'}, 'null', 'null = "test"\n'),
        ({None: 'test'}, 'foo', 'foo = "test"\n'),
        ({None: 'test'}, None, ''),
        ({'test': [1, None, 2]}, 'null', 'test = [1, "null", 2]\n'),
        ({'test': [1, None, 2]}, 'foo', 'test = [1, "foo", 2]\n'),
        ({'test': [1, None, 2]}, None, 'test = [1, 2]\n'),
        (
            {'test': {'x': [{'y': [1, None, 2]}], 'z': None}},
            'null',
            '[test]\nz = "null"\n\n[[test.x]]\ny = [1, "null", 2]\n',
        ),
        (
            {'test': {'x': [{'y': [1, None, 2]}], 'z': None}},
            'foo',
            '[test]\nz = "foo"\n\n[[test.x]]\ny = [1, "foo", 2]\n',
        ),
        ({'test': {'x': [{'y': [1, None, 2]}], 'z': None}}, None, '[[test.x]]\ny = [1, 2]\n'),
    ],
)
def test_none_value(input_obj, none_value, output_toml):
    assert rtoml.dumps(input_obj, none_value=none_value) == output_toml


@pytest.mark.parametrize(
    'input_obj,output_toml',
    [
        ({'a': True, 'b': False}, 'a = true\nb = false\n'),
        ({'a': 1.5}, 'a = 1.5\n'),
        ({'a': -3}, 'a = -3\n'),
        ({'a': 0}, 'a = 0\n'),
        ({'a': math.inf, 'b': -math.inf, 'c': math.nan}, 'a = inf\nb = -inf\nc = nan\n'),
        ({'a': bytearray(b'hi')}, 'a = [104, 105]\n'),
        ({'a': {}, 'b': []}, 'b = []\n\n[a]\n'),
        ({'a b': 1, '': 2, 'ü': 3, 'a.b': 4}, '"a b" = 1\n"" = 2\n"ü" = 3\n"a.b" = 4\n'),
        # strings containing double quotes but no single quotes are written as literal strings
        ({'a': 'he said "hi"\t\\'}, 'a = \'he said "hi"\t\\\'\n'),
        ({'a': "it's"}, 'a = "it\'s"\n'),
        ({'a': [{'x': 1}, {'x': 2}]}, '[[a]]\nx = 1\n\n[[a]]\nx = 2\n'),
        ({'a': {'b': {'c': 1}}}, '[a.b]\nc = 1\n'),
        (
            {'a': datetime(2020, 1, 1, tzinfo=timezone(timedelta(hours=5, minutes=30)))},
            'a = 2020-01-01T00:00:00+05:30\n',
        ),
        ({'a': datetime(2020, 1, 1, 0, 0, 0, 5)}, 'a = 2020-01-01T00:00:00.000005\n'),
        (1.5, '1.5'),
        (True, 'true'),
        ('foo', '"foo"'),
    ],
)
def test_dumps_more(input_obj, output_toml):
    assert rtoml.dumps(input_obj) == output_toml


def test_dumps_bool_key():
    assert rtoml.dumps({True: 1, False: 2}) == 'true = 1\nfalse = 2\n'


@pytest.mark.parametrize(
    'input_obj,output_toml',
    [
        ({'a': None, 'b': [None, 1]}, 'a = "N"\nb = [\n    "N",\n    1,\n]\n'),
        ({'a': {'b': {'c': 1}}, 'l': [{'x': 1}]}, '[[l]]\nx = 1\n\n[a.b]\nc = 1\n'),
        (1, '1'),
    ],
)
def test_dumps_pretty_more(input_obj, output_toml):
    assert rtoml.dumps(input_obj, pretty=True, none_value='N') == output_toml


@pytest.mark.parametrize(
    'input_obj,error',
    [
        ({1: 'x'}, r'1 \(int\) is not serializable as a TOML key'),
        ({1.5: 'x'}, r'1\.5 \(float\) is not serializable as a TOML key'),
        ({'a': {1, 2}}, r'\{1, 2\} \(set\) is not serializable to TOML'),
        ({'a': object()}, r'<object object at 0x[0-9a-f]+> \(object\) is not serializable to TOML'),
        ({'a': 2**127}, '^OverflowError: '),
    ],
)
def test_dumps_errors(input_obj, error):
    with pytest.raises(rtoml.TomlSerializationError, match=error):
        rtoml.dumps(input_obj)


def test_dumps_error_is_value_error():
    with pytest.raises(ValueError):
        rtoml.dumps({'a': object()})


class StrSubclass(str):
    pass


@pytest.mark.parametrize(
    'input_obj,error',
    [
        ({'a': OrderedDict(x=1)}, r'\(OrderedDict\) is not serializable to TOML'),
        ({'a': StrSubclass('v')}, r"'v' \(StrSubclass\) is not serializable to TOML"),
    ],
)
def test_dumps_subclasses_not_supported(input_obj, error):
    """
    Types are matched by exact type pointer for speed, so subclasses of supported types are rejected.
    """
    with pytest.raises(rtoml.TomlSerializationError, match=error):
        rtoml.dumps(input_obj)


def test_dumps_mixed_table_scalar_array():
    output = rtoml.dumps({'a': [{'x': 1}, 2]})
    assert output == 'a = [{ x = 1 }, 2]\n'
    assert rtoml.loads(output) == {'a': [{'x': 1}, 2]}


def test_dumps_big_int():
    assert rtoml.dumps({'a': 2**63, 'b': -(2**63) - 1, 'c': 2**127 - 1}) == (
        'a = 9223372036854775808\nb = -9223372036854775809\nc = 170141183460469231731687303715884105727\n'
    )


class NoOffset(tzinfo):
    """A tzinfo whose utcoffset is None, Python treats such datetimes as naive."""

    def utcoffset(self, dt):
        return None

    def tzname(self, dt):
        return 'no-offset'

    def dst(self, dt):
        return None


@pytest.mark.parametrize(
    'value,output_toml',
    [
        (datetime(2020, 7, 1, 12, tzinfo=ZoneInfo('Europe/London')), 'a = 2020-07-01T12:00:00+01:00\n'),
        (datetime(2020, 1, 1, 12, tzinfo=ZoneInfo('Europe/London')), 'a = 2020-01-01T12:00:00Z\n'),
        (datetime(2020, 1, 1, 12, tzinfo=ZoneInfo('Asia/Kolkata')), 'a = 2020-01-01T12:00:00+05:30\n'),
        (datetime(2020, 1, 1, 12, tzinfo=timezone(timedelta(minutes=-30))), 'a = 2020-01-01T12:00:00-00:30\n'),
        (datetime(2020, 1, 1, 12, tzinfo=timezone(timedelta(hours=23, minutes=59))), 'a = 2020-01-01T12:00:00+23:59\n'),
        (
            datetime(2020, 1, 1, 12, tzinfo=timezone(-timedelta(hours=23, minutes=59))),
            'a = 2020-01-01T12:00:00-23:59\n',
        ),
        (datetime(2020, 1, 1, 12, tzinfo=NoOffset()), 'a = 2020-01-01T12:00:00\n'),
        (datetime(1, 1, 1), 'a = 0001-01-01T00:00:00\n'),
        (datetime(9999, 12, 31, 23, 59, 59, 999999), 'a = 9999-12-31T23:59:59.999999\n'),
        (datetime(2020, 1, 1, 12, 0, 0, 100000), 'a = 2020-01-01T12:00:00.1\n'),
        # TOML has no time with an offset, so the tzinfo is dropped
        (time(12, 30, tzinfo=timezone.utc), 'a = 12:30:00\n'),
        (time(12, 30, 0, 7), 'a = 12:30:00.000007\n'),
        (date(1, 1, 1), 'a = 0001-01-01\n'),
    ],
)
def test_dumps_datetimes(value, output_toml):
    assert rtoml.dumps({'a': value}) == output_toml


def test_dumps_rtoml_tzinfo():
    """datetimes loaded by rtoml carry its own TzInfo, which has a fast path when dumping."""
    loaded = rtoml.loads('a = 2020-01-01T12:00:00-08:00\nb = 2020-01-01T12:00:00Z')
    assert type(loaded['a'].tzinfo).__name__ == 'TzInfo'
    assert rtoml.dumps(loaded) == 'a = 2020-01-01T12:00:00-08:00\nb = 2020-01-01T12:00:00Z\n'


def test_dumps_sub_minute_offset():
    dt = datetime(2020, 1, 1, tzinfo=timezone(timedelta(seconds=30)))
    with pytest.raises(
        rtoml.TomlSerializationError, match='TOML offsets must be a whole number of minutes, got 0:00:30'
    ):
        rtoml.dumps({'a': dt})


class BadOffset(tzinfo):
    def utcoffset(self, dt):
        return timedelta(hours=24)


def test_dumps_out_of_range_offset():
    """Python itself rejects offsets of 24 hours or more, make sure that check isn't bypassed."""
    with pytest.raises(rtoml.TomlSerializationError, match='ValueError: offset must be a timedelta strictly between'):
        rtoml.dumps({'a': datetime(2020, 1, 1, tzinfo=BadOffset())})


@pytest.mark.parametrize(
    'input_obj,none_value,pretty,output_toml',
    [
        (
            {'a': 1, 't': {'b': 2, 'u': {'c': 3, 'v': {'d': 4, 'w': {'e': 5}}}}, 'z': 26},
            None,
            False,
            'a = 1\nz = 26\n\n[t]\nb = 2\n\n[t.u]\nc = 3\n\n[t.u.v]\nd = 4\n\n[t.u.v.w]\ne = 5\n',
        ),
        (
            {'a': 1, 't': {'b': 2, 'u': {'c': 3, 'v': {'d': 4, 'w': {'e': 5}}}}, 'z': 26},
            None,
            True,
            'a = 1\nz = 26\n\n[t]\nb = 2\n\n[t.u]\nc = 3\n\n[t.u.v]\nd = 4\n\n[t.u.v.w]\ne = 5\n',
        ),
        ({'a': {'b': {'c': {'d': 1}}}}, None, False, '[a.b.c]\nd = 1\n'),
        ({'a': {'b': {'c': {'d': 1}}}}, None, True, '[a.b.c]\nd = 1\n'),
        (
            {'a': {'b': {'c': 1}, 'd': {'e': 2}}, 'f': {'g': {}}, 'h': {}},
            None,
            False,
            '[a.b]\nc = 1\n\n[a.d]\ne = 2\n\n[f.g]\n\n[h]\n',
        ),
        (
            {'a': {'b': {'c': 1}, 'd': {'e': 2}}, 'f': {'g': {}}, 'h': {}},
            None,
            True,
            '[a.b]\nc = 1\n\n[a.d]\ne = 2\n\n[f.g]\n\n[h]\n',
        ),
        ({'a': {}, 'b': {'c': {}}, 'd': {'e': {}, 'f': 1}}, None, False, '[a]\n\n[b.c]\n\n[d]\nf = 1\n\n[d.e]\n'),
        ({'a': {}, 'b': {'c': {}}, 'd': {'e': {}, 'f': 1}}, None, True, '[a]\n\n[b.c]\n\n[d]\nf = 1\n\n[d.e]\n'),
        ({'a': {'b': [{'x': 1}, {'x': 2}]}}, None, False, '[[a.b]]\nx = 1\n\n[[a.b]]\nx = 2\n'),
        ({'a': {'b': [{'x': 1}, {'x': 2}]}}, None, True, '[[a.b]]\nx = 1\n\n[[a.b]]\nx = 2\n'),
        (
            {'t': {'x': 1}, 'v': 1, 'u': {'y': 2}, 'w': 2, 'arr': [1], 'aot': [{'z': 1}]},
            None,
            False,
            'v = 1\nw = 2\narr = [1]\n\n[[aot]]\nz = 1\n\n[t]\nx = 1\n\n[u]\ny = 2\n',
        ),
        (
            {'t': {'x': 1}, 'v': 1, 'u': {'y': 2}, 'w': 2, 'arr': [1], 'aot': [{'z': 1}]},
            None,
            True,
            'v = 1\nw = 2\narr = [1]\n\n[[aot]]\nz = 1\n\n[t]\nx = 1\n\n[u]\ny = 2\n',
        ),
        (
            {'a': [{'x': 1}, {'x': 2, 'y': {'z': 3}}, {}], 'b': 1},
            None,
            False,
            'b = 1\n\n[[a]]\nx = 1\n\n[[a]]\nx = 2\n\n[a.y]\nz = 3\n\n[[a]]\n',
        ),
        (
            {'a': [{'x': 1}, {'x': 2, 'y': {'z': 3}}, {}], 'b': 1},
            None,
            True,
            'b = 1\n\n[[a]]\nx = 1\n\n[[a]]\nx = 2\n\n[a.y]\nz = 3\n\n[[a]]\n',
        ),
        ({'a': [{'b': [{'c': [{'d': 1}]}]}]}, None, False, '[[a]]\n\n[[a.b]]\n\n[[a.b.c]]\nd = 1\n'),
        ({'a': [{'b': [{'c': [{'d': 1}]}]}]}, None, True, '[[a]]\n\n[[a.b]]\n\n[[a.b.c]]\nd = 1\n'),
        ({'a': [{}, {}]}, None, False, '[[a]]\n\n[[a]]\n'),
        ({'a': [{}, {}]}, None, True, '[[a]]\n\n[[a]]\n'),
        ({'a': [{'x': [1, 2], 'y': [{'z': 1}]}]}, None, False, '[[a]]\nx = [1, 2]\n\n[[a.y]]\nz = 1\n'),
        ({'a': [{'x': [1, 2], 'y': [{'z': 1}]}]}, None, True, '[[a]]\nx = [\n    1,\n    2,\n]\n\n[[a.y]]\nz = 1\n'),
        (
            {'a': [{'x': 1}, 2], 'b': [[{'x': 1}]], 'c': [{'x': {'y': {'z': [1, {'w': 2}]}}}, 'str'], 'd': [{}, 1]},
            None,
            False,
            'a = [{ x = 1 }, 2]\nb = [[{ x = 1 }]]\nc = [{ x = { y = { z = [1, { w = 2 }] } } }, "str"]\nd = [{}, 1]\n',
        ),
        (
            {'a': [{'x': 1}, 2], 'b': [[{'x': 1}]], 'c': [{'x': {'y': {'z': [1, {'w': 2}]}}}, 'str'], 'd': [{}, 1]},
            None,
            True,
            'a = [\n    { x = 1 },\n    2,\n]\nb = [[{ x = 1 }]]\nc = [\n    { x = { y = { z = [\n    1,\n    { w = 2 },\n] } } },\n    "str",\n]\nd = [\n    {},\n    1,\n]\n',
        ),
        (
            {'a': [[{'x': 1, 'y': {'z': 2}}]], 'b': [{'e': {}}, 'x'], 'c': [{'k': [1, [2, {'m': 3}]]}, None]},
            None,
            False,
            'a = [[{ x = 1, y = { z = 2 } }]]\nb = [{ e = {} }, "x"]\n\n[[c]]\nk = [1, [2, { m = 3 }]]\n',
        ),
        (
            {'a': [[{'x': 1, 'y': {'z': 2}}]], 'b': [{'e': {}}, 'x'], 'c': [{'k': [1, [2, {'m': 3}]]}, None]},
            None,
            True,
            'a = [[{ x = 1, y = { z = 2 } }]]\nb = [\n    { e = {} },\n    "x",\n]\n\n[[c]]\nk = [\n    1,\n    [\n    2,\n    { m = 3 },\n],\n]\n',
        ),
        (
            {'a': [[{'x': 1, 'y': {'z': 2}}]], 'b': [{'e': {}}, 'x'], 'c': [{'k': [1, [2, {'m': 3}]]}, None]},
            'null',
            False,
            'a = [[{ x = 1, y = { z = 2 } }]]\nb = [{ e = {} }, "x"]\nc = [{ k = [1, [2, { m = 3 }]] }, "null"]\n',
        ),
        (
            {'a': [[{'x': 1, 'y': {'z': 2}}]], 'b': [{'e': {}}, 'x'], 'c': [{'k': [1, [2, {'m': 3}]]}, None]},
            'null',
            True,
            'a = [[{ x = 1, y = { z = 2 } }]]\nb = [\n    { e = {} },\n    "x",\n]\nc = [\n    { k = [\n    1,\n    [\n    2,\n    { m = 3 },\n],\n] },\n    "null",\n]\n',
        ),
        (
            {'a': [{'x': None}, {'y': 1}], 'b': [None, {'x': 1}], 'c': [{'x': 1}, None]},
            None,
            False,
            '[[a]]\n\n[[a]]\ny = 1\n\n[[b]]\nx = 1\n\n[[c]]\nx = 1\n',
        ),
        (
            {'a': [{'x': None}, {'y': 1}], 'b': [None, {'x': 1}], 'c': [{'x': 1}, None]},
            None,
            True,
            '[[a]]\n\n[[a]]\ny = 1\n\n[[b]]\nx = 1\n\n[[c]]\nx = 1\n',
        ),
        (
            {'a': [{'x': None}, {'y': 1}], 'b': [None, {'x': 1}], 'c': [{'x': 1}, None]},
            'null',
            False,
            'b = ["null", { x = 1 }]\nc = [{ x = 1 }, "null"]\n\n[[a]]\nx = "null"\n\n[[a]]\ny = 1\n',
        ),
        (
            {'a': [{'x': None}, {'y': 1}], 'b': [None, {'x': 1}], 'c': [{'x': 1}, None]},
            'null',
            True,
            'b = [\n    "null",\n    { x = 1 },\n]\nc = [\n    { x = 1 },\n    "null",\n]\n\n[[a]]\nx = "null"\n\n[[a]]\ny = 1\n',
        ),
        (
            {'z': 1, 'y': {'x': 1}, 'w': [1], 'v': 2, 'u': [{'t': 1}], 's': {'r': 2}, 'q': 3},
            None,
            False,
            'z = 1\nv = 2\nq = 3\nw = [1]\n\n[[u]]\nt = 1\n\n[y]\nx = 1\n\n[s]\nr = 2\n',
        ),
        (
            {'z': 1, 'y': {'x': 1}, 'w': [1], 'v': 2, 'u': [{'t': 1}], 's': {'r': 2}, 'q': 3},
            None,
            True,
            'z = 1\nv = 2\nq = 3\nw = [1]\n\n[[u]]\nt = 1\n\n[y]\nx = 1\n\n[s]\nr = 2\n',
        ),
        ([[1, 2], {'a': 1}, 'x', None], None, False, '[[1, 2], { a = 1 }, "x"]'),
        ([[1, 2], {'a': 1}, 'x', None], None, True, '[[1, 2], { a = 1 }, "x"]'),
        ([[1, 2], {'a': 1}, 'x', None], 'null', False, '[[1, 2], { a = 1 }, "x", "null"]'),
        ([[1, 2], {'a': 1}, 'x', None], 'null', True, '[[1, 2], { a = 1 }, "x", "null"]'),
        ([{'a': 1}, {'b': 2}], None, False, '[{ a = 1 }, { b = 2 }]'),
        ([{'a': 1}, {'b': 2}], None, True, '[{ a = 1 }, { b = 2 }]'),
    ],
)
def test_dumps_structures(input_obj, none_value, pretty, output_toml):
    """
    Table layout cases, the expected output was recorded from the serde based serializer these replaced,
    the direct writer must match it exactly.
    """
    assert rtoml.dumps(input_obj, pretty=pretty, none_value=none_value) == output_toml


def nest(depth, kind):
    obj = {} if kind == 'dict' else []
    for _ in range(depth):
        obj = {'a': obj} if kind == 'dict' else [obj]
    return obj


@pytest.mark.parametrize('kind', ['dict', 'list'])
def test_dumps_nesting_limit(kind):
    """Deep nesting raises rather than overflowing the stack, the limit counts every table and array."""
    ok = nest(120, kind)
    rtoml.dumps({'a': ok})
    rtoml.dumps({'a': ok}, pretty=True)
    rtoml.dumps({'a': [ok]}) if kind == 'dict' else rtoml.dumps({'a': [{'b': ok}]})
    with pytest.raises(rtoml.TomlSerializationError, match='TOML nesting too deep, the limit is 128 levels'):
        rtoml.dumps({'a': nest(200, kind)})
    with pytest.raises(rtoml.TomlSerializationError, match='TOML nesting too deep'):
        rtoml.dumps({'a': nest(100_000, kind)})


def test_dumps_self_referential():
    d = {}
    d['self'] = d
    with pytest.raises(rtoml.TomlSerializationError, match='does the object contain itself'):
        rtoml.dumps(d)
    lst = []
    lst.append(lst)
    with pytest.raises(rtoml.TomlSerializationError, match='does the object contain itself'):
        rtoml.dumps({'a': lst})
    with pytest.raises(rtoml.TomlSerializationError, match='does the object contain itself'):
        rtoml.dumps({'a': [d, 1]})
