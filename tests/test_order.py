import pytest

import rtoml


@pytest.mark.parametrize(
    'input_toml,expected_output',
    [
        (
            """
something = true
lion = 'aslan'
""",
            "{'something': True, 'lion': 'aslan'}",
        ),
        (
            """
[section]
z = "last"
a = "first"
[default]
dir = "/home"
beta = true
""",
            "{'section': {'z': 'last', 'a': 'first'}, 'default': {'dir': '/home', 'beta': True}}",
        ),
    ],
)
def test_load_order(input_toml, expected_output):
    """
    When testing preserving of order we just check if
    the stringified TOML dictionary is in the same sequence
    as the original TOML string.
    """

    assert str(rtoml.load(input_toml)) == expected_output
