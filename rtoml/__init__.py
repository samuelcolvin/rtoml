from io import TextIOBase
from pathlib import Path
from typing import Any, Dict, TextIO, Union

from . import _rtoml

__all__ = '__version__', 'TomlParsingError', 'TomlSerializationError', 'load', 'loads', 'dumps', 'dump'

# VERSION is set in Cargo.toml
VERSION = _rtoml.__version__
__version__ = _rtoml.__version__
TomlParsingError = _rtoml.TomlParsingError
TomlSerializationError = _rtoml.TomlSerializationError


def load(toml: Union[str, Path, TextIO]) -> Dict[str, Any]:
    """
    Parse TOML via a string or file and return a python dict. The `toml` argument may be a `str`,
    `Path` or file object from `open()`.
    """
    if isinstance(toml, Path):
        toml = toml.read_text(encoding='UTF-8')
    elif isinstance(toml, (TextIOBase, TextIO)):
        toml = toml.read()

    return loads(toml)


def loads(toml: str) -> Dict[str, Any]:
    """
    Parse a TOML string and return a python dict. (provided to match the interface of `json` and similar libraries)
    """
    if not isinstance(toml, str):
        raise TypeError(f'invalid toml input, must be str not {type(toml)}')
    return _rtoml.deserialize(toml)


def dumps(obj: Any, *, pretty: bool = False) -> str:
    """
    Serialize a python object to TOML.

    If `pretty` is true, output has a more "pretty" format.
    """
    if pretty:
        serialize = _rtoml.serialize_pretty
    else:
        serialize = _rtoml.serialize

    return serialize(obj)


def dump(obj: Any, file: Union[Path, TextIO], *, pretty: bool = False) -> int:
    """
    Serialize a python object to TOML and write it to a file. `file` may be a `Path` or file object from `open()`.

    If `pretty` is true, output has a more "pretty" format.
    """
    s = dumps(obj, pretty=pretty)
    if isinstance(file, Path):
        return file.write_text(s, encoding='UTF-8')
    else:
        return file.write(s)
