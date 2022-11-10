#!/usr/bin/env python3
import timeit
from pathlib import Path

import rtoml

toml_str = (Path(__file__).parent / 'data.toml').read_text()


def rtoml_load():
    return rtoml.loads(toml_str)


if __name__ == '__main__':
    steps = 100

    timeit.timeit(rtoml_load, number=steps)
    rtoml_time = timeit.timeit(rtoml_load, number=steps)
    print(f'rtoml     version: {rtoml.VERSION:8} {rtoml_time / steps * 1000:0.3f} ms/parse')
