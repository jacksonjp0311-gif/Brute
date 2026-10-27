"""Write experiments/BRUTE_SOURCE_FREEZE_014.json (study-014 source lock, BRUTE_PLAN_014 process step 5). Refuses to overwrite.

The study-002..013 source freezes and the v0.7.0_R1 / v0.8.0 / v0.9.0_R1 / v0.10.0 / v0.11.0 release freezes stay in force;
experiments/brute_common_014.check_freeze verifies all of them plus this one (G13).
The scoring scripts (make_gates_014, make_paired_014, make_reproducibility_014, clean_clone_014) are locked separately by
the scoring_freeze_014 ledger entry (>= 10 minutes before run_start_014). tests/test_release_0120.py and
scripts/verify_release_0120.py are written at release, after the run, and are not frozen here.
"""
import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from experiments.brute_common_014 import FREEZE,PLAN,sha,write_new
FILES=sorted(['brute/boundedtransfer.py','brute/api/certify2.py',
    'experiments/BRUTE_PLAN_014.json','experiments/BRUTE_PLAN_FREEZE_014.json','experiments/brute_common_014.py',
    'experiments/brute_study_014.py','experiments/v0120_reference.py',
    'scripts/check_seeds_014.py','scripts/make_freeze_014.py','scripts/run_reference_014.py','scripts/run_tests_0120.py',
    'scripts/run_study_014.py','scripts/seal_014.py','scripts/watchdog_014.py','scripts/study014_storage.py',
    'scripts/diag_license_014.py','scripts/diag_license_014b.py','requirements.txt','requirements-gmc.txt',
    'tests/test_seeds_014.py','tests/test_study_014.py','tests/test_boundedtransfer_014.py','tests/test_api_certify2_0120.py',
    'tests/test_v0120_reference.py','tests/test_scripts_014.py','docs/research/BRUTE_DEVIATIONS_014.md',
    'results/diag-014/LICENSE_DIAG_SEEN.json','results/diag-014/LICENSE_DIAG_SEEN_B.json','results/diag-014/SEEDCHECK_014.json'])


def build(implementation_commits):
    return {'schema':'brute.source-freeze.v1','study':'BRUTE-0120-BOUNDED-TRANSFER-014','status':'frozen',
            'also_requires':['experiments/BRUTE_SOURCE_FREEZE_00%d.json'%i for i in range(2,10)]+['experiments/BRUTE_SOURCE_FREEZE_0%d.json'%i for i in (10,11,12,13)]+
                            ['experiments/BRUTE_RELEASE_FREEZE_070_R1.json','experiments/BRUTE_RELEASE_FREEZE_080.json',
                             'experiments/BRUTE_RELEASE_FREEZE_090_R1.json','experiments/BRUTE_RELEASE_FREEZE_0100.json',
                             'experiments/BRUTE_RELEASE_FREEZE_0110.json'],
            'plan_sha256':sha(PLAN),'preregistration_commit':'ef865e7','diagnostic_commits':['d613662','59c3560'],'seedcheck_commit':'f87f5bc',
            'reference_commit':'89ff5b8','implementation_commits':implementation_commits,'deviations_in_force':[59,60,61],
            'sha256_files':{rel:sha(ROOT/rel) for rel in FILES}}


if __name__=='__main__':
    write_new(FREEZE,build(sys.argv[1:]));print(len(FILES),'files frozen')
