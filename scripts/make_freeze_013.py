"""Write experiments/BRUTE_SOURCE_FREEZE_013.json (study-013 source lock, BRUTE_PLAN_013 process step 6). Refuses to overwrite.

The study-002..012 source freezes and the v0.7.0_R1 / v0.8.0 / v0.9.0_R1 / v0.10.0 release freezes stay in force;
experiments/brute_common_013.check_freeze verifies all of them plus this one (G13).
The scoring scripts (make_gates_013, make_paired_013, make_reproducibility_013, clean_clone_013) are locked separately by
the scoring_freeze_013 ledger entry (>= 10 minutes before run_start_013). tests/test_release_0110.py and
scripts/verify_release_0110.py are written at release, after the run, and are not frozen here.
"""
import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from experiments.brute_common_013 import FREEZE,PLAN,sha,write_new
FILES=sorted(['brute/soundtransfer.py','brute/api/certify.py',
    'experiments/BRUTE_PLAN_013.json','experiments/BRUTE_PLAN_FREEZE_013.json','experiments/brute_common_013.py',
    'experiments/brute_study_013.py','experiments/worlds_013.py','experiments/v0110_reference.py',
    'scripts/check_seeds_013.py','scripts/make_freeze_013.py','scripts/run_reference_013.py','scripts/run_tests_0110.py',
    'scripts/run_study_013.py','scripts/seal_013.py','scripts/watchdog_013.py','scripts/study013_storage.py',
    'scripts/diag_applicability_013.py','requirements.txt','requirements-gmc.txt',
    'tests/test_seeds_013.py','tests/test_study_013.py','tests/test_soundtransfer_013.py','tests/test_api_certify_0110.py','results/diag-013/APPLICABILITY_DIAG_SEEN.json','results/diag-013/SEEDCHECK_013.json'])


def build(implementation_commits):
    return {'schema':'brute.source-freeze.v1','study':'BRUTE-0110-SOUND-TRANSFER-013','status':'frozen',
            'also_requires':['experiments/BRUTE_SOURCE_FREEZE_00%d.json'%i for i in range(2,10)]+['experiments/BRUTE_SOURCE_FREEZE_0%d.json'%i for i in (10,11,12)]+
                            ['experiments/BRUTE_RELEASE_FREEZE_070_R1.json','experiments/BRUTE_RELEASE_FREEZE_080.json',
                             'experiments/BRUTE_RELEASE_FREEZE_090_R1.json','experiments/BRUTE_RELEASE_FREEZE_0100.json'],
            'plan_sha256':sha(PLAN),'preregistration_commit':'bb1d96e','diagnostic_commit':'e0aa431','seedcheck_commit':'780be3b',
            'reference_commit':'eed2ada','implementation_commits':implementation_commits,'deviations_in_force':[52],
            'sha256_files':{rel:sha(ROOT/rel) for rel in FILES}}


if __name__=='__main__':
    write_new(FREEZE,build(sys.argv[1:]));print(len(FILES),'files frozen')
