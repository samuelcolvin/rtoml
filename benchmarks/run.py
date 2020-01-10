#!/usr/bin/env python3
import timeit
from pathlib import Path

import toml as uiri_toml
import tomlkit

import rtoml

toml_str = (Path(__file__).parent / 'data.toml').read_text()


def rtoml_load():
    return rtoml.loads(toml_str)


def uiri_toml_load():
    return uiri_toml.loads(toml_str)


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
    print(f'rtoml     version: {rtoml.VERSION:8} {rtoml_time / steps * 1000:0.3f} ms/parse')

    toml_time = timeit.timeit(uiri_toml_load, number=steps)
    print(
        f'uiri/toml version: {uiri_toml.__version__:8} {toml_time / steps * 1000:0.3f} ms/parse '
        f'({toml_time / rtoml_time:0.2f} X slower)'
    )

    tomlkit_time = timeit.timeit(tomlkit_load, number=steps)
    print(
        f'tomlkit   version: {tomlkit.__version__:8} {tomlkit_time / steps * 1000:0.3f} ms/parse '
        f'({tomlkit_time / rtoml_time:0.2f} X slower)'
    )
