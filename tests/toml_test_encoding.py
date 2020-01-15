#!/usr/bin/env python3
# used to test encoding against https://github.com/BurntSushi/toml-test
# via `make toml-test` or `~/go/bin/toml-test -encoder ./tests/toml_test_encoding.py`
import json
import sys
from pathlib import Path

ROOT_DIR = (Path(__file__).parent / '..').resolve()

sys.path.append(str(ROOT_DIR))

import rtoml  # noqa


def get_values(value):
    if isinstance(value, list):
        return [get_values(v) for v in value]
        # raise TypeError(f'invalid type not dict: {value}')
    elif not isinstance(value, dict):
        raise TypeError(f'invalid type not dict: {value}')

    if value.keys() != {'type', 'value'}:
        return {k: get_values(v) for k, v in value.items()}

    t, v = value['type'], value['value']

    if t == 'integer':
        return int(v)
    elif t == 'float':
        return float(v)
    elif t == 'bool':
        return v == 'true'
    elif t == 'datetime':
        return rtoml.parse_datetime(v)
    elif t == 'array':
        return [get_values(v) for v in v]
    elif t == 'string':
        return v
    else:
        raise TypeError(f'invalid type value: {value!r}')


if __name__ == '__main__':
    stdin = sys.stdin.read()
    raw = json.loads(stdin)
    values = get_values(raw)
    toml = rtoml.dumps(values)
    print(toml)
