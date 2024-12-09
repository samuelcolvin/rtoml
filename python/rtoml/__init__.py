from io import TextIOBase
from pathlib import Path
from typing import Any, Optional, TextIO, Union

from . import _rtoml

__all__ = '__version__', 'TomlParsingError', 'TomlSerializationError', 'load', 'loads', 'dumps', 'dump'

# VERSION is set in Cargo.toml
VERSION = _rtoml.__version__
__version__ = _rtoml.__version__
TomlParsingError = _rtoml.TomlParsingError
TomlSerializationError = _rtoml.TomlSerializationError


def load(toml: Union[str, Path, TextIO], *, none_value: Optional[str] = None) -> dict[str, Any]:
    """
    Parse TOML via a string or file and return a python dict.

    Args:
        toml: a `str`, `Path` or file object from `open()`.
        none_value: controlling which value in `toml` is loaded as `None` in python.
            By default, `none_value` is `None`, which means nothing is loaded as `None`.
    """
    if isinstance(toml, Path):
        toml = toml.read_text(encoding='UTF-8')
    elif isinstance(toml, (TextIOBase, TextIO)):
        toml = toml.read()

    return loads(toml, none_value=none_value)


def loads(toml: str, *, none_value: Optional[str] = None) -> dict[str, Any]:
    """
    Parse a TOML string and return a python dict. (provided to match the interface of `json` and similar libraries)

    Args:
        toml: a `str` containing TOML.
        none_value: controlling which value in `toml` is loaded as `None` in python.
            By default, `none_value` is `None`, which means nothing is loaded as `None`.
    """
    if not isinstance(toml, str):
        raise TypeError(f'invalid toml input, must be str not {type(toml)}')
    return _rtoml.deserialize(toml, none_value=none_value)


def dumps(obj: Any, *, pretty: bool = False, none_value: Optional[str] = 'null') -> str:
    """
    Serialize a python object to TOML.

    Args:
        obj: a python object to be serialized.
        pretty: if true, output has a more "pretty" format.
        none_value: controlling how `None` values in `obj` are serialized.
            `none_value=None` means `None` values are ignored.
    """
    if pretty:
        serialize = _rtoml.serialize_pretty
    else:
        serialize = _rtoml.serialize

    return serialize(obj, none_value=none_value)


def dump(obj: Any, file: Union[Path, TextIO], *, pretty: bool = False, none_value: Optional[str] = 'null') -> int:
    """
    Serialize a python object to TOML and write it to a file.

    Args:
        obj: a python object to be serialized.
        file: a `Path` or file object from `open()`.
        pretty: if `True` the output has a more "pretty" format.
        none_value: controlling how `None` values in `obj` are serialized.
            `none_value=None` means `None` values are ignored.
    """
    s = dumps(obj, pretty=pretty, none_value=none_value)
    if isinstance(file, Path):
        return file.write_text(s, encoding='UTF-8')
    else:
        return file.write(s)
