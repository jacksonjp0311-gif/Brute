"""ADDENDUM to the frozen scripts/verify_release_0250.py (deviation #129). New file. It runs the same five checks
through the frozen module's functions. The only change is step 4: GATES_028 must reproduce through
scripts/make_gates_028b.py --check, because the frozen make_gates_028 cannot read wall-clock fields from
SCIENTIFIC.json. The step also checks that the frozen make_gates_028.py and verify_release_0250.py are byte-unchanged
against BRUTE_SOURCE_FREEZE_028.
  PYTHONPATH=. python scripts/verify_release_0250b.py [--root R]"""
from __future__ import annotations
import argparse,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from experiments.brute_common import VerificationError,check,sha
from scripts.verify_release_060 import jload,manifest_ok
from scripts import verify_release_0250 as V


def verify(root=ROOT):
    root=Path(root);out={}
    R=V.release_ok(root);out['release']=R['version']
    check(manifest_ok(root),'MANIFEST.sha256 does not match');out['manifest']=True
    out['raw_restore']=V._script(root,'scripts/study028_storage.py','restore')
    out['source_freeze']=V._script(root,'-c','from experiments.brute_common_028 import check_freeze;check_freeze();print("ok")')
    fz=jload(root/'experiments/BRUTE_SOURCE_FREEZE_028.json')['sha256_files']
    for f in ('scripts/make_gates_028.py','scripts/verify_release_0250.py'):check(fz[f]==sha(root/f),f'{f} changed after the freeze')
    out['frozen_scorers_unchanged']=True
    out['gates_check']=V._script(root,'scripts/make_gates_028b.py','--check')
    out['commit_chain']=V.chain(root,R)
    return out


if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--root',default=str(ROOT));a=ap.parse_args()
    try:print(json.dumps({'passed':True,**verify(Path(a.root))},sort_keys=True))
    except VerificationError as e:print(json.dumps({'passed':False,'error':str(e)}));sys.exit(1)
