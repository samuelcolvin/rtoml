import pytest

import rtoml


@pytest.mark.parametrize(
    'input_toml,expected_output',
    [
        (
            """something = true
lion = "aslan"
""",
            {'something': True, 'lion': 'aslan'},
        ),
        (
            """[section]
z = "last"
a = "first"

[default]
dir = "/home"
beta = true
""",
            {'section': {'z': 'last', 'a': 'first'}, 'default': {'dir': '/home', 'beta': True}},
        ),
    ],
)
def test_load_order(input_toml, expected_output):
    loaded = rtoml.load(input_toml)
    assert loaded == expected_output
    assert list(loaded.items()) == list(expected_output.items())  # check order is maintained

    assert rtoml.dumps(expected_output) == input_toml
