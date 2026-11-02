"""Lean source freeze for study-062: writes experiments/COMMIT_ORDER_062.json (ledger events from preregistration_062) and
experiments/BRUTE_SOURCE_FREEZE_062.json (plan and source/scoring/test/release-tooling/deviation hashes; FILES = the 061 list, the
remaining 061 files (commit order, freeze, deviations #196 and #197, the sealed 061 main SEAL, its recount, reference, API checks,
tests and gates), plan 062, the exploratory budget probe, the new API module brute/api/certify20w.py with its test and the new 062
files). Plan 062 freeze rule: caps [C, B62, K], read_bits, bound, probe word, arms, arm spec (key, family, bound, api), workers, the
stop rule (conflict-only, hook None, case hard kill), the probe sha and the cut variables n_seeds = brute_study_062.N_SEEDS and
n_w2b = N_W2B are part of the freeze. Refuses overwrite. New file; built from scripts/make_freeze_061.py (frozen).
  PYTHONPATH=. python scripts/make_freeze_062.py"""
import json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from experiments.brute_common_062 import (PLAN,FREEZE,PROBE,sha,write_new,C62,B62,K62,READ_BITS,BOUND,PROBE_WORD,ALL_ARMS,ARM_SPEC,WORKERS,
                                          HARD_KILL_S,STOP_RULE)
from scripts.make_freeze_061 import FILES as FILES_061
ORDER=ROOT/'experiments/COMMIT_ORDER_062.json'
STUDY='BRUTE-0590-WINDOW2B20-062'
NEW=['brute/api/certify20w.py','tests/test_certify20w.py','brute/release_version_0590.py','experiments/brute_common_062.py',
     'experiments/brute_study_062.py','scripts/check_seeds_062.py','scripts/api_checks_062.py','scripts/recount_062.py',
     'scripts/run_reference_062.py','scripts/make_gates_062.py','scripts/make_freeze_062.py','scripts/study062_storage.py',
     'scripts/verify_release_0590.py','scripts/run_tests_0590.py','scripts/prefreeze_smoke_062.py',
     'tests/test_scripts_062.py','tests/test_release_0590.py','docs/research/BRUTE_DEVIATIONS_062_198.md',
     'results/diag-062/SEEDCHECK_062.json','results/diag-062/PREFREEZE_SMOKE_GATES_062.json',
     'scripts/probe_062.py','results/diag-062/BUDGET_PROBE_062.json']
FILES=list(FILES_061)+['experiments/COMMIT_ORDER_061.json','experiments/BRUTE_SOURCE_FREEZE_061.json',
       'docs/research/BRUTE_DEVIATIONS_061_196.md','docs/research/BRUTE_DEVIATIONS_061_197.md',
       'results/study-061/main/SEAL.json','results/study-061/main/RECOUNT_061.json','results/study-061/main/REFERENCE_061.json',
       'results/study-061/API_CHECKS_061.json','results/study-061/TEST_SUITE_061.json',
       'results/study-061/GATES_061.json','experiments/BRUTE_PLAN_062.json']+NEW


def entries():
    L=[json.loads(x) for x in (ROOT/'results/RESEARCH_LEDGER.jsonl').read_text().splitlines() if x.strip()]
    i0=next(i for i,e in enumerate(L) if e.get('event')=='preregistration_062')
    return [{'event':e['event'],'commit':e.get('commit'),'note_time':str(e.get('note',''))[:25]} for e in L[i0:]]


def main():
    from experiments import brute_study_062 as ST
    ev=entries()
    write_new(ORDER,{'schema':'brute.commit-order.v1','study':STUDY,'order':[e['event'] for e in ev],'entries':ev})
    files={f:sha(ROOT/f) for f in sorted(set(FILES))}
    write_new(FREEZE,{'schema':'brute.source-freeze.v1','study':STUDY,'process':'lean','plan_sha256':sha(PLAN),'probe_sha256':sha(PROBE),
                      'caps':[C62,B62,K62],'max_chunks':None,'read_bits':READ_BITS,'bound':BOUND,'probe_word':list(PROBE_WORD),
                      'arms':list(ALL_ARMS),'arm_spec':ARM_SPEC,'workers':WORKERS,'stop':{'hard_kill_s':HARD_KILL_S,'stop_rule':STOP_RULE},
                      'n_seeds':ST.N_SEEDS,'n_w2b':ST.N_W2B,'sha256_files':files})
    print(len(files),'files frozen; caps',[C62,B62,K62],'N_SEEDS',ST.N_SEEDS,'N_W2B',ST.N_W2B)


if __name__=='__main__':main()
