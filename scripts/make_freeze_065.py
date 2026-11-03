"""Lean source freeze for study-065: writes experiments/COMMIT_ORDER_065.json (ledger events from preregistration_065, EXCLUDING the
three v0.61.0 release-closing events release_0610, fresh_clone_verify_064 and handoff_released_064, which were ledgered on the 065
branch after the 065 preregistration but belong to the 064 study; deviation #204) and experiments/BRUTE_SOURCE_FREEZE_065.json
(plan and source/scoring/test/release-tooling/deviation hashes; FILES = the 064 list, the remaining 064 files (commit order, freeze,
deviations #202 and #203, the sealed 064 main SEAL, its recount, reference, API checks, tests and gates), plan 065, the new API module
brute/api/certify20s.py with its test and the new 065 files). Plan 065 freeze rule: caps [C, B, K], read_bits, node cap, bound,
delta, arms, arm noise, noise rng, workers, the stop dict and the cut variables n_seeds, n_s20, n_s10 and n_s30b are part of the
freeze. Refuses overwrite. New file; built from scripts/make_freeze_064.py (frozen).
  PYTHONPATH=. python scripts/make_freeze_065.py"""
import json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from experiments.brute_common_065 import (PLAN,FREEZE,sha,write_new,C65,B65,K65,READ_BITS,NODE_CAP,BOUND,DELTA,ALL_ARMS,ARM_NOISE,NOISE_RNG,
                                          WORKERS,HARD_KILL_S,STOP_RULE,MAIN_CAP_S)
from scripts.make_freeze_064 import FILES as FILES_064
ORDER=ROOT/'experiments/COMMIT_ORDER_065.json'
STUDY='BRUTE-0620-SEQNOISE2B20-065'
PREV_RELEASE=('release_0610','fresh_clone_verify_064','handoff_released_064')
NEW=['brute/api/certify20s.py','tests/test_certify20s.py','brute/release_version_0620.py','experiments/brute_common_065.py',
     'experiments/brute_study_065.py','experiments/worlds_065.py','scripts/check_seeds_065.py',
     'scripts/api_checks_065.py','scripts/recount_065.py','scripts/run_reference_065.py','scripts/make_gates_065.py','scripts/make_freeze_065.py',
     'scripts/study065_storage.py','scripts/verify_release_0620.py','scripts/run_tests_0620.py','scripts/prefreeze_smoke_065.py',
     'tests/test_scripts_065.py','tests/test_release_0620.py','docs/research/BRUTE_DEVIATIONS_065_204.md',
     'results/diag-065/SEEDCHECK_065.json','results/diag-065/PREFREEZE_SMOKE_GATES_065.json']
FILES=list(FILES_064)+['experiments/COMMIT_ORDER_064.json','experiments/BRUTE_SOURCE_FREEZE_064.json',
       'docs/research/BRUTE_DEVIATIONS_064_202.md','docs/research/BRUTE_DEVIATIONS_064_203.md',
       'results/study-064/main/SEAL.json','results/study-064/main/RECOUNT_064.json','results/study-064/main/REFERENCE_064.json',
       'results/study-064/API_CHECKS_064.json','results/study-064/TEST_SUITE_064.json',
       'results/study-064/GATES_064.json','experiments/BRUTE_PLAN_065.json']+NEW


def entries():
    L=[json.loads(x) for x in (ROOT/'results/RESEARCH_LEDGER.jsonl').read_text().splitlines() if x.strip()]
    i0=next(i for i,e in enumerate(L) if e.get('event')=='preregistration_065')
    return [{'event':e['event'],'commit':e.get('commit'),'note_time':str(e.get('note',''))[:25]} for e in L[i0:] if e.get('event') not in PREV_RELEASE]


def main():
    from experiments import brute_study_065 as ST
    ev=entries()
    write_new(ORDER,{'schema':'brute.commit-order.v1','study':STUDY,'order':[e['event'] for e in ev],'entries':ev,'excluded_prev_release':list(PREV_RELEASE)})
    files={f:sha(ROOT/f) for f in sorted(set(FILES))}
    write_new(FREEZE,{'schema':'brute.source-freeze.v1','study':STUDY,'process':'lean','plan_sha256':sha(PLAN),'caps':[C65,B65,K65],'max_chunks':None,
                      'read_bits':READ_BITS,'node_cap':NODE_CAP,'bound':BOUND,'delta':DELTA,'arms':list(ALL_ARMS),'arm_noise':ARM_NOISE,
                      'noise_rng':NOISE_RNG,'workers':WORKERS,'stop':{'hard_kill_s':HARD_KILL_S,'stop_rule':STOP_RULE,'main_cap_s':MAIN_CAP_S},
                      'n_seeds':ST.N_SEEDS,'n_s20':ST.N_S20,'n_s10':ST.N_S10,'n_s30b':ST.N_S30B,'sha256_files':files})
    print(len(files),'files frozen; caps',[C65,B65,K65],'N_SEEDS',ST.N_SEEDS,'N_S20',ST.N_S20,'N_S10',ST.N_S10,'N_S30B',ST.N_S30B)


if __name__=='__main__':main()
