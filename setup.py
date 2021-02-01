import re
from pathlib import Path

from setuptools import setup
from setuptools_rust import Binding, RustExtension

description = 'A better TOML library for python implemented in rust.'

THIS_DIR = Path(__file__).resolve().parent
try:
    long_description = (THIS_DIR / 'README.md').read_text()
except FileNotFoundError:
    long_description = description

# VERSION is set in Cargo.toml
cargo = Path(THIS_DIR / 'Cargo.toml').read_text()
VERSION = re.search('version *= *"(.*?)"', cargo).group(1)

setup(
    name='rtoml',
    version=VERSION,
    description=description,
    long_description=long_description,
    long_description_content_type='text/markdown',
    author='Samuel Colvin',
    author_email='s@muelcolvin.com',
    url='https://github.com/samuelcolvin/rtoml',
    license='MIT',
    package_data={'rtoml': ['py.typed']},
    python_requires='>=3.7',
    rust_extensions=[RustExtension('rtoml._rtoml', binding=Binding.PyO3)],
    packages=['rtoml'],
    zip_safe=False,
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3 :: Only',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Intended Audience :: Developers',
        'Intended Audience :: Information Technology',
        'Intended Audience :: System Administrators',
        'License :: OSI Approved :: MIT License',
        'Operating System :: Unix',
        'Operating System :: POSIX :: Linux',
        'Environment :: Console',
        'Environment :: MacOS X',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'Topic :: Internet',
    ],
)
