from importlib.machinery import SourceFileLoader
from pathlib import Path
from types import ModuleType

import rtoml


def test_example():
    loader = SourceFileLoader('example', str(Path(__file__).parent / '../example.py'))
    module = ModuleType(loader.name)
    loader.exec_module(module)
    # check it looks about right
    assert isinstance(module.obj, dict)
    assert module.obj['title'] == 'TOML Example'


def test_version():
    assert isinstance(rtoml.VERSION, str)
    print('rtoml VERSION:', rtoml.VERSION)
