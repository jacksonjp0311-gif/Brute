"""Lean source freeze for study-048: writes experiments/COMMIT_ORDER_048.json (ledger events from preregistration_048) and
experiments/BRUTE_SOURCE_FREEZE_048.json (plan and source/scoring/test/release-tooling/deviation hashes; FILES = the 047 list, the
remaining 047 files (plan, commit order, freeze, deviations #167 and #168, the sealed 047 main SEAL and its API checks), and the
new 048 files). Plan 048 freeze_rule: C, B and the scale20 case count are part of the freeze (conflict_cap, budget_conflicts,
n_scale20 = brute_study_048.N20). Refuses overwrite. New file; built from scripts/make_freeze_047.py (frozen).
  PYTHONPATH=. python scripts/make_freeze_048.py"""
import json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from experiments.brute_common_048 import PLAN,FREEZE,sha,write_new,C48,B16,B20
from scripts.make_freeze_047 import FILES as FILES_047
ORDER=ROOT/'experiments/COMMIT_ORDER_048.json'
NEW=['brute/release_version_0450.py','experiments/brute_common_048.py','experiments/brute_study_048.py','scripts/check_seeds_048.py',
     'scripts/api_checks_048.py','scripts/recount_048.py','scripts/run_reference_048.py','scripts/make_gates_048.py','scripts/make_freeze_048.py',
     'scripts/push_checkpoint_048.py','scripts/study048_storage.py','scripts/verify_release_0450.py','scripts/run_tests_0450.py',
     'scripts/prefreeze_smoke_048.py','tests/test_scripts_048.py','tests/test_release_0450.py',
     'docs/research/BRUTE_DEVIATIONS_048_169.md','results/diag-048/SEEDCHECK_048.json','results/diag-048/PREFREEZE_SMOKE_GATES_048.json']
FILES=list(FILES_047)+['experiments/BRUTE_PLAN_047.json','experiments/COMMIT_ORDER_047.json','experiments/BRUTE_SOURCE_FREEZE_047.json',
       'docs/research/BRUTE_DEVIATIONS_047_167.md','docs/research/BRUTE_DEVIATIONS_047_168.md','results/study-047/main/SEAL.json',
       'results/study-047/API_CHECKS_047.json','scripts/study047_storage.py']+NEW


def entries():
    L=[json.loads(x) for x in (ROOT/'results/RESEARCH_LEDGER.jsonl').read_text().splitlines() if x.strip()]
    i0=next(i for i,e in enumerate(L) if e.get('event')=='preregistration_048')
    return [{'event':e['event'],'commit':e.get('commit'),'note_time':str(e.get('note',''))[:25]} for e in L[i0:]]


def main():
    from experiments import brute_study_048 as ST
    ev=entries()
    write_new(ORDER,{'schema':'brute.commit-order.v1','study':'BRUTE-0450-CERTIFY16D-WALLFREE-SCALE20-048','order':[e['event'] for e in ev],'entries':ev})
    files={f:sha(ROOT/f) for f in sorted(set(FILES))}
    write_new(FREEZE,{'schema':'brute.source-freeze.v1','study':'BRUTE-0450-CERTIFY16D-WALLFREE-SCALE20-048','process':'lean','plan_sha256':sha(PLAN),
                      'conflict_cap':C48,'budget_conflicts':{'scale16':B16,'control':B16,'scale20':B20},'n_scale20':ST.N20,'sha256_files':files})
    print(len(files),'files frozen; C',C48,'B',B16,B20,'N20',ST.N20)


if __name__=='__main__':main()
