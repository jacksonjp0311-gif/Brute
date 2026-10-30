"""Lean source freeze for study-026: writes experiments/COMMIT_ORDER_026.json (ledger events from preregistration_026)
and experiments/BRUTE_SOURCE_FREEZE_026.json (plan and source/scoring/test/deviation hashes). Refuses overwrite. New file.
  PYTHONPATH=. python scripts/make_freeze_026.py"""
import json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from experiments.brute_common_026 import PLAN,FREEZE,sha,write_new
ORDER=ROOT/'experiments/COMMIT_ORDER_026.json'
FILES=['brute/scalesearch.py','brute/scalebetting.py','brute/api/certify12.py','brute/release_version_0230.py',
       'experiments/brute_common_026.py','experiments/brute_study_026.py','experiments/worlds_026.py','experiments/v0230_reference.py',
       'experiments/BRUTE_PLAN_026.json','scripts/check_seeds_026.py','scripts/run_reference_026.py','scripts/recount_026.py',
       'scripts/api_check_026.py','scripts/make_gates_026.py','scripts/run_tests_0230.py','scripts/make_freeze_026.py',
       'tests/test_scalesearch_0230.py','tests/test_certify12_0230.py','tests/test_scripts_026.py',
       'docs/research/v0.23.0/PLAN_026.md','docs/research/BRUTE_DEVIATIONS_026_123.md','docs/research/BRUTE_DEVIATIONS_026_124.md',
       'results/diag-026/SEEDCHECK_026.json','experiments/COMMIT_ORDER_026.json']


def main():
    L=[json.loads(x) for x in (ROOT/'results/RESEARCH_LEDGER.jsonl').read_text().splitlines() if x.strip()]
    i0=next(i for i,e in enumerate(L) if e.get('event')=='preregistration_026')
    ev=[{'event':e['event'],'commit':e.get('commit'),'note_time':str(e.get('note',''))[:25]} for e in L[i0:]]
    write_new(ORDER,{'schema':'brute.commit-order.v1','study':'BRUTE-0230-SCALE-026','order':[e['event'] for e in ev],'entries':ev})
    files={f:sha(ROOT/f) for f in sorted(FILES)}
    write_new(FREEZE,{'schema':'brute.source-freeze.v1','study':'BRUTE-0230-SCALE-026','process':'lean','plan_sha256':sha(PLAN),'sha256_files':files})
    print(len(files),'files frozen')


if __name__=='__main__':main()
