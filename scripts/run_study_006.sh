#!/usr/bin/env bash
# Resumable study-006 run (process step 7). Each step is skipped when its output already exists; every output
# refuses to overwrite. Run with: nohup bash scripts/run_study_006.sh > /tmp/p6/run006.log 2>&1 &
set -euo pipefail
cd "$(dirname "$0")/.."
PY=${PY:-/workspace/bgr/venv/bin/python}; W=${W:-6}; D=results/study-006
mkdir -p "$D"
stamp(){ date --iso-8601=seconds; }
echo "[$(stamp)] start"
if [ ! -f "$D/CALIBRATION_006.json" ]; then echo "[$(stamp)] calibrate"; $PY -m experiments.brute_calibrate_006 --workers $W; fi
if [ ! -f "$D/SEAL.json" ]; then echo "[$(stamp)] study"; $PY -m experiments.brute_study_006 --workers $W; fi
if [ ! -f "$D/RESULTS.json.gz" ]; then echo "[$(stamp)] pack"; $PY scripts/study006_storage.py pack; fi
echo "[$(stamp)] RUN_DONE"
