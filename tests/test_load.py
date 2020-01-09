from datetime import datetime, timezone

import pytest

import rtoml


@pytest.mark.parametrize(
    'input_toml,output_obj',
    [
        ('foo = "bar"', {'foo': 'bar'}),
        ('ports = [ 8001, 8001, 8002 ]', {'ports': [8001, 8001, 8002]}),
        ('x = 1979-05-27T07:32:00Z', {'x': datetime(1979, 5, 27, 7, 32, tzinfo=timezone.utc)}),
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
    with pytest.raises(rtoml.TomlError, match='invalid number at line 1 column 5'):
        rtoml.load('x = y')


def test_version():
    assert isinstance(rtoml.VERSION, str)
