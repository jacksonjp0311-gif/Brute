"""Brute v0.33.0 release verification, lean process (BRUTE_PLAN_036 + deviations #126/#144/#145). New file; earlier verifiers
stay frozen. Short verify:
  1. RELEASE.json parses, version 0.33.0, required keys present, gate lists match results/study-036/GATES_036.json;
  2. MANIFEST.sha256 matches the tree; BRUTE_SOURCE_FREEZE_036 (check_freeze, incl. the 025 to 035 freezes) holds;
     the release tooling is inside the source freeze (deviation #126, kept by #128 to #144), so there is no separate release freeze;
  3. raw study-036 main files restore from their committed .json.gz and match main/SEAL.json;
  4. GATES_036 reproduces byte-for-byte from the sealed inputs (make_gates_036 --check);
  5. the commit order (COMMIT_ORDER_036 entries, then source freeze -> seal -> HEAD) is an ancestor chain (git, when available).
  PYTHONPATH=. python scripts/verify_release_0330.py [--root R]"""
from __future__ import annotations
import argparse,json,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from experiments.brute_common import VerificationError,check
from scripts.verify_release_060 import jload,req,_freeze,manifest_ok

STUDY='results/study-036'
RELEASE_KEYS=('version','preregistration','source_freeze','source_freeze_commit','release_freeze','seal_commit',
              'results_dir','case_count','gates_passed','gates_failed','headline','api','deviations','process','gates_not_exercised',
              'secondary')


def release_ok(root):
    R=jload(root/'RELEASE.json')
    for k in RELEASE_KEYS:req(R,k,'RELEASE.json')
    check(R['version']=='0.33.0','RELEASE.json version is not 0.33.0')
    G=jload(root/STUDY/'GATES_036.json');gates=req(G,'gates','GATES_036.json')
    passed=sorted(k for k,v in gates.items() if v.get('pass') is True);failed=sorted(k for k,v in gates.items() if v.get('pass') is False)
    nx=sorted(k for k,v in gates.items() if v.get('pass') is None)
    check(sorted(R['gates_passed'])==passed and sorted(R['gates_failed'])==failed and sorted(R['gates_not_exercised'])==nx,'RELEASE.json gate lists differ from GATES_036.json')
    sec={k:v.get('pass') for k,v in (G.get('secondary') or {}).items()}
    check(R['secondary']==sec,'RELEASE.json secondary gates differ from GATES_036.json')
    return R


def chain(root,R):
    order=[e['commit'] for e in jload(root/'experiments/COMMIT_ORDER_036.json')['entries']]+[R['source_freeze_commit'],R['seal_commit'],'HEAD']
    try:subprocess.run(['git','-C',str(root),'rev-parse','HEAD'],check=True,capture_output=True)
    except (OSError,subprocess.CalledProcessError):return 'skipped (no git)'
    for a,b in zip(order,order[1:]):
        r=subprocess.run(['git','-C',str(root),'merge-base','--is-ancestor',a,b],capture_output=True)
        check(r.returncode==0,f'commit order: {a} is not an ancestor of {b}')
    return len(order)


def _script(root,*args):
    r=subprocess.run([sys.executable,*args],cwd=root,capture_output=True,text=True,env={'PYTHONPATH':'.','PATH':'/usr/bin:/bin'})
    check(r.returncode==0,f'{args[0]} failed: {(r.stdout+r.stderr)[-400:]}')
    return r.stdout.strip()[-200:]


def verify(root=ROOT):
    root=Path(root);out={}
    R=release_ok(root);out['release']=R['version']
    check(manifest_ok(root),'MANIFEST.sha256 does not match');out['manifest']=True
    out['raw_restore']=_script(root,'scripts/study036_storage.py','restore')
    out['source_freeze']=_script(root,'-c','from experiments.brute_common_036 import check_freeze;check_freeze();print("ok")')
    out['gates_check']=_script(root,'scripts/make_gates_036.py','--check')
    out['commit_chain']=chain(root,R)
    return out


if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--root',default=str(ROOT));a=ap.parse_args()
    try:print(json.dumps({'passed':True,**verify(Path(a.root))},sort_keys=True))
    except VerificationError as e:print(json.dumps({'passed':False,'error':str(e)}));sys.exit(1)
