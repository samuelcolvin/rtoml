from datetime import datetime, timezone
from io import TextIOBase
from pathlib import Path
from typing import Any, TextIO, Union

from . import _rtoml

__all__ = 'VERSION', 'TomlError', 'load', 'loads', 'dumps', 'dump'

# VERSION is set in Cargo.toml
VERSION = _rtoml.VERSION
TomlError = _rtoml.TomlError


def load(toml: Union[str, Path, TextIO]) -> Any:
    """
    Parse TOML via a string or file and return a python object. The `toml` argument by be a `str`,
    `Path` or file object from `open()`.
    """
    if isinstance(toml, Path):
        toml = toml.read_text()
    elif isinstance(toml, (TextIOBase, TextIO)):
        toml = toml.read()

    return loads(toml)


def loads(toml: str) -> Any:
    """
    Parse a TOML string and return a python object.
    """
    if not isinstance(toml, str):
        raise TypeError(f'invalid toml input, must be str not {type(toml)}')
    return _rtoml.deserialize(toml, parse_datetime)


def dumps(obj: Any) -> str:
    """
    Serialize a python object to TOML.
    """
    return _rtoml.serialize(obj)


def dump(obj: Any, file: Union[Path, TextIO]) -> int:
    """
    Serialize a python object to TOML and write it to a file. `file` maybe a `Path` or file object from `open()`.
    """
    s = dumps(obj)
    if isinstance(file, Path):
        return file.write_text(s)
    else:
        return file.write(s)


def parse_datetime(v: str) -> datetime:
    tz = None
    if v.endswith(('z', 'Z')):
        tz = timezone.utc
        v = v[:-1]
    dt = datetime.fromisoformat(v)
    if tz:
        dt = dt.replace(tzinfo=tz)
    return dt
