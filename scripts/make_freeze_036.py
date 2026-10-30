"""Lean source freeze for study-036: writes experiments/COMMIT_ORDER_036.json (ledger events from preregistration_036)
and experiments/BRUTE_SOURCE_FREEZE_036.json (plan and source/scoring/test/release-tooling/deviation hashes).
Refuses overwrite. New file; built from scripts/make_freeze_035.py (frozen).
  PYTHONPATH=. python scripts/make_freeze_036.py"""
import json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from experiments.brute_common_036 import PLAN,FREEZE,sha,write_new
ORDER=ROOT/'experiments/COMMIT_ORDER_036.json'
FILES=['brute/region.py','brute/scalesearch.py','brute/scalesearch4.py','brute/scalesearch5.py','brute/scalesearch6.py','brute/scalesearch7.py',
       'brute/scalesearch8.py','brute/scalesearch9.py','brute/scalesearch10.py','brute/scalesearch11.py','brute/release_version_0330.py',
       'experiments/brute_common_026.py','experiments/worlds_026.py','experiments/brute_common_032.py','experiments/brute_common_033.py',
       'experiments/brute_study_033.py','experiments/v0300_reference.py','experiments/brute_common_034.py','experiments/brute_study_034.py',
       'experiments/brute_common_035.py','experiments/v0320_reference.py','experiments/brute_common_036.py','experiments/brute_study_036.py',
       'experiments/BRUTE_PLAN_036.json',
       'scripts/check_seeds_035.py','scripts/check_seeds_036.py','scripts/recount_033.py','scripts/recount_035.py','scripts/make_gates_034.py',
       'scripts/run_reference_036.py','scripts/recount_036.py','scripts/make_gates_036.py',
       'scripts/run_tests_0330.py','scripts/make_freeze_036.py','scripts/push_checkpoint_036.py','scripts/study036_storage.py',
       'scripts/verify_release_0330.py','scripts/prefreeze_smoke_036.py',
       'tests/test_scalesearch11_0330.py','tests/test_scalesearch10_0320.py','tests/test_scalesearch9_0310.py','tests/test_scalesearch8_0300.py',
       'tests/test_scalesearch_0230.py','tests/test_scripts_036.py','tests/test_release_0330.py',
       'docs/research/v0.33.0/PLAN_036.md','docs/research/BRUTE_DEVIATIONS_036_144.md',
       'results/diag-036/SEEDCHECK_036.json','results/diag-036/PREFREEZE_SMOKE_GATES_036.json',
       'experiments/COMMIT_ORDER_036.json']


def main():
    L=[json.loads(x) for x in (ROOT/'results/RESEARCH_LEDGER.jsonl').read_text().splitlines() if x.strip()]
    i0=next(i for i,e in enumerate(L) if e.get('event')=='preregistration_036')
    ev=[{'event':e['event'],'commit':e.get('commit'),'note_time':str(e.get('note',''))[:25]} for e in L[i0:]]
    write_new(ORDER,{'schema':'brute.commit-order.v1','study':'BRUTE-0330-REPEATED-READS-036','order':[e['event'] for e in ev],'entries':ev})
    files={f:sha(ROOT/f) for f in sorted(FILES)}
    write_new(FREEZE,{'schema':'brute.source-freeze.v1','study':'BRUTE-0330-REPEATED-READS-036','process':'lean','plan_sha256':sha(PLAN),
                      'sha256_files':files})
    print(len(files),'files frozen')


if __name__=='__main__':main()
