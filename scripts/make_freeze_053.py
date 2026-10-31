"""Lean source freeze for study-053: writes experiments/COMMIT_ORDER_053.json (ledger events from preregistration_053) and
experiments/BRUTE_SOURCE_FREEZE_053.json (plan and source/scoring/test/release-tooling/deviation hashes; FILES = the 052 list, the
remaining 052 files (plan, commit order, freeze, deviations #177 and #178, the sealed 052 main SEAL, its recount, reference, API
checks, tests and gates), and the new 053 files). Plan 053 freeze rule: caps per key (C, B16N, B16, C20, B20), eps, eps_hi, eps_bar,
delta, the k rule (certify16n.py, hashed), max_chunks None, workers {total 8, A 7, B 1}, the part B stop rule (conflict-only, hook
None, 900 s hard kill) and the cut variables n_noise16_bar = brute_study_053.N16BAR and n_scale20c = brute_study_053.N20C are part
of the freeze. Refuses overwrite. New file; built from scripts/make_freeze_052.py (frozen).
  PYTHONPATH=. python scripts/make_freeze_053.py"""
import json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from experiments.brute_common_053 import (PLAN,FREEZE,sha,write_new,CAPS_OF,EPS,EPS_HI,EPS_BAR,DELTA,NOISE_OF,WORKERS,WORKERS_A,WORKERS_B,
                                          PART_B_KEYS,HARD_KILL_B_S,STOP_RULE)
from scripts.make_freeze_052 import FILES as FILES_052
ORDER=ROOT/'experiments/COMMIT_ORDER_053.json'
STUDY='BRUTE-0500-NOISE16-SCALE20-CONFLICTSTOP-053'
NEW=['brute/release_version_0500.py','experiments/brute_common_053.py','experiments/brute_study_053.py',
     'scripts/check_seeds_053.py','scripts/api_checks_053.py','scripts/recount_053.py','scripts/run_reference_053.py','scripts/make_gates_053.py',
     'scripts/make_freeze_053.py','scripts/push_checkpoint_053.py','scripts/study053_storage.py','scripts/verify_release_0500.py',
     'scripts/run_tests_0500.py','scripts/prefreeze_smoke_053.py','tests/test_scripts_053.py','tests/test_release_0500.py',
     'docs/research/BRUTE_DEVIATIONS_053_179.md','results/diag-053/SEEDCHECK_053.json','results/diag-053/PREFREEZE_SMOKE_GATES_053.json']
FILES=list(FILES_052)+['experiments/BRUTE_PLAN_052.json','experiments/COMMIT_ORDER_052.json','experiments/BRUTE_SOURCE_FREEZE_052.json',
       'docs/research/BRUTE_DEVIATIONS_052_177.md','docs/research/BRUTE_DEVIATIONS_052_178.md',
       'results/study-052/main/SEAL.json','results/study-052/main/RECOUNT_052.json','results/study-052/main/REFERENCE_052.json',
       'results/study-052/API_CHECKS_052.json','results/study-052/TEST_SUITE_052.json',
       'results/study-052/GATES_052.json','experiments/BRUTE_PLAN_053.json']+NEW


def entries():
    L=[json.loads(x) for x in (ROOT/'results/RESEARCH_LEDGER.jsonl').read_text().splitlines() if x.strip()]
    i0=next(i for i,e in enumerate(L) if e.get('event')=='preregistration_053')
    return [{'event':e['event'],'commit':e.get('commit'),'note_time':str(e.get('note',''))[:25]} for e in L[i0:]]


def main():
    from experiments import brute_study_053 as ST
    ev=entries()
    write_new(ORDER,{'schema':'brute.commit-order.v1','study':STUDY,'order':[e['event'] for e in ev],'entries':ev})
    files={f:sha(ROOT/f) for f in sorted(set(FILES))}
    write_new(FREEZE,{'schema':'brute.source-freeze.v1','study':STUDY,'process':'lean','plan_sha256':sha(PLAN),
                      'caps':{k:list(v) for k,v in CAPS_OF.items()},'max_chunks':None,
                      'noise':{'eps':EPS,'eps_hi':EPS_HI,'eps_bar':EPS_BAR,'delta':DELTA,'arms':{k:list(v) for k,v in NOISE_OF.items()}},
                      'workers':{'total':WORKERS,'A':WORKERS_A,'B':WORKERS_B},
                      'part_b':{'keys':list(PART_B_KEYS),'hard_kill_s':HARD_KILL_B_S,'stop_rule':STOP_RULE['B']},
                      'n_noise16_bar':ST.N16BAR,'n_scale20c':ST.N20C,'sha256_files':files})
    print(len(files),'files frozen; caps',CAPS_OF,'N16BAR',ST.N16BAR,'N20C',ST.N20C)


if __name__=='__main__':main()
