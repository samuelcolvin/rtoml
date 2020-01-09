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
load(toml: Union[str, Path, TextIO]) -> Any
```

Parse TOML via a string or file and return a python object. The `toml` argument by be a `str`,
`Path` or file object from `open()`.

#### loads
```python
loads(toml: str) -> Any
```

Parse a TOML string and return a python object.

#### dumps
```python
dumps(obj: Any) -> str
```

Serialize a python object to TOML.

#### dump
```python
dump(obj: Any, file: Union[Path, TextIO]) -> int
```

Serialize a python object to TOML and write it to a file. `file` maybe a `Path` or file object from `open()`.

### Example

```py
TODO
```
