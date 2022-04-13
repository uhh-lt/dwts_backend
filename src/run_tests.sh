#!/bin/bash

set -e
set -x

export PYTHONPATH=${PWD}

poetry run pytest --cov=. --cov-report=html test "${@}"
