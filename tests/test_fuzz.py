"""
Property based tests for dumps: whatever we write must parse back to the same values, both with rtoml and with
the standard library's tomllib as an independent TOML 1.0 parser, and unsupported input must raise
TomlSerializationError rather than anything else.
"""

import math
from datetime import datetime, timedelta, timezone

import pytest
from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st

import rtoml

try:
    import tomllib
except ImportError:  # Python 3.10
    tomllib = None

pytestmark = pytest.mark.filterwarnings('ignore::pytest.PytestUnraisableExceptionWarning')

# surrogates can't be encoded as UTF-8, so they're tested separately as an error case
text = st.text(alphabet=st.characters(exclude_categories=['Cs']), max_size=20)
offsets = st.integers(-1439, 1439).map(lambda m: timezone(timedelta(minutes=m)))
datetimes = st.datetimes(
    min_value=datetime(1, 1, 1), max_value=datetime(9999, 12, 31, 23, 59, 59), timezones=st.none() | offsets
)
scalars = st.one_of(
    st.none(),
    st.booleans(),
    st.integers(-(2**127), 2**127 - 1),
    st.floats(allow_subnormal=True),
    text,
    datetimes,
    st.dates(),
    st.times(),
    st.binary(max_size=8),
)
keys = st.one_of(text, st.booleans(), st.none())
values = st.recursive(
    scalars,
    lambda children: st.one_of(
        st.lists(children, max_size=5), st.tuples(children, children), st.dictionaries(keys, children, max_size=5)
    ),
    max_leaves=25,
)
documents = st.dictionaries(keys, values, max_size=6)
none_values = st.sampled_from([None, 'null', ''])


def expected(value, none_value):
    """What parsing the output of dumps(value, none_value=none_value) should give."""
    if value is None:
        return none_value
    elif isinstance(value, float):
        return ('nan',) if math.isnan(value) else value
    elif isinstance(value, (bytes, bytearray)):
        return list(value)
    elif isinstance(value, (list, tuple)):
        return [expected(v, none_value) for v in value if not (v is None and none_value is None)]
    elif isinstance(value, dict):
        out = {}
        for k, v in value.items():
            if none_value is None and (k is None or v is None):
                continue
            if k is None:
                k = none_value
            elif isinstance(k, bool):
                k = 'true' if k else 'false'
            out[k] = expected(v, none_value)
        return out
    else:
        return value


def normalise(value):
    """nan never compares equal, so replace it with a marker before comparing."""
    if isinstance(value, float) and math.isnan(value):
        return ('nan',)
    elif isinstance(value, list):
        return [normalise(v) for v in value]
    elif isinstance(value, dict):
        return {k: normalise(v) for k, v in value.items()}
    return value


def keys_collide(value, none_value):
    """True and 'true', or None and the none_value string, become the same TOML key, skip such inputs."""
    if isinstance(value, dict):
        encoded = []
        for k in value:
            if none_value is None and k is None:
                continue
            encoded.append('true' if k is True else 'false' if k is False else none_value if k is None else k)
        return len(set(encoded)) != len(encoded) or any(keys_collide(v, none_value) for v in value.values())
    elif isinstance(value, (list, tuple)):
        return any(keys_collide(v, none_value) for v in value)
    return False


@pytest.mark.skipif(tomllib is None, reason='tomllib was added in Python 3.11')
@settings(max_examples=300, deadline=None, suppress_health_check=[HealthCheck.too_slow])
@given(documents, none_values, st.booleans())
def test_roundtrip(document, none_value, pretty):
    if keys_collide(document, none_value):
        return
    output = rtoml.dumps(document, none_value=none_value, pretty=pretty)
    want = normalise(expected(document, none_value))
    assert normalise(rtoml.loads(output)) == want, output
    assert normalise(tomllib.loads(output)) == want, output


class Custom:
    pass


class NoRepr:
    def __repr__(self):
        raise RuntimeError('no repr for you')


class DictSubclass(dict):
    pass


class StrSubclass(str):
    pass


surrogates = st.text(alphabet=st.characters(min_codepoint=0xD800, max_codepoint=0xDFFF), min_size=1, max_size=3)
unsupported = st.one_of(
    st.builds(Custom),
    st.builds(NoRepr),
    st.builds(DictSubclass, st.just({'a': 1})),
    st.builds(StrSubclass, st.just('x')),
    st.sets(st.integers(), max_size=3),
    st.complex_numbers(),
    st.just(2**128),
    st.just(-(2**128)),
    surrogates,
    st.just(range(3)),
)
simple_scalars = st.one_of(st.none(), st.booleans(), st.integers(-(2**64), 2**64), st.floats(), st.text(max_size=5))
odd_keys = st.one_of(st.text(max_size=5), st.integers(), st.none(), st.booleans(), surrogates, st.floats())
mixed = st.recursive(
    st.one_of(simple_scalars, unsupported),
    lambda children: st.one_of(st.lists(children, max_size=4), st.dictionaries(odd_keys, children, max_size=4)),
    max_leaves=12,
)


@settings(max_examples=300, deadline=None, suppress_health_check=[HealthCheck.too_slow])
@given(mixed, st.sampled_from([None, 'null']), st.booleans())
def test_unsupported_input_raises_cleanly(obj, none_value, pretty):
    try:
        output = rtoml.dumps(obj, none_value=none_value, pretty=pretty)
    except rtoml.TomlSerializationError:
        return
    # if it was accepted, it must at least be valid TOML
    if isinstance(obj, dict):
        rtoml.loads(output)
