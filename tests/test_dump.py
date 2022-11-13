from datetime import date, datetime, time, timezone

import pytest

import rtoml


@pytest.mark.parametrize(
    'input_obj,output_toml',
    [
        ({'text': '\nfoo\nbar\n'}, 'text = "\\nfoo\\nbar\\n"\n'),
        ({'foo': 'bar'}, 'foo = "bar"\n'),
        ([1, 2, 3], '[1, 2, 3]'),
        (datetime(1979, 5, 27, 7, 32), '1979-05-27T07:32:00'),
        (datetime(1979, 5, 27, 7, 32, tzinfo=timezone.utc), '1979-05-27T07:32:00Z'),
        (date(2022, 12, 31), '2022-12-31'),
        (time(12, 00, 59, 23456), '12:00:59.023456'),
        ({'x': datetime(1979, 5, 27, 7, 32)}, 'x = 1979-05-27T07:32:00\n'),
        # order changed to avoid https://github.com/alexcrichton/toml-rs/issues/142
        ({'x': {'a': 1}, 'y': 4}, 'y = 4\n\n[x]\na = 1\n'),
        ((1, 2, 3), '[1, 2, 3]'),
        ({'emoji': '😷'}, 'emoji = "😷"\n'),
        ({'polish': 'Witaj świecie'}, 'polish = "Witaj świecie"\n'),
        ({'bytes': b'hello'}, 'bytes = "hello"\n'),
        ({'bytes': b'\xf0\x9f\x98\xb7'}, 'bytes = "😷"\n'),
        ({'bytes': b'\x00\x01\x02'}, 'bytes = "\\u0000\\u0001\\u0002"\n'),
        ({'bytes': bytearray(b'hello')}, 'bytes = "hello"\n'),
    ],
)
def test_dumps(input_obj, output_toml):
    assert rtoml.dumps(input_obj) == output_toml


@pytest.mark.parametrize('input_value', [b'\x81', bytearray(b'\x81')])
def test_utf8_error(input_value):
    with pytest.raises(rtoml.TomlSerializationError, match='invalid utf-8 sequence of 1 bytes from index 0'):
        rtoml.dumps({'bytes': input_value})


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
