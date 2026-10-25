"""Scoring-script order check for study-005 (v0.3.0 errata, review L4). verify_release_030 is release-frozen, so this is
a separate check. It verifies, from git parent order only (git cannot prove wall-clock time; review M3a):
  1. each scoring script (make_gates_005, make_paired_005, make_reproducibility_005) is first added by a commit that is a
     strict ancestor of the first commit adding results/study-005/SEAL.json (the sealed results);
  2. each scoring script is byte-identical between that commit and HEAD.
  python scripts/check_order_030.py
"""
import json,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
SCRIPTS=('scripts/make_gates_005.py','scripts/make_paired_005.py','scripts/make_reproducibility_005.py')
SEALED='results/study-005/SEAL.json'


def git(*a):return subprocess.run(['git','-C',str(ROOT),*a],capture_output=True,text=True)


def first_add(path):
    c=git('log','--diff-filter=A','--format=%H','--',path).stdout.split();return c[-1] if c else None


def check_order(scripts=SCRIPTS,sealed=SEALED):
    seal=first_add(sealed);out={'sealed_results_commit':seal,'scripts':{}};ok=seal is not None
    for s in scripts:
        c=first_add(s);anc=c is not None and c!=seal and git('merge-base','--is-ancestor',c,seal).returncode==0
        same=c is not None and git('show',f'{c}:{s}').stdout==(ROOT/s).read_text()
        out['scripts'][s]={'first_commit':c,'strict_ancestor_of_sealed_results':anc,'unchanged_since':same};ok&=anc and same
    out['status']='passed' if ok else 'failed';out['note']='parent order only; commit times are author-set and cannot prove when results were seen'
    return out


if __name__=='__main__':
    r=check_order();print(json.dumps(r,indent=1));sys.exit(0 if r['status']=='passed' else 1)
