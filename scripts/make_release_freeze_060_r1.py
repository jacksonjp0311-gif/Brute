"""Write experiments/BRUTE_RELEASE_FREEZE_060_R1.json, which supersedes BRUTE_RELEASE_FREEZE_060.json (DEVIATIONS_008 D26).
It locks the same files plus this script, after the git-order fix to scripts/verify_release_060.py: pre-freeze fixes are
checked as reference descendants and source-freeze ancestors instead of as links after the implementation commits.
The original freeze file is kept unchanged as the record. No overwrite."""
import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from experiments.brute_common import sha,write_new
from scripts.make_release_freeze_060 import FILES as FILES_060
OUT=ROOT/'experiments/BRUTE_RELEASE_FREEZE_060_R1.json'
FILES=tuple(FILES_060)+('scripts/make_release_freeze_060_r1.py',)


def build():
    return {'schema':'brute.source-freeze.v1','release':'0.6.0','status':'frozen','supersedes':'experiments/BRUTE_RELEASE_FREEZE_060.json',
            'reason':'verify_release_060 git_order placed pre_freeze_fix commits after the implementation commits; cae25ce precedes them (D26)',
            'scope':'code added for v0.6.0 outside BRUTE_SOURCE_FREEZE_008','sha256_files':{rel:sha(ROOT/rel) for rel in sorted(FILES)}}


if __name__=='__main__':write_new(OUT,build());print(len(FILES),'files frozen')
