"""Write experiments/BRUTE_RELEASE_FREEZE_0200_R1.json: lock for the deviation-#113 files (verify_release_0200_r1, its test,
this script). BRUTE_RELEASE_FREEZE_0200.json stays as committed. No overwrite."""
import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from experiments.brute_common import sha,write_new
OUT=ROOT/'experiments/BRUTE_RELEASE_FREEZE_0200_R1.json'
FILES=('scripts/verify_release_0200_r1.py','tests/test_release_0200_r1.py','scripts/make_release_freeze_0200_r1.py')
if __name__=='__main__':
    write_new(OUT,{'schema':'brute.source-freeze.v1','release':'0.20.0','status':'frozen','revision':'r1 (deviation #113)',
                   'scope':'release-verifier revision 1; supplements BRUTE_RELEASE_FREEZE_0200','sha256_files':{f:sha(ROOT/f) for f in sorted(FILES)}})
    print(len(FILES),'files frozen')
