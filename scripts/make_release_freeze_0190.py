"""Write experiments/BRUTE_RELEASE_FREEZE_0190.json: lock for v0.19.0 code outside BRUTE_SOURCE_FREEZE_021 (release verifier,
its test, this script). The study-021 scoring and clean-clone scripts and brute/release_version_0190.py are already bound by
BRUTE_SOURCE_FREEZE_021 and the scoring_freeze_021 ledger entries; they are listed again here for one-file auditing. No overwrite."""
import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from experiments.brute_common import sha,write_new
OUT=ROOT/'experiments/BRUTE_RELEASE_FREEZE_0190.json'
FILES=('scripts/make_gates_021.py','scripts/make_paired_021.py','scripts/make_reproducibility_021.py','scripts/clean_clone_021.py',
       'scripts/verify_release_0190.py','tests/test_release_0190.py','tests/test_scoring_021.py','brute/release_version_0190.py',
       'scripts/make_release_freeze_0190.py')


def build():
    return {'schema':'brute.source-freeze.v1','release':'0.19.0','status':'frozen',
            'scope':'code added for v0.19.0 outside BRUTE_SOURCE_FREEZE_021','sha256_files':{rel:sha(ROOT/rel) for rel in sorted(FILES)}}


if __name__=='__main__':write_new(OUT,build());print(len(FILES),'files frozen')
