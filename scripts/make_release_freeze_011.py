"""Write experiments/BRUTE_RELEASE_FREEZE_011.json: lock for v0.1.1 code outside freeze 003
(study-003 analysis generators, release verifier and its test). No overwrite."""
import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from experiments.brute_common import sha,write_new
OUT=ROOT/'experiments/BRUTE_RELEASE_FREEZE_011.json'
FILES=('scripts/make_gates_003.py','scripts/make_paired_003.py','scripts/make_reproducibility_003.py','scripts/drift_stress_003.py',
       'scripts/verify_release_011.py','scripts/make_release_freeze_011.py','tests/test_release_011.py')


def build():
    return {'schema':'brute.source-freeze.v1','release':'0.1.1','status':'frozen',
            'scope':'code added for v0.1.1 outside BRUTE_SOURCE_FREEZE_003','sha256_files':{rel:sha(ROOT/rel) for rel in sorted(FILES)}}


if __name__=='__main__':write_new(OUT,build());print(len(FILES),'files frozen')
