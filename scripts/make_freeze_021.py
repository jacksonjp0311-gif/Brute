"""Write experiments/BRUTE_SOURCE_FREEZE_021.json (study-021 source lock, BRUTE_PLAN_021 process). Refuses to overwrite.

Every earlier source freeze (002..020) and release freeze (v0.7.0_R1 .. v0.18.0) stays in force;
experiments/brute_common_021.check_freeze verifies all of them plus this one (G13).
The scoring scripts (make_gates_021, make_paired_021, make_reproducibility_021, clean_clone_021, tests/test_scoring_021)
are locked separately by the scoring_freeze_021 ledger entry (>= 600 s before run_start_021). tests/test_release_0190.py
and scripts/verify_release_0190.py are written at release, after the run, and are not frozen here.
"""
import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from experiments.brute_common_021 import FREEZE,PLAN,sha,write_new
FILES=sorted(['brute/anytimemargin.py','brute/api/certify8.py','brute/release_version_0190.py',
    'experiments/BRUTE_PLAN_021.json','experiments/BRUTE_PLAN_FREEZE_021.json','experiments/brute_common_021.py',
    'experiments/brute_study_021.py','experiments/v0190_reference.py',
    'scripts/check_seeds_021.py','scripts/make_freeze_021.py','scripts/run_reference_021.py','scripts/rate_math_021.py',
    'scripts/run_tests_0190.py','scripts/run_study_021.py','scripts/seal_021.py','scripts/watchdog_021.py','scripts/study021_storage.py',
    'scripts/hbsentinel_021.py','scripts/hb_attribution_021.py','scripts/api_check_021.py','scripts/drill_021.py',
    'requirements.txt','requirements-gmc.txt',
    'tests/test_seeds_0190.py','tests/test_study_0190.py','tests/test_anytime_0190.py','tests/test_certify8_0190.py',
    'tests/test_reference_0190.py','tests/test_scripts_021.py',
    'docs/research/v0.19.0/PLAN_021.md','docs/research/v0.19.0/ANYTIME_LEMMA_021.md',
    'docs/research/v0.19.0/RATE_MATH_021.md','docs/research/v0.19.0/RATE_MATH_021.json',
    'results/diag-021/SEEDCHECK_021.json','results/smoke-021/KILL_DRILL_021.json','results/smoke-021/RESUME_DRILL_021.json',
    'results/smoke-021/API_CHECK_021.json'])
DEVS=[]   # deviation numbers in force at the freeze (BRUTE_DEVIATIONS_021.md, #107 onward); filled before the freeze
EXTRA=[x for x in sys.argv[1:] if x.startswith('+')]   # '+path' adds a file written after this script (e.g. a deviations addendum)
FILES=sorted(FILES+[x[1:] for x in EXTRA])


def build(implementation_commits):
    return {'schema':'brute.source-freeze.v1','study':'BRUTE-0190-ANYTIME-021','status':'frozen',
            'also_requires':['experiments/BRUTE_SOURCE_FREEZE_00%d.json'%i for i in range(2,10)]+['experiments/BRUTE_SOURCE_FREEZE_0%d.json'%i for i in range(10,21)]+
                            ['experiments/BRUTE_RELEASE_FREEZE_070_R1.json','experiments/BRUTE_RELEASE_FREEZE_080.json',
                             'experiments/BRUTE_RELEASE_FREEZE_090_R1.json','experiments/BRUTE_RELEASE_FREEZE_0100.json',
                             'experiments/BRUTE_RELEASE_FREEZE_0110.json','experiments/BRUTE_RELEASE_FREEZE_0120.json',
                             'experiments/BRUTE_RELEASE_FREEZE_0130.json','experiments/BRUTE_RELEASE_FREEZE_0140.json',
                             'experiments/BRUTE_RELEASE_FREEZE_0150.json','experiments/BRUTE_RELEASE_FREEZE_0160.json','experiments/BRUTE_RELEASE_FREEZE_0170.json','experiments/BRUTE_RELEASE_FREEZE_0180.json'],
            'plan_sha256':sha(PLAN),'preregistration_commit':'a51275e','seedcheck_commit':'2358199',
            'reference_commits':['9fcca7f'],'implementation_commits':implementation_commits,'deviations_in_force':DEVS,
            'sha256_files':{rel:sha(ROOT/rel) for rel in FILES}}


if __name__=='__main__':
    write_new(FREEZE,build([x for x in sys.argv[1:] if not x.startswith('+')]));print(len(FILES),'files frozen')
