"""Brute v0.23.0 release verification, lean process (BRUTE_PLAN_026 + deviations #123/#124). New file; earlier verifiers
stay frozen. Short verify:
  1. RELEASE.json parses, version 0.23.0, required keys present, gate lists match results/study-026/GATES_026.json;
  2. MANIFEST.sha256 matches the tree; BRUTE_SOURCE_FREEZE_026 (check_freeze, incl. the 025 freeze) and
     BRUTE_RELEASE_FREEZE_0230 hold;
  3. raw study-026 main files restore from their committed .json.gz and match main/SEAL.json;
  4. GATES_026 reproduces byte-for-byte from the sealed inputs (make_gates_026 --check);
  5. the commit order (COMMIT_ORDER_026 entries, then source freeze -> seal -> HEAD) is an ancestor chain (git, when available).
  PYTHONPATH=. python scripts/verify_release_0230.py [--root R]"""
from __future__ import annotations
import argparse,json,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from experiments.brute_common import VerificationError,check
from scripts.verify_release_060 import jload,req,_freeze,manifest_ok

STUDY='results/study-026'
RELEASE_KEYS=('version','preregistration','source_freeze','source_freeze_commit','release_freeze','seal_commit',
              'results_dir','case_count','gates_passed','gates_failed','headline','api','deviations','process')


def release_ok(root):
    R=jload(root/'RELEASE.json')
    for k in RELEASE_KEYS:req(R,k,'RELEASE.json')
    check(R['version']=='0.23.0','RELEASE.json version is not 0.23.0')
    G=jload(root/STUDY/'GATES_026.json');gates=req(G,'gates','GATES_026.json')
    passed=sorted(k for k,v in gates.items() if v.get('pass') is True);failed=sorted(k for k,v in gates.items() if v.get('pass') is not True)
    check(sorted(R['gates_passed'])==passed and sorted(R['gates_failed'])==failed,'RELEASE.json gate lists differ from GATES_026.json')
    return R


def chain(root,R):
    order=[e['commit'] for e in jload(root/'experiments/COMMIT_ORDER_026.json')['entries']]+[R['source_freeze_commit'],R['seal_commit'],'HEAD']
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
    out['raw_restore']=_script(root,'scripts/study026_storage.py','restore')
    out['source_freeze']=_script(root,'-c','from experiments.brute_common_026 import check_freeze;check_freeze();print("ok")')
    out['release_freeze_files']=_freeze(root,'experiments/BRUTE_RELEASE_FREEZE_0230.json')
    out['gates_check']=_script(root,'scripts/make_gates_026.py','--check')
    out['commit_chain']=chain(root,R)
    return out


if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--root',default=str(ROOT));a=ap.parse_args()
    try:print(json.dumps({'passed':True,**verify(Path(a.root))},sort_keys=True))
    except VerificationError as e:print(json.dumps({'passed':False,'error':str(e)}));sys.exit(1)
