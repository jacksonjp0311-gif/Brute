"""Brute v0.57.0 release verification, lean process (BRUTE_PLAN_060 + deviation #194; built from the frozen
scripts/verify_release_0560.py, whose release_ok shape and the 0440 chain() are reused with the 060 names; plan G_RT). Short verify:
  1. RELEASE.json parses, version 0.57.0, required keys present, gate lists, secondary, the certification flags and the status
     phrase (plan 060 status_wording_rule) match results/study-060/GATES_060.json;
  2. MANIFEST.sha256 matches the tree; BRUTE_SOURCE_FREEZE_060 (check_freeze, incl. the 025 to 059 freezes) holds;
  3. raw study-045 to 060 main files restore from their committed .json.gz and match main/SEAL.json;
  4. GATES_060 reproduces byte-for-byte from the sealed inputs (make_gates_060 --check);
  5. commit order: as 0440 (the build_authorization_060 exception rule), then source freeze -> seal -> HEAD strictly.
  The test suite is NOT run here; run scripts/run_tests_0570.py.
  PYTHONPATH=. python scripts/verify_release_0570.py [--root R]"""
from __future__ import annotations
import argparse,json,sys
from pathlib import Path
from unittest import mock
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from experiments.brute_common import VerificationError,check
from scripts.verify_release_060 import jload,req,manifest_ok
from scripts.verify_release_0380 import _script
from scripts import verify_release_0440 as V44

VERSION='0.57.0';STUDY='results/study-060';ORDER='experiments/COMMIT_ORDER_060.json';AUTH='build_authorization_060'
RELEASE_KEYS=V44.RELEASE_KEYS;RESTORE=('045','046','047','048','049','050','051','052','053','054','055','056','057','058','059','060')


def release_ok(root):
    R=jload(root/'RELEASE.json')
    for k in RELEASE_KEYS:req(R,k,'RELEASE.json')
    check(R['version']==VERSION,f'RELEASE.json version is not {VERSION}')
    G=jload(root/STUDY/'GATES_060.json');gates=req(G,'gates','GATES_060.json')
    passed=sorted(k for k,v in gates.items() if v.get('pass') is True);failed=sorted(k for k,v in gates.items() if v.get('pass') is False)
    nx=sorted(k for k,v in gates.items() if v.get('pass') is None)
    check(sorted(R['gates_passed'])==passed and sorted(R['gates_failed'])==failed and sorted(R['gates_not_exercised'])==nx,'RELEASE.json gate lists differ from GATES_060.json')
    check(R['secondary']=={k:v.get('pass') for k,v in (G.get('secondary') or {}).items()},'RELEASE.json secondary gates differ from GATES_060.json')
    check(R.get('certified_readbits4_N24')==G.get('certified_readbits4_N24') and R.get('sound_not_certified_N24')==G.get('sound_not_certified_N24'),
          'RELEASE.json certification flags differ from GATES_060.json')
    check(R.get('status_phrase')==G.get('status_phrase'),'RELEASE.json status_phrase differs from GATES_060.json (status_wording_rule)')
    return R


def chain(root,R,E=None):
    E=E if E is not None else jload(Path(root)/ORDER)['entries']
    with mock.patch.object(V44,'AUTH',AUTH):return V44.chain(root,R,E)


def verify(root=ROOT):
    root=Path(root);out={}
    R=release_ok(root);out['release']=R['version']
    check(manifest_ok(root),'MANIFEST.sha256 does not match');out['manifest']=True
    out['raw_restore']={s:_script(root,f'scripts/study{s}_storage.py','restore') for s in RESTORE}
    out['source_freeze']=_script(root,'-c','from experiments.brute_common_060 import check_freeze;check_freeze();print("ok")')
    out['gates_check']=_script(root,'scripts/make_gates_060.py','--check')
    out['commit_chain']=chain(root,R)
    return out


if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--root',default=str(ROOT));a=ap.parse_args()
    try:print(json.dumps({'passed':True,**verify(Path(a.root))},sort_keys=True))
    except VerificationError as e:print(json.dumps({'passed':False,'error':str(e)}));sys.exit(1)
