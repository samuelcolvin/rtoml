#!/usr/bin/env python3
# used to test the encoder against https://github.com/toml-lang/toml-test
# via `toml-test test -toml 1.1.0 -encoder tests/toml_test_encoder.py`
import json
import re
import sys
from datetime import date, datetime, time
from pathlib import Path

ROOT_DIR = (Path(__file__).parent / '..').resolve()

sys.path.append(str(ROOT_DIR))

import rtoml


def parse_time_part(s: str):
    """Python 3.10's fromisoformat is strict, normalise the fraction to six digits and `Z` to an offset."""
    s = s.replace('Z', '+00:00').replace('z', '+00:00')
    return re.sub(r'\.(\d+)', lambda m: '.' + m.group(1)[:6].ljust(6, '0'), s)


def restore(value):
    """Convert the toml-test JSON description back into Python objects."""
    if isinstance(value, list):
        return [restore(v) for v in value]
    if not (isinstance(value, dict) and set(value) == {'type', 'value'} and isinstance(value['type'], str)):
        return {k: restore(v) for k, v in value.items()}
    t, v = value['type'], value['value']
    if t == 'string':
        return v
    elif t == 'integer':
        return int(v)
    elif t == 'float':
        return float(v.replace('inf', 'inf').replace('nan', 'nan'))
    elif t == 'bool':
        return v == 'true'
    elif t == 'datetime' or t == 'datetime-local':
        return datetime.fromisoformat(parse_time_part(v.replace(' ', 'T').replace('t', 'T')))
    elif t == 'date-local':
        return date.fromisoformat(v)
    elif t == 'time-local':
        return time.fromisoformat(parse_time_part(v))
    raise ValueError(f'unknown type {t!r}')


if __name__ == '__main__':
    data = restore(json.load(sys.stdin))
    sys.stdout.write(rtoml.dumps(data))
