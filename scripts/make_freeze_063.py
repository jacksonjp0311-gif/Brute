"""Lean source freeze for study-063: writes experiments/COMMIT_ORDER_063.json (ledger events from preregistration_063) and
experiments/BRUTE_SOURCE_FREEZE_063.json (plan and source/scoring/test/release-tooling/deviation hashes; FILES = the 062 list, the
remaining 062 files (commit order, freeze, deviations #198 and #199, the sealed 062 main SEAL, its recount, reference, API checks,
tests and gates), plan 063, the capability probe and clique diagnostic with their scripts, the new API module
brute/api/certify20p.py with its test and the new 063 files, including both seedcheck attempts). Plan 063 freeze rule: caps
[C, B63, K], read_bits, bound, node cap, arms, arm spec, workers, the stop rule, the probe sha and the cut variables
n_seeds = brute_study_063.N_SEEDS and n_p2b = N_P2B are part of the freeze. Refuses overwrite. New file; built from
scripts/make_freeze_062.py (frozen).
  PYTHONPATH=. python scripts/make_freeze_063.py"""
import json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from experiments.brute_common_063 import (PLAN,FREEZE,PROBE,sha,write_new,C63,B63,K63,READ_BITS,BOUND,NODE_CAP,ALL_ARMS,ARM_SPEC,WORKERS,
                                          HARD_KILL_S,STOP_RULE)
from scripts.make_freeze_062 import FILES as FILES_062
ORDER=ROOT/'experiments/COMMIT_ORDER_063.json'
STUDY='BRUTE-0600-ANCHOR2B20-063'
NEW=['brute/api/certify20p.py','tests/test_certify20p.py','brute/release_version_0600.py','experiments/brute_common_063.py',
     'experiments/brute_study_063.py','scripts/check_seeds_063.py','scripts/check_seeds_063_m.py','scripts/api_checks_063.py',
     'scripts/recount_063.py','scripts/run_reference_063.py','scripts/make_gates_063.py','scripts/make_freeze_063.py',
     'scripts/study063_storage.py','scripts/verify_release_0600.py','scripts/run_tests_0600.py','scripts/prefreeze_smoke_063.py',
     'tests/test_scripts_063.py','tests/test_release_0600.py','docs/research/BRUTE_DEVIATIONS_063_200.md',
     'results/diag-063/SEEDCHECK_063_ATTEMPT1_FAIL.json','results/diag-063/SEEDCHECK_063.json',
     'results/diag-063/PREFREEZE_SMOKE_GATES_063.json','scripts/probe_063.py','scripts/diag_clique_063.py',
     'results/diag-063/CAPABILITY_PROBE_063.json','results/diag-063/CLIQUE_DIAG_063.json']
FILES=list(FILES_062)+['experiments/COMMIT_ORDER_062.json','experiments/BRUTE_SOURCE_FREEZE_062.json',
       'docs/research/BRUTE_DEVIATIONS_062_198.md','docs/research/BRUTE_DEVIATIONS_062_199.md',
       'results/study-062/main/SEAL.json','results/study-062/main/RECOUNT_062.json','results/study-062/main/REFERENCE_062.json',
       'results/study-062/API_CHECKS_062.json','results/study-062/TEST_SUITE_062.json',
       'results/study-062/GATES_062.json','experiments/BRUTE_PLAN_063.json']+NEW


def entries():
    L=[json.loads(x) for x in (ROOT/'results/RESEARCH_LEDGER.jsonl').read_text().splitlines() if x.strip()]
    i0=next(i for i,e in enumerate(L) if e.get('event')=='preregistration_063')
    return [{'event':e['event'],'commit':e.get('commit'),'note_time':str(e.get('note',''))[:25]} for e in L[i0:]]


def main():
    from experiments import brute_study_063 as ST
    ev=entries()
    write_new(ORDER,{'schema':'brute.commit-order.v1','study':STUDY,'order':[e['event'] for e in ev],'entries':ev})
    files={f:sha(ROOT/f) for f in sorted(set(FILES))}
    write_new(FREEZE,{'schema':'brute.source-freeze.v1','study':STUDY,'process':'lean','plan_sha256':sha(PLAN),'probe_sha256':sha(PROBE),
                      'caps':[C63,B63,K63],'max_chunks':None,'read_bits':READ_BITS,'bound':BOUND,'node_cap':NODE_CAP,
                      'arms':list(ALL_ARMS),'arm_spec':ARM_SPEC,'workers':WORKERS,'stop':{'hard_kill_s':HARD_KILL_S,'stop_rule':STOP_RULE},
                      'n_seeds':ST.N_SEEDS,'n_p2b':ST.N_P2B,'sha256_files':files})
    print(len(files),'files frozen; caps',[C63,B63,K63],'N_SEEDS',ST.N_SEEDS,'N_P2B',ST.N_P2B)


if __name__=='__main__':main()
