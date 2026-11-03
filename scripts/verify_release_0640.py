"""Brute v0.64.0 release verification, lean process (BRUTE_PLAN_068; new file, self-contained). Short verify:
  1. RELEASE.json parses, version 0.64.0, the 0440 release keys present, gate lists and status phrase equal GATES_068.json;
  2. MANIFEST.sha256 matches the tree; BRUTE_SOURCE_FREEZE_068 holds; the v0.63.0 freeze chain (brute_common_066.check_freeze) holds;
  3. the pre-run truth check, the recount and the gates reproduce (truthcheck_068 / recount_068 / make_gates_068 --check);
  4. commit order: plan -> truth -> build_authorization -> truthcheck -> freeze -> run_start -> run_end (ledger commits, each an
     ancestor of the next) -> HEAD, and the truth file unchanged since truth_068.
  The test suite is NOT run here; run scripts/run_tests_0640.py.
  PYTHONPATH=. python scripts/verify_release_0640.py [--root R]"""
from __future__ import annotations
import argparse,json,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from experiments.brute_common import VerificationError,check
from scripts.verify_release_060 import jload,req,manifest_ok
from scripts.verify_release_0380 import _script
from scripts import verify_release_0440 as V44
VERSION='0.64.0';GATES='results/study-068/GATES_068.json';RELEASE_KEYS=V44.RELEASE_KEYS


def release_ok(root):
    R=jload(root/'RELEASE.json')
    for k in RELEASE_KEYS:req(R,k,'RELEASE.json')
    check(R['version']==VERSION,f'RELEASE.json version is not {VERSION}')
    G=jload(root/GATES);check(sorted(R['gates_passed'])==G['passed'] and sorted(R['gates_failed'])==G['failed'],'gate lists differ from GATES_068.json')
    check(R['status_phrase']==G['status'],'status_phrase differs from GATES_068.json');return R


def order_ok(root):
    G=jload(root/GATES)['gates']['G_PROC68'];check(G['pass'] is True,'G_PROC68 did not pass');last=G['chain'][-1]
    r=subprocess.run(['git','merge-base','--is-ancestor',last,'HEAD'],cwd=root);check(r.returncode==0,'run_end is not an ancestor of HEAD')
    return G['chain']


def verify(root=ROOT):
    root=Path(root);out={'release':release_ok(root)['version']}
    check(manifest_ok(root),'MANIFEST.sha256 does not match');out['manifest']=True
    out['freeze_068']=_script(root,'-c','from scripts.make_freeze_068 import check_freeze;check_freeze();print("ok")')
    out['freeze_066']=_script(root,'-c','from experiments.brute_common_066 import check_freeze;check_freeze();print("ok")')
    out['truthcheck']=_script(root,'scripts/truthcheck_068.py','--check')
    out['recount']=_script(root,'scripts/recount_068.py','--check')
    out['gates']=_script(root,'scripts/make_gates_068.py','--check')
    out['commit_chain']=order_ok(root);return out


if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--root',default=str(ROOT));a=ap.parse_args()
    try:print(json.dumps({'passed':True,**verify(Path(a.root))},sort_keys=True))
    except VerificationError as e:print(json.dumps({'passed':False,'error':str(e)}));sys.exit(1)
