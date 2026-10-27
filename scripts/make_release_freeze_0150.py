"""Write experiments/BRUTE_RELEASE_FREEZE_0150.json: lock for v0.15.0 code outside BRUTE_SOURCE_FREEZE_017 (study-017 scoring
and clean-clone scripts, release verifier, its test, the release version module, this script). The scoring
scripts are also bound by the scoring_freeze_017 ledger entries and by verify_release_0150's git check. No overwrite."""
import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from experiments.brute_common import sha,write_new
OUT=ROOT/'experiments/BRUTE_RELEASE_FREEZE_0150.json'
FILES=('scripts/make_gates_017.py','scripts/make_paired_017.py','scripts/make_reproducibility_017.py','scripts/clean_clone_017.py',
       'scripts/verify_release_0150.py','tests/test_release_0150.py','tests/test_scoring_017.py','brute/release_version_0150.py',
       'scripts/make_release_freeze_0150.py','tests/test_streams_017_R1.py')


def build():
    return {'schema':'brute.source-freeze.v1','release':'0.15.0','status':'frozen',
            'scope':'code added for v0.15.0 outside BRUTE_SOURCE_FREEZE_017','sha256_files':{rel:sha(ROOT/rel) for rel in sorted(FILES)}}


if __name__=='__main__':write_new(OUT,build());print(len(FILES),'files frozen')
