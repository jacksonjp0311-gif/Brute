"""Write experiments/BRUTE_SOURCE_FREEZE_009.json (study-009 source lock, BRUTE_PLAN_009 process_controls (6)). Refuses to overwrite.

The study-002..008 source freezes, the v0.6.0 release freeze r1 and the adopted files stay in force;
experiments/brute_common_009.check_freeze verifies all of them plus this one before any held-out run.
The scoring scripts (make_gates_009, make_paired_009) are locked separately by the scoring_freeze_009 ledger entry.
"""
import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from experiments.brute_common_009 import FREEZE,PLAN,sha,write_new,load
FILES=sorted(['brute/syncevent.py','brute/planner.py',
    'experiments/BRUTE_PLAN_009.json','experiments/brute_common_009.py','experiments/brute_study_009.py','experiments/worlds_009.py',
    'experiments/v070_reference.py','experiments/v070_xcheck.py',
    'scripts/check_seeds_009.py','scripts/diag_lag_009.py','scripts/make_freeze_009.py','scripts/run_reference_009.py',
    'scripts/check_planning_009.py','scripts/run_tests_070.py','scripts/run_study_009.py','scripts/seal_009.py',
    'requirements.txt','requirements-gmc.txt',
    'tests/test_syncevent.py','tests/test_planner.py','tests/test_run_tests_070.py','tests/test_v070_reference.py','tests/test_seeds_009.py',
    'results/study-009/SEEDCHECK_009.json','results/study-009/SPOT_SAMPLE_009.json'])


def build(implementation_commits):
    plan=load(PLAN)
    return {'schema':'brute.source-freeze.v1','study':'BRUTE-070-SYNCPLAN-009','status':'frozen',
            'also_requires':['experiments/BRUTE_SOURCE_FREEZE_00%d.json'%i for i in range(2,9)]+
                            ['experiments/BRUTE_RELEASE_FREEZE_060.json','experiments/BRUTE_RELEASE_FREEZE_060_R1.json'],
            'plan_sha256':sha(PLAN),'preregistration_commit':'3825ad3','seedcheck_commit':'8bf979a','diagnostic_commit':'496e11d',
            'reference_commit':'5349433','adopted_files_commit':'3a31e3b','adopted_files':plan['adopted_files']['files'],
            'implementation_commits':implementation_commits,
            'sha256_files':{rel:sha(ROOT/rel) for rel in FILES}}


if __name__=='__main__':
    write_new(FREEZE,build(sys.argv[1:]));print(len(FILES),'files frozen')
