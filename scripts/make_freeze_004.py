"""Write experiments/BRUTE_SOURCE_FREEZE_004.json (study-004 source lock). Refuses to overwrite.

The study-002 and study-003 freezes stay in force; experiments/brute_common_004.check_freeze verifies all three.
"""
import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from experiments.brute_common_004 import FREEZE,PLAN,sha,write_new
FILES=sorted(['brute/active.py','brute/release_version.py','brute/api/service_v020.py',
    'brute/api/schema/request.v1_2.json','brute/api/schema/response.v1_2.json',
    'experiments/BRUTE_PLAN_004.json','experiments/brute_common_004.py','experiments/brute_study_004.py',
    'experiments/brute_calibrate_004.py','experiments/v020_independent_reference.py','scripts/make_freeze_004.py',
    'tests/test_brute_active.py','tests/test_api_contract_v020.py','tests/test_study_004.py'])


def build():
    return {'schema':'brute.source-freeze.v1','study':'BRUTE-020-ACTIVE-004','status':'frozen',
            'also_requires':['experiments/BRUTE_SOURCE_FREEZE_002.json','experiments/BRUTE_SOURCE_FREEZE_003.json'],
            'plan_sha256':sha(PLAN),'preregistration_commit':'c0ac594',
            'sha256_files':{rel:sha(ROOT/rel) for rel in FILES}}


if __name__=='__main__':
    write_new(FREEZE,build());print(len(FILES),'files frozen')
