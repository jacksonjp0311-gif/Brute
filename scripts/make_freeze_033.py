"""Lean source freeze for study-033: writes experiments/COMMIT_ORDER_033.json (ledger events from preregistration_033)
and experiments/BRUTE_SOURCE_FREEZE_033.json (plan and source/scoring/test/release-tooling/deviation hashes).
Refuses overwrite. New file; built from scripts/make_freeze_032.py (frozen).
  PYTHONPATH=. python scripts/make_freeze_033.py"""
import json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from experiments.brute_common_033 import PLAN,FREEZE,sha,write_new
ORDER=ROOT/'experiments/COMMIT_ORDER_033.json'
FILES=['brute/region.py','brute/scalesearch.py','brute/scalesearch4.py','brute/scalesearch5.py','brute/scalesearch6.py','brute/scalesearch8.py',
       'brute/release_version_0300.py',
       'experiments/brute_common_026.py','experiments/worlds_026.py','experiments/brute_common_032.py',
       'experiments/brute_common_033.py','experiments/brute_study_033.py','experiments/v0300_reference.py','experiments/BRUTE_PLAN_033.json',
       'scripts/check_seeds_033.py','scripts/run_reference_033.py','scripts/recount_033.py','scripts/make_gates_033.py',
       'scripts/run_tests_0300.py','scripts/make_freeze_033.py','scripts/push_checkpoint_033.py','scripts/study033_storage.py',
       'scripts/verify_release_0300.py','scripts/prefreeze_smoke_033.py',
       'tests/test_scalesearch8_0300.py','tests/test_scalesearch_0230.py','tests/test_scripts_033.py','tests/test_release_0300.py',
       'docs/research/v0.30.0/PLAN_033.md','docs/research/BRUTE_DEVIATIONS_033_138.md',
       'results/diag-033/SEEDCHECK_033.json','results/diag-033/PREFREEZE_SMOKE_GATES_033.json',
       'experiments/COMMIT_ORDER_033.json']


def main():
    L=[json.loads(x) for x in (ROOT/'results/RESEARCH_LEDGER.jsonl').read_text().splitlines() if x.strip()]
    i0=next(i for i,e in enumerate(L) if e.get('event')=='preregistration_033')
    ev=[{'event':e['event'],'commit':e.get('commit'),'note_time':str(e.get('note',''))[:25]} for e in L[i0:]]
    write_new(ORDER,{'schema':'brute.commit-order.v1','study':'BRUTE-0300-ACTIVE-EXPERIMENTS-033','order':[e['event'] for e in ev],'entries':ev})
    files={f:sha(ROOT/f) for f in sorted(FILES)}
    write_new(FREEZE,{'schema':'brute.source-freeze.v1','study':'BRUTE-0300-ACTIVE-EXPERIMENTS-033','process':'lean','plan_sha256':sha(PLAN),
                      'sha256_files':files})
    print(len(files),'files frozen')


if __name__=='__main__':main()
