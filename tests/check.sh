#!/bin/bash

DISABLE=invalid-name
DISABLE+=,attribute-defined-outside-init
DISABLE+=,too-few-public-methods
DISABLE+=,protected-access
DISABLE+=,too-many-arguments
DISABLE+=,missing-class-docstring

[ -z $VIRTUAL_ENV ] && source .venv/bin/activate
export PYTHONPATH="../src"
python -m black ../src .
python -m pylint --disable=$DISABLE ../src/gpio.py
python -m mypy ../src/gpio.py
python -m pytest -rP

