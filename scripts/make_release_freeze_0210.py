"""Write experiments/BRUTE_RELEASE_FREEZE_0210.json: lock for v0.21.0 code outside BRUTE_SOURCE_FREEZE_024 (release verifier,
its test, this script). The study-024 scoring and clean-clone scripts and brute/release_version_0210.py are already bound by
BRUTE_SOURCE_FREEZE_024 and the scoring_freeze_024 ledger entry; they are listed again here for one-file auditing. No overwrite.
Written only after run_start_024 (#107)."""
import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from experiments.brute_common import sha,write_new
OUT=ROOT/'experiments/BRUTE_RELEASE_FREEZE_0210.json'
FILES=('scripts/make_gates_024.py','scripts/make_paired_024.py','scripts/make_reproducibility_024.py','scripts/clean_clone_024.py','scripts/clean_clone_024_gitclone.py',
       'scripts/early_window_024.py','scripts/host_pause_probe_024.py','scripts/verify_release_0210.py','tests/test_release_0210.py','tests/test_scoring_024.py',
       'brute/release_version_0210.py','scripts/make_release_freeze_0210.py')


def build():
    return {'schema':'brute.source-freeze.v1','release':'0.21.0','status':'frozen',
            'scope':'code added for v0.21.0 outside BRUTE_SOURCE_FREEZE_024','sha256_files':{rel:sha(ROOT/rel) for rel in sorted(FILES)}}


if __name__=='__main__':write_new(OUT,build());print(len(FILES),'files frozen')
