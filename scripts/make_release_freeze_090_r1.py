"""Write experiments/BRUTE_RELEASE_FREEZE_090_R1.json. Supersedes BRUTE_RELEASE_FREEZE_090.json (kept unchanged as the record)
after verify_release_090.git_order was fixed for the actual scoring-commit order (deviation #44). Same files plus this script.
No overwrite."""
import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from experiments.brute_common import sha,write_new
from scripts.make_release_freeze_090 import FILES as F0
OUT=ROOT/'experiments/BRUTE_RELEASE_FREEZE_090_R1.json'
FILES=tuple(F0)+('scripts/make_release_freeze_090_r1.py',)


def build():
    return {'schema':'brute.source-freeze.v1','release':'0.9.0','status':'frozen','supersedes':'experiments/BRUTE_RELEASE_FREEZE_090.json',
            'scope':'code added for v0.9.0 outside BRUTE_SOURCE_FREEZE_011','sha256_files':{rel:sha(ROOT/rel) for rel in sorted(FILES)}}


if __name__=='__main__':write_new(OUT,build());print(len(FILES),'files frozen')
