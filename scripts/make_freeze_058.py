"""Lean source freeze for study-058: writes experiments/COMMIT_ORDER_058.json (ledger events from preregistration_058) and
experiments/BRUTE_SOURCE_FREEZE_058.json (plan and source/scoring/test/release-tooling/deviation hashes; FILES = the 057 list, the
remaining 057 files (commit order, freeze, deviations #188 and #189, the sealed 057 main SEAL, its recount, reference, API checks,
tests and gates), plan 058 and the new 058 files). Plan 058 freeze rule: caps [C, B, K], bound, arms, arm families, workers, the stop
rule (conflict-only, hook None, 900 s hard kill), the emission RNG and the cut variable n58 = brute_study_058.N58 are part of the
freeze. Refuses overwrite. New file; built from scripts/make_freeze_057.py (frozen).
  PYTHONPATH=. python scripts/make_freeze_058.py"""
import json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from experiments.brute_common_058 import (PLAN,FREEZE,sha,write_new,C58,B58,K58,BOUND,ALL_ARMS,ARM_FAMILY,WORKERS,HARD_KILL_S,STOP_RULE,EMISSION_RNG)
from scripts.make_freeze_057 import FILES as FILES_057
ORDER=ROOT/'experiments/COMMIT_ORDER_058.json'
STUDY='BRUTE-0550-READBITS-058'
NEW=['brute/api/certify20b.py','brute/release_version_0550.py','experiments/worlds_058.py','experiments/brute_common_058.py',
     'experiments/brute_study_058.py','scripts/check_seeds_058.py','scripts/api_checks_058.py','scripts/recount_058.py',
     'scripts/run_reference_058.py','scripts/make_gates_058.py','scripts/make_freeze_058.py','scripts/study058_storage.py',
     'scripts/verify_release_0550.py','scripts/run_tests_0550.py','scripts/prefreeze_smoke_058.py','tests/test_certify20b.py',
     'tests/test_scripts_058.py','tests/test_release_0550.py','docs/research/BRUTE_DEVIATIONS_058_190.md',
     'results/diag-058/SEEDCHECK_058.json','results/diag-058/PREFREEZE_SMOKE_GATES_058.json']
FILES=list(FILES_057)+['experiments/COMMIT_ORDER_057.json','experiments/BRUTE_SOURCE_FREEZE_057.json',
       'docs/research/BRUTE_DEVIATIONS_057_188.md','docs/research/BRUTE_DEVIATIONS_057_189.md',
       'results/study-057/main/SEAL.json','results/study-057/main/RECOUNT_057.json','results/study-057/main/REFERENCE_057.json',
       'results/study-057/API_CHECKS_057.json','results/study-057/TEST_SUITE_057.json',
       'results/study-057/GATES_057.json','experiments/BRUTE_PLAN_058.json']+NEW


def entries():
    L=[json.loads(x) for x in (ROOT/'results/RESEARCH_LEDGER.jsonl').read_text().splitlines() if x.strip()]
    i0=next(i for i,e in enumerate(L) if e.get('event')=='preregistration_058')
    return [{'event':e['event'],'commit':e.get('commit'),'note_time':str(e.get('note',''))[:25]} for e in L[i0:]]


def main():
    from experiments import brute_study_058 as ST
    ev=entries()
    write_new(ORDER,{'schema':'brute.commit-order.v1','study':STUDY,'order':[e['event'] for e in ev],'entries':ev})
    files={f:sha(ROOT/f) for f in sorted(set(FILES))}
    write_new(FREEZE,{'schema':'brute.source-freeze.v1','study':STUDY,'process':'lean','plan_sha256':sha(PLAN),
                      'caps':[C58,B58,K58],'max_chunks':None,'bound':BOUND,'arms':list(ALL_ARMS),'arm_family':ARM_FAMILY,'workers':WORKERS,
                      'stop':{'hard_kill_s':HARD_KILL_S,'stop_rule':STOP_RULE},'emission_rng':EMISSION_RNG,
                      'n58':ST.N58,'sha256_files':files})
    print(len(files),'files frozen; caps',[C58,B58,K58],'N58',ST.N58)


if __name__=='__main__':main()
