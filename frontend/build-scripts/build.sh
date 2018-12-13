#!/usr/bin/env bash

export LC_ALL="C.UTF-8"
export LANG="C.UTF-8"

set -e
PYENV=/tmp/.pyenv

python3 -m venv ${PYENV}
${PYENV}/bin/pip3 install -U -r requirements.txt
${PYENV}/bin/python3 build.py build --verbose
${PYENV}/bin/python3 build.py update_latest
