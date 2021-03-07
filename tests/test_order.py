
import pytest

import rtoml

"""
When testing preserving of order we just check if
the stringified TOML dictionary is in the same sequence
as the original TOML string.
"""

@pytest.mark.parametrize(
    'input_toml,output_toml',
    [
        ("""
            something = true
            lion = 'aslan'
    """,
        "{'something': True, 'lion': 'aslan'}"
        ),
        ("""
            [section]
            z = "last"
            a = "first"
            [default]
            dir = "/home"
            beta = true
    """,
        "{'section': {'z': 'last', 'a': 'first'}, 'default': {'dir': '/home', 'beta': True}}"
        ),
]
)


def test_load(input_toml, output_toml):
    assert str(rtoml.load(input_toml)) == output_toml
