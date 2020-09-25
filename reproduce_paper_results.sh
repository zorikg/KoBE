#!/bin/bash

CURR_DIR=$PWD
BASE_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
CODE_DIR="${BASE_DIR}/code"
DATA_DIR="${BASE_DIR}/data"

mkdir -p "${DATA_DIR}"
mkdir -p "${DATA_DIR}"/"wmt19_metric_task_results"

curl -o "${DATA_DIR}"/"annotations.zip" http://storage.googleapis.com/gresearch/kobe/data/annotations.zip
curl -o "${DATA_DIR}"/"wmt19_metric_task_results"/"sys-level_scores_metrics.csv" http://storage.googleapis.com/gresearch/kobe/data/wmt19_metric_task_results/sys-level_scores_metrics.csv

cd "${DATA_DIR}"
unzip "${DATA_DIR}/annotations.zip"
cd "${CURR_DIR}"

python "${CODE_DIR}/eval_main.py"

