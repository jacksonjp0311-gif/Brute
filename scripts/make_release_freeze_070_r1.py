"""Write experiments/BRUTE_RELEASE_FREEZE_070_R1.json, superseding BRUTE_RELEASE_FREEZE_070.json after the
verify_release_070 fix found by the final-tree test run (DEVIATIONS_009 entry 26). Same file list plus this script. No overwrite."""
import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from experiments.brute_common import sha,write_new
from scripts.make_release_freeze_070 import FILES as F070
OUT=ROOT/'experiments/BRUTE_RELEASE_FREEZE_070_R1.json'
FILES=F070+('scripts/make_release_freeze_070_r1.py',)


def build():
    return {'schema':'brute.source-freeze.v1','release':'0.7.0','status':'frozen','supersedes':'experiments/BRUTE_RELEASE_FREEZE_070.json',
            'reason':'verify_release_070 required a schema key on PROGRESS_009.json and re-checked the superseded BRUTE_RELEASE_FREEZE_060.json (entry 26)',
            'scope':'code added for v0.7.0 outside BRUTE_SOURCE_FREEZE_009','sha256_files':{rel:sha(ROOT/rel) for rel in sorted(FILES)}}


if __name__=='__main__':write_new(OUT,build());print(len(FILES),'files frozen')
