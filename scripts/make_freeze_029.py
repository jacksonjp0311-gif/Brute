"""Lean source freeze for study-029: writes experiments/COMMIT_ORDER_029.json (ledger events from preregistration_029)
and experiments/BRUTE_SOURCE_FREEZE_029.json (plan, amendment A1 and source/scoring/test/release-tooling/deviation hashes).
Refuses overwrite. New file.
  PYTHONPATH=. python scripts/make_freeze_029.py"""
import json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from experiments.brute_common_029 import PLAN,AMENDMENT,FREEZE,sha,write_new
ORDER=ROOT/'experiments/COMMIT_ORDER_029.json'
FILES=['brute/region.py','brute/scalesearch.py','brute/scalesearch3.py','brute/scalesearch4.py','brute/api/certify13.py','brute/api/certify14.py',
       'brute/release_version_0260.py',
       'experiments/brute_common_026.py','experiments/brute_study_026.py','experiments/worlds_026.py','experiments/v0230_reference.py',
       'experiments/brute_common_029.py','experiments/brute_study_029.py',
       'experiments/BRUTE_PLAN_029.json','experiments/BRUTE_PLAN_029_A1.json','scripts/check_seeds_029.py','scripts/diag_029.py',
       'scripts/run_reference_029.py','scripts/recount_029.py',
       'scripts/api_check_029.py','scripts/make_gates_029.py','scripts/run_tests_0260.py','scripts/make_freeze_029.py',
       'scripts/push_checkpoint_029.py','scripts/study029_storage.py','scripts/verify_release_0260.py',
       'tests/test_scalesearch4_0260.py','tests/test_scalesearch3_0250.py','tests/test_scalesearch_0230.py','tests/test_certify12_0230.py',
       'tests/test_scripts_029.py','tests/test_release_0260.py',
       'docs/research/v0.26.0/PLAN_029.md','docs/research/v0.26.0/PLAN_029_A1.md','docs/research/BRUTE_DEVIATIONS_029_130.md',
       'results/diag-029/SEEDCHECK_029.json','results/diag-029/S1_COST_029.json','results/diag-029/PREFREEZE_SMOKE_GATES_029.json',
       'experiments/COMMIT_ORDER_029.json']


def main():
    L=[json.loads(x) for x in (ROOT/'results/RESEARCH_LEDGER.jsonl').read_text().splitlines() if x.strip()]
    i0=next(i for i,e in enumerate(L) if e.get('event')=='preregistration_029')
    ev=[{'event':e['event'],'commit':e.get('commit'),'note_time':str(e.get('note',''))[:25]} for e in L[i0:]]
    write_new(ORDER,{'schema':'brute.commit-order.v1','study':'BRUTE-0260-QUERY-THROUGHPUT-029','order':[e['event'] for e in ev],'entries':ev})
    files={f:sha(ROOT/f) for f in sorted(FILES)}
    write_new(FREEZE,{'schema':'brute.source-freeze.v1','study':'BRUTE-0260-QUERY-THROUGHPUT-029','process':'lean','plan_sha256':sha(PLAN),
                      'amendment_sha256':sha(AMENDMENT),'sha256_files':files})
    print(len(files),'files frozen')


if __name__=='__main__':main()
