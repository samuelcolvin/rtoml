#!/bin/bash
set -ex
pip install -U pip setuptools setuptools-rust
curl https://sh.rustup.rs -sSf | sh -s -- --default-toolchain=nightly --profile=minimal -y
