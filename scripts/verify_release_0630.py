"""Brute v0.63.0 release verification, lean process (BRUTE_PLAN_066 + deviation #206; new file, built from the frozen
scripts/verify_release_0620.py, whose release_ok shape and the 0440 chain() are reused with the 066 names; plan G_RT). Short verify:
  1. RELEASE.json parses, version 0.63.0, required keys present, gate lists, secondary, the certification flags and the status
     phrase (plan 066 status_wording_rule) match results/study-066/GATES_066.json;
  2. MANIFEST.sha256 matches the tree; BRUTE_SOURCE_FREEZE_066 (check_freeze, incl. the 025 to 065 freezes) holds;
  3. raw study-045 to 066 main files restore from their committed .json.gz and match main/SEAL.json;
  4. GATES_066 reproduces byte-for-byte from the sealed inputs (make_gates_066 --check);
  5. commit order: as 0440 (the build_authorization_066 exception rule), then source freeze -> seal -> HEAD strictly.
  The test suite is NOT run here; run scripts/run_tests_0630.py.
  PYTHONPATH=. python scripts/verify_release_0620.py [--root R]"""
from __future__ import annotations
import argparse,json,sys
from pathlib import Path
from unittest import mock
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from experiments.brute_common import VerificationError,check
from scripts.verify_release_060 import jload,req,manifest_ok
from scripts.verify_release_0380 import _script
from scripts import verify_release_0440 as V44

VERSION='0.63.0';STUDY='results/study-066';ORDER='experiments/COMMIT_ORDER_066.json';AUTH='build_authorization_066'
RELEASE_KEYS=V44.RELEASE_KEYS;RESTORE=tuple(f'{i:03d}' for i in range(45,67))
FLAGS=('certified_readbits2_N24_eps030_seq','certified_readbits2_N20_eps030_seq')


def release_ok(root):
    R=jload(root/'RELEASE.json')
    for k in RELEASE_KEYS:req(R,k,'RELEASE.json')
    check(R['version']==VERSION,f'RELEASE.json version is not {VERSION}')
    G=jload(root/STUDY/'GATES_066.json');gates=req(G,'gates','GATES_066.json')
    passed=sorted(k for k,v in gates.items() if v.get('pass') is True);failed=sorted(k for k,v in gates.items() if v.get('pass') is False)
    nx=sorted(k for k,v in gates.items() if v.get('pass') is None)
    check(sorted(R['gates_passed'])==passed and sorted(R['gates_failed'])==failed and sorted(R['gates_not_exercised'])==nx,'RELEASE.json gate lists differ from GATES_066.json')
    check(R['secondary']=={k:v.get('pass') for k,v in (G.get('secondary') or {}).items()},'RELEASE.json secondary gates differ from GATES_066.json')
    check(all(R.get(f)==G.get(f) for f in FLAGS),'RELEASE.json certification flags differ from GATES_066.json')
    check(R.get('status_phrase')==G.get('status_phrase'),'RELEASE.json status_phrase differs from GATES_066.json (status_wording_rule)')
    return R


def chain(root,R,E=None):
    E=E if E is not None else jload(Path(root)/ORDER)['entries']
    with mock.patch.object(V44,'AUTH',AUTH):return V44.chain(root,R,E)


def verify(root=ROOT):
    root=Path(root);out={}
    R=release_ok(root);out['release']=R['version']
    check(manifest_ok(root),'MANIFEST.sha256 does not match');out['manifest']=True
    out['raw_restore']={s:_script(root,f'scripts/study{s}_storage.py','restore') for s in RESTORE}
    out['source_freeze']=_script(root,'-c','from experiments.brute_common_066 import check_freeze;check_freeze();print("ok")')
    out['gates_check']=_script(root,'scripts/make_gates_066.py','--check')
    out['commit_chain']=chain(root,R)
    return out


if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--root',default=str(ROOT));a=ap.parse_args()
    try:print(json.dumps({'passed':True,**verify(Path(a.root))},sort_keys=True))
    except VerificationError as e:print(json.dumps({'passed':False,'error':str(e)}));sys.exit(1)
