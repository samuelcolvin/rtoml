import rtoml


def test_load_str():
    assert rtoml.load('foo = "bar"') == {'foo': 'bar'}
