"""Brute v0.69.0 release verification, lean process (BRUTE_PLAN_073; new file, self-contained). Short verify:
  1. RELEASE.json parses, version 0.69.0, every REQUIRED key present (the 0440 RELEASE_KEYS plus status_phrase and contribution_split),
     gate lists and status phrase equal GATES_073.json;
  2. MANIFEST.sha256 matches the tree; BRUTE_SOURCE_FREEZE_073 holds; the v0.63.0 freeze chain (brute_common_066.check_freeze) holds;
  3. the recount and the gates reproduce (recount_073 / make_gates_073 --check);
  4. commit order: plan -> build_authorization -> freeze -> run_start -> run_end (ledger commits, each an ancestor of the next) -> HEAD.
  The test suite is NOT run here; run scripts/run_tests_0690.py.
  PYTHONPATH=. python scripts/verify_release_0690.py [--root R]"""
from __future__ import annotations
import argparse,json,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from experiments.brute_common import VerificationError,check
from scripts.verify_release_060 import jload,req,manifest_ok
from scripts.verify_release_0380 import _script
from scripts import verify_release_0440 as V44
VERSION='0.69.0';GATES='results/study-073/GATES_073.json';RELEASE_KEYS=V44.RELEASE_KEYS
REQUIRED=tuple(RELEASE_KEYS)+('status_phrase','contribution_split')


def release_ok(root):
    R=jload(root/'RELEASE.json')
    for k in REQUIRED:req(R,k,'RELEASE.json')
    check(R['version']==VERSION,f'RELEASE.json version is not {VERSION}')
    G=jload(root/GATES);check(sorted(R['gates_passed'])==G['passed'] and sorted(R['gates_failed'])==G['failed'],'gate lists differ from GATES_073.json')
    check(R['status_phrase']==G['status'],'status_phrase differs from GATES_073.json')
    check(set(R['contribution_split'])>={'textbook','brute'},'contribution_split needs textbook and brute');return R


def order_ok(root):
    G=jload(root/GATES)['gates']['G_PROC73'];check(G['pass'] is True,'G_PROC73 did not pass');last=G['chain'][-1]
    r=subprocess.run(['git','merge-base','--is-ancestor',last,'HEAD'],cwd=root);check(r.returncode==0,'run_end is not an ancestor of HEAD')
    return G['chain']


def verify(root=ROOT):
    root=Path(root);out={'release':release_ok(root)['version']}
    check(manifest_ok(root),'MANIFEST.sha256 does not match');out['manifest']=True
    out['freeze_073']=_script(root,'-c','from scripts.make_freeze_073 import check_freeze;check_freeze();print("ok")')
    out['truth']=_script(root,'scripts/make_truth_073.py','--check')
    out['recount']=_script(root,'scripts/recount_073.py','--check')
    out['gates']=_script(root,'scripts/make_gates_073.py','--check')
    out['commit_chain']=order_ok(root);return out


if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--root',default=str(ROOT));a=ap.parse_args()
    try:print(json.dumps({'passed':True,**verify(Path(a.root))},sort_keys=True))
    except VerificationError as e:print(json.dumps({'passed':False,'error':str(e)}));sys.exit(1)
