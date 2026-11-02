"""Lean source freeze for study-061: writes experiments/COMMIT_ORDER_061.json (ledger events from preregistration_061) and
experiments/BRUTE_SOURCE_FREEZE_061.json (plan and source/scoring/test/release-tooling/deviation hashes; FILES = the 060 list, the
remaining 060 files (commit order, freeze, deviations #194 and #195, the sealed 060 main SEAL, its recount, reference, API checks,
tests and gates), plan 061, the exploratory budget probe and the new 061 files). Plan 061 freeze rule: caps [C, B61, K], read_bits,
arms, arm spec (key, family, bound), workers, the stop rule (conflict-only, hook None, case hard kill), the probe sha and the cut
variables n24 = brute_study_061.N24, n24b = N24B and n32 = N32 are part of the freeze. Refuses overwrite. New file; built from
scripts/make_freeze_060.py (frozen).
  PYTHONPATH=. python scripts/make_freeze_061.py"""
import json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from experiments.brute_common_061 import (PLAN,FREEZE,PROBE,sha,write_new,C61,B61,K61,READ_BITS,ALL_ARMS,ARM_SPEC,WORKERS,HARD_KILL_S,STOP_RULE)
from scripts.make_freeze_060 import FILES as FILES_060
ORDER=ROOT/'experiments/COMMIT_ORDER_061.json'
STUDY='BRUTE-0580-BUDGET24W-061'
NEW=['brute/release_version_0580.py','experiments/brute_common_061.py',
     'experiments/brute_study_061.py','scripts/check_seeds_061.py','scripts/api_checks_061.py','scripts/recount_061.py',
     'scripts/run_reference_061.py','scripts/make_gates_061.py','scripts/make_freeze_061.py','scripts/study061_storage.py',
     'scripts/verify_release_0580.py','scripts/run_tests_0580.py','scripts/prefreeze_smoke_061.py',
     'tests/test_scripts_061.py','tests/test_release_0580.py','docs/research/BRUTE_DEVIATIONS_061_196.md',
     'results/diag-061/SEEDCHECK_061.json','results/diag-061/PREFREEZE_SMOKE_GATES_061.json',
     'scripts/probe_061.py','results/diag-061/BUDGET_PROBE_061.json']
FILES=list(FILES_060)+['experiments/COMMIT_ORDER_060.json','experiments/BRUTE_SOURCE_FREEZE_060.json',
       'docs/research/BRUTE_DEVIATIONS_060_194.md','docs/research/BRUTE_DEVIATIONS_060_195.md',
       'results/study-060/main/SEAL.json','results/study-060/main/RECOUNT_060.json','results/study-060/main/REFERENCE_060.json',
       'results/study-060/API_CHECKS_060.json','results/study-060/TEST_SUITE_060.json',
       'results/study-060/GATES_060.json','experiments/BRUTE_PLAN_061.json']+NEW


def entries():
    L=[json.loads(x) for x in (ROOT/'results/RESEARCH_LEDGER.jsonl').read_text().splitlines() if x.strip()]
    i0=next(i for i,e in enumerate(L) if e.get('event')=='preregistration_061')
    return [{'event':e['event'],'commit':e.get('commit'),'note_time':str(e.get('note',''))[:25]} for e in L[i0:]]


def main():
    from experiments import brute_study_061 as ST
    ev=entries()
    write_new(ORDER,{'schema':'brute.commit-order.v1','study':STUDY,'order':[e['event'] for e in ev],'entries':ev})
    files={f:sha(ROOT/f) for f in sorted(set(FILES))}
    write_new(FREEZE,{'schema':'brute.source-freeze.v1','study':STUDY,'process':'lean','plan_sha256':sha(PLAN),'probe_sha256':sha(PROBE),
                      'caps':[C61,B61,K61],'max_chunks':None,'read_bits':READ_BITS,'arms':list(ALL_ARMS),'arm_spec':ARM_SPEC,
                      'workers':WORKERS,'stop':{'hard_kill_s':HARD_KILL_S,'stop_rule':STOP_RULE},
                      'n24':ST.N24,'n24b':ST.N24B,'n32':ST.N32,'sha256_files':files})
    print(len(files),'files frozen; caps',[C61,B61,K61],'N24',ST.N24,'N24B',ST.N24B,'N32',ST.N32)


if __name__=='__main__':main()
