"""Write experiments/BRUTE_RELEASE_FREEZE_070.json: lock for v0.7.0 code outside BRUTE_SOURCE_FREEZE_009 (study-009
scoring scripts, final-gates writer, storage, release verifier, its test, the release version module). No overwrite."""
import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from experiments.brute_common import sha,write_new
OUT=ROOT/'experiments/BRUTE_RELEASE_FREEZE_070.json'
FILES=('scripts/make_gates_009.py','scripts/make_paired_009.py','scripts/make_reproducibility_009.py','scripts/make_gates_final_009.py',
       'scripts/study009_storage.py','scripts/verify_release_070.py','tests/test_release_070.py','brute/release_version_070.py',
       'scripts/make_release_freeze_070.py')


def build():
    return {'schema':'brute.source-freeze.v1','release':'0.7.0','status':'frozen',
            'scope':'code added for v0.7.0 outside BRUTE_SOURCE_FREEZE_009','sha256_files':{rel:sha(ROOT/rel) for rel in sorted(FILES)}}


if __name__=='__main__':write_new(OUT,build());print(len(FILES),'files frozen')
