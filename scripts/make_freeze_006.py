"""Write experiments/BRUTE_SOURCE_FREEZE_006.json (study-006 source lock, process step (4)). Refuses to overwrite.

The study-002..005 freezes stay in force; experiments/brute_common_006.check_freeze verifies all five.
"""
import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from experiments.brute_common_006 import FREEZE,PLAN,sha,write_new
FILES=sorted(['brute/resume.py','brute/geometry.py','brute/release_version_040.py','brute/api/service_v040.py',
    'brute/api/schema/request.v1_4.json','brute/api/schema/response.v1_4.json',
    'experiments/BRUTE_PLAN_006.json','experiments/brute_common_006.py','experiments/brute_study_006.py',
    'experiments/brute_calibrate_006.py','experiments/worlds_006.py','experiments/v040_reference.py',
    'experiments/exactness_006.py','scripts/make_freeze_006.py','scripts/study006_storage.py','requirements.txt',
    'tests/test_brute_resume_006.py','tests/test_api_contract_v040.py','tests/test_v040_reference.py',
    'tests/test_exactness_mutation_006.py'])


def build():
    return {'schema':'brute.source-freeze.v1','study':'BRUTE-040-GEOMETRY-006','status':'frozen',
            'also_requires':['experiments/BRUTE_SOURCE_FREEZE_002.json','experiments/BRUTE_SOURCE_FREEZE_003.json',
                             'experiments/BRUTE_SOURCE_FREEZE_004.json','experiments/BRUTE_SOURCE_FREEZE_005.json'],
            'plan_sha256':sha(PLAN),'preregistration_commit':'5fa3628','reference_commit':'2eba00b',
            'implementation_commit':'2811904','pre_freeze_fix_commit':'b5e7077','sha256_files':{rel:sha(ROOT/rel) for rel in FILES}}


if __name__=='__main__':
    write_new(FREEZE,build());print(len(FILES),'files frozen')
