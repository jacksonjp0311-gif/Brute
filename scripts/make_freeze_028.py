"""Lean source freeze for study-028: writes experiments/COMMIT_ORDER_028.json (ledger events from preregistration_028)
and experiments/BRUTE_SOURCE_FREEZE_028.json (plan and source/scoring/test/release-tooling/deviation hashes).
Refuses overwrite. New file.
  PYTHONPATH=. python scripts/make_freeze_028.py"""
import json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from experiments.brute_common_028 import PLAN,FREEZE,sha,write_new
ORDER=ROOT/'experiments/COMMIT_ORDER_028.json'
FILES=['brute/scalesearch.py','brute/scalesearch3.py','brute/api/certify12.py','brute/api/certify13.py','brute/release_version_0250.py',
       'experiments/brute_common_026.py','experiments/brute_study_026.py','experiments/worlds_026.py','experiments/v0230_reference.py',
       'experiments/brute_common_028.py','experiments/brute_study_028.py',
       'experiments/BRUTE_PLAN_028.json','scripts/check_seeds_028.py','scripts/run_reference_028.py','scripts/recount_028.py',
       'scripts/api_check_028.py','scripts/make_gates_028.py','scripts/run_tests_0250.py','scripts/make_freeze_028.py',
       'scripts/push_checkpoint_028.py','scripts/study028_storage.py','scripts/verify_release_0250.py',
       'tests/test_scalesearch3_0250.py','tests/test_scalesearch_0230.py','tests/test_certify12_0230.py','tests/test_scripts_028.py','tests/test_release_0250.py',
       'docs/research/v0.25.0/PLAN_028.md','docs/research/BRUTE_DEVIATIONS_028_128.md',
       'results/diag-028/SEEDCHECK_028.json','results/diag-028/S2_ABLATION_028.json','results/diag-028/S3_PORTFOLIO_028.json','experiments/COMMIT_ORDER_028.json']


def main():
    L=[json.loads(x) for x in (ROOT/'results/RESEARCH_LEDGER.jsonl').read_text().splitlines() if x.strip()]
    i0=next(i for i,e in enumerate(L) if e.get('event')=='preregistration_028')
    ev=[{'event':e['event'],'commit':e.get('commit'),'note_time':str(e.get('note',''))[:25]} for e in L[i0:]]
    write_new(ORDER,{'schema':'brute.commit-order.v1','study':'BRUTE-0250-SOLVER-COST-028','order':[e['event'] for e in ev],'entries':ev})
    files={f:sha(ROOT/f) for f in sorted(FILES)}
    write_new(FREEZE,{'schema':'brute.source-freeze.v1','study':'BRUTE-0250-SOLVER-COST-028','process':'lean','plan_sha256':sha(PLAN),'sha256_files':files})
    print(len(files),'files frozen')


if __name__=='__main__':main()
