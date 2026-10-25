#!/usr/bin/env bash
# Resumable study-007 runs (process step 6). Every step is skipped when its output exists; every output refuses to
# overwrite; study / calibration / scaling checkpoint per case, so an interrupted step resumes where it stopped.
# The ledger 'run_start' entry is appended BEFORE this script starts and 'run_end' after RUN_DONE (by the operator).
# Run with: nohup bash scripts/run_study_007.sh > /tmp/w7/run007.log 2>&1 &
set -euo pipefail
cd "$(dirname "$0")/.."
PY=${PY:-/workspace/bgr/venv/bin/python}; W=${W:-6}; D=results/study-007
mkdir -p "$D/calibration-repro" "$D/repro"
stamp(){ date --iso-8601=seconds; }
echo "[$(stamp)] start"
if [ ! -f "$D/CALIBRATION_007.json" ]; then echo "[$(stamp)] calibrate"; $PY -m experiments.brute_calibrate_007 --workers $W; fi
if [ ! -f "$D/calibration-repro/CALIBRATION_007.json" ]; then echo "[$(stamp)] calibrate (G12 repro)"; $PY -m experiments.brute_calibrate_007 --workers $W --output "$D/calibration-repro/CALIBRATION_007.json"; fi
if [ ! -f "$D/SEAL.json" ]; then echo "[$(stamp)] study"; $PY -m experiments.brute_study_007 --workers $W; fi
if [ ! -f "$D/SCALING_007.json" ]; then echo "[$(stamp)] scaling"; $PY -m experiments.scaling_007 --workers $W; fi
if [ ! -f "$D/repro/SEAL.json" ]; then echo "[$(stamp)] repro subset (every 3rd job)"; $PY -m experiments.brute_study_007 --workers $W --every 3 --offset 0 --output "$D/repro"; fi
if [ ! -f "$D/RESULTS.json.gz" ]; then echo "[$(stamp)] pack"; $PY scripts/study007_storage.py pack; fi
echo "[$(stamp)] RUN_DONE"
