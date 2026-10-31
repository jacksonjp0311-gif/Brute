"""Brute v0.39.0 release verification, lean process (BRUTE_PLAN_042 + deviation #157; built from the frozen
scripts/verify_release_0380.py and its addendum scripts/verify_release_0380a.py, which stay frozen). Short verify:
  1. RELEASE.json parses, version 0.39.0, required keys present, gate lists and secondary match results/study-042/GATES_042.json;
  2. MANIFEST.sha256 matches the tree; BRUTE_SOURCE_FREEZE_042 (check_freeze, incl. the 025 to 041 freezes) holds; the release
     tooling is inside the source freeze, so there is no separate release freeze;
  3. raw study-042 main files restore from their committed .json.gz and match main/SEAL.json;
  4. GATES_042 reproduces byte-for-byte from the sealed inputs (make_gates_042 --check);
  5. commit order (git, when available): every pair of consecutive COMMIT_ORDER_042 commits is an ancestor pair, EXCEPT a
     build_authorization_042 entry, which must name the preregistration commit, and that commit must be an ancestor of the
     previous entry's commit (the 0380a rule, declared before data in #157); every entry commit is an ancestor of the source
     freeze; then source freeze -> seal -> HEAD strictly.
  The test suite is NOT run here; run scripts/run_tests_0390.py (default output is a scratch path outside the tree).
  python scripts/study042_storage.py restore && PYTHONPATH=. python scripts/verify_release_0390.py [--root R]"""
from __future__ import annotations
import argparse,json,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from experiments.brute_common import VerificationError,check
from scripts.verify_release_060 import jload,req,manifest_ok
from scripts.verify_release_0380 import _script

VERSION='0.39.0';STUDY='results/study-042';ORDER='experiments/COMMIT_ORDER_042.json';AUTH='build_authorization_042'
RELEASE_KEYS=('version','preregistration','preregistration_commit','source_freeze','source_freeze_commit','release_freeze','seal_commit',
              'results_dir','case_count','gates_passed','gates_failed','headline','api','deviations','process','gates_not_exercised','secondary')


def release_ok(root):
    R=jload(root/'RELEASE.json')
    for k in RELEASE_KEYS:req(R,k,'RELEASE.json')
    check(R['version']==VERSION,f'RELEASE.json version is not {VERSION}')
    G=jload(root/STUDY/'GATES_042.json');gates=req(G,'gates','GATES_042.json')
    passed=sorted(k for k,v in gates.items() if v.get('pass') is True);failed=sorted(k for k,v in gates.items() if v.get('pass') is False)
    nx=sorted(k for k,v in gates.items() if v.get('pass') is None)
    check(sorted(R['gates_passed'])==passed and sorted(R['gates_failed'])==failed and sorted(R['gates_not_exercised'])==nx,'RELEASE.json gate lists differ from GATES_042.json')
    check(R['secondary']=={k:v.get('pass') for k,v in (G.get('secondary') or {}).items()},'RELEASE.json secondary gates differ from GATES_042.json')
    return R


def _anc(root,a,b):
    return subprocess.run(['git','-C',str(root),'merge-base','--is-ancestor',a,b],capture_output=True).returncode==0


def _count(root,c):return int(subprocess.run(['git','-C',str(root),'rev-list','--count',c],capture_output=True,text=True).stdout or 0)


def chain(root,R,E=None):
    try:subprocess.run(['git','-C',str(root),'rev-parse','HEAD'],check=True,capture_output=True)
    except (OSError,subprocess.CalledProcessError):return 'skipped (no git)'
    E=E if E is not None else jload(root/ORDER)['entries'];exc=0
    for p,q in zip(E,E[1:]):
        if _anc(root,p['commit'],q['commit']):continue
        ok=q['event']==AUTH and q['commit']==R['preregistration_commit'] and _anc(root,q['commit'],p['commit'])
        check(ok,f"commit order: {p['commit']} is not an ancestor of {q['commit']}");exc+=1
    for e in E:check(_anc(root,e['commit'],R['source_freeze_commit']),f"commit order: {e['commit']} is not an ancestor of the source freeze")
    order=[max((e['commit'] for e in E),key=lambda c:_count(root,c)),R['source_freeze_commit'],R['seal_commit'],'HEAD']
    for a,b in zip(order,order[1:]):check(_anc(root,a,b),f'commit order: {a} is not an ancestor of {b}')
    return {'links':len(E)-1+len(order)-1,'authorization_exceptions':exc}


def verify(root=ROOT):
    root=Path(root);out={}
    R=release_ok(root);out['release']=R['version']
    check(manifest_ok(root),'MANIFEST.sha256 does not match');out['manifest']=True
    out['raw_restore']=_script(root,'scripts/study042_storage.py','restore')
    out['source_freeze']=_script(root,'-c','from experiments.brute_common_042 import check_freeze;check_freeze();print("ok")')
    out['gates_check']=_script(root,'scripts/make_gates_042.py','--check')
    out['commit_chain']=chain(root,R)
    return out


if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--root',default=str(ROOT));a=ap.parse_args()
    try:print(json.dumps({'passed':True,**verify(Path(a.root))},sort_keys=True))
    except VerificationError as e:print(json.dumps({'passed':False,'error':str(e)}));sys.exit(1)
