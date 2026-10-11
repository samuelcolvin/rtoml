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
