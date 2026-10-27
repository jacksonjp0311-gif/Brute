"""Write experiments/BRUTE_SOURCE_FREEZE_018.json (study-018 source lock, BRUTE_PLAN_018 process). Refuses to overwrite.

Every earlier source freeze (002..017) and release freeze (v0.7.0_R1 .. v0.15.0) stays in force;
experiments/brute_common_018.check_freeze verifies all of them plus this one (G13).
The scoring scripts (make_gates_018, make_paired_018, make_reproducibility_018, clean_clone_018, tests/test_scoring_018)
are locked separately by the scoring_freeze_018 ledger entry (>= 600 s before run_start_018). tests/test_release_0160.py
and scripts/verify_release_0160.py are written at release, after the run, and are not frozen here.
"""
import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from experiments.brute_common_018 import FREEZE,PLAN,sha,write_new
FILES=sorted(['brute/noisyregion.py','brute/api/certify6.py','brute/release_version_0160.py',
    'experiments/BRUTE_PLAN_018.json','experiments/BRUTE_PLAN_FREEZE_018.json','experiments/brute_common_018.py',
    'experiments/brute_study_018.py','experiments/v0160_reference.py',
    'scripts/check_seeds_018.py','scripts/make_freeze_018.py','scripts/run_reference_018.py','scripts/rate_math_018.py',
    'scripts/run_tests_0160.py','scripts/run_study_018.py','scripts/seal_018.py','scripts/watchdog_018.py','scripts/study018_storage.py',
    'scripts/hbsentinel_018.py','scripts/hb_attribution_018.py',
    'requirements.txt','requirements-gmc.txt',
    'tests/test_seeds_0160.py','tests/test_study_0160.py','tests/test_noisyregion_0160.py','tests/test_api_certify6_0160.py',
    'tests/test_v0160_reference.py','tests/test_scripts_018.py',
    'docs/research/BRUTE_DEVIATIONS_018.md','docs/research/BRUTE_DEVIATIONS_018_ADDENDUM_1.md',
    'docs/research/v0.16.0/PLAN_018.md','docs/research/v0.16.0/RATE_MATH_018.md','docs/research/v0.16.0/RATE_MATH_018.json',
    'results/diag-018/SEEDCHECK_018.json','results/smoke-018/KILL_DRILL_018.json'])


def build(implementation_commits):
    return {'schema':'brute.source-freeze.v1','study':'BRUTE-0160-NOISY-OBSERVATION-018','status':'frozen',
            'also_requires':['experiments/BRUTE_SOURCE_FREEZE_00%d.json'%i for i in range(2,10)]+['experiments/BRUTE_SOURCE_FREEZE_0%d.json'%i for i in range(10,18)]+
                            ['experiments/BRUTE_RELEASE_FREEZE_070_R1.json','experiments/BRUTE_RELEASE_FREEZE_080.json',
                             'experiments/BRUTE_RELEASE_FREEZE_090_R1.json','experiments/BRUTE_RELEASE_FREEZE_0100.json',
                             'experiments/BRUTE_RELEASE_FREEZE_0110.json','experiments/BRUTE_RELEASE_FREEZE_0120.json',
                             'experiments/BRUTE_RELEASE_FREEZE_0130.json','experiments/BRUTE_RELEASE_FREEZE_0140.json',
                             'experiments/BRUTE_RELEASE_FREEZE_0150.json'],
            'plan_sha256':sha(PLAN),'preregistration_commit':'9beb459','deviations_commit':'a74cbaf','seedcheck_commit':'503d61a',
            'reference_commits':['f6ef422'],'implementation_commits':implementation_commits,'deviations_in_force':[97,98,99],
            'sha256_files':{rel:sha(ROOT/rel) for rel in FILES}}


if __name__=='__main__':
    write_new(FREEZE,build(sys.argv[1:]));print(len(FILES),'files frozen')
