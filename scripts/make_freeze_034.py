"""Lean source freeze for study-034: writes experiments/COMMIT_ORDER_034.json (ledger events from preregistration_034)
and experiments/BRUTE_SOURCE_FREEZE_034.json (plan and source/scoring/test/release-tooling/deviation hashes).
Refuses overwrite. New file; built from scripts/make_freeze_033.py (frozen).
  PYTHONPATH=. python scripts/make_freeze_034.py"""
import json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from experiments.brute_common_034 import PLAN,FREEZE,sha,write_new
ORDER=ROOT/'experiments/COMMIT_ORDER_034.json'
FILES=['brute/region.py','brute/scalesearch.py','brute/scalesearch4.py','brute/scalesearch5.py','brute/scalesearch6.py','brute/scalesearch8.py',
       'brute/scalesearch9.py','brute/release_version_0310.py',
       'experiments/brute_common_026.py','experiments/worlds_026.py','experiments/brute_common_032.py','experiments/brute_common_033.py',
       'experiments/brute_study_033.py','experiments/v0300_reference.py',
       'experiments/brute_common_034.py','experiments/brute_study_034.py','experiments/v0310_reference.py','experiments/BRUTE_PLAN_034.json',
       'scripts/check_seeds_034.py','scripts/run_reference_033.py','scripts/recount_033.py',
       'scripts/run_reference_034.py','scripts/recount_034.py','scripts/make_gates_034.py',
       'scripts/run_tests_0310.py','scripts/make_freeze_034.py','scripts/push_checkpoint_034.py','scripts/study034_storage.py',
       'scripts/verify_release_0310.py','scripts/prefreeze_smoke_034.py',
       'tests/test_scalesearch9_0310.py','tests/test_scalesearch8_0300.py','tests/test_scalesearch_0230.py','tests/test_scripts_034.py','tests/test_release_0310.py',
       'docs/research/v0.31.0/PLAN_034.md','docs/research/BRUTE_DEVIATIONS_034_140.md',
       'results/diag-034/SEEDCHECK_034.json','results/diag-034/PREFREEZE_SMOKE_GATES_034.json',
       'experiments/COMMIT_ORDER_034.json']


def main():
    L=[json.loads(x) for x in (ROOT/'results/RESEARCH_LEDGER.jsonl').read_text().splitlines() if x.strip()]
    i0=next(i for i,e in enumerate(L) if e.get('event')=='preregistration_034')
    ev=[{'event':e['event'],'commit':e.get('commit'),'note_time':str(e.get('note',''))[:25]} for e in L[i0:]]
    write_new(ORDER,{'schema':'brute.commit-order.v1','study':'BRUTE-0310-SOUND-ACTIVE-ID-034','order':[e['event'] for e in ev],'entries':ev})
    files={f:sha(ROOT/f) for f in sorted(FILES)}
    write_new(FREEZE,{'schema':'brute.source-freeze.v1','study':'BRUTE-0310-SOUND-ACTIVE-ID-034','process':'lean','plan_sha256':sha(PLAN),
                      'sha256_files':files})
    print(len(files),'files frozen')


if __name__=='__main__':main()
