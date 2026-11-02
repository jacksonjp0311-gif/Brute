"""Lean source freeze for study-057: writes experiments/COMMIT_ORDER_057.json (ledger events from preregistration_057) and
experiments/BRUTE_SOURCE_FREEZE_057.json (plan and source/scoring/test/release-tooling/deviation hashes; FILES = the 056 list, the
remaining 056 files (commit order, freeze, deviations #185 and #187, the sealed 056 main SEAL, its recount, reference, API checks,
tests and gates), plan 057 and the new 057 files). Plan 057 freeze rule: caps, bound, arms, workers, the stop rule (conflict-only,
hook None, 900 s hard kill), the cover20 settings, the LEN_R RNG, the oracle rule and the cut variable n57 = brute_study_057.N57 are
part of the freeze. Refuses overwrite. New file; built from scripts/make_freeze_056.py (frozen).
  PYTHONPATH=. python scripts/make_freeze_057.py"""
import json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from experiments.brute_common_057 import (PLAN,FREEZE,sha,write_new,C20,B20,BOUND,ALL_ARMS,WORKERS,HARD_KILL_S,STOP_RULE,COVER,LEN_RNG,ORACLE_RULE)
from scripts.make_freeze_056 import FILES as FILES_056
ORDER=ROOT/'experiments/COMMIT_ORDER_057.json'
STUDY='BRUTE-0540-SCALE20-COVERFIRST-057'
NEW=['brute/api/cover20.py','brute/release_version_0540.py','experiments/brute_common_057.py','experiments/brute_study_057.py',
     'scripts/check_seeds_057.py','scripts/api_checks_057.py','scripts/recount_057.py','scripts/run_reference_057.py',
     'scripts/make_gates_057.py','scripts/make_freeze_057.py','scripts/push_checkpoint_057.py','scripts/study057_storage.py',
     'scripts/verify_release_0540.py','scripts/run_tests_0540.py','scripts/prefreeze_smoke_057.py','tests/test_cover20.py',
     'tests/test_scripts_057.py','tests/test_release_0540.py','docs/research/BRUTE_DEVIATIONS_057_188.md',
     'results/diag-057/SEEDCHECK_057.json','results/diag-057/PREFREEZE_SMOKE_GATES_057.json']
FILES=list(FILES_056)+['experiments/COMMIT_ORDER_056.json','experiments/BRUTE_SOURCE_FREEZE_056.json',
       'docs/research/BRUTE_DEVIATIONS_056_187.md',
       'results/study-056/main/SEAL.json','results/study-056/main/RECOUNT_056.json','results/study-056/main/REFERENCE_056.json',
       'results/study-056/API_CHECKS_056.json','results/study-056/TEST_SUITE_056.json',
       'results/study-056/GATES_056.json','experiments/BRUTE_PLAN_057.json']+NEW


def entries():
    L=[json.loads(x) for x in (ROOT/'results/RESEARCH_LEDGER.jsonl').read_text().splitlines() if x.strip()]
    i0=next(i for i,e in enumerate(L) if e.get('event')=='preregistration_057')
    return [{'event':e['event'],'commit':e.get('commit'),'note_time':str(e.get('note',''))[:25]} for e in L[i0:]]


def main():
    from experiments import brute_study_057 as ST
    ev=entries()
    write_new(ORDER,{'schema':'brute.commit-order.v1','study':STUDY,'order':[e['event'] for e in ev],'entries':ev})
    files={f:sha(ROOT/f) for f in sorted(set(FILES))}
    write_new(FREEZE,{'schema':'brute.source-freeze.v1','study':STUDY,'process':'lean','plan_sha256':sha(PLAN),
                      'caps':[C20,B20],'max_chunks':None,'bound':BOUND,'arms':list(ALL_ARMS),'workers':WORKERS,
                      'stop':{'hard_kill_s':HARD_KILL_S,'stop_rule':STOP_RULE},'cover':COVER,'len_rng':LEN_RNG,'oracle_rule':ORACLE_RULE,
                      'n57':ST.N57,'sha256_files':files})
    print(len(files),'files frozen; caps',[C20,B20],'N57',ST.N57)


if __name__=='__main__':main()
