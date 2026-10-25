"""Write experiments/BRUTE_RELEASE_FREEZE_040.json: lock for v0.4.0 code outside freeze 006
(study-006 scoring scripts, run script, release verifier and its test). No overwrite."""
import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from experiments.brute_common import sha,write_new
OUT=ROOT/'experiments/BRUTE_RELEASE_FREEZE_040.json'
FILES=('scripts/make_gates_006.py','scripts/make_paired_006.py','scripts/make_reproducibility_006.py','scripts/run_study_006.sh',
       'scripts/verify_release_040.py','scripts/make_release_freeze_040.py','tests/test_release_040.py')


def build():
    return {'schema':'brute.source-freeze.v1','release':'0.4.0','status':'frozen',
            'scope':'code added for v0.4.0 outside BRUTE_SOURCE_FREEZE_006','sha256_files':{rel:sha(ROOT/rel) for rel in sorted(FILES)}}


if __name__=='__main__':write_new(OUT,build());print(len(FILES),'files frozen')
