#!/usr/bin/env bash
set -e

cargo build

cp target/debug/librtoml.so rtoml.so

echo "========================================================"
python3.7 run.py
