from datetime import date, datetime, time, timezone

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
            (None, 'null'),
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
