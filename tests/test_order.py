import pytest

import rtoml

cases = [
    (
        """\
something = true
lion = "aslan"
""",
        {'something': True, 'lion': 'aslan'},
    ),
    (
        """\
[section]
z = "last"
a = "first"

[default]
dir = "/home"
beta = true
""",
        {'section': {'z': 'last', 'a': 'first'}, 'default': {'dir': '/home', 'beta': True}},
    ),
]


@pytest.mark.parametrize('toml_string,python_object', cases)
def test_load_order(toml_string, python_object):
    loaded = rtoml.load(toml_string)
    assert loaded == python_object
    assert list(loaded.items()) == list(python_object.items())  # check order is maintained


@pytest.mark.parametrize('toml_string,python_object', cases)
def test_dump_order(toml_string, python_object):
    assert rtoml.dumps(python_object) == toml_string
