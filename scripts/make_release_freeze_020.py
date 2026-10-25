"""Write experiments/BRUTE_RELEASE_FREEZE_020.json: lock for v0.2.0 code outside freeze 004
(study-004 analysis generators, release verifier and its test). No overwrite."""
import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from experiments.brute_common import sha,write_new
OUT=ROOT/'experiments/BRUTE_RELEASE_FREEZE_020.json'
FILES=('scripts/make_gates_004.py','scripts/make_paired_004.py','scripts/make_reproducibility_004.py',
       'scripts/verify_release_020.py','scripts/make_release_freeze_020.py','scripts/study004_storage.py',
       'tests/test_release_020.py')


def build():
    return {'schema':'brute.source-freeze.v1','release':'0.2.0','status':'frozen',
            'scope':'code added for v0.2.0 outside BRUTE_SOURCE_FREEZE_004','sha256_files':{rel:sha(ROOT/rel) for rel in sorted(FILES)}}


if __name__=='__main__':write_new(OUT,build());print(len(FILES),'files frozen')
