"""Lean source freeze for study-032: writes experiments/COMMIT_ORDER_032.json (ledger events from preregistration_032)
and experiments/BRUTE_SOURCE_FREEZE_032.json (plan and source/scoring/test/release-tooling/deviation hashes).
Refuses overwrite. New file; built from scripts/make_freeze_031.py (frozen).
  PYTHONPATH=. python scripts/make_freeze_032.py"""
import json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from experiments.brute_common_032 import PLAN,FREEZE,sha,write_new
ORDER=ROOT/'experiments/COMMIT_ORDER_032.json'
FILES=['brute/region.py','brute/scalesearch.py','brute/scalesearch4.py','brute/scalesearch5.py','brute/scalesearch7.py','brute/noisyregion.py',
       'brute/release_version_0290.py',
       'experiments/brute_common_026.py','experiments/brute_study_026.py','experiments/worlds_026.py','experiments/v0290_reference.py',
       'experiments/brute_common_031.py','experiments/brute_common_032.py','experiments/brute_study_032.py','experiments/BRUTE_PLAN_032.json',
       'scripts/check_seeds_032.py','scripts/run_reference_032.py','scripts/recount_032.py','scripts/make_gates_032.py',
       'scripts/run_tests_0290.py','scripts/make_freeze_032.py','scripts/push_checkpoint_032.py','scripts/study032_storage.py',
       'scripts/verify_release_0290.py',
       'tests/test_scalesearch7_0290.py','tests/test_scalesearch5_0270.py','tests/test_scalesearch_0230.py',
       'tests/test_scripts_032.py','tests/test_release_0290.py',
       'docs/research/v0.29.0/PLAN_032.md','docs/research/BRUTE_DEVIATIONS_032_136.md',
       'results/diag-032/SEEDCHECK_032.json','results/diag-032/PREFREEZE_SMOKE_GATES_032.json',
       'experiments/COMMIT_ORDER_032.json']


def main():
    L=[json.loads(x) for x in (ROOT/'results/RESEARCH_LEDGER.jsonl').read_text().splitlines() if x.strip()]
    i0=next(i for i,e in enumerate(L) if e.get('event')=='preregistration_032')
    ev=[{'event':e['event'],'commit':e.get('commit'),'note_time':str(e.get('note',''))[:25]} for e in L[i0:]]
    write_new(ORDER,{'schema':'brute.commit-order.v1','study':'BRUTE-0280-ROBUST-PERCEPTION-032','order':[e['event'] for e in ev],'entries':ev})
    files={f:sha(ROOT/f) for f in sorted(FILES)}
    write_new(FREEZE,{'schema':'brute.source-freeze.v1','study':'BRUTE-0280-ROBUST-PERCEPTION-032','process':'lean','plan_sha256':sha(PLAN),
                      'sha256_files':files})
    print(len(files),'files frozen')


if __name__=='__main__':main()
