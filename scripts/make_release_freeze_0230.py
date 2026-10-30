"""Write experiments/BRUTE_RELEASE_FREEZE_0230.json: lock for v0.23.0 code outside BRUTE_SOURCE_FREEZE_026 (lean release
verifier, its test, this script). Written only after run_start_026. No overwrite."""
import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from experiments.brute_common import sha,write_new
OUT=ROOT/'experiments/BRUTE_RELEASE_FREEZE_0230.json'
FILES=('scripts/verify_release_0230.py','scripts/study026_storage.py','tests/test_release_0230.py','scripts/make_release_freeze_0230.py')


def build():
    return {'schema':'brute.source-freeze.v1','release':'0.23.0','status':'frozen',
            'scope':'code added for v0.23.0 outside BRUTE_SOURCE_FREEZE_026','sha256_files':{rel:sha(ROOT/rel) for rel in sorted(FILES)}}


if __name__=='__main__':write_new(OUT,build());print(len(FILES),'files frozen')
