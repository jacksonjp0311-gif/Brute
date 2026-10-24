"""Write experiments/BRUTE_SOURCE_FREEZE_003.json (study-003 source lock). Refuses to overwrite.

The study-002 freeze (experiments/BRUTE_SOURCE_FREEZE_002.json) stays in force as well;
experiments/brute_common_003.check_freeze verifies both.
"""
import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from experiments.brute_common_003 import FREEZE,sha,write_new
FILES=sorted(['brute/fallback.py','brute/version.py','brute/api/service_v011.py',
    'brute/api/schema/request.v1_1.json','brute/api/schema/response.v1_1.json',
    'experiments/BRUTE_PLAN_003.json','experiments/brute_common_003.py','experiments/brute_study_003.py',
    'experiments/brute_calibrate_003.py','experiments/v011_independent_reference.py',
    'scripts/witness_audit.py','scripts/make_freeze_003.py',
    'tests/test_brute_fallback.py','tests/test_api_contract_v011.py','tests/test_witness_audit.py','tests/test_study_003.py'])


def build():
    return {'schema':'brute.source-freeze.v1','study':'BRUTE-011-FALLBACK-003','status':'frozen',
            'also_requires':'experiments/BRUTE_SOURCE_FREEZE_002.json',
            'sha256_files':{rel:sha(ROOT/rel) for rel in FILES}}


if __name__=='__main__':
    write_new(FREEZE,build());print(len(FILES),'files frozen')
