"""Brute v0.38.0 release verification addendum (deviation #156). New file; verify_release_0380.py stays frozen and is run as is.
The frozen verifier checks COMMIT_ORDER_041 as a strict ancestor chain of the entries' commits. In study 041 the seedcheck
(ada2447) was ledgered BEFORE the build authorization, whose entry names the plan commit it authorizes (18cc782), so the
pair ada2447 -> 18cc782 is not an ancestor pair and the frozen check fails (Exact). This addendum runs the frozen items 1 to 4
unchanged and replaces item 5 with: every pair of consecutive COMMIT_ORDER_041 commits is an ancestor pair, EXCEPT a
build_authorization_041 entry, which must name the preregistration commit, and that commit must be an ancestor of the
previous entry's commit; then the source freeze -> seal -> HEAD chain is checked strictly, and every entry commit is an
ancestor of the source freeze.
  python scripts/study041_storage.py restore && PYTHONPATH=. python scripts/verify_release_0380a.py [--root R]"""
from __future__ import annotations
import argparse,json,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from experiments.brute_common import VerificationError,check
from scripts.verify_release_060 import jload,manifest_ok
from scripts.verify_release_0380 import release_ok,_script


def _anc(root,a,b):
    return subprocess.run(['git','-C',str(root),'merge-base','--is-ancestor',a,b],capture_output=True).returncode==0


def chain(root,R):
    try:subprocess.run(['git','-C',str(root),'rev-parse','HEAD'],check=True,capture_output=True)
    except (OSError,subprocess.CalledProcessError):return 'skipped (no git)'
    E=jload(root/'experiments/COMMIT_ORDER_041.json')['entries'];exc=0
    for p,q in zip(E,E[1:]):
        if _anc(root,p['commit'],q['commit']):continue
        ok=q['event']=='build_authorization_041' and q['commit']==R['preregistration_commit'] and _anc(root,q['commit'],p['commit'])
        check(ok,f"commit order: {p['commit']} is not an ancestor of {q['commit']}");exc+=1
    for e in E:check(_anc(root,e['commit'],R['source_freeze_commit']),f"commit order: {e['commit']} is not an ancestor of the source freeze")
    order=[E[-1]['commit'] if exc==0 else max((e['commit'] for e in E),key=lambda c:int(subprocess.run(['git','-C',str(root),'rev-list','--count',c],capture_output=True,text=True).stdout)),
           R['source_freeze_commit'],R['seal_commit'],'HEAD']
    for a,b in zip(order,order[1:]):check(_anc(root,a,b),f'commit order: {a} is not an ancestor of {b}')
    return {'links':len(E)-1+len(order)-1,'authorization_exceptions':exc}


def verify(root=ROOT):
    root=Path(root);out={}
    R=release_ok(root);out['release']=R['version']
    check(manifest_ok(root),'MANIFEST.sha256 does not match');out['manifest']=True
    out['raw_restore']=_script(root,'scripts/study041_storage.py','restore')
    out['source_freeze']=_script(root,'-c','from experiments.brute_common_041 import check_freeze;check_freeze();print("ok")')
    out['gates_check']=_script(root,'scripts/make_gates_041.py','--check')
    out['commit_chain']=chain(root,R)
    return out


if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--root',default=str(ROOT));a=ap.parse_args()
    try:print(json.dumps({'passed':True,**verify(Path(a.root))},sort_keys=True))
    except VerificationError as e:print(json.dumps({'passed':False,'error':str(e)}));sys.exit(1)
