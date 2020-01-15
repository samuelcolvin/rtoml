from importlib.machinery import SourceFileLoader
from pathlib import Path

import rtoml


def test_example():
    module = SourceFileLoader('example', str(Path(__file__).parent / '../example.py')).load_module()
    # check it looks about right
    assert isinstance(module.obj, dict)
    assert module.obj['title'] == 'TOML Example'


def test_version():
    assert isinstance(rtoml.VERSION, str)
    print('rtoml VERSION:', rtoml.VERSION)
