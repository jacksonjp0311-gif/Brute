"""Lean source freeze for study-064: writes experiments/COMMIT_ORDER_064.json (ledger events from preregistration_064) and
experiments/BRUTE_SOURCE_FREEZE_064.json (plan and source/scoring/test/release-tooling/deviation hashes; FILES = the 063 list, the
remaining 063 files (commit order, freeze, deviations #200 and #201, the sealed 063 main SEAL, its recount, reference, API checks,
tests and gates), plan 064, the capability probe and the reference diagnostic with their scripts and the pinned reference module,
the new API module brute/api/certify32p.py with its test and the new 064 files). Plan 064 freeze rule: caps [C, B64, K], read_bits,
node cap, arms, arm spec, workers, the stop dict (case kill, stop rule, main-run cap), the probe and reference-diagnostic shas and
the cut variables n_seeds, n_b24 and n_p20b are part of the freeze. Refuses overwrite. New file; built from
scripts/make_freeze_063.py (frozen).
  PYTHONPATH=. python scripts/make_freeze_064.py"""
import json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from experiments.brute_common_064 import (PLAN,FREEZE,PROBE,REFDIAG,sha,write_new,C64,B64,K64,READ_BITS,NODE_CAP,ALL_ARMS,ARM_SPEC,WORKERS,
                                          HARD_KILL_S,STOP_RULE,MAIN_CAP_S)
from scripts.make_freeze_063 import FILES as FILES_063
ORDER=ROOT/'experiments/COMMIT_ORDER_064.json'
STUDY='BRUTE-0610-SCALE2B24-064'
NEW=['brute/api/certify32p.py','tests/test_certify32p.py','brute/release_version_0610.py','experiments/brute_common_064.py',
     'experiments/brute_study_064.py','experiments/worlds_064.py','experiments/v0610_reference.py','scripts/check_seeds_064.py',
     'scripts/api_checks_064.py','scripts/recount_064.py','scripts/run_reference_064.py','scripts/make_gates_064.py','scripts/make_freeze_064.py',
     'scripts/study064_storage.py','scripts/verify_release_0610.py','scripts/run_tests_0610.py','scripts/prefreeze_smoke_064.py',
     'tests/test_scripts_064.py','tests/test_release_0610.py','docs/research/BRUTE_DEVIATIONS_064_202.md',
     'results/diag-064/SEEDCHECK_064.json','results/diag-064/PREFREEZE_SMOKE_GATES_064.json','scripts/probe_064.py','scripts/diag_ref_064.py',
     'results/diag-064/CAPABILITY_PROBE_064.json','results/diag-064/REF_PIN_DIAG_064.json']
FILES=list(FILES_063)+['experiments/COMMIT_ORDER_063.json','experiments/BRUTE_SOURCE_FREEZE_063.json',
       'docs/research/BRUTE_DEVIATIONS_063_200.md','docs/research/BRUTE_DEVIATIONS_063_201.md',
       'results/study-063/main/SEAL.json','results/study-063/main/RECOUNT_063.json','results/study-063/main/REFERENCE_063.json',
       'results/study-063/API_CHECKS_063.json','results/study-063/TEST_SUITE_063.json',
       'results/study-063/GATES_063.json','experiments/BRUTE_PLAN_064.json']+NEW


def entries():
    L=[json.loads(x) for x in (ROOT/'results/RESEARCH_LEDGER.jsonl').read_text().splitlines() if x.strip()]
    i0=next(i for i,e in enumerate(L) if e.get('event')=='preregistration_064')
    return [{'event':e['event'],'commit':e.get('commit'),'note_time':str(e.get('note',''))[:25]} for e in L[i0:]]


def main():
    from experiments import brute_study_064 as ST
    ev=entries()
    write_new(ORDER,{'schema':'brute.commit-order.v1','study':STUDY,'order':[e['event'] for e in ev],'entries':ev})
    files={f:sha(ROOT/f) for f in sorted(set(FILES))}
    write_new(FREEZE,{'schema':'brute.source-freeze.v1','study':STUDY,'process':'lean','plan_sha256':sha(PLAN),'probe_sha256':sha(PROBE),
                      'refdiag_sha256':sha(REFDIAG),'caps':[C64,B64,K64],'max_chunks':None,'read_bits':READ_BITS,'node_cap':NODE_CAP,
                      'arms':list(ALL_ARMS),'arm_spec':ARM_SPEC,'workers':WORKERS,
                      'stop':{'hard_kill_s':HARD_KILL_S,'stop_rule':STOP_RULE,'main_cap_s':MAIN_CAP_S},
                      'n_seeds':ST.N_SEEDS,'n_b24':ST.N_B24,'n_p20b':ST.N_P20B,'sha256_files':files})
    print(len(files),'files frozen; caps',[C64,B64,K64],'N_SEEDS',ST.N_SEEDS,'N_B24',ST.N_B24,'N_P20B',ST.N_P20B)


if __name__=='__main__':main()
