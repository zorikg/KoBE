#!/bin/bash

CURR_DIR=$PWD
BASE_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
CODE_DIR="${BASE_DIR}/code"
DATA_DIR="${BASE_DIR}/data"

cd "${DATA_DIR}"
unzip "${DATA_DIR}/annotations.zip"
cd "${CURR_DIR}"


python "${CODE_DIR}/eval_main.py"

