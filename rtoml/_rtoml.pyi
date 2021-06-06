from datetime import date, time
from typing import Any, Callable, Union

VERSION: str

def deserialize(toml: str) -> Any: ...
def serialize(obj: Any) -> str: ...
def serialize_pretty(obj: Any) -> str: ...

class TomlParsingError(ValueError): ...
class TomlSerializationError(ValueError): ...
