"""Write experiments/BRUTE_RELEASE_FREEZE_0200.json: lock for v0.20.0 code outside BRUTE_SOURCE_FREEZE_023 (release verifier,
its test, this script). The study-023 scoring and clean-clone scripts and brute/release_version_0200.py are already bound by
BRUTE_SOURCE_FREEZE_023 and the scoring_freeze_023 ledger entries; they are listed again here for one-file auditing. No overwrite."""
import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from experiments.brute_common import sha,write_new
OUT=ROOT/'experiments/BRUTE_RELEASE_FREEZE_0200.json'
FILES=('scripts/make_gates_023.py','scripts/make_paired_023.py','scripts/make_reproducibility_023.py','scripts/clean_clone_023.py','scripts/clean_clone_023_gitclone.py',
       'scripts/verify_release_0200.py','tests/test_release_0200.py','tests/test_scoring_023.py','brute/release_version_0200.py',
       'scripts/make_release_freeze_0200.py')


def build():
    return {'schema':'brute.source-freeze.v1','release':'0.20.0','status':'frozen',
            'scope':'code added for v0.20.0 outside BRUTE_SOURCE_FREEZE_023','sha256_files':{rel:sha(ROOT/rel) for rel in sorted(FILES)}}


if __name__=='__main__':write_new(OUT,build());print(len(FILES),'files frozen')
