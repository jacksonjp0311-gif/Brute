"""Write experiments/BRUTE_RELEASE_FREEZE_030.json: lock for v0.3.0 code outside freeze 005
(study-005 analysis generators, storage, release verifier and its test). No overwrite."""
import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from experiments.brute_common import sha,write_new
OUT=ROOT/'experiments/BRUTE_RELEASE_FREEZE_030.json'
FILES=('scripts/make_gates_005.py','scripts/make_paired_005.py','scripts/make_reproducibility_005.py',
       'scripts/verify_release_030.py','scripts/make_release_freeze_030.py','scripts/study005_storage.py',
       'tests/test_release_030.py')


def build():
    return {'schema':'brute.source-freeze.v1','release':'0.3.0','status':'frozen',
            'scope':'code added for v0.3.0 outside BRUTE_SOURCE_FREEZE_005','sha256_files':{rel:sha(ROOT/rel) for rel in sorted(FILES)}}


if __name__=='__main__':write_new(OUT,build());print(len(FILES),'files frozen')
