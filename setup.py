from setuptools import setup
from setuptools_rust import Binding, RustExtension

setup(
    name='rtoml',
    version='0.1',
    rust_extensions=[RustExtension('rtoml._rtoml', binding=Binding.PyO3)],
    packages=['rtoml'],
    zip_safe=False,
)
