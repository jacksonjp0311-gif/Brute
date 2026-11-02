"""Lean source freeze for study-059: writes experiments/COMMIT_ORDER_059.json (ledger events from preregistration_059) and
experiments/BRUTE_SOURCE_FREEZE_059.json (plan and source/scoring/test/release-tooling/deviation hashes; FILES = the 058 list, the
remaining 058 files (commit order, freeze, deviations #190 and #191, the sealed 058 main SEAL, its recount, reference, API checks,
tests and gates), plan 059 and the new 059 files). Plan 059 freeze rule: caps [C, B, K], bound, arms, arm noise (eps, eps_bar), delta,
workers, the stop rule (conflict-only, hook None, 900 s hard kill), the noise RNG and the cut variable n59 = brute_study_059.N59 are
part of the freeze. Refuses overwrite. New file; built from scripts/make_freeze_058.py (frozen).
  PYTHONPATH=. python scripts/make_freeze_059.py"""
import json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from experiments.brute_common_059 import (PLAN,FREEZE,sha,write_new,C59,B59,K59,BOUND,ALL_ARMS,ARM_NOISE,DELTA,WORKERS,HARD_KILL_S,STOP_RULE,NOISE_RNG)
from scripts.make_freeze_058 import FILES as FILES_058
ORDER=ROOT/'experiments/COMMIT_ORDER_059.json'
STUDY='BRUTE-0560-NOISYWIDE-059'
NEW=['brute/api/certify20n.py','brute/release_version_0560.py','experiments/worlds_059.py','experiments/brute_common_059.py',
     'experiments/brute_study_059.py','scripts/check_seeds_059.py','scripts/api_checks_059.py','scripts/recount_059.py',
     'scripts/run_reference_059.py','scripts/make_gates_059.py','scripts/make_freeze_059.py','scripts/study059_storage.py',
     'scripts/verify_release_0560.py','scripts/run_tests_0560.py','scripts/prefreeze_smoke_059.py','tests/test_certify20n.py',
     'tests/test_scripts_059.py','tests/test_release_0560.py','docs/research/BRUTE_DEVIATIONS_059_192.md',
     'results/diag-059/SEEDCHECK_059.json','results/diag-059/PREFREEZE_SMOKE_GATES_059.json']
FILES=list(FILES_058)+['experiments/COMMIT_ORDER_058.json','experiments/BRUTE_SOURCE_FREEZE_058.json',
       'docs/research/BRUTE_DEVIATIONS_058_190.md','docs/research/BRUTE_DEVIATIONS_058_191.md',
       'results/study-058/main/SEAL.json','results/study-058/main/RECOUNT_058.json','results/study-058/main/REFERENCE_058.json',
       'results/study-058/API_CHECKS_058.json','results/study-058/TEST_SUITE_058.json',
       'results/study-058/GATES_058.json','experiments/BRUTE_PLAN_059.json']+NEW


def entries():
    L=[json.loads(x) for x in (ROOT/'results/RESEARCH_LEDGER.jsonl').read_text().splitlines() if x.strip()]
    i0=next(i for i,e in enumerate(L) if e.get('event')=='preregistration_059')
    return [{'event':e['event'],'commit':e.get('commit'),'note_time':str(e.get('note',''))[:25]} for e in L[i0:]]


def main():
    from experiments import brute_study_059 as ST
    ev=entries()
    write_new(ORDER,{'schema':'brute.commit-order.v1','study':STUDY,'order':[e['event'] for e in ev],'entries':ev})
    files={f:sha(ROOT/f) for f in sorted(set(FILES))}
    write_new(FREEZE,{'schema':'brute.source-freeze.v1','study':STUDY,'process':'lean','plan_sha256':sha(PLAN),
                      'caps':[C59,B59,K59],'max_chunks':None,'bound':BOUND,'arms':list(ALL_ARMS),'arm_noise':ARM_NOISE,'delta':DELTA,
                      'workers':WORKERS,'stop':{'hard_kill_s':HARD_KILL_S,'stop_rule':STOP_RULE},'noise_rng':NOISE_RNG,
                      'n59':ST.N59,'sha256_files':files})
    print(len(files),'files frozen; caps',[C59,B59,K59],'N59',ST.N59)


if __name__=='__main__':main()
