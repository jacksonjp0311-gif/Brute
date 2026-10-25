"""Write experiments/BRUTE_SOURCE_FREEZE_008.json (study-008 source lock, BRUTE_PLAN_008 process step (5)). Refuses to overwrite.

The study-002..007 source freezes and the v0.5.0 release freeze stay in force; experiments/brute_common_008.check_freeze
verifies all of them plus this one before any held-out run.
"""
import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from experiments.brute_common_008 import FREEZE,PLAN,sha,write_new
FILES=sorted(['brute/driftsound.py','brute/xcheck_sat.py','brute/modelcount.py',
    'experiments/BRUTE_PLAN_008.json','experiments/brute_common_008.py','experiments/brute_study_008.py','experiments/worlds_008.py',
    'experiments/v060_reference.py','experiments/v060_xcheck.py','experiments/make_count_008.py',
    'scripts/check_seeds_008.py','scripts/make_freeze_008.py','scripts/make_second_impl_008.py','scripts/study008_storage.py',
    'scripts/run_study_008.sh','requirements-gmc.txt',
    'tests/test_driftsound.py','tests/test_v060_reference.py','tests/test_xcheck_sat.py','tests/test_seeds_008.py'])


def build():
    return {'schema':'brute.source-freeze.v1','study':'BRUTE-060-DRIFTSOUND-008','status':'frozen',
            'also_requires':['experiments/BRUTE_SOURCE_FREEZE_00%d.json'%i for i in range(2,8)]+['experiments/BRUTE_RELEASE_FREEZE_050.json'],
            'plan_sha256':sha(PLAN),'preregistration_commit':'89c2d3b','seedcheck_commit':'1de8170','reference_commit':'8863f06',
            'implementation_commits':['457db5a','6556186','ff4d0d8','6f6cd22'],'pre_freeze_fix_commits':['cae25ce'],
            'sha256_files':{rel:sha(ROOT/rel) for rel in FILES}}


if __name__=='__main__':
    write_new(FREEZE,build());print(len(FILES),'files frozen')
