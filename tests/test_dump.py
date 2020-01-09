from datetime import datetime, timezone

import pytest

import rtoml


@pytest.mark.parametrize(
    'input_obj,output_toml',
    [
        ({'foo': 'bar'}, 'foo = "bar"\n'),
        ([1, 2, 3], '[1, 2, 3]'),
        (datetime(1979, 5, 27, 7, 32), '1979-05-27T07:32:00'),
        (datetime(1979, 5, 27, 7, 32, tzinfo=timezone.utc), '1979-05-27T07:32:00Z'),
        ({'x': datetime(1979, 5, 27, 7, 32)}, 'x = 1979-05-27T07:32:00\n'),
        # order changed to avoid https://github.com/alexcrichton/toml-rs/issues/142
        ({'x': {'a': 1}, 'y': 4}, 'y = 4\n\n[x]\na = 1\n'),
        ((1, 2, 3), '[1, 2, 3]'),
    ],
)
def test_dumps(input_obj, output_toml):
    assert rtoml.dumps(input_obj) == output_toml


def test_dump_path(tmp_path):
    p = tmp_path / 'test.toml'
    assert rtoml.dump({'foo': 'bar'}, p) == 12
    assert p.read_text() == 'foo = "bar"\n'


def test_dump_file(tmp_path):
    p = tmp_path / 'test.toml'
    with p.open('w') as f:
        assert rtoml.dump({'foo': 'bar'}, f) == 12
    assert p.read_text() == 'foo = "bar"\n'
