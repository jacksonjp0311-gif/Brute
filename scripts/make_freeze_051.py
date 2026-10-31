"""Lean source freeze for study-051: writes experiments/COMMIT_ORDER_051.json (ledger events from preregistration_051) and
experiments/BRUTE_SOURCE_FREEZE_051.json (plan and source/scoring/test/release-tooling/deviation hashes; FILES = the 050 list, the
remaining 050 files (plan, commit order, freeze, deviations #173 and #174, the sealed 050 main SEAL, its API checks, tests and
gates), and the new 051 files). Plan 051 freeze_rule: caps per key (C20, B20, C, B12, B12N), eps, eps_bar, delta, the k rule
(certify16n.py, hashed), max_chunks None, the phase workers (A 4, B 8) and the case lists (n_noise12_b = brute_study_051.N12B,
n_compat = NCOMPAT) are part of the freeze. Refuses overwrite. New file; built from scripts/make_freeze_050.py (frozen).
  PYTHONPATH=. python scripts/make_freeze_051.py"""
import json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from experiments.brute_common_051 import PLAN,FREEZE,sha,write_new,CAPS_OF,EPS,EPS_BAR,DELTA,NOISE_OF,WORKERS_A,WORKERS_B
from scripts.make_freeze_050 import FILES as FILES_050
ORDER=ROOT/'experiments/COMMIT_ORDER_051.json'
STUDY='BRUTE-0480-SCALE20-ISOLATED-SYMBREAK-NOISE12-051'
NEW=['brute/api/certify16s.py','brute/release_version_0480.py','experiments/brute_common_051.py','experiments/brute_study_051.py',
     'scripts/check_seeds_051.py','scripts/api_checks_051.py','scripts/recount_051.py','scripts/run_reference_051.py','scripts/make_gates_051.py',
     'scripts/make_freeze_051.py','scripts/push_checkpoint_051.py','scripts/study051_storage.py','scripts/verify_release_0480.py',
     'scripts/run_tests_0480.py','scripts/prefreeze_smoke_051.py','tests/test_certify16s.py','tests/test_scripts_051.py','tests/test_release_0480.py',
     'docs/research/BRUTE_DEVIATIONS_051_175.md','results/diag-051/SEEDCHECK_051.json','results/diag-051/PREFREEZE_SMOKE_GATES_051.json']
FILES=list(FILES_050)+['experiments/BRUTE_PLAN_050.json','experiments/COMMIT_ORDER_050.json','experiments/BRUTE_SOURCE_FREEZE_050.json',
       'docs/research/BRUTE_DEVIATIONS_050_173.md','docs/research/BRUTE_DEVIATIONS_050_174.md','results/study-050/main/SEAL.json',
       'results/study-050/API_CHECKS_050.json','results/study-050/TEST_SUITE_050.json','results/study-050/GATES_050.json']+NEW


def entries():
    L=[json.loads(x) for x in (ROOT/'results/RESEARCH_LEDGER.jsonl').read_text().splitlines() if x.strip()]
    i0=next(i for i,e in enumerate(L) if e.get('event')=='preregistration_051')
    return [{'event':e['event'],'commit':e.get('commit'),'note_time':str(e.get('note',''))[:25]} for e in L[i0:]]


def main():
    from experiments import brute_study_051 as ST
    ev=entries()
    write_new(ORDER,{'schema':'brute.commit-order.v1','study':STUDY,'order':[e['event'] for e in ev],'entries':ev})
    files={f:sha(ROOT/f) for f in sorted(set(FILES))}
    write_new(FREEZE,{'schema':'brute.source-freeze.v1','study':STUDY,'process':'lean','plan_sha256':sha(PLAN),
                      'caps':{k:list(v) for k,v in CAPS_OF.items()},'max_chunks':None,
                      'noise':{'eps':EPS,'eps_bar':EPS_BAR,'delta':DELTA,'arms':{k:list(v) for k,v in NOISE_OF.items()}},
                      'workers':{'A':WORKERS_A,'B':WORKERS_B},'n_noise12_b':ST.N12B,'n_compat':ST.NCOMPAT,'sha256_files':files})
    print(len(files),'files frozen; caps',CAPS_OF,'N12B',ST.N12B,'NCOMPAT',ST.NCOMPAT)


if __name__=='__main__':main()
