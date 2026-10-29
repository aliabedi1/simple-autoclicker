#!/bin/sh
set -eu
cd -- "$(dirname -- "$0")"
if [ -x .venv/bin/python ]; then
    exec .venv/bin/python autoclicker.py
fi
exec python3 autoclicker.py
