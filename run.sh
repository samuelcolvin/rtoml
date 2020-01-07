#!/usr/bin/env bash
set -e

cargo build -q

cp target/debug/librtoml.so rtoml.so

echo "========================================================"
python3 run.py
