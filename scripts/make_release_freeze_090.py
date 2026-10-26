"""Write experiments/BRUTE_RELEASE_FREEZE_090.json: lock for v0.9.0 code outside BRUTE_SOURCE_FREEZE_011 (study-011 scoring
and clean-clone scripts, seal, storage, release verifier, its test, the release version module, this script). The scoring
scripts are also bound by the scoring_freeze_011 ledger entries and by verify_release_090's git check. No overwrite."""
import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from experiments.brute_common import sha,write_new
OUT=ROOT/'experiments/BRUTE_RELEASE_FREEZE_090.json'
FILES=('scripts/make_gates_011.py','scripts/make_paired_011.py','scripts/make_reproducibility_011.py','scripts/clean_clone_011.py',
       'scripts/study011_storage.py','scripts/seal_011.py','scripts/verify_release_090.py','tests/test_release_090.py',
       'tests/test_scoring_011.py','brute/release_version_090.py','scripts/make_release_freeze_090.py')


def build():
    return {'schema':'brute.source-freeze.v1','release':'0.9.0','status':'frozen',
            'scope':'code added for v0.9.0 outside BRUTE_SOURCE_FREEZE_011','sha256_files':{rel:sha(ROOT/rel) for rel in sorted(FILES)}}


if __name__=='__main__':write_new(OUT,build());print(len(FILES),'files frozen')
