"""Write experiments/BRUTE_SOURCE_FREEZE_018.json (study-018 source lock, BRUTE_PLAN_018 process). Refuses to overwrite.

The study-002..016 source freezes and the v0.7.0_R1 / v0.8.0 / v0.9.0_R1 / v0.10.0 / v0.11.0 / v0.12.0 / v0.13.0 / v0.14.0 release
freezes stay in force; experiments/brute_common_018.check_freeze verifies all of them plus this one (G13).
The scoring scripts (make_gates_018, make_paired_018, make_reproducibility_018, clean_clone_018) are locked separately by
the scoring_freeze_018 ledger entry (>= 600 s before run_start_018). tests/test_release_0150.py and
scripts/verify_release_0150.py are written at release, after the run, and are not frozen here.
"""
import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from experiments.brute_common_018 import FREEZE,PLAN,sha,write_new
FILES=sorted(['brute/boundedlookahead.py','brute/api/certify5.py','brute/release_version_0150.py',
    'experiments/BRUTE_PLAN_018.json','experiments/BRUTE_PLAN_FREEZE_018.json','experiments/brute_common_018.py',
    'experiments/brute_study_018.py','experiments/v0150_reference.py',
    'scripts/check_seeds_018.py','scripts/make_freeze_018.py','scripts/run_reference_018.py',
    'scripts/run_tests_0150.py','scripts/run_study_018.py','scripts/seal_018.py','scripts/watchdog_018.py','scripts/study017_storage.py',
    'scripts/hbsentinel_018.py','scripts/hb_attribution_018.py',
    'requirements.txt','requirements-gmc.txt',
    'tests/test_seeds_0150.py','tests/test_study_018.py','tests/test_boundedlookahead_0150.py','tests/test_api_certify5_0150.py',
    'tests/test_v0150_reference.py','tests/test_scripts_018.py','docs/research/BRUTE_DEVIATIONS_018.md',
    'docs/research/v0.15.0/RATE_MATH_018.md','results/diag-017/SEEDCHECK_018.json'])


def build(implementation_commits):
    return {'schema':'brute.source-freeze.v1','study':'BRUTE-0160-NOISY-OBSERVATION-018','status':'frozen',
            'also_requires':['experiments/BRUTE_SOURCE_FREEZE_00%d.json'%i for i in range(2,10)]+['experiments/BRUTE_SOURCE_FREEZE_0%d.json'%i for i in (10,11,12,13,14,15,16)]+
                            ['experiments/BRUTE_RELEASE_FREEZE_070_R1.json','experiments/BRUTE_RELEASE_FREEZE_080.json',
                             'experiments/BRUTE_RELEASE_FREEZE_090_R1.json','experiments/BRUTE_RELEASE_FREEZE_0100.json',
                             'experiments/BRUTE_RELEASE_FREEZE_0110.json','experiments/BRUTE_RELEASE_FREEZE_0120.json',
                             'experiments/BRUTE_RELEASE_FREEZE_0130.json','experiments/BRUTE_RELEASE_FREEZE_0140.json'],
            'plan_sha256':sha(PLAN),'preregistration_commit':'908fe9b','deviations_commit':'f720f1b','seedcheck_commit':'5506eff',
            'reference_commits':['5c88600'],'implementation_commits':implementation_commits,'deviations_in_force':[86,87,88,89,90,91],
            'sha256_files':{rel:sha(ROOT/rel) for rel in FILES}}


if __name__=='__main__':
    write_new(FREEZE,build(sys.argv[1:]));print(len(FILES),'files frozen')
