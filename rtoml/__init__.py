from io import TextIOBase
from pathlib import Path
from typing import Any, Union

from . import rust_rtoml
from .utils import TomlError, parse_datetime

__all__ = 'TomlError', 'load'


def load(v: Union[str, bytes, Path, TextIOBase]) -> Any:
    if isinstance(v, Path):
        v = v.read_text()
    elif isinstance(v, TextIOBase):
        v = v.read()

    if isinstance(v, bytes):
        v = v.decode()

    return rust_rtoml.deserialize(v, parse_datetime)
