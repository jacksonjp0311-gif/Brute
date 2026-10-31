"""Lean source freeze for study-043: writes experiments/COMMIT_ORDER_043.json (ledger events from preregistration_043)
and experiments/BRUTE_SOURCE_FREEZE_043.json (plan and source/scoring/test/release-tooling/deviation hashes).
Refuses overwrite. New file; built from scripts/make_freeze_042.py (frozen).
  PYTHONPATH=. python scripts/make_freeze_043.py"""
import json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from experiments.brute_common_043 import PLAN,FREEZE,sha,write_new
ORDER=ROOT/'experiments/COMMIT_ORDER_043.json'
FILES=['brute/region.py','brute/scalesearch.py','brute/scalesearch4.py','brute/scalesearch5.py','brute/scalesearch6.py','brute/scalesearch7.py',
       'brute/scalesearch8.py','brute/scalesearch9.py','brute/scalesearch10.py','brute/scalesearch11.py','brute/scalesearch12.py',
       'brute/scalesearch13.py','brute/evaluation.py','brute/scalesearch14.py','brute/scalesearch15.py','brute/encaudit16.py','brute/release_version_0380.py',
       'experiments/brute_common_009.py','experiments/brute_common_026.py','experiments/worlds_007.py','experiments/worlds_026.py',
       'experiments/worlds_039.py','experiments/worlds_040.py','experiments/brute_common_032.py','experiments/brute_common_033.py',
       'experiments/brute_study_033.py','experiments/brute_study_034.py','experiments/brute_study_040.py','experiments/v0300_reference.py',
       'experiments/v0310_reference.py','experiments/brute_common_034.py','experiments/brute_common_035.py','experiments/brute_common_038.py',
       'experiments/brute_common_039.py','experiments/brute_common_040.py','experiments/brute_common_041.py','experiments/brute_study_041.py',
       'experiments/solver_proxy_041.py','experiments/BRUTE_PLAN_041.json',
       'scripts/check_seeds_040.py','scripts/check_seeds_041.py','scripts/recount_033.py','scripts/recount_034.py','scripts/run_reference_033.py',
       'scripts/run_reference_040.py','scripts/make_gates_034.py','scripts/recount_041.py','scripts/run_reference_041.py','scripts/make_gates_041.py',
       'scripts/run_tests_0370.py','scripts/run_tests_0380.py','scripts/make_freeze_041.py','scripts/push_checkpoint_041.py','scripts/study041_storage.py',
       'scripts/verify_release_0380.py','scripts/prefreeze_smoke_041.py',
       'tests/test_encaudit16_0380.py','tests/test_scripts_041.py','tests/test_release_0380.py','tests/test_scalesearch15_0370.py','tests/test_scalesearch14_0360.py',
       'docs/research/BRUTE_DEVIATIONS_041_154.md',
       'results/diag-041/SEEDCHECK_041.json','results/diag-041/PREFREEZE_SMOKE_GATES_041.json',
       'experiments/COMMIT_ORDER_041.json','experiments/BRUTE_SOURCE_FREEZE_041.json','scripts/verify_release_0380a.py',
       'brute/scalesearch16.py','brute/release_version_0390.py','experiments/brute_common_042.py','experiments/brute_study_042.py',
       'experiments/BRUTE_PLAN_042.json','scripts/check_seeds_042.py','scripts/recount_042.py','scripts/recount_041b.py','scripts/run_reference_042.py',
       'scripts/make_gates_042.py','scripts/make_freeze_042.py','scripts/push_checkpoint_042.py','scripts/study042_storage.py',
       'scripts/verify_release_0390.py','scripts/run_tests_0390.py','scripts/prefreeze_smoke_042.py',
       'tests/test_scalesearch16_0390.py','tests/test_scripts_042.py','tests/test_release_0390.py',
       'docs/research/BRUTE_DEVIATIONS_042_157.md','results/diag-042/SEEDCHECK_042.json','results/diag-042/PREFREEZE_SMOKE_GATES_042.json',
       'experiments/COMMIT_ORDER_042.json','experiments/BRUTE_SOURCE_FREEZE_042.json','docs/research/BRUTE_DEVIATIONS_042_158.md',
       'experiments/worlds_043.py','brute/release_version_0400.py','experiments/brute_common_043.py','experiments/brute_study_043.py',
       'experiments/BRUTE_PLAN_043.json','scripts/check_seeds_043.py','scripts/check_seeds_043b.py','scripts/recount_043.py',
       'scripts/run_reference_043.py','scripts/make_gates_043.py','scripts/make_freeze_043.py','scripts/push_checkpoint_043.py',
       'scripts/study043_storage.py','scripts/verify_release_0400.py','scripts/run_tests_0400.py','scripts/prefreeze_smoke_043.py',
       'tests/test_worlds_043.py','tests/test_scripts_043.py','tests/test_release_0400.py',
       'docs/research/BRUTE_DEVIATIONS_043_159.md','results/diag-043/SEEDCHECK_043.json','results/diag-043/SEEDCHECK_043B.json',
       'results/diag-043/PREFREEZE_SMOKE_GATES_043.json','experiments/COMMIT_ORDER_043.json']


def entries():
    L=[json.loads(x) for x in (ROOT/'results/RESEARCH_LEDGER.jsonl').read_text().splitlines() if x.strip()]
    i0=next(i for i,e in enumerate(L) if e.get('event')=='preregistration_043')
    return [{'event':e['event'],'commit':e.get('commit'),'note_time':str(e.get('note',''))[:25]} for e in L[i0:]]


def main():
    ev=entries()
    write_new(ORDER,{'schema':'brute.commit-order.v1','study':'BRUTE-0400-A16-LOWOBS-043','order':[e['event'] for e in ev],'entries':ev})
    files={f:sha(ROOT/f) for f in sorted(FILES)}
    write_new(FREEZE,{'schema':'brute.source-freeze.v1','study':'BRUTE-0400-A16-LOWOBS-043','process':'lean','plan_sha256':sha(PLAN),
                      'sha256_files':files})
    print(len(files),'files frozen')


if __name__=='__main__':main()
