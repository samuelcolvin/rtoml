import math
from collections import OrderedDict
from datetime import date, datetime, time, timedelta, timezone

import pytest

import rtoml


@pytest.mark.parametrize(
    'input_obj,output_toml',
    [
        ({'text': '\nfoo\nbar\n'}, 'text = "\\nfoo\\nbar\\n"\n'),
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
        ({'text': '\nfoo\nbar\n'}, "text = '''\n\nfoo\nbar\n'''\n"),
        ({'foo': 'bar'}, "foo = 'bar'\n"),
        ([1, 2, 3], '[\n    1,\n    2,\n    3,\n]'),
        ((1, 2, 3), '[\n    1,\n    2,\n    3,\n]'),
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
        ({'a': 'he said "hi"\t\\'}, 'a = "he said \\"hi\\"\\t\\\\"\n'),
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
        ({'a': None, 'b': [None, 1]}, "a = 'N'\nb = [\n    'N',\n    1,\n]\n"),
        ({'a': {'b': {'c': 1}}, 'l': [{'x': 1}]}, '[[l]]\nx = 1\n[a.b]\nc = 1\n'),
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
        ({'a': 2**63}, 'OverflowError: Python int too large to convert to C long'),
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


@pytest.mark.xfail(reason='toml-rs 0.5 emits invalid TOML for arrays mixing tables and scalars', strict=True)
def test_dumps_mixed_table_scalar_array():
    output = rtoml.dumps({'a': [{'x': 1}, 2]})
    assert rtoml.loads(output) == {'a': [{'x': 1}, 2]}
