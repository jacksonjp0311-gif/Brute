"""Lean source freeze for study-039: writes experiments/COMMIT_ORDER_039.json (ledger events from preregistration_039)
and experiments/BRUTE_SOURCE_FREEZE_039.json (plan and source/scoring/test/release-tooling/deviation hashes).
Refuses overwrite. New file; built from scripts/make_freeze_038.py (frozen).
  PYTHONPATH=. python scripts/make_freeze_039.py"""
import json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from experiments.brute_common_039 import PLAN,FREEZE,sha,write_new
ORDER=ROOT/'experiments/COMMIT_ORDER_039.json'
FILES=['brute/region.py','brute/scalesearch.py','brute/scalesearch4.py','brute/scalesearch5.py','brute/scalesearch6.py','brute/scalesearch7.py',
       'brute/scalesearch8.py','brute/scalesearch9.py','brute/scalesearch10.py','brute/scalesearch11.py','brute/scalesearch12.py',
       'brute/scalesearch13.py','brute/scalesearch14.py','brute/release_version_0360.py',
       'experiments/brute_common_009.py','experiments/brute_common_026.py','experiments/worlds_007.py','experiments/worlds_026.py','experiments/worlds_039.py',
       'experiments/brute_common_032.py','experiments/brute_common_033.py','experiments/brute_study_033.py','experiments/v0300_reference.py',
       'experiments/v0310_reference.py','experiments/brute_common_034.py','experiments/brute_study_034.py','experiments/brute_common_035.py',
       'experiments/brute_common_038.py','experiments/brute_common_039.py','experiments/brute_study_039.py','experiments/BRUTE_PLAN_039.json',
       'scripts/check_seeds_013.py','scripts/check_seeds_033.py','scripts/check_seeds_034.py','scripts/check_seeds_038.py','scripts/check_seeds_039.py',
       'scripts/recount_033.py','scripts/recount_034.py','scripts/run_reference_033.py','scripts/make_gates_034.py',
       'scripts/recount_039.py','scripts/run_reference_039.py','scripts/make_gates_039.py',
       'scripts/run_tests_0360.py','scripts/make_freeze_039.py','scripts/push_checkpoint_039.py','scripts/study039_storage.py',
       'scripts/verify_release_0360.py','scripts/prefreeze_smoke_039.py',
       'tests/test_scalesearch14_0360.py','tests/test_scalesearch13_0350.py','tests/test_scalesearch12_0340.py','tests/test_scalesearch11_0330.py',
       'tests/test_scalesearch10_0320.py','tests/test_scalesearch9_0310.py','tests/test_scalesearch8_0300.py','tests/test_scalesearch_0230.py',
       'tests/test_scripts_039.py','tests/test_release_0360.py',
       'docs/research/BRUTE_DEVIATIONS_039_150.md',
       'results/diag-039/SEEDCHECK_039.json','results/diag-039/PREFREEZE_SMOKE_GATES_039.json',
       'experiments/COMMIT_ORDER_039.json']


def main():
    L=[json.loads(x) for x in (ROOT/'results/RESEARCH_LEDGER.jsonl').read_text().splitlines() if x.strip()]
    i0=next(i for i,e in enumerate(L) if e.get('event')=='preregistration_039')
    ev=[{'event':e['event'],'commit':e.get('commit'),'note_time':str(e.get('note',''))[:25]} for e in L[i0:]]
    write_new(ORDER,{'schema':'brute.commit-order.v1','study':'BRUTE-0360-CLEAN-SCALE-039','order':[e['event'] for e in ev],'entries':ev})
    files={f:sha(ROOT/f) for f in sorted(FILES)}
    write_new(FREEZE,{'schema':'brute.source-freeze.v1','study':'BRUTE-0360-CLEAN-SCALE-039','process':'lean','plan_sha256':sha(PLAN),
                      'sha256_files':files})
    print(len(files),'files frozen')


if __name__=='__main__':main()
