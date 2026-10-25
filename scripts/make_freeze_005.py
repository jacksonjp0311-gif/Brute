"""Write experiments/BRUTE_SOURCE_FREEZE_005.json (study-005 source lock). Refuses to overwrite.

The study-002/003/004 freezes stay in force; experiments/brute_common_005.check_freeze verifies all four.
"""
import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from experiments.brute_common_005 import FREEZE,PLAN,sha,write_new
FILES=sorted(['brute/changepoint.py','brute/release_version_030.py','brute/api/service_v030.py',
    'brute/api/schema/request.v1_3.json','brute/api/schema/response.v1_3.json',
    'experiments/BRUTE_PLAN_005.json','experiments/brute_common_005.py','experiments/brute_study_005.py',
    'experiments/brute_calibrate_005.py','experiments/v030_independent_reference.py','scripts/make_freeze_005.py',
    'tests/test_brute_changepoint.py','tests/test_api_contract_v030.py','tests/test_study_005.py'])


def build():
    return {'schema':'brute.source-freeze.v1','study':'BRUTE-030-CHANGEPOINT-005','status':'frozen',
            'also_requires':['experiments/BRUTE_SOURCE_FREEZE_002.json','experiments/BRUTE_SOURCE_FREEZE_003.json',
                             'experiments/BRUTE_SOURCE_FREEZE_004.json'],
            'plan_sha256':sha(PLAN),'preregistration_commit':'25fa47b',
            'sha256_files':{rel:sha(ROOT/rel) for rel in FILES}}


if __name__=='__main__':
    write_new(FREEZE,build());print(len(FILES),'files frozen')
