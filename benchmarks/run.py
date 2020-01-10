#!/usr/bin/env python3
import timeit
from pathlib import Path

import toml
import tomlkit

import rtoml

print(f'rtoml version: {rtoml.VERSION}')
toml_str = (Path(__file__).parent / 'data.toml').read_text()


def rtoml_load():
    return rtoml.loads(toml_str)


def uiri_toml_load():
    return toml.loads(toml_str)


def tomlkit_load():
    return tomlkit.parse(toml_str)


def test_matching_output():
    rtoml_data = rtoml_load()
    # debug(rtoml_data)
    assert rtoml_data == uiri_toml_load()
    assert rtoml_data == tomlkit_load()


if __name__ == '__main__':
    steps = 100

    rtoml_time = timeit.timeit(rtoml_load, number=steps)
    print(f'rtoml:      {rtoml_time / steps * 1000:0.3f} ms/parse')

    toml_time = timeit.timeit(uiri_toml_load, number=steps)
    print(f'uiri/toml:  {toml_time / steps * 1000:0.3f} ms/parse ({toml_time / rtoml_time:0.2f} X slower)')

    tomlkit_time = timeit.timeit(tomlkit_load, number=steps)
    print(f'tomlkit:    {tomlkit_time / steps * 1000:0.3f} ms/parse ({tomlkit_time / rtoml_time:0.2f} X slower)')
