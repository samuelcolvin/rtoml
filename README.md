# rtoml

[![Actions Status](https://github.com/samuelcolvin/rtoml/workflows/CI/badge.svg)](https://github.com/samuelcolvin/rtoml/actions?query=event%3Apush+branch%3Amain+workflow%3ACI)
[![Coverage](https://codecov.io/gh/samuelcolvin/rtoml/branch/main/graph/badge.svg)](https://codecov.io/gh/samuelcolvin/rtoml)
[![pypi](https://img.shields.io/pypi/v/rtoml.svg)](https://pypi.python.org/pypi/rtoml)
[![license](https://img.shields.io/github/license/samuelcolvin/rtoml.svg)](https://github.com/samuelcolvin/rtoml/blob/main/LICENSE)


A better TOML library for python implemented in rust.

## Why Use rtoml

* Correctness: rtoml is based on the widely used and very stable [toml-rs](https://github.com/alexcrichton/toml-rs)
library, it passes all the [standard TOML tests](https://github.com/BurntSushi/toml-test) as well as having 100%
coverage on python code. Other TOML libraries for python I tried all failed to parse some valid TOML.
* Performance: see [benchmarks](https://github.com/samuelcolvin/rtoml/tree/main/benchmarks) -
  rtoml is much faster than pure Python TOML libraries.

## Install

Requires `python>=3.7`, binaries are available from pypi for linux, macos and windows,
see [here](https://pypi.org/project/rtoml/#files).

```bash
pip install rtoml
```

If no binary is available on pypi for you system configuration; you'll need rust nightly and
[`setuptools-rust`](https://github.com/PyO3/setuptools-rust) installed before you can install rtoml.

## Usage

#### load
```python
def load(toml: Union[str, Path, TextIO]) -> Dict[str, Any]: ...
```

Parse TOML via a string or file and return a python dictionary. The `toml` argument may be a `str`,
`Path` or file object from `open()`.

#### loads
```python
def loads(toml: str) -> Dict[str, Any]: ...
```

Parse a TOML string and return a python dictionary. (provided to match the interface of `json` and similar libraries)

#### dumps
```python
def dumps(obj: Any, *, pretty: bool = False) -> str: ...
```

Serialize a python object to TOML.

If `pretty` is true, output has a more "pretty" format.

#### dump
```python
def dump(obj: Any, file: Union[Path, TextIO], *, pretty: bool = False) -> int: ...
```

Serialize a python object to TOML and write it to a file. `file` may be a `Path` or file object from `open()`.

If `pretty` is true, output has a more "pretty" format.

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
