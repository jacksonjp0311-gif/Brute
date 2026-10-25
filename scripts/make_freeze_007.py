"""Write experiments/BRUTE_SOURCE_FREEZE_007.json (study-007 source lock, process step (5)). Refuses to overwrite.

The study-002..006 freezes stay in force; experiments/brute_common_007.check_freeze verifies all six.
"""
import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from experiments.brute_common_007 import FREEZE,PLAN,sha,write_new
FILES=sorted(['brute/region.py','brute/region_learner.py','brute/breadth.py','brute/release_version_050.py',
    'brute/api/service_v050.py','brute/api/schema/request.v1_5.json','brute/api/schema/response.v1_5.json',
    'experiments/BRUTE_PLAN_007.json','experiments/brute_common_007.py','experiments/brute_study_007.py',
    'experiments/brute_calibrate_007.py','experiments/worlds_007.py','experiments/scaling_007.py',
    'experiments/v050_reference.py','scripts/make_freeze_007.py','scripts/study007_storage.py','scripts/run_study_007.sh',
    'requirements.txt','tests/test_v050_reference.py','tests/test_v050_impl.py'])


def build():
    return {'schema':'brute.source-freeze.v1','study':'BRUTE-050-REGION-007','status':'frozen',
            'also_requires':['experiments/BRUTE_SOURCE_FREEZE_00%d.json'%i for i in range(2,7)],
            'plan_sha256':sha(PLAN),'preregistration_commit':'5be08aa','reference_commit':'1b57efe',
            'implementation_commits':['fc2bed8','c8e8611','b693113'],'pre_freeze_fix_commits':['0c86d90','__FIX2__'],
            'sha256_files':{rel:sha(ROOT/rel) for rel in FILES}}


if __name__=='__main__':
    write_new(FREEZE,build());print(len(FILES),'files frozen')
