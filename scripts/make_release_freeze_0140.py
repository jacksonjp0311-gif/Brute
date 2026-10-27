"""Write experiments/BRUTE_RELEASE_FREEZE_0140.json: lock for v0.14.0 code outside BRUTE_SOURCE_FREEZE_016 (study-016 scoring
and clean-clone scripts, release verifier, its test, the release version module, this script). The scoring
scripts are also bound by the scoring_freeze_016 ledger entries and by verify_release_0140's git check. No overwrite."""
import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from experiments.brute_common import sha,write_new
OUT=ROOT/'experiments/BRUTE_RELEASE_FREEZE_0140.json'
FILES=('scripts/make_gates_016.py','scripts/make_paired_016.py','scripts/make_reproducibility_016.py','scripts/clean_clone_016.py',
       'scripts/verify_release_0140.py','tests/test_release_0140.py','tests/test_scoring_016.py','brute/release_version_0140.py',
       'scripts/make_release_freeze_0140.py')


def build():
    return {'schema':'brute.source-freeze.v1','release':'0.14.0','status':'frozen',
            'scope':'code added for v0.14.0 outside BRUTE_SOURCE_FREEZE_016','sha256_files':{rel:sha(ROOT/rel) for rel in sorted(FILES)}}


if __name__=='__main__':write_new(OUT,build());print(len(FILES),'files frozen')
