"""Write experiments/BRUTE_RELEASE_FREEZE_0130.json: lock for v0.13.0 code outside BRUTE_SOURCE_FREEZE_015 (study-015 scoring
and clean-clone scripts, release verifier, its test, the release version module, this script). The scoring
scripts are also bound by the scoring_freeze_015 ledger entries and by verify_release_0130's git check. No overwrite."""
import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from experiments.brute_common import sha,write_new
OUT=ROOT/'experiments/BRUTE_RELEASE_FREEZE_0130.json'
FILES=('scripts/make_gates_015.py','scripts/make_paired_015.py','scripts/make_reproducibility_015.py','scripts/clean_clone_015.py',
       'scripts/verify_release_0130.py','tests/test_release_0130.py','tests/test_scoring_015.py','brute/release_version_0130.py',
       'scripts/make_release_freeze_0130.py')


def build():
    return {'schema':'brute.source-freeze.v1','release':'0.13.0','status':'frozen',
            'scope':'code added for v0.13.0 outside BRUTE_SOURCE_FREEZE_015','sha256_files':{rel:sha(ROOT/rel) for rel in sorted(FILES)}}


if __name__=='__main__':write_new(OUT,build());print(len(FILES),'files frozen')
