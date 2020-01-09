from datetime import datetime, timezone
from io import TextIOBase
from pathlib import Path
from typing import Any, TextIO, Union

from . import _rtoml
from .version import VERSION

__all__ = 'TomlError', 'load', 'loads'

TomlError = _rtoml.TomlError


def load(toml: Union[str, Path, TextIO]) -> Any:
    if isinstance(toml, Path):
        toml = toml.read_text()
    elif isinstance(toml, (TextIOBase, TextIO)):
        toml = toml.read()

    return loads(toml)


def loads(toml: str) -> Any:
    if not isinstance(toml, str):
        raise TypeError(f'invalid toml input, must be str not {type(toml)}')
    return _rtoml.deserialize(toml, parse_datetime)


def parse_datetime(v: str) -> datetime:
    tz = None
    if v.endswith(('z', 'Z')):
        tz = timezone.utc
        v = v[:-1]
    dt = datetime.fromisoformat(v)
    if tz:
        dt = dt.replace(tzinfo=tz)
    return dt
