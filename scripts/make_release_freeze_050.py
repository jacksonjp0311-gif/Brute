"""Write experiments/BRUTE_RELEASE_FREEZE_050.json: lock for v0.5.0 code outside BRUTE_SOURCE_FREEZE_007 (study-007
scoring scripts, run/storage scripts, release verifier and its test). No overwrite."""
import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from experiments.brute_common import sha,write_new
OUT=ROOT/'experiments/BRUTE_RELEASE_FREEZE_050.json'
FILES=('scripts/make_count_007.py','scripts/make_gates_007.py','scripts/make_paired_007.py','scripts/make_reproducibility_007.py',
       'scripts/verify_release_050.py','scripts/make_release_freeze_050.py','tests/test_release_050.py')


def build():
    return {'schema':'brute.source-freeze.v1','release':'0.5.0','status':'frozen',
            'scope':'code added for v0.5.0 outside BRUTE_SOURCE_FREEZE_007','sha256_files':{rel:sha(ROOT/rel) for rel in sorted(FILES)}}


if __name__=='__main__':write_new(OUT,build());print(len(FILES),'files frozen')
