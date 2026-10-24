"""Write experiments/BRUTE_RELEASE_FREEZE_010.json: the lock for v0.1.0 code that is not part of
the study-002 freeze (API, language adapter, analysis generators, release checks). No overwrite."""
import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from experiments.brute_common import sha,write_new
OUT=ROOT/'experiments/BRUTE_RELEASE_FREEZE_010.json'
DIRS=('brute/api','adapters')
EXTRA=('brute/api/schema/request.v1.json','brute/api/schema/response.v1.json','scripts/make_api_replay.py',
       'scripts/make_gates.py','scripts/make_paired_analysis.py','scripts/make_reproducibility.py','scripts/verify_release.py',
       'scripts/make_manifest.py','scripts/explore_v020.py','scripts/append_ledger.py','scripts/package_release.py',
       'tests/test_api_contract.py','tests/test_adapter_boundary.py','tests/test_adapter_grounding.py',
       'tests/test_brute_reporting.py','tests/test_brute_repro.py')


def files():
    return sorted({*(p.relative_to(ROOT).as_posix() for d in DIRS for p in (ROOT/d).rglob('*.py') if '__pycache__' not in p.parts),*EXTRA})


def build():
    return {'schema':'brute.source-freeze.v1','release':'0.1.0','status':'frozen',
            'scope':'code added for v0.1.0 outside the study-002 freeze','sha256_files':{rel:sha(ROOT/rel) for rel in files()}}


if __name__=='__main__':write_new(OUT,build());print(len(files()),'files frozen')
