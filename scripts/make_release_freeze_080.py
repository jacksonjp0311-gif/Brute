"""Write experiments/BRUTE_RELEASE_FREEZE_080.json: lock for v0.8.0 code outside BRUTE_SOURCE_FREEZE_010 (study-010
storage, release verifier, its test, the release version module, this script). The study-010 scoring scripts are bound
by the scoring_freeze_010 ledger entries and by verify_release_080's git check. No overwrite."""
import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from experiments.brute_common import sha,write_new
OUT=ROOT/'experiments/BRUTE_RELEASE_FREEZE_080.json'
FILES=('scripts/make_gates_010.py','scripts/make_paired_010.py','scripts/make_reproducibility_010.py',
       'scripts/study010_storage.py','scripts/verify_release_080.py','tests/test_release_080.py','brute/release_version_080.py',
       'scripts/make_release_freeze_080.py')


def build():
    return {'schema':'brute.source-freeze.v1','release':'0.8.0','status':'frozen',
            'scope':'code added for v0.8.0 outside BRUTE_SOURCE_FREEZE_010','sha256_files':{rel:sha(ROOT/rel) for rel in sorted(FILES)}}


if __name__=='__main__':write_new(OUT,build());print(len(FILES),'files frozen')
