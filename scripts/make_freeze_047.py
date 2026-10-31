"""Lean source freeze for study-047: writes experiments/COMMIT_ORDER_047.json (ledger events from preregistration_047)
and experiments/BRUTE_SOURCE_FREEZE_047.json (plan and source/scoring/test/release-tooling/deviation hashes; FILES = the 046 list,
the remaining 046 files (plan, commit order, freeze, deviation #166, the sealed 046 main SEAL), and the new 047 files, the cap
calibration included). Plan 047 freeze_rule: C and B are part of the freeze, so the freeze also records conflict_cap,
budget_conflicts and the sha of results/diag-047/CAP_CALIBRATION_047.json, and the part-d cut flag (brute_study_047.CUT_D).
Refuses overwrite. New file; built from scripts/make_freeze_046.py (frozen).
  PYTHONPATH=. python scripts/make_freeze_047.py"""
import json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from experiments.brute_common_047 import PLAN,FREEZE,CALIBRATION,sha,write_new,caps
from scripts.make_freeze_046 import FILES as FILES_046
ORDER=ROOT/'experiments/COMMIT_ORDER_047.json'
FILES=list(FILES_046)+['experiments/BRUTE_PLAN_046.json','experiments/COMMIT_ORDER_046.json','experiments/BRUTE_SOURCE_FREEZE_046.json',
       'docs/research/BRUTE_DEVIATIONS_046_166.md','results/study-046/main/SEAL.json',
       'brute/api/certify16d.py','brute/release_version_0440.py','experiments/worlds_047.py','experiments/host_hook_047.py',
       'experiments/brute_common_047.py','experiments/brute_study_047.py','scripts/check_seeds_047.py','scripts/calibrate_cap_047.py',
       'scripts/api_checks_047.py','scripts/recount_047.py','scripts/run_reference_047.py','scripts/make_gates_047.py','scripts/make_freeze_047.py',
       'scripts/push_checkpoint_047.py','scripts/study047_storage.py','scripts/verify_release_0440.py','scripts/run_tests_0440.py',
       'scripts/prefreeze_smoke_047.py','tests/test_certify16d.py','tests/test_scripts_047.py','tests/test_release_0440.py',
       'docs/research/BRUTE_DEVIATIONS_047_167.md','results/diag-047/SEEDCHECK_047.json','results/diag-047/CAP_CALIBRATION_047.json',
       'results/diag-047/PREFREEZE_SMOKE_GATES_047.json']


def entries():
    L=[json.loads(x) for x in (ROOT/'results/RESEARCH_LEDGER.jsonl').read_text().splitlines() if x.strip()]
    i0=next(i for i,e in enumerate(L) if e.get('event')=='preregistration_047')
    return [{'event':e['event'],'commit':e.get('commit'),'note_time':str(e.get('note',''))[:25]} for e in L[i0:]]


def main():
    from experiments import brute_study_047 as ST
    ev=entries();C,B=caps()
    write_new(ORDER,{'schema':'brute.commit-order.v1','study':'BRUTE-0440-CERTIFY16D-SCALE20-047','order':[e['event'] for e in ev],'entries':ev})
    files={f:sha(ROOT/f) for f in sorted(set(FILES))}
    write_new(FREEZE,{'schema':'brute.source-freeze.v1','study':'BRUTE-0440-CERTIFY16D-SCALE20-047','process':'lean','plan_sha256':sha(PLAN),
                      'conflict_cap':C,'budget_conflicts':B,'calibration_sha256':sha(CALIBRATION),'cut_d':ST.CUT_D,'sha256_files':files})
    print(len(files),'files frozen; C',C,'B',B,'cut_d',ST.CUT_D)


if __name__=='__main__':main()
