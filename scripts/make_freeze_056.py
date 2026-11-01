"""Lean source freeze for study-056: writes experiments/COMMIT_ORDER_056.json (ledger events from preregistration_056) and
experiments/BRUTE_SOURCE_FREEZE_056.json (plan and source/scoring/test/release-tooling/deviation hashes; FILES = the 055 list, the
remaining 055 files (plan 055 is already listed; commit order, freeze, deviations #183 and #184, the 055 status addendum, the sealed
055 main SEAL, its recount, reference, API checks, tests and gates), plan 056 and the new 056 files). Plan 056 freeze rule: caps per
key, bounds, arms, workers {total 8, scale20t 4, compat20t 4}, the stop rule (conflict-only, hook None, 900 s hard kill), max_chunks
None, the hypothesis-round limit (certify20l.HYP_ROUNDS) and the cut variables n_scale20t = brute_study_056.N20L and
n_compat20t = brute_study_056.NC20L are part of the freeze. Refuses overwrite.
New file; built from scripts/make_freeze_055.py (frozen).
  PYTHONPATH=. python scripts/make_freeze_056.py"""
import json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from experiments.brute_common_056 import (PLAN,FREEZE,sha,write_new,CAPS_OF,BOUND_OF,ARMS_OF,WORKERS,WORKERS_S,WORKERS_C,HARD_KILL_S,STOP_RULE,HYP_ROUNDS)
from scripts.make_freeze_055 import FILES as FILES_055
ORDER=ROOT/'experiments/COMMIT_ORDER_056.json'
STUDY='BRUTE-0530-SCALE20-LSTAR-056'
NEW=['brute/api/certify20l.py','brute/release_version_0530.py','experiments/brute_common_056.py','experiments/brute_study_056.py',
     'scripts/check_seeds_056.py','scripts/api_checks_056.py','scripts/recount_056.py','scripts/run_reference_056.py','scripts/table_audit_056.py',
     'scripts/make_gates_056.py','scripts/make_freeze_056.py','scripts/push_checkpoint_056.py','scripts/study056_storage.py',
     'scripts/verify_release_0530.py','scripts/run_tests_0530.py','scripts/prefreeze_smoke_056.py','tests/test_certify20l.py',
     'tests/test_scripts_056.py','tests/test_release_0530.py','docs/research/BRUTE_DEVIATIONS_056_185.md',
     'results/diag-056/SEEDCHECK_056.json','results/diag-056/PREFREEZE_SMOKE_GATES_056.json']
FILES=list(FILES_055)+['experiments/COMMIT_ORDER_055.json','experiments/BRUTE_SOURCE_FREEZE_055.json',
       'docs/research/BRUTE_DEVIATIONS_055_183.md','docs/research/BRUTE_DEVIATIONS_055_184.md','docs/research/BRUTE_ADDENDUM_055_STATUS.md',
       'results/study-055/main/SEAL.json','results/study-055/main/RECOUNT_055.json','results/study-055/main/REFERENCE_055.json',
       'results/study-055/API_CHECKS_055.json','results/study-055/TEST_SUITE_055.json',
       'results/study-055/GATES_055.json','experiments/BRUTE_PLAN_056.json']+NEW


def entries():
    L=[json.loads(x) for x in (ROOT/'results/RESEARCH_LEDGER.jsonl').read_text().splitlines() if x.strip()]
    i0=next(i for i,e in enumerate(L) if e.get('event')=='preregistration_056')
    return [{'event':e['event'],'commit':e.get('commit'),'note_time':str(e.get('note',''))[:25]} for e in L[i0:]]


def main():
    from experiments import brute_study_056 as ST
    ev=entries()
    write_new(ORDER,{'schema':'brute.commit-order.v1','study':STUDY,'order':[e['event'] for e in ev],'entries':ev})
    files={f:sha(ROOT/f) for f in sorted(set(FILES))}
    write_new(FREEZE,{'schema':'brute.source-freeze.v1','study':STUDY,'process':'lean',
                      'plan_sha256':sha(PLAN),'caps':{k:list(v) for k,v in CAPS_OF.items()},'max_chunks':None,
                      'bounds':BOUND_OF,'arms':{k:list(v) for k,v in ARMS_OF.items()},
                      'workers':{'total':WORKERS,'scale20t':WORKERS_S,'compat20t':WORKERS_C},
                      'stop':{'hard_kill_s':HARD_KILL_S,'stop_rule':STOP_RULE},'hyp_rounds':HYP_ROUNDS,
                      'n_scale20t':ST.N20L,'n_compat20t':ST.NC20L,'sha256_files':files})
    print(len(files),'files frozen; caps',CAPS_OF,'N20L',ST.N20L,'NC20L',ST.NC20L,'hyp_rounds',HYP_ROUNDS)


if __name__=='__main__':main()
