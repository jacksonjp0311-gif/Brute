"""Lean source freeze for study-052: writes experiments/COMMIT_ORDER_052.json (ledger events from preregistration_052) and
experiments/BRUTE_SOURCE_FREEZE_052.json (plan and source/scoring/test/release-tooling/deviation hashes; FILES = the 051 list, the
remaining 051 files (plan, commit order, freeze, deviations #175, #176 and its addendum, the sealed 051 main SEAL, its API checks,
tests and gates), and the new 052 files). Plan 052 freeze_rule: caps per key (C, B12N, B12), eps, eps_hi, eps_bar, delta, the
k rule (certify16n.py, hashed), max_chunks None, workers 8 and the cut variable n_noise12_bar = brute_study_052.N12BAR are part
of the freeze. Refuses overwrite. New file; built from scripts/make_freeze_051.py (frozen).
  PYTHONPATH=. python scripts/make_freeze_052.py"""
import json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from experiments.brute_common_052 import PLAN,FREEZE,sha,write_new,CAPS_OF,EPS,EPS_HI,EPS_BAR,DELTA,NOISE_OF,WORKERS
from scripts.make_freeze_051 import FILES as FILES_051
ORDER=ROOT/'experiments/COMMIT_ORDER_052.json'
STUDY='BRUTE-0490-CERTIFY16N-NOISE12-052'
NEW=['brute/release_version_0490.py','experiments/brute_common_052.py','experiments/brute_study_052.py',
     'scripts/check_seeds_052.py','scripts/api_checks_052.py','scripts/recount_052.py','scripts/run_reference_052.py','scripts/make_gates_052.py',
     'scripts/make_freeze_052.py','scripts/push_checkpoint_052.py','scripts/study052_storage.py','scripts/verify_release_0490.py',
     'scripts/run_tests_0490.py','scripts/prefreeze_smoke_052.py','tests/test_scripts_052.py','tests/test_release_0490.py',
     'docs/research/BRUTE_DEVIATIONS_052_177.md','results/diag-052/SEEDCHECK_052.json','results/diag-052/PREFREEZE_SMOKE_GATES_052.json']
FILES=list(FILES_051)+['experiments/BRUTE_PLAN_051.json','experiments/COMMIT_ORDER_051.json','experiments/BRUTE_SOURCE_FREEZE_051.json',
       'docs/research/BRUTE_DEVIATIONS_051_175.md','docs/research/BRUTE_DEVIATIONS_051_176.md','docs/research/BRUTE_DEVIATIONS_051_176_ADDENDUM_1.md',
       'results/study-051/main/SEAL.json','results/study-051/API_CHECKS_051.json','results/study-051/TEST_SUITE_051.json',
       'results/study-051/GATES_051.json','experiments/BRUTE_PLAN_052.json']+NEW


def entries():
    L=[json.loads(x) for x in (ROOT/'results/RESEARCH_LEDGER.jsonl').read_text().splitlines() if x.strip()]
    i0=next(i for i,e in enumerate(L) if e.get('event')=='preregistration_052')
    return [{'event':e['event'],'commit':e.get('commit'),'note_time':str(e.get('note',''))[:25]} for e in L[i0:]]


def main():
    from experiments import brute_study_052 as ST
    ev=entries()
    write_new(ORDER,{'schema':'brute.commit-order.v1','study':STUDY,'order':[e['event'] for e in ev],'entries':ev})
    files={f:sha(ROOT/f) for f in sorted(set(FILES))}
    write_new(FREEZE,{'schema':'brute.source-freeze.v1','study':STUDY,'process':'lean','plan_sha256':sha(PLAN),
                      'caps':{k:list(v) for k,v in CAPS_OF.items()},'max_chunks':None,
                      'noise':{'eps':EPS,'eps_hi':EPS_HI,'eps_bar':EPS_BAR,'delta':DELTA,'arms':{k:list(v) for k,v in NOISE_OF.items()}},
                      'workers':WORKERS,'n_noise12_bar':ST.N12BAR,'sha256_files':files})
    print(len(files),'files frozen; caps',CAPS_OF,'N12BAR',ST.N12BAR)


if __name__=='__main__':main()
