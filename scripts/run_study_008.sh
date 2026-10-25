#!/usr/bin/env bash
# Resumable study-008 held-out run (BRUTE_PLAN_008 process step 7). Every step is skipped when its output exists; every
# output refuses to overwrite; study / xcheck / GMC checkpoint per case, so an interrupted step resumes where it stopped.
# The ledger 'run_start' entry is appended BEFORE this script starts and 'run_end' after RUN_DONE (by the operator).
# Run with: nohup bash scripts/run_study_008.sh > /tmp/w8/run008.log 2>&1 &
# After the study, three streams run in parallel (8 CPUs): A = GX2' xcheck then R_dev_xcheck_007 (every 4th case, reported
# only); B = GMC 2x2 then GMC breadth (reported only) under ONE shared 6 h counting cap; C = second implementation (G11) +
# B5 enumeration (GX2' iv), then the every-3rd repro study (G12) and the GMC recount on it (G12).
set -euo pipefail
cd "$(dirname "$0")/.."
PY=${PY:-/workspace/bgr/venv/bin/python}; export PYTHONPATH=.; D=${D:-results/study-008}
# Dry-run hooks for the pre-freeze smoke of this script only (unset in the held-out run): SMOKE=1 adds --smoke to the
# study runs, LIMIT=n adds --limit n to every step. The held-out run uses neither.
SM=""; LM=""; [ -n "${SMOKE:-}" ] && SM="--smoke"; [ -n "${LIMIT:-}" ] && LM="--limit $LIMIT"
mkdir -p "$D/repro"
stamp(){ date --iso-8601=seconds; }
echo "[$(stamp)] start"
if [ ! -f "$D/SEAL.json" ]; then echo "[$(stamp)] study"; $PY -m experiments.brute_study_008 --output "$D" --workers 7 $SM $LM; fi
streamA(){
  if [ ! -f "$D/XCHECK_008.json" ]; then echo "[$(stamp)] A xcheck"; $PY -m experiments.v060_xcheck --results "$D/RESULTS.json" --output "$D/XCHECK_008.json" --checkpoint "$D/XCHECK_008_CHECKPOINT.jsonl" --workers 3 $LM; fi
  if [ ! -f "$D/R_DEV_XCHECK_007.json" ]; then echo "[$(stamp)] A R_dev_xcheck_007"; $PY scripts/study007_storage.py restore >/dev/null; $PY -m experiments.v060_xcheck --results results/study-007/RESULTS.json --arms B5,BM5,BP5 --plan experiments/BRUTE_PLAN_007.json --tau7-from-results --every 4 --output "$D/R_DEV_XCHECK_007.json" --checkpoint "$D/R_DEV_XCHECK_007_CHECKPOINT.jsonl" --workers 3 $LM; fi
  echo "[$(stamp)] A done"
}
streamB(){
  [ -f "$D/GMC_BUDGET_START" ] || date +%s > "$D/GMC_BUDGET_START"; BS=$(cat "$D/GMC_BUDGET_START")
  if [ ! -f "$D/GMC_COUNT_008.json" ]; then echo "[$(stamp)] B GMC 2x2"; $PY -m experiments.make_count_008 --results "$D/RESULTS.json" --output "$D/GMC_COUNT_008.json" --checkpoint "$D/GMC_COUNT_008_CHECKPOINT.jsonl" --workers 3 --budget-start "$BS" $LM > /tmp/w8/gmc2x2.log 2>&1; fi
  if [ ! -f "$D/GMC_BREADTH_008.json" ]; then echo "[$(stamp)] B GMC breadth"; $PY -m experiments.make_count_008 --breadth --results "$D/RESULTS.json" --output "$D/GMC_BREADTH_008.json" --checkpoint "$D/GMC_BREADTH_008_CHECKPOINT.jsonl" --workers 3 --budget-start "$BS" $LM > /tmp/w8/gmcbreadth.log 2>&1; fi
  echo "[$(stamp)] B done"
}
streamC(){
  echo "[$(stamp)] C second implementation + B5 enumeration"; $PY scripts/make_second_impl_008.py --results-dir "$D" --workers 2 $LM
  if [ ! -f "$D/repro/SEAL.json" ]; then echo "[$(stamp)] C repro subset (every 3rd job)"; $PY -m experiments.brute_study_008 --workers 2 --every 3 --offset 0 --output "$D/repro" $SM $LM; fi
  [ -f "$D/repro/GMC_BUDGET_START" ] || date +%s > "$D/repro/GMC_BUDGET_START"
  if [ ! -f "$D/repro/GMC_COUNT_008.json" ]; then echo "[$(stamp)] C GMC recount on repro"; $PY -m experiments.make_count_008 --results "$D/repro/RESULTS.json" --output "$D/repro/GMC_COUNT_008.json" --checkpoint "$D/repro/GMC_COUNT_008_CHECKPOINT.jsonl" --workers 2 --budget-start "$(cat "$D/repro/GMC_BUDGET_START")" $LM > /tmp/w8/gmcrepro.log 2>&1; fi
  echo "[$(stamp)] C done"
}
mkdir -p /tmp/w8
streamA > /tmp/w8/streamA.log 2>&1 & PA=$!
streamB > /tmp/w8/streamB.log 2>&1 & PB=$!
streamC > /tmp/w8/streamC.log 2>&1 & PC=$!
RC=0; wait $PA || RC=1; wait $PB || RC=1; wait $PC || RC=1
cat /tmp/w8/streamA.log /tmp/w8/streamB.log /tmp/w8/streamC.log | grep '^\[' || true
if [ $RC -ne 0 ]; then echo "[$(stamp)] a stream failed (see /tmp/w8/stream*.log); re-run this script to resume"; exit 1; fi
if [ ! -f "$D/RESULTS.json.gz" ]; then echo "[$(stamp)] pack"; [ "$D" = results/study-008 ] && $PY scripts/study008_storage.py pack; fi
echo "[$(stamp)] RUN_DONE"
