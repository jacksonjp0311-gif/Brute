"""r1 of verify_release_0220.py (deviation #122: COMMIT_ORDER_025 key is entries, not events; also checks BRUTE_RELEASE_FREEZE_0220_R1). Brute v0.22.0 release verification, lean process (BRUTE_PLAN_025 + A1 + A2). New file; earlier verifiers stay frozen.

Short verify only (A2 dropped the long re-run and the double fresh-clone check):
  1. RELEASE.json parses, version 0.22.0, required keys present, gate lists match results/study-025/GATES_025.json;
  2. MANIFEST.sha256 matches the tree; BRUTE_SOURCE_FREEZE_025 (check_freeze, incl. A2) and BRUTE_RELEASE_FREEZE_0220 hold;
  3. raw study-025 transfer files restore from their committed .json.gz and match transfer/SEAL.json;
  4. PAIRED_ANALYSIS_025 and GATES_025 reproduce byte-for-byte from the sealed inputs (make_paired_025 / make_gates_025 --check);
  5. the commit order (COMMIT_ORDER_025.json, then source freeze -> seal -> HEAD) is an ancestor chain (git, when available).

  PYTHONPATH=. python scripts/verify_release_0220.py [--root R]
"""
from __future__ import annotations
import argparse,json,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from experiments.brute_common import VerificationError,check
from scripts.verify_release_060 import jload,req,_freeze,manifest_ok

STUDY='results/study-025'
RELEASE_KEYS=('version','preregistration','amendments','source_freeze','source_freeze_commit','release_freeze','seal_commit',
              'results_dir','case_count','gates_passed','gates_failed','headline','api','deviations','process')


def release_ok(root):
    R=jload(root/'RELEASE.json')
    for k in RELEASE_KEYS:req(R,k,'RELEASE.json')
    check(R['version']=='0.22.0','RELEASE.json version is not 0.22.0')
    G=jload(root/STUDY/'GATES_025.json');gates=req(G,'gates','GATES_025.json')
    passed=sorted(k for k,v in gates.items() if v.get('pass') is True);failed=sorted(k for k,v in gates.items() if v.get('pass') is not True)
    check(sorted(R['gates_passed'])==passed and sorted(R['gates_failed'])==failed,'RELEASE.json gate lists differ from GATES_025.json')
    return R


def chain(root,R):
    order=[e['commit'] for e in jload(root/'experiments/COMMIT_ORDER_025.json')['entries']]+[R['source_freeze_commit'],R['seal_commit'],'HEAD']
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
    from experiments.brute_common_025 import check_freeze
    check_freeze();out['source_freeze']=True
    out['release_freeze_files']=_freeze(root,'experiments/BRUTE_RELEASE_FREEZE_0220.json')+_freeze(root,'experiments/BRUTE_RELEASE_FREEZE_0220_R1.json')
    out['raw_restore']=_script(root,'scripts/study025_storage.py','restore')
    out['paired_check']=_script(root,'scripts/make_paired_025.py','--check')
    out['gates_check']=_script(root,'scripts/make_gates_025.py','--check')
    out['commit_chain']=chain(root,R)
    return out


if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--root',default=str(ROOT));a=ap.parse_args()
    try:print(json.dumps({'passed':True,**verify(Path(a.root))},sort_keys=True))
    except VerificationError as e:print(json.dumps({'passed':False,'error':str(e)}));sys.exit(1)
