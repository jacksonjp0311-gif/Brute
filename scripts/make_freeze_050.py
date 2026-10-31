"""Lean source freeze for study-050: writes experiments/COMMIT_ORDER_050.json (ledger events from preregistration_050) and
experiments/BRUTE_SOURCE_FREEZE_050.json (plan and source/scoring/test/release-tooling/deviation hashes; FILES = the 049 list, the
remaining 049 files (plan, commit order, freeze, deviations #171 and #172, the sealed 049 main SEAL, its API checks, tests and
gates), and the new 050 files). Plan 050 freeze_rule: C, B20, B12, eps, eps_bar, delta, the k rule (certify16n.py, hashed),
max_chunks defaults and the case lists (n_scale20_b = brute_study_050.N20B, n_noise12_b = N12B) are part of the freeze. Refuses
overwrite. New file; built from scripts/make_freeze_049.py (frozen).
  PYTHONPATH=. python scripts/make_freeze_050.py"""
import json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from experiments.brute_common_050 import PLAN,FREEZE,sha,write_new,C50,BUDGET_OF,EPS,EPS_BAR,DELTA,NOISE_OF
from scripts.make_freeze_049 import FILES as FILES_049
ORDER=ROOT/'experiments/COMMIT_ORDER_050.json'
NEW=['brute/api/certify16n.py','brute/release_version_0470.py','experiments/brute_common_050.py','experiments/brute_study_050.py','experiments/worlds_050.py',
     'scripts/check_seeds_050.py','scripts/api_checks_050.py','scripts/recount_050.py','scripts/run_reference_050.py','scripts/make_gates_050.py',
     'scripts/make_freeze_050.py','scripts/push_checkpoint_050.py','scripts/study050_storage.py','scripts/verify_release_0470.py',
     'scripts/run_tests_0470.py','scripts/prefreeze_smoke_050.py','tests/test_certify16n.py','tests/test_scripts_050.py','tests/test_release_0470.py',
     'docs/research/BRUTE_DEVIATIONS_050_173.md','results/diag-050/SEEDCHECK_050.json','results/diag-050/PREFREEZE_SMOKE_GATES_050.json']
FILES=list(FILES_049)+['experiments/BRUTE_PLAN_049.json','experiments/COMMIT_ORDER_049.json','experiments/BRUTE_SOURCE_FREEZE_049.json',
       'docs/research/BRUTE_DEVIATIONS_049_171.md','docs/research/BRUTE_DEVIATIONS_049_172.md','results/study-049/main/SEAL.json',
       'results/study-049/API_CHECKS_049.json','results/study-049/TEST_SUITE_049.json','results/study-049/GATES_049.json']+NEW


def entries():
    L=[json.loads(x) for x in (ROOT/'results/RESEARCH_LEDGER.jsonl').read_text().splitlines() if x.strip()]
    i0=next(i for i,e in enumerate(L) if e.get('event')=='preregistration_050')
    return [{'event':e['event'],'commit':e.get('commit'),'note_time':str(e.get('note',''))[:25]} for e in L[i0:]]


def main():
    from experiments import brute_study_050 as ST
    ev=entries()
    write_new(ORDER,{'schema':'brute.commit-order.v1','study':'BRUTE-0470-SCALE20-REPLICATION-NOISE12-050','order':[e['event'] for e in ev],'entries':ev})
    files={f:sha(ROOT/f) for f in sorted(set(FILES))}
    write_new(FREEZE,{'schema':'brute.source-freeze.v1','study':'BRUTE-0470-SCALE20-REPLICATION-NOISE12-050','process':'lean','plan_sha256':sha(PLAN),
                      'conflict_cap':C50,'budget_conflicts':dict(BUDGET_OF),'max_chunks':None,
                      'noise':{'eps':EPS,'eps_bar':EPS_BAR,'delta':DELTA,'arms':{k:list(v) for k,v in NOISE_OF.items()}},
                      'n_scale20_b':ST.N20B,'n_noise12_b':ST.N12B,'sha256_files':files})
    print(len(files),'files frozen; C',C50,'B',BUDGET_OF,'N20B',ST.N20B,'N12B',ST.N12B)


if __name__=='__main__':main()
