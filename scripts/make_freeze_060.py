"""Lean source freeze for study-060: writes experiments/COMMIT_ORDER_060.json (ledger events from preregistration_060) and
experiments/BRUTE_SOURCE_FREEZE_060.json (plan and source/scoring/test/release-tooling/deviation hashes; FILES = the 059 list, the
remaining 059 files (commit order, freeze, deviations #192 and #193, the sealed 059 main SEAL, its recount, reference, API checks,
tests and gates), plan 060, the exploratory probes and the new 060 files). Plan 060 freeze rule: caps [C, B, K], read_bits, arms,
arm spec (key, family, bound), workers, the stop rule (conflict-only, hook None, 3600 s hard kill) and the cut variables
n24 = brute_study_060.N24 and n32 = brute_study_060.N32 are part of the freeze. Refuses overwrite. New file; built from
scripts/make_freeze_059.py (frozen).
  PYTHONPATH=. python scripts/make_freeze_060.py"""
import json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from experiments.brute_common_060 import (PLAN,FREEZE,sha,write_new,C60,B60,K60,READ_BITS,ALL_ARMS,ARM_SPEC,WORKERS,HARD_KILL_S,STOP_RULE)
from scripts.make_freeze_059 import FILES as FILES_059
ORDER=ROOT/'experiments/COMMIT_ORDER_060.json'
STUDY='BRUTE-0570-SCALE24W-060'
NEW=['brute/api/certify32b.py','brute/release_version_0570.py','experiments/worlds_060.py','experiments/brute_common_060.py',
     'experiments/brute_study_060.py','scripts/check_seeds_060.py','scripts/api_checks_060.py','scripts/recount_060.py',
     'scripts/run_reference_060.py','scripts/make_gates_060.py','scripts/make_freeze_060.py','scripts/study060_storage.py',
     'scripts/verify_release_0570.py','scripts/run_tests_0570.py','scripts/prefreeze_smoke_060.py','tests/test_certify32b.py',
     'tests/test_scripts_060.py','tests/test_release_0570.py','docs/research/BRUTE_DEVIATIONS_060_194.md',
     'results/diag-060/SEEDCHECK_060.json','results/diag-060/PREFREEZE_SMOKE_GATES_060.json',
     'scripts/probe_060.py','scripts/probe_060_ref.py','results/diag-060/BUDGET_PROBE_060.json','results/diag-060/REFERENCE_PROBE_060.json']
FILES=list(FILES_059)+['experiments/COMMIT_ORDER_059.json','experiments/BRUTE_SOURCE_FREEZE_059.json',
       'docs/research/BRUTE_DEVIATIONS_059_192.md','docs/research/BRUTE_DEVIATIONS_059_193.md',
       'results/study-059/main/SEAL.json','results/study-059/main/RECOUNT_059.json','results/study-059/main/REFERENCE_059.json',
       'results/study-059/API_CHECKS_059.json','results/study-059/TEST_SUITE_059.json',
       'results/study-059/GATES_059.json','experiments/BRUTE_PLAN_060.json']+NEW


def entries():
    L=[json.loads(x) for x in (ROOT/'results/RESEARCH_LEDGER.jsonl').read_text().splitlines() if x.strip()]
    i0=next(i for i,e in enumerate(L) if e.get('event')=='preregistration_060')
    return [{'event':e['event'],'commit':e.get('commit'),'note_time':str(e.get('note',''))[:25]} for e in L[i0:]]


def main():
    from experiments import brute_study_060 as ST
    ev=entries()
    write_new(ORDER,{'schema':'brute.commit-order.v1','study':STUDY,'order':[e['event'] for e in ev],'entries':ev})
    files={f:sha(ROOT/f) for f in sorted(set(FILES))}
    write_new(FREEZE,{'schema':'brute.source-freeze.v1','study':STUDY,'process':'lean','plan_sha256':sha(PLAN),
                      'caps':[C60,B60,K60],'max_chunks':None,'read_bits':READ_BITS,'arms':list(ALL_ARMS),'arm_spec':ARM_SPEC,
                      'workers':WORKERS,'stop':{'hard_kill_s':HARD_KILL_S,'stop_rule':STOP_RULE},
                      'n24':ST.N24,'n32':ST.N32,'sha256_files':files})
    print(len(files),'files frozen; caps',[C60,B60,K60],'N24',ST.N24,'N32',ST.N32)


if __name__=='__main__':main()
