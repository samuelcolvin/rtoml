from datetime import datetime, timezone

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
        ({'x': datetime(1979, 5, 27, 7, 32)}, 'x = 1979-05-27T07:32:00\n'),
        # order changed to avoid https://github.com/alexcrichton/toml-rs/issues/142
        ({'x': {'a': 1}, 'y': 4}, 'y = 4\n\n[x]\na = 1\n'),
        ((1, 2, 3), '[1, 2, 3]'),
        ({'emoji': '😷'}, 'emoji = "😷"\n'),
        ({'polish': 'Witaj świecie'}, 'polish = "Witaj świecie"\n'),
    ],
)
def test_dumps(input_obj, output_toml):
    assert rtoml.dumps(input_obj) == output_toml


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
    'input_obj,output_toml',
    [
        ({None: 1}, ''),
        ({'key': None}, ''),
        ({'foo': 'bar', 'key1': None}, 'foo = "bar"\n'),
        ({'key1': None, 'foo': 'bar'}, 'foo = "bar"\n'),
        ({'key1': None, 'foo': 'bar', 'key2': None}, 'foo = "bar"\n'),
    ],
)
def test_none_map_value(input_obj, output_toml):
    assert rtoml.dumps(input_obj, include_none=False) == output_toml

@pytest.mark.parametrize(
    'input_obj,output_toml',
    [
        ([None], '[]'),
        (["a", None], '["a"]'),
        ([None, "b"], '["b"]'),
        (["a", None, "b"], '["a", "b"]'),
        ({'foo': 'bar', 'list': [None]}, 'foo = "bar"\nlist = []\n'),
        ({'foo': 'bar', 'list': [None, "b"]}, 'foo = "bar"\nlist = ["b"]\n'),
        ({'foo': 'bar', 'list': ["a", None]}, 'foo = "bar"\nlist = ["a"]\n'),
        ({'foo': 'bar', 'list': ["a", None, "b"]}, 'foo = "bar"\nlist = ["a", "b"]\n'),
    ],
)
def test_none_values_inside_list(input_obj, output_toml):
    assert rtoml.dumps(input_obj, include_none=False) == output_toml

@pytest.mark.parametrize(
    'input_obj,output_toml',
    [
        ((None), '"null"'),
        (("a", None), '["a"]'),
        ((None, "b"), '["b"]'),
        (("a", None, "b"), '["a", "b"]'),
        ({'foo': 'bar', 'list': (None)}, 'foo = "bar"\n'),
        ({'foo': 'bar', 'list': (None, "b")}, 'foo = "bar"\nlist = ["b"]\n'),
        ({'foo': 'bar', 'list': ("a", None)}, 'foo = "bar"\nlist = ["a"]\n'),
        ({'foo': 'bar', 'list': ("a", None, "b")}, 'foo = "bar"\nlist = ["a", "b"]\n'),
    ],
)
def test_none_values_inside_tuple(input_obj, output_toml):
    assert rtoml.dumps(input_obj, include_none=False) == output_toml
