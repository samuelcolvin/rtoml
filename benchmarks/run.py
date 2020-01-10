#!/usr/bin/env python3
import timeit
from pathlib import Path

import tomlkit

import rtoml

toml = (Path(__file__).parent / 'data.toml').read_text()


def rtoml_load():
    return rtoml.loads(toml)


def tomlkit_load():
    return tomlkit.parse(toml)


rtoml_data = rtoml_load()
debug(rtoml_data)
debug(list(rtoml_data.keys()))
# assert rtoml_data == tomlkit_load()


steps = 100

print(timeit.timeit(rtoml_load, number=steps))
# print(timeit.timeit(pyd_func, number=100000))
