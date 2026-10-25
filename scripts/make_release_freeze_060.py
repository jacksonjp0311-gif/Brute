"""Write experiments/BRUTE_RELEASE_FREEZE_060.json: lock for v0.6.0 code outside BRUTE_SOURCE_FREEZE_008 (study-008
scoring scripts, GT1 tooling: release verifier, its test, the GT1 writer and the release version module). No overwrite."""
import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from experiments.brute_common import sha,write_new
OUT=ROOT/'experiments/BRUTE_RELEASE_FREEZE_060.json'
FILES=('scripts/make_gates_008.py','scripts/make_paired_008.py','scripts/make_reproducibility_008.py',
       'scripts/verify_release_060.py','tests/test_release_060.py','scripts/make_gt1_008.py','brute/release_version_060.py',
       'scripts/make_release_freeze_060.py')


def build():
    return {'schema':'brute.source-freeze.v1','release':'0.6.0','status':'frozen',
            'scope':'code added for v0.6.0 outside BRUTE_SOURCE_FREEZE_008','sha256_files':{rel:sha(ROOT/rel) for rel in sorted(FILES)}}


if __name__=='__main__':write_new(OUT,build());print(len(FILES),'files frozen')
