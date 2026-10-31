"""Lean source freeze for study-054: writes experiments/COMMIT_ORDER_054.json (ledger events from preregistration_054) and
experiments/BRUTE_SOURCE_FREEZE_054.json (plan, amendment 054a and source/scoring/test/release-tooling/deviation hashes; FILES = the
053 list, the remaining 053 files (plan, commit order, freeze, deviations #179 and #180, the sealed 053 main SEAL, its recount,
reference, API checks, tests and gates), plan 054, amendment 054a and the new 054 files). Plan 054 freeze rule: caps per key, bounds,
arms, workers {total 8, scale20t 4, compat20t 4}, the stop rule (conflict-only, hook None, 900 s hard kill), max_chunks None and the
cut variables n_scale20t = brute_study_054.N20T and n_compat20t = brute_study_054.NC20T are part of the freeze. Refuses overwrite.
New file; built from scripts/make_freeze_053.py (frozen).
  PYTHONPATH=. python scripts/make_freeze_054.py"""
import json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from experiments.brute_common_054 import (PLAN,AMEND,FREEZE,sha,write_new,CAPS_OF,BOUND_OF,ARMS_OF,WORKERS,WORKERS_S,WORKERS_C,HARD_KILL_S,STOP_RULE)
from scripts.make_freeze_053 import FILES as FILES_053
ORDER=ROOT/'experiments/COMMIT_ORDER_054.json'
STUDY='BRUTE-0510-SCALE20-TREECOLOR-054'
NEW=['brute/api/certify20t.py','brute/release_version_0510.py','experiments/brute_common_054.py','experiments/brute_study_054.py',
     'scripts/check_seeds_054.py','scripts/api_checks_054.py','scripts/recount_054.py','scripts/run_reference_054.py','scripts/make_gates_054.py',
     'scripts/make_freeze_054.py','scripts/push_checkpoint_054.py','scripts/study054_storage.py','scripts/verify_release_0510.py',
     'scripts/run_tests_0510.py','scripts/prefreeze_smoke_054.py','tests/test_certify20t.py','tests/test_scripts_054.py','tests/test_release_0510.py',
     'docs/research/BRUTE_DEVIATIONS_054_181.md','results/diag-054/SEEDCHECK_054.json','results/diag-054/PREFREEZE_SMOKE_GATES_054.json']
FILES=list(FILES_053)+['experiments/BRUTE_PLAN_053.json','experiments/COMMIT_ORDER_053.json','experiments/BRUTE_SOURCE_FREEZE_053.json',
       'docs/research/BRUTE_DEVIATIONS_053_179.md','docs/research/BRUTE_DEVIATIONS_053_180.md',
       'results/study-053/main/SEAL.json','results/study-053/main/RECOUNT_053.json','results/study-053/main/REFERENCE_053.json',
       'results/study-053/API_CHECKS_053.json','results/study-053/TEST_SUITE_053.json',
       'results/study-053/GATES_053.json','experiments/BRUTE_PLAN_054.json','experiments/BRUTE_PLAN_054a.json']+NEW


def entries():
    L=[json.loads(x) for x in (ROOT/'results/RESEARCH_LEDGER.jsonl').read_text().splitlines() if x.strip()]
    i0=next(i for i,e in enumerate(L) if e.get('event')=='preregistration_054')
    return [{'event':e['event'],'commit':e.get('commit'),'note_time':str(e.get('note',''))[:25]} for e in L[i0:]]


def main():
    from experiments import brute_study_054 as ST
    ev=entries()
    write_new(ORDER,{'schema':'brute.commit-order.v1','study':STUDY,'order':[e['event'] for e in ev],'entries':ev})
    files={f:sha(ROOT/f) for f in sorted(set(FILES))}
    write_new(FREEZE,{'schema':'brute.source-freeze.v1','study':STUDY,'amended_by':'experiments/BRUTE_PLAN_054a.json','process':'lean',
                      'plan_sha256':sha(PLAN),'amendment_sha256':sha(AMEND),'caps':{k:list(v) for k,v in CAPS_OF.items()},'max_chunks':None,
                      'bounds':BOUND_OF,'arms':{k:list(v) for k,v in ARMS_OF.items()},
                      'workers':{'total':WORKERS,'scale20t':WORKERS_S,'compat20t':WORKERS_C},
                      'stop':{'hard_kill_s':HARD_KILL_S,'stop_rule':STOP_RULE},
                      'n_scale20t':ST.N20T,'n_compat20t':ST.NC20T,'sha256_files':files})
    print(len(files),'files frozen; caps',CAPS_OF,'N20T',ST.N20T,'NC20T',ST.NC20T)


if __name__=='__main__':main()
