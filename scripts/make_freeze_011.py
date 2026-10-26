"""Write experiments/BRUTE_SOURCE_FREEZE_011.json (study-011 source lock, BRUTE_PLAN_011 process step 5). Refuses to overwrite.

The study-002..010 source freezes, the adopted files and the v0.7.0 r1 / v0.8.0 release freezes stay in force;
experiments/brute_common_011.check_freeze verifies all of them plus this one (G13).
The scoring scripts (make_gates_011, make_paired_011, make_reproducibility_011, clean_clone_011) are locked separately by
the scoring_freeze_011 ledger entry (>= 10 minutes before run_start_011). tests/test_release_090.py and
scripts/verify_release_090.py are written at release, after the run, and are not frozen here.
tests/test_study_011.py and tests/test_run_tests_090.py are frozen here although the plan's freeze_rule list does not
name them (it lists the files that must descend from the plan commit; freezing more is stricter).
"""
import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from experiments.brute_common_011 import FREEZE,PLAN,sha,write_new
FILES=sorted(['brute/jumpwindow.py','brute/jumphull.py','brute/align.py',
    'experiments/BRUTE_PLAN_011.json','experiments/brute_common_011.py','experiments/brute_study_011.py','experiments/worlds_011.py',
    'experiments/v090_reference.py',
    'scripts/check_seeds_011.py','scripts/feasibility_011.py','scripts/make_freeze_011.py','scripts/run_reference_011.py',
    'scripts/run_tests_090.py','scripts/run_study_011.py','scripts/seal_011.py','scripts/watchdog_011.py','scripts/study011_storage.py',
    'scripts/diag_lag_011.py','requirements.txt','requirements-gmc.txt',
    'tests/test_jumpwindow.py','tests/test_v090_reference.py','tests/test_seeds_011.py','tests/test_watchdog_011.py',
    'tests/test_feasibility_011.py','tests/test_study_011.py','tests/test_run_tests_090.py','tests/test_diag_lag_011.py',
    'results/study-011/SEEDCHECK_011.json','results/diag-011/LAG_DIAG_SEEN.json'])


def build(implementation_commits):
    return {'schema':'brute.source-freeze.v1','study':'BRUTE-090-WINDOW-011','status':'frozen',
            'also_requires':['experiments/BRUTE_SOURCE_FREEZE_00%d.json'%i for i in range(2,10)]+['experiments/BRUTE_SOURCE_FREEZE_010.json',
                             'experiments/BRUTE_RELEASE_FREEZE_070_R1.json','experiments/BRUTE_RELEASE_FREEZE_080.json'],
            'plan_sha256':sha(PLAN),'preregistration_commit':'7950513','diagnostic_commit':'a5ef9c8','seedcheck_commit':'06249f7',
            'reference_commit':'d5c6a54','implementation_commits':implementation_commits,
            'sha256_files':{rel:sha(ROOT/rel) for rel in FILES}}


if __name__=='__main__':
    write_new(FREEZE,build(sys.argv[1:]));print(len(FILES),'files frozen')
