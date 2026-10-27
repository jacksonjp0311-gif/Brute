"""Write experiments/BRUTE_RELEASE_FREEZE_0160.json: lock for v0.16.0 code outside BRUTE_SOURCE_FREEZE_018 (release verifier,
its test, this script). The study-018 scoring and clean-clone scripts and brute/release_version_0160.py are already bound by
BRUTE_SOURCE_FREEZE_018 and the scoring_freeze_018 ledger entries; they are listed again here for one-file auditing. No overwrite."""
import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from experiments.brute_common import sha,write_new
OUT=ROOT/'experiments/BRUTE_RELEASE_FREEZE_0160.json'
FILES=('scripts/make_gates_018.py','scripts/make_paired_018.py','scripts/make_reproducibility_018.py','scripts/clean_clone_018.py',
       'scripts/verify_release_0160.py','tests/test_release_0160.py','tests/test_scoring_018.py','brute/release_version_0160.py',
       'scripts/make_release_freeze_0160.py')


def build():
    return {'schema':'brute.source-freeze.v1','release':'0.16.0','status':'frozen',
            'scope':'code added for v0.16.0 outside BRUTE_SOURCE_FREEZE_018','sha256_files':{rel:sha(ROOT/rel) for rel in sorted(FILES)}}


if __name__=='__main__':write_new(OUT,build());print(len(FILES),'files frozen')
