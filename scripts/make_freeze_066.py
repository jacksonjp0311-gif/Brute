"""Lean source freeze for study-066: writes experiments/COMMIT_ORDER_066.json (ledger events from preregistration_066; the v0.62.0
release-closing events were ledgered BEFORE preregistration_066, so nothing is excluded) and experiments/BRUTE_SOURCE_FREEZE_066.json
(plan and source/scoring/test/release-tooling/deviation hashes; FILES = the 065 list, the remaining 065 files (commit order, freeze,
deviations #204 and #205, the sealed 065 main SEAL, its recount, reference, API checks, tests and gates), plan 066, the new API module
brute/api/certify32s.py with its test and the new 066 files). Plan 066 freeze rule: caps [C, B, K], read_bits, node cap, per-arm
bound and key, delta, arms, arm noise, noise rng, workers, the stop dict (incl. job_kill_s) and the case counts n20, n24 and n_s30b
are part of the freeze. Refuses overwrite. New file; built from scripts/make_freeze_065.py (frozen).
  PYTHONPATH=. python scripts/make_freeze_066.py"""
import json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from experiments.brute_common_066 import (PLAN,FREEZE,sha,write_new,C66,B66,K66,READ_BITS,NODE_CAP,ARM_BOUND,ARM_KEY,DELTA,ALL_ARMS,ARM_NOISE,
                                          NOISE_RNG,WORKERS,HARD_KILL_S,JOB_KILL_S,STOP_RULE,MAIN_CAP_S)
from scripts.make_freeze_065 import FILES as FILES_065
ORDER=ROOT/'experiments/COMMIT_ORDER_066.json'
STUDY='BRUTE-0630-SEQNOISE24-066'
NEW=['brute/api/certify32s.py','tests/test_certify32s.py','brute/release_version_0630.py','experiments/brute_common_066.py',
     'experiments/brute_study_066.py','experiments/worlds_066.py','scripts/check_seeds_066.py',
     'scripts/api_checks_066.py','scripts/recount_066.py','scripts/run_reference_066.py','scripts/make_gates_066.py','scripts/make_freeze_066.py',
     'scripts/study066_storage.py','scripts/verify_release_0630.py','scripts/run_tests_0630.py','scripts/prefreeze_smoke_066.py',
     'tests/test_scripts_066.py','tests/test_release_0630.py','docs/research/BRUTE_DEVIATIONS_066_206.md',
     'results/diag-066/SEEDCHECK_066.json','results/diag-066/PREFREEZE_SMOKE_GATES_066.json']
FILES=list(FILES_065)+['experiments/COMMIT_ORDER_065.json','experiments/BRUTE_SOURCE_FREEZE_065.json',
       'docs/research/BRUTE_DEVIATIONS_065_204.md','docs/research/BRUTE_DEVIATIONS_065_205.md',
       'results/study-065/main/SEAL.json','results/study-065/main/RECOUNT_065.json','results/study-065/main/REFERENCE_065.json',
       'results/study-065/API_CHECKS_065.json','results/study-065/TEST_SUITE_065.json',
       'results/study-065/GATES_065.json','experiments/BRUTE_PLAN_066.json']+NEW


def entries():
    L=[json.loads(x) for x in (ROOT/'results/RESEARCH_LEDGER.jsonl').read_text().splitlines() if x.strip()]
    i0=next(i for i,e in enumerate(L) if e.get('event')=='preregistration_066')
    return [{'event':e['event'],'commit':e.get('commit'),'note_time':str(e.get('note',''))[:25]} for e in L[i0:]]


def main():
    from experiments import brute_study_066 as ST
    ev=entries()
    write_new(ORDER,{'schema':'brute.commit-order.v1','study':STUDY,'order':[e['event'] for e in ev],'entries':ev,'excluded_prev_release':[]})
    files={f:sha(ROOT/f) for f in sorted(set(FILES))}
    write_new(FREEZE,{'schema':'brute.source-freeze.v1','study':STUDY,'process':'lean','plan_sha256':sha(PLAN),'caps':[C66,B66,K66],'max_chunks':None,
                      'read_bits':READ_BITS,'node_cap':NODE_CAP,'arm_bound':ARM_BOUND,'arm_key':ARM_KEY,'delta':DELTA,'arms':list(ALL_ARMS),
                      'arm_noise':ARM_NOISE,'noise_rng':NOISE_RNG,'workers':WORKERS,
                      'stop':{'hard_kill_s':HARD_KILL_S,'job_kill_s':JOB_KILL_S,'stop_rule':STOP_RULE,'main_cap_s':MAIN_CAP_S},
                      'n20':ST.N20,'n24':ST.N24,'n_s30b':ST.N_S30B,'sha256_files':files})
    print(len(files),'files frozen; caps',[C66,B66,K66],'N20',ST.N20,'N24',ST.N24,'N_S30B',ST.N_S30B)


if __name__=='__main__':main()
