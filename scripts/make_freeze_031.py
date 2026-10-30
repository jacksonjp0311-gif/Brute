"""Lean source freeze for study-031: writes experiments/COMMIT_ORDER_031.json (ledger events from preregistration_031)
and experiments/BRUTE_SOURCE_FREEZE_031.json (plan and source/scoring/test/release-tooling/deviation hashes).
Refuses overwrite. New file; built from scripts/make_freeze_030.py (frozen).
  PYTHONPATH=. python scripts/make_freeze_031.py"""
import json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from experiments.brute_common_031 import PLAN,FREEZE,sha,write_new
ORDER=ROOT/'experiments/COMMIT_ORDER_031.json'
FILES=['brute/region.py','brute/scalesearch.py','brute/scalesearch4.py','brute/scalesearch5.py','brute/scalesearch6.py','brute/release_version_0280.py',
       'experiments/brute_common_026.py','experiments/brute_study_026.py','experiments/worlds_026.py','experiments/v0230_reference.py',
       'experiments/brute_common_030.py','experiments/brute_common_031.py','experiments/brute_study_031.py','experiments/BRUTE_PLAN_031.json',
       'scripts/check_seeds_031.py','scripts/diag_031.py','scripts/run_reference_031.py','scripts/recount_031.py','scripts/make_gates_031.py',
       'scripts/run_tests_0280.py','scripts/make_freeze_031.py','scripts/push_checkpoint_031.py','scripts/study031_storage.py',
       'scripts/verify_release_0280.py',
       'tests/test_scalesearch6_0280.py','tests/test_scalesearch5_0270.py','tests/test_scalesearch4_0260.py','tests/test_scalesearch_0230.py',
       'tests/test_certify12_0230.py','tests/test_scripts_031.py','tests/test_release_0280.py',
       'docs/research/v0.28.0/PLAN_031.md','docs/research/BRUTE_DEVIATIONS_031_134.md',
       'results/diag-031/SEEDCHECK_031.json','results/diag-031/IDENTIFY_DIAG_031.json','results/diag-031/PREFREEZE_SMOKE_GATES_031.json',
       'experiments/COMMIT_ORDER_031.json']


def main():
    L=[json.loads(x) for x in (ROOT/'results/RESEARCH_LEDGER.jsonl').read_text().splitlines() if x.strip()]
    i0=next(i for i,e in enumerate(L) if e.get('event')=='preregistration_031')
    ev=[{'event':e['event'],'commit':e.get('commit'),'note_time':str(e.get('note',''))[:25]} for e in L[i0:]]
    write_new(ORDER,{'schema':'brute.commit-order.v1','study':'BRUTE-0280-SIXTEEN-STATE-ID-031','order':[e['event'] for e in ev],'entries':ev})
    files={f:sha(ROOT/f) for f in sorted(FILES)}
    write_new(FREEZE,{'schema':'brute.source-freeze.v1','study':'BRUTE-0280-SIXTEEN-STATE-ID-031','process':'lean','plan_sha256':sha(PLAN),
                      'sha256_files':files})
    print(len(files),'files frozen')


if __name__=='__main__':main()
