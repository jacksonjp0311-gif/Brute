"""Write experiments/BRUTE_SOURCE_FREEZE_015.json (study-015 source lock, BRUTE_PLAN_015 process). Refuses to overwrite.

The study-002..014 source freezes and the v0.7.0_R1 / v0.8.0 / v0.9.0_R1 / v0.10.0 / v0.11.0 / v0.12.0 release freezes stay
in force; experiments/brute_common_015.check_freeze verifies all of them plus this one (G13).
The scoring scripts (make_gates_015, make_paired_015, make_reproducibility_015, clean_clone_015) are locked separately by
the scoring_freeze_015 ledger entry (>= 600 s before run_start_015). tests/test_release_0130.py and
scripts/verify_release_0130.py are written at release, after the run, and are not frozen here.
"""
import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from experiments.brute_common_015 import FREEZE,PLAN,sha,write_new
FILES=sorted(['brute/regionsplit.py','brute/api/certify3.py','brute/release_version_0130.py',
    'experiments/BRUTE_PLAN_015.json','experiments/BRUTE_PLAN_FREEZE_015.json','experiments/brute_common_015.py',
    'experiments/brute_study_015.py','experiments/v0130_reference.py',
    'scripts/check_seeds_015.py','scripts/make_freeze_015.py','scripts/run_reference_015.py','scripts/run_tests_0130.py',
    'scripts/run_study_015.py','scripts/run_study_015_R1.py','scripts/seal_015.py','scripts/watchdog_015.py','scripts/study015_storage.py',
    'requirements.txt','requirements-gmc.txt',
    'tests/test_seeds_015.py','tests/test_study_015.py','tests/test_regionsplit_015.py','tests/test_api_certify3_0130.py',
    'tests/test_v0130_reference.py','tests/test_scripts_015.py','tests/test_run_study_015_R1.py','docs/research/BRUTE_DEVIATIONS_015.md',
    'docs/research/v0.13.0/RATE_MATH_015.md','results/diag-015/SEEDCHECK_015.json'])


def build(implementation_commits):
    return {'schema':'brute.source-freeze.v1','study':'BRUTE-0130-REGION-SPLIT-015','status':'frozen',
            'also_requires':['experiments/BRUTE_SOURCE_FREEZE_00%d.json'%i for i in range(2,10)]+['experiments/BRUTE_SOURCE_FREEZE_0%d.json'%i for i in (10,11,12,13,14)]+
                            ['experiments/BRUTE_RELEASE_FREEZE_070_R1.json','experiments/BRUTE_RELEASE_FREEZE_080.json',
                             'experiments/BRUTE_RELEASE_FREEZE_090_R1.json','experiments/BRUTE_RELEASE_FREEZE_0100.json',
                             'experiments/BRUTE_RELEASE_FREEZE_0110.json','experiments/BRUTE_RELEASE_FREEZE_0120.json'],
            'plan_sha256':sha(PLAN),'preregistration_commit':'c6bfcb3','seedcheck_commit':'f6fbb92',
            'reference_commits':['f95a176','305b739'],'implementation_commits':implementation_commits,'deviations_in_force':list(range(64,74)),
            'sha256_files':{rel:sha(ROOT/rel) for rel in FILES}}


if __name__=='__main__':
    write_new(FREEZE,build(sys.argv[1:]));print(len(FILES),'files frozen')
