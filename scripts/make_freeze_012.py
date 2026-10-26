"""Write experiments/BRUTE_SOURCE_FREEZE_012.json (study-012 source lock, BRUTE_PLAN_012 process step 5). Refuses to overwrite.

The study-002..011 source freezes and the v0.7.0_R1 / v0.8.0 / v0.9.0_R1 release freezes (0.9.0 superseded by 0.9.0_R1) stay in force;
experiments/brute_common_012.check_freeze verifies all of them plus this one (G13).
The scoring scripts (make_gates_012, make_paired_012, make_reproducibility_012, clean_clone_012) are locked separately by
the scoring_freeze_012 ledger entry (>= 10 minutes before run_start_012). tests/test_release_0100.py and
scripts/verify_release_0100.py are written at release, after the run, and are not frozen here.
"""
import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from experiments.brute_common_012 import FREEZE,PLAN,sha,write_new
FILES=sorted(['brute/supportwindow.py','brute/bigstate.py','brute/transfer.py',
    'experiments/BRUTE_PLAN_012.json','experiments/BRUTE_PLAN_FREEZE_012.json','experiments/brute_common_012.py',
    'experiments/brute_study_012.py','experiments/worlds_012.py','experiments/v0100_reference.py',
    'scripts/check_seeds_012.py','scripts/make_freeze_012.py','scripts/run_reference_012.py','scripts/run_tests_0100.py',
    'scripts/run_study_012.py','scripts/seal_012.py','scripts/watchdog_012.py','scripts/study012_storage.py',
    'scripts/diag_downgrade_012.py','scripts/diag_transfer_seen_012.py','scripts/gti_k080_012.py','requirements.txt','requirements-gmc.txt',
    'tests/test_seeds_012.py','tests/test_study_012.py','tests/test_v0100_reference.py',
    'results/diag-012/DOWNGRADE_DIAG_SEEN.json','results/diag-012/TRANSFER_DIAG_SEEN.json'])


def build(implementation_commits):
    return {'schema':'brute.source-freeze.v1','study':'BRUTE-0100-SUPPORT-TRANSFER-012','status':'frozen',
            'also_requires':['experiments/BRUTE_SOURCE_FREEZE_00%d.json'%i for i in range(2,10)]+['experiments/BRUTE_SOURCE_FREEZE_010.json',
                             'experiments/BRUTE_SOURCE_FREEZE_011.json','experiments/BRUTE_RELEASE_FREEZE_070_R1.json','experiments/BRUTE_RELEASE_FREEZE_080.json',
                             'experiments/BRUTE_RELEASE_FREEZE_090_R1.json'],
            'plan_sha256':sha(PLAN),'preregistration_commit':'0cccf0d','diagnostic_commit':'6494a35','seedcheck_commit':'9f4d4db',
            'reference_commit':'a44a8da','implementation_commits':implementation_commits,'deviations_in_force':[49,50],
            'sha256_files':{rel:sha(ROOT/rel) for rel in FILES}}


if __name__=='__main__':
    write_new(FREEZE,build(sys.argv[1:]));print(len(FILES),'files frozen')
