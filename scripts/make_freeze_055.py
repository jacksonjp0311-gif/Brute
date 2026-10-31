"""Lean source freeze for study-055: writes experiments/COMMIT_ORDER_055.json (ledger events from preregistration_055) and
experiments/BRUTE_SOURCE_FREEZE_055.json (plan and source/scoring/test/release-tooling/deviation hashes; FILES = the
054 list, the remaining 054 files (plan, commit order, freeze, deviations #181 and #182, the sealed 054 main SEAL, its recount,
reference, API checks, tests and gates), plan 055 and the new 055 files). Plan 055 freeze rule: caps per key, bounds,
arms, workers {total 8, scale20t 4, compat20t 4}, the stop rule (conflict-only, hook None, 900 s hard kill), max_chunks None, the cube depth (certify20c.CUBE_DEPTH = 5) and the
cut variables n_scale20t = brute_study_055.N20C and n_compat20t = brute_study_055.NC20C are part of the freeze. Refuses overwrite.
New file; built from scripts/make_freeze_054.py (frozen).
  PYTHONPATH=. python scripts/make_freeze_055.py"""
import json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from experiments.brute_common_055 import (PLAN,FREEZE,sha,write_new,CAPS_OF,BOUND_OF,ARMS_OF,WORKERS,WORKERS_S,WORKERS_C,HARD_KILL_S,STOP_RULE,CUBE_DEPTH)
from scripts.make_freeze_054 import FILES as FILES_054
ORDER=ROOT/'experiments/COMMIT_ORDER_055.json'
STUDY='BRUTE-0520-SCALE20-CUBECONQUER-055'
NEW=['brute/api/certify20c.py','brute/release_version_0520.py','experiments/brute_common_055.py','experiments/brute_study_055.py',
     'scripts/check_seeds_055.py','scripts/api_checks_055.py','scripts/recount_055.py','scripts/run_reference_055.py','scripts/cube_audit_055.py','scripts/make_gates_055.py',
     'scripts/make_freeze_055.py','scripts/push_checkpoint_055.py','scripts/study055_storage.py','scripts/verify_release_0520.py',
     'scripts/run_tests_0520.py','scripts/prefreeze_smoke_055.py','tests/test_certify20c.py','tests/test_scripts_055.py','tests/test_release_0520.py',
     'docs/research/BRUTE_DEVIATIONS_055_183.md','results/diag-055/SEEDCHECK_055.json','results/diag-055/PREFREEZE_SMOKE_GATES_055.json']
FILES=list(FILES_054)+['experiments/BRUTE_PLAN_054.json','experiments/BRUTE_PLAN_054a.json','experiments/COMMIT_ORDER_054.json','experiments/BRUTE_SOURCE_FREEZE_054.json',
       'docs/research/BRUTE_DEVIATIONS_054_181.md','docs/research/BRUTE_DEVIATIONS_054_182.md',
       'results/study-054/main/SEAL.json','results/study-054/main/RECOUNT_054.json','results/study-054/main/REFERENCE_054.json',
       'results/study-054/API_CHECKS_054.json','results/study-054/TEST_SUITE_054.json',
       'results/study-054/GATES_054.json','experiments/BRUTE_PLAN_055.json']+NEW


def entries():
    L=[json.loads(x) for x in (ROOT/'results/RESEARCH_LEDGER.jsonl').read_text().splitlines() if x.strip()]
    i0=next(i for i,e in enumerate(L) if e.get('event')=='preregistration_055')
    return [{'event':e['event'],'commit':e.get('commit'),'note_time':str(e.get('note',''))[:25]} for e in L[i0:]]


def main():
    from experiments import brute_study_055 as ST
    ev=entries()
    write_new(ORDER,{'schema':'brute.commit-order.v1','study':STUDY,'order':[e['event'] for e in ev],'entries':ev})
    files={f:sha(ROOT/f) for f in sorted(set(FILES))}
    write_new(FREEZE,{'schema':'brute.source-freeze.v1','study':STUDY,'process':'lean',
                      'plan_sha256':sha(PLAN),'caps':{k:list(v) for k,v in CAPS_OF.items()},'max_chunks':None,
                      'bounds':BOUND_OF,'arms':{k:list(v) for k,v in ARMS_OF.items()},
                      'workers':{'total':WORKERS,'scale20t':WORKERS_S,'compat20t':WORKERS_C},
                      'stop':{'hard_kill_s':HARD_KILL_S,'stop_rule':STOP_RULE},'cube_depth':CUBE_DEPTH,
                      'n_scale20t':ST.N20C,'n_compat20t':ST.NC20C,'sha256_files':files})
    print(len(files),'files frozen; caps',CAPS_OF,'N20C',ST.N20C,'NC20C',ST.NC20C)


if __name__=='__main__':main()
