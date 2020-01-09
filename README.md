# rtoml

A better TOML library for python implemented in rust.

## Install

Requires linux and `python>=3.7`.

```bash
pip install rtoml
```

## Usage

#### load
```python
def load(toml: Union[str, Path, TextIO]) -> Any: ...
```

Parse TOML via a string or file and return a python object. The `toml` argument may be a `str`,
`Path` or file object from `open()`.

#### loads
```python
def loads(toml: str) -> Any: ...
```

Parse a TOML string and return a python object. (provided to match the interface of `json` and similar libraries)

#### dumps
```python
def dumps(obj: Any) -> str: ...
```

Serialize a python object to TOML.

#### dump
```python
def dump(obj: Any, file: Union[Path, TextIO]) -> int: ...
```

Serialize a python object to TOML and write it to a file. `file` may be a `Path` or file object from `open()`.

### Example

```py
from datetime import datetime, timezone, timedelta
import rtoml

obj = {
    'title': 'TOML Example',
    'owner': {
        'dob': datetime(1979, 5, 27, 7, 32, tzinfo=timezone(timedelta(hours=-8))),
        'name': 'Tom Preston-Werner',
    },
    'database': {
        'connection_max': 5000,
        'enabled': True,
        'ports': [8001, 8001, 8002],
        'server': '192.168.1.1',
    },
}

loaded_obj = rtoml.load("""\
# This is a TOML document.

title = "TOML Example"

[owner]
name = "Tom Preston-Werner"
dob = 1979-05-27T07:32:00-08:00 # First class dates

[database]
server = "192.168.1.1"
ports = [8001, 8001, 8002]
connection_max = 5000
enabled = true
""")

assert loaded_obj == obj

assert rtoml.dumps(obj) == """\
title = "TOML Example"

[owner]
dob = 1979-05-27T07:32:00-08:00
name = "Tom Preston-Werner"

[database]
connection_max = 5000
enabled = true
server = "192.168.1.1"
ports = [8001, 8001, 8002]
"""
```
