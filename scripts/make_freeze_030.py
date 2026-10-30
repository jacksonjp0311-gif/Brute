"""Lean source freeze for study-030: writes experiments/COMMIT_ORDER_030.json (ledger events from preregistration_030)
and experiments/BRUTE_SOURCE_FREEZE_030.json (plan and source/scoring/test/release-tooling/deviation hashes).
Refuses overwrite. New file; built from scripts/make_freeze_029.py (frozen).
  PYTHONPATH=. python scripts/make_freeze_030.py"""
import json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from experiments.brute_common_030 import PLAN,FREEZE,sha,write_new
ORDER=ROOT/'experiments/COMMIT_ORDER_030.json'
FILES=['brute/region.py','brute/scalesearch.py','brute/scalesearch4.py','brute/scalesearch5.py','brute/release_version_0270.py',
       'experiments/brute_common_026.py','experiments/brute_study_026.py','experiments/worlds_026.py','experiments/v0230_reference.py',
       'experiments/brute_common_030.py','experiments/brute_study_030.py','experiments/BRUTE_PLAN_030.json',
       'scripts/check_seeds_030.py','scripts/diag_030.py','scripts/run_reference_030.py','scripts/recount_030.py','scripts/make_gates_030.py',
       'scripts/run_tests_0270.py','scripts/make_freeze_030.py','scripts/push_checkpoint_030.py','scripts/study030_storage.py',
       'scripts/verify_release_0270.py',
       'tests/test_scalesearch5_0270.py','tests/test_scalesearch4_0260.py','tests/test_scalesearch_0230.py','tests/test_certify12_0230.py',
       'tests/test_scripts_030.py','tests/test_release_0270.py',
       'docs/research/v0.27.0/PLAN_030.md','docs/research/BRUTE_DEVIATIONS_030_132.md',
       'results/diag-030/SEEDCHECK_030.json','results/diag-030/OVERRUN_DIAG_030.json','results/diag-030/PREFREEZE_SMOKE_GATES_030.json',
       'experiments/COMMIT_ORDER_030.json']


def main():
    L=[json.loads(x) for x in (ROOT/'results/RESEARCH_LEDGER.jsonl').read_text().splitlines() if x.strip()]
    i0=next(i for i,e in enumerate(L) if e.get('event')=='preregistration_030')
    ev=[{'event':e['event'],'commit':e.get('commit'),'note_time':str(e.get('note',''))[:25]} for e in L[i0:]]
    write_new(ORDER,{'schema':'brute.commit-order.v1','study':'BRUTE-0270-SYMMETRY-FREE-030','order':[e['event'] for e in ev],'entries':ev})
    files={f:sha(ROOT/f) for f in sorted(FILES)}
    write_new(FREEZE,{'schema':'brute.source-freeze.v1','study':'BRUTE-0270-SYMMETRY-FREE-030','process':'lean','plan_sha256':sha(PLAN),
                      'sha256_files':files})
    print(len(files),'files frozen')


if __name__=='__main__':main()
