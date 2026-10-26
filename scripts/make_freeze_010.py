"""Write experiments/BRUTE_SOURCE_FREEZE_010.json (study-010 source lock, BRUTE_PLAN_010 process controls). Refuses to overwrite.

The study-002..009 source freezes, the adopted files and the v0.7.0 release freeze r1 stay in force;
experiments/brute_common_010.check_freeze verifies all of them plus this one (G13).
The scoring scripts (make_gates_010, make_paired_010, make_reproducibility_010) are locked separately by the
scoring_freeze_010 ledger entry (>= 10 minutes before run_start_010).
tests/test_run_tests_080.py, tests/test_v080_xcheck.py and tests/test_diag_stale_010.py are frozen here although the plan's
freeze_rule list does not name them (disclosed deviation); tests/test_release_080.py and scripts/verify_release_080.py are
written at release, after the run, and are not frozen here.
"""
import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from experiments.brute_common_010 import FREEZE,PLAN,sha,write_new
FILES=sorted(['brute/jumphull.py','brute/align.py',
    'experiments/BRUTE_PLAN_010.json','experiments/brute_common_010.py','experiments/brute_study_010.py','experiments/worlds_010.py',
    'experiments/v080_reference.py','experiments/v080_xcheck.py',
    'scripts/check_seeds_010.py','scripts/diag_stale_010.py','scripts/make_freeze_010.py','scripts/run_reference_010.py',
    'scripts/run_tests_080.py','scripts/run_study_010.py','scripts/seal_010.py','scripts/watchdog_010.py',
    'requirements.txt','requirements-gmc.txt',
    'tests/test_jumphull.py','tests/test_align.py','tests/test_v080_reference.py','tests/test_seeds_010.py','tests/test_watchdog_010.py',
    'tests/test_run_tests_080.py','tests/test_v080_xcheck.py','tests/test_diag_stale_010.py',
    'results/study-010/SEEDCHECK_010.json','results/study-010/SPOT_SAMPLE_010.json','results/study-010/DIAG_REPLAY_009.json'])


def build(implementation_commits):
    return {'schema':'brute.source-freeze.v1','study':'BRUTE-080-ALIGN-010','status':'frozen',
            'also_requires':['experiments/BRUTE_SOURCE_FREEZE_00%d.json'%i for i in range(2,10)]+['experiments/BRUTE_RELEASE_FREEZE_070_R1.json'],
            'plan_sha256':sha(PLAN),'preregistration_commit':'881f0a6','seedcheck_commit':'c80bdd7','diagnostic_commit':'299babf',
            'reference_commit':'385ea23','implementation_commits':implementation_commits,
            'sha256_files':{rel:sha(ROOT/rel) for rel in FILES}}


if __name__=='__main__':
    write_new(FREEZE,build(sys.argv[1:]));print(len(FILES),'files frozen')
