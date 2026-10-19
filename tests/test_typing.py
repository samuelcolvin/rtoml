from collections.abc import Callable, Mapping
from io import BytesIO, StringIO
from typing import IO, TYPE_CHECKING, Any
from unittest.mock import Mock

import rtoml


def test_load_text_io() -> None:
    stream: IO[str] = StringIO('answer = 42')
    assert rtoml.load(stream) == {'answer': 42}


def test_load_callback() -> None:
    # Match the callback signature used by Flask's Config.from_file.
    loader: Callable[[IO[Any]], Mapping[str, Any]] = rtoml.load
    assert loader(StringIO('answer = 42')) == {'answer': 42}


def test_load_io_reader() -> None:
    reader = Mock(spec=IO)
    reader.read.return_value = 'answer = 42'
    assert rtoml.load(reader) == {'answer': 42}
    reader.read.assert_called_once_with()


def test_load_binary_io() -> None:
    try:
        rtoml.load(BytesIO(b'answer = 42'))  # type: ignore[arg-type]
    except TypeError as exc:
        assert 'invalid toml input' in str(exc)
    else:
        raise AssertionError('binary input must be rejected')


if TYPE_CHECKING:
    # These ignores must remain necessary: binary streams are not supported.
    binary_stream: IO[bytes] = BytesIO(b'answer = 42')
    rtoml.load(binary_stream)  # type: ignore[arg-type]
