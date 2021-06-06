#!/usr/bin/env python3
import timeit
from pathlib import Path

import pytomlpp
import toml as uiri_toml
import tomli
import tomlkit

import rtoml

toml_str = (Path(__file__).parent / 'data.toml').read_text()


def rtoml_load():
    return rtoml.loads(toml_str)


def uiri_toml_load():
    return uiri_toml.loads(toml_str)

def tomli_load():
    return tomli.loads(toml_str)

def pytomlpp_load():
    return pytomlpp.loads(toml_str)

def tomlkit_load():
    return tomlkit.parse(toml_str)


def test_matching_output():
    rtoml_data = rtoml_load()
    # debug(rtoml_data)
    assert rtoml_data == uiri_toml_load()
    assert rtoml_data == tomlkit_load()
    assert rtoml_data == tomli_load()
    assert rtoml_data == pytomlpp_load()


if __name__ == '__main__':
    steps = 100

    timeit.timeit(rtoml_load, number=steps)
    rtoml_time = timeit.timeit(rtoml_load, number=steps)
    print(f'rtoml     version: {rtoml.VERSION:8} {rtoml_time / steps * 1000:0.3f} ms/parse')

    timeit.timeit(pytomlpp_load, number=steps)
    pytomlpp_time = timeit.timeit(pytomlpp_load, number=steps)
    print(
        f'pytomlpp  version: {pytomlpp.lib_version:8} {pytomlpp_time / steps * 1000:0.3f} ms/parse '
        f'({rtoml_time / pytomlpp_time:0.2f} X faster)'
    )

    tomli_time = timeit.timeit(tomli_load, number=steps)
    print(
        f'tomli     version: {tomli.__version__:8} {tomli_time / steps * 1000:0.3f} ms/parse '
        f'({tomli_time / rtoml_time:0.2f} X slower)'
    )

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
