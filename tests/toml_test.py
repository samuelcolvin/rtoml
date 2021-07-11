#!/usr/bin/env python3
# used to test against https://github.com/BurntSushi/toml-test
# via `~/go/bin/toml-test ./tests/toml_test.py`
import json
import sys
from datetime import datetime, date, time
from pathlib import Path

ROOT_DIR = (Path(__file__).parent / '..').resolve()

sys.path.append(str(ROOT_DIR))

import rtoml  # noqa


def simplify(value):
    if isinstance(value, dict):
        return {k: simplify(v) for k, v in value.items()}
    elif isinstance(value, list):
        a = [simplify(v) for v in value]
        try:
            a[0]['value']
        except KeyError:
            return a
        except IndexError:
            pass
        return {'type': 'array', 'value': a}
    elif isinstance(value, str):
        return {'type': 'string', 'value': value}
    elif isinstance(value, bool):
        return {'type': 'bool', 'value': str(value).lower()}
    elif isinstance(value, int):
        return {'type': 'integer', 'value': str(value)}
    elif isinstance(value, float):
        return {'type': 'float', 'value': repr(value)}
    elif isinstance(value, datetime):
        return {'type': 'datetime', 'value': value.isoformat().replace('+00:00', 'Z')}
    elif isinstance(value, date):
        return {'type': 'date', 'value': value.isoformat()}
    elif isinstance(value, time):
        return {'type': 'time', 'value': value.strftime('%H:%M:%S.%f')}
    assert False, f'Unknown type: {type(value)}'


if __name__ == '__main__':
    data = rtoml.loads(sys.stdin.read())
    result = simplify(data)
    print(json.dumps(result, indent=2))
