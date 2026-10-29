"""Brute v0.20.0 release verification, revision 1 (deviation #113). New file; scripts/verify_release_0200.py stays frozen
under BRUTE_RELEASE_FREEZE_0200.

The frozen verify_release_0200.git_order requires every adjacent pair of the process chain to be distinct commits. In
BRUTE_SOURCE_FREEZE_023, commit 9e0ca70 is both the last reference commit and the first implementation commit: it landed
the second implementation (v0200_reference) and the RGL4 code together. So the frozen verifier stops with
"reference_1 and implementation_0 are the same commit" before it checks anything else.

This revision changes one thing. A repeated commit is accepted only at the reference→implementation boundary, and only
when the source freeze itself lists the same hash as reference_commits[-1] and implementation_commits[0]. Every other
check is the frozen code, called unchanged. It also checks BRUTE_RELEASE_FREEZE_0200_R1.json.

  python scripts/verify_release_0200_r1.py [--long]
"""
from __future__ import annotations
import argparse,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from experiments.brute_common import VerificationError,check
from scripts import verify_release_0200 as V
from scripts.verify_release_060 import req,_guard,_freeze
R1_FREEZE='experiments/BRUTE_RELEASE_FREEZE_0200_R1.json'


def git_order(root,rel):
    from scripts.verify_release_020 import _git
    def anc(a,b):return _git(root,'merge-base','--is-ancestor',a,b).returncode==0
    def same(a,b):return _git(root,'rev-parse',a).stdout==_git(root,'rev-parse',b).stdout
    check(_git(root,'rev-parse','--git-dir').returncode==0,'not a git checkout')
    fr=V.jload(root/rel['source_freeze'])
    check(rel['preregistration_commit']==req(fr,'preregistration_commit','freeze'),'RELEASE.json preregistration_commit differs from the source freeze')
    refs=req(fr,'reference_commits','freeze');imps=req(fr,'implementation_commits','freeze')
    dual=refs[-1]==imps[0]
    chain=[('preregistration',fr['preregistration_commit']),('seedcheck',req(fr,'seedcheck_commit','freeze'))]
    chain+=[(f'reference_{i}',c) for i,c in enumerate(refs)]+[(f'implementation_{i}',c) for i,c in enumerate(imps)]
    chain+=[('source_freeze',rel['source_freeze_commit']),('seal',rel['seal_commit']),('head','HEAD')]
    allowed={(f'reference_{len(refs)-1}','implementation_0')} if dual else set()
    for (na,a),(nb,b) in zip(chain,chain[1:]):
        check(anc(a,b),f'{na} {a} is not an ancestor of {nb} {b}')
        if b!='HEAD' and (na,nb) not in allowed:check(not same(a,b),f'{na} and {nb} are the same commit')
    sc=rel['scoring_scripts_commit'];sf=rel['source_freeze_commit']
    for a,b,na,nb in ((sf,sc,'source_freeze','scoring_scripts'),(sc,rel['seal_commit'],'scoring_scripts','seal')):
        check(anc(a,b) and not same(a,b),f'{na} {a} is not a strict ancestor of {nb} {b}')
    chain.insert([n for n,_ in chain].index('seal'),('scoring_scripts',sc))
    plan=_git(root,'show',f"{rel['preregistration_commit']}:{rel['preregistration']}")
    check(plan.returncode==0 and plan.stdout==(root/rel['preregistration']).read_text(),'plan changed after pre-registration')
    for f in V.SCORING:
        b=_git(root,'show',f"{sc}:{f}");check(b.returncode==0 and b.stdout==(root/f).read_text(),f'{f} changed after the scoring freeze')
    out={n:c for n,c in chain if c!='HEAD'}
    out['dual_role_commits']=[refs[-1]] if dual else []
    return out


def verify(root=ROOT,fast=True,git=True,long=False):
    frozen=V.git_order;V.git_order=git_order
    def run(r,g):
        out=V._verify(r,g,long);out['schema']='brute.verify-release.v20_0_r1'
        out['locked_files'][R1_FREEZE]=_freeze(r,R1_FREEZE);out['revision']='r1 (deviation #113)';return out
    try:return _guard(run,Path(root),git)
    finally:V.git_order=frozen  # never leak the replacement into the frozen module


if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--long',action='store_true');ap.add_argument('--fast',action='store_true');a=ap.parse_args()
    try:print(json.dumps(verify(long=a.long),indent=2))
    except VerificationError as e:print('VERIFICATION FAILED:',e);sys.exit(1)
