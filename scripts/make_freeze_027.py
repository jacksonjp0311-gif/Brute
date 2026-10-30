"""Lean source freeze for study-027: writes experiments/COMMIT_ORDER_027.json (ledger events from preregistration_027)
and experiments/BRUTE_SOURCE_FREEZE_027.json (plan and source/scoring/test/release-tooling/deviation hashes).
Refuses overwrite. New file.
  PYTHONPATH=. python scripts/make_freeze_027.py"""
import json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from experiments.brute_common_027 import PLAN,FREEZE,sha,write_new
ORDER=ROOT/'experiments/COMMIT_ORDER_027.json'
FILES=['brute/scalesearch.py','brute/scalebetting.py','brute/api/certify12.py','brute/release_version_0240.py',
       'experiments/brute_common_026.py','experiments/brute_study_026.py','experiments/worlds_026.py','experiments/v0230_reference.py',
       'experiments/brute_common_027.py','experiments/brute_study_027.py',
       'experiments/BRUTE_PLAN_027.json','scripts/check_seeds_027.py','scripts/run_reference_027.py','scripts/recount_027.py',
       'scripts/api_check_027.py','scripts/make_gates_027.py','scripts/run_tests_0240.py','scripts/make_freeze_027.py',
       'scripts/push_checkpoint_027.py','scripts/study027_storage.py','scripts/verify_release_0240.py',
       'tests/test_scalesearch_0230.py','tests/test_certify12_0230.py','tests/test_scripts_027.py','tests/test_release_0240.py',
       'docs/research/v0.24.0/PLAN_027.md','docs/research/BRUTE_DEVIATIONS_027_126.md',
       'results/diag-027/SEEDCHECK_027.json','experiments/COMMIT_ORDER_027.json']


def main():
    L=[json.loads(x) for x in (ROOT/'results/RESEARCH_LEDGER.jsonl').read_text().splitlines() if x.strip()]
    i0=next(i for i,e in enumerate(L) if e.get('event')=='preregistration_027')
    ev=[{'event':e['event'],'commit':e.get('commit'),'note_time':str(e.get('note',''))[:25]} for e in L[i0:]]
    write_new(ORDER,{'schema':'brute.commit-order.v1','study':'BRUTE-0240-SCALE-REPLAY-027','order':[e['event'] for e in ev],'entries':ev})
    files={f:sha(ROOT/f) for f in sorted(FILES)}
    write_new(FREEZE,{'schema':'brute.source-freeze.v1','study':'BRUTE-0240-SCALE-REPLAY-027','process':'lean','plan_sha256':sha(PLAN),'sha256_files':files})
    print(len(files),'files frozen')


if __name__=='__main__':main()
