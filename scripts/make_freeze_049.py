"""Lean source freeze for study-049: writes experiments/COMMIT_ORDER_049.json (ledger events from preregistration_049) and
experiments/BRUTE_SOURCE_FREEZE_049.json (plan and source/scoring/test/release-tooling/deviation hashes; FILES = the 048 list, the
remaining 048 files (plan, commit order, freeze, deviations #169 and #170, the sealed 048 main SEAL, its API checks and gates), and
the new 049 files). Plan 049 freeze_rule: C, B16, B20, max_chunks defaults and the case lists are part of the freeze
(conflict_cap, budget_conflicts, max_chunks, n_scale20 = brute_study_049.N20, r_scale20 = brute_study_049.R20). Refuses
overwrite. New file; built from scripts/make_freeze_048.py (frozen).
  PYTHONPATH=. python scripts/make_freeze_049.py"""
import json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from experiments.brute_common_049 import PLAN,FREEZE,sha,write_new,C49,B16,B20,MAX_CHUNKS
from scripts.make_freeze_048 import FILES as FILES_048
ORDER=ROOT/'experiments/COMMIT_ORDER_049.json'
NEW=['brute/api/certify16e.py','brute/release_version_0460.py','experiments/brute_common_049.py','experiments/brute_study_049.py',
     'scripts/check_seeds_049.py','scripts/api_checks_049.py','scripts/recount_049.py','scripts/run_reference_049.py','scripts/make_gates_049.py',
     'scripts/make_freeze_049.py','scripts/push_checkpoint_049.py','scripts/study049_storage.py','scripts/verify_release_0460.py',
     'scripts/run_tests_0460.py','scripts/prefreeze_smoke_049.py','tests/test_certify16e.py','tests/test_scripts_049.py','tests/test_release_0460.py',
     'docs/research/BRUTE_DEVIATIONS_049_171.md','results/diag-049/SEEDCHECK_049.json','results/diag-049/PREFREEZE_SMOKE_GATES_049.json']
FILES=list(FILES_048)+['experiments/BRUTE_PLAN_048.json','experiments/COMMIT_ORDER_048.json','experiments/BRUTE_SOURCE_FREEZE_048.json',
       'docs/research/BRUTE_DEVIATIONS_048_169.md','docs/research/BRUTE_DEVIATIONS_048_170.md','results/study-048/main/SEAL.json',
       'results/study-048/API_CHECKS_048.json','results/study-048/GATES_048.json']+NEW


def entries():
    L=[json.loads(x) for x in (ROOT/'results/RESEARCH_LEDGER.jsonl').read_text().splitlines() if x.strip()]
    i0=next(i for i,e in enumerate(L) if e.get('event')=='preregistration_049')
    return [{'event':e['event'],'commit':e.get('commit'),'note_time':str(e.get('note',''))[:25]} for e in L[i0:]]


def main():
    from experiments import brute_study_049 as ST
    ev=entries()
    write_new(ORDER,{'schema':'brute.commit-order.v1','study':'BRUTE-0460-CERTIFY16E-RESUME-SCALE20-049','order':[e['event'] for e in ev],'entries':ev})
    files={f:sha(ROOT/f) for f in sorted(set(FILES))}
    write_new(FREEZE,{'schema':'brute.source-freeze.v1','study':'BRUTE-0460-CERTIFY16E-RESUME-SCALE20-049','process':'lean','plan_sha256':sha(PLAN),
                      'conflict_cap':C49,'budget_conflicts':{'scale16':B16,'control':B16,'scale20':B20},'max_chunks':MAX_CHUNKS,
                      'n_scale20':ST.N20,'r_scale20':ST.R20,'sha256_files':files})
    print(len(files),'files frozen; C',C49,'B',B16,B20,'max_chunks',MAX_CHUNKS,'N20',ST.N20,'R20',ST.R20)


if __name__=='__main__':main()
