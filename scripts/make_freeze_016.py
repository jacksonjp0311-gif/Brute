"""Write experiments/BRUTE_SOURCE_FREEZE_016.json (study-016 source lock, BRUTE_PLAN_016 process). Refuses to overwrite.

The study-002..015 source freezes and the v0.7.0_R1 / v0.8.0 / v0.9.0_R1 / v0.10.0 / v0.11.0 / v0.12.0 / v0.13.0 release
freezes stay in force; experiments/brute_common_016.check_freeze verifies all of them plus this one (G13).
The scoring scripts (make_gates_016, make_paired_016, make_reproducibility_016, clean_clone_016) are locked separately by
the scoring_freeze_016 ledger entry (>= 600 s before run_start_016). tests/test_release_0140.py and
scripts/verify_release_0140.py are written at release, after the run, and are not frozen here.
"""
import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from experiments.brute_common_016 import FREEZE,PLAN,sha,write_new
FILES=sorted(['brute/deferredsplit.py','brute/api/certify4.py','brute/release_version_0140.py',
    'experiments/BRUTE_PLAN_016.json','experiments/BRUTE_PLAN_FREEZE_016.json','experiments/brute_common_016.py',
    'experiments/brute_study_016.py','experiments/v0140_reference.py',
    'scripts/check_seeds_016.py','scripts/diag_license_016.py','scripts/make_freeze_016.py','scripts/run_reference_016.py',
    'scripts/run_tests_0140.py','scripts/run_study_016.py','scripts/seal_016.py','scripts/watchdog_016.py','scripts/study016_storage.py',
    'requirements.txt','requirements-gmc.txt',
    'tests/test_seeds_016.py','tests/test_study_016.py','tests/test_deferredsplit_016.py','tests/test_api_certify4_0140.py',
    'tests/test_v0140_reference.py','tests/test_scripts_016.py','docs/research/BRUTE_DEVIATIONS_016.md',
    'docs/research/v0.14.0/RATE_MATH_016.md','results/diag-016/SEEDCHECK_016.json','results/diag-016/DIAG_LICENSE_016.json'])


def build(implementation_commits):
    return {'schema':'brute.source-freeze.v1','study':'BRUTE-0140-DEFERRED-SPLIT-016','status':'frozen',
            'also_requires':['experiments/BRUTE_SOURCE_FREEZE_00%d.json'%i for i in range(2,10)]+['experiments/BRUTE_SOURCE_FREEZE_0%d.json'%i for i in (10,11,12,13,14,15)]+
                            ['experiments/BRUTE_RELEASE_FREEZE_070_R1.json','experiments/BRUTE_RELEASE_FREEZE_080.json',
                             'experiments/BRUTE_RELEASE_FREEZE_090_R1.json','experiments/BRUTE_RELEASE_FREEZE_0100.json',
                             'experiments/BRUTE_RELEASE_FREEZE_0110.json','experiments/BRUTE_RELEASE_FREEZE_0120.json',
                             'experiments/BRUTE_RELEASE_FREEZE_0130.json'],
            'plan_sha256':sha(PLAN),'preregistration_commit':'498d768','seedcheck_commit':'35b9840','diagnosis_commit':'afb89a9',
            'reference_commits':['ac717c4'],'implementation_commits':implementation_commits,'deviations_in_force':[75,76,77,78,79],
            'sha256_files':{rel:sha(ROOT/rel) for rel in FILES}}


if __name__=='__main__':
    write_new(FREEZE,build(sys.argv[1:]));print(len(FILES),'files frozen')
