import math
from datetime import datetime, timedelta, timezone
from importlib.machinery import SourceFileLoader
from pathlib import Path
from types import ModuleType

import pytest

import rtoml


def test_example():
    loader = SourceFileLoader('example', str(Path(__file__).parent / '../example.py'))
    module = ModuleType(loader.name)
    loader.exec_module(module)
    # check it looks about right
    assert isinstance(module.obj, dict)
    assert module.obj['title'] == 'TOML Example'


def test_version():
    assert isinstance(rtoml.__version__, str)
    print('rtoml __version__:', rtoml.__version__)


@pytest.mark.parametrize(
    'dt',
    [
        datetime(2020, 5, 25, 12, 0, 1, 123456),
        # trailing zero in the microseconds, serialised as .12345 which must still parse
        datetime(2020, 5, 25, 12, 0, 1, 123450),
        datetime(2020, 5, 25, 12, 0, 1, 5),
        datetime(2020, 5, 25, 12, 0, 1, 123456, tzinfo=timezone.utc),
        datetime(2020, 5, 25, 12, 0, 1, 123450, tzinfo=timezone(timedelta(hours=-8))),
    ],
)
def test_datetime_precision(dt):
    assert rtoml.loads(rtoml.dumps({'a': dt})) == {'a': dt}


def test_version_alias():
    assert rtoml.VERSION == rtoml.__version__


def test_exceptions_are_value_errors():
    assert issubclass(rtoml.TomlParsingError, ValueError)
    assert issubclass(rtoml.TomlSerializationError, ValueError)
    assert rtoml.TomlParsingError is not rtoml.TomlSerializationError


def test_all():
    for name in rtoml.__all__:
        assert hasattr(rtoml, name)


def _strip_nan(value):
    if isinstance(value, dict):
        return {k: _strip_nan(v) for k, v in value.items()}
    elif isinstance(value, list):
        return [_strip_nan(v) for v in value]
    elif isinstance(value, float) and math.isnan(value):
        # a tuple can never come out of the parser, so this cannot collide with a real value
        return ('nan',)
    return value


@pytest.mark.parametrize('pretty', [False, True])
def test_data_toml_roundtrip(pretty):
    data = rtoml.load(Path(__file__).parent / 'data.toml')
    assert len(data) > 10
    loaded = rtoml.loads(rtoml.dumps(data, pretty=pretty))
    # nan never compares equal, so normalise it before comparing
    assert _strip_nan(loaded) == _strip_nan(data)
