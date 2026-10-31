"""Seed assertion for study-055, attempt 3 (deviation #183). New file. Attempts 1 and 2 (SEEDCHECK_055_ATTEMPT1_FAIL / _ATTEMPT2_FAIL,
published) scanned HEAD after study-055's own tooling, tests and ledger notes had been committed, so they found the plan's own seeds
declared there. Study-054 ran its check right after build authorization and its certify module. This attempt runs check_seeds_055
unchanged (rules J, K and L, every check, every negative control) against the tracked tree at a fixed commit, by default 7fd27d5
(build_authorization_055 e8ac749 + certify/20c), checked out in a scratch git worktree, and records that commit in the output.
  PYTHONPATH=. python scripts/check_seeds_055_at.py [--commit 7fd27d5] --write results/diag-055/SEEDCHECK_055.json"""
import json,subprocess,sys,tempfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from scripts import check_seeds_055 as C
COMMIT='7fd27d5'


def main(argv=()):
    argv=list(argv);commit=argv[argv.index('--commit')+1] if '--commit' in argv else COMMIT
    out=ROOT/argv[argv.index('--write')+1] if '--write' in argv else None
    full=subprocess.run(['git','rev-parse',commit],cwd=ROOT,capture_output=True,text=True,check=True).stdout.strip()
    tree=Path(tempfile.mkdtemp(prefix='seedtree055-',dir='/tmp'))/'t'
    subprocess.run(['git','worktree','add','--detach',str(tree),full],cwd=ROOT,check=True,capture_output=True)
    tmp=tree.parent/'rep.json';err=None
    try:
        C.ROOT=tree
        try:C.main(['--write',str(tmp)])
        except C.VerificationError as e:err=str(e)
        rep=json.loads(tmp.read_text())
    finally:
        subprocess.run(['git','worktree','remove','--force',str(tree)],cwd=ROOT,check=True,capture_output=True)
    rep={'scanned_commit':full,'attempt':3,'deviation':'#183',**rep};txt=json.dumps(rep,indent=1,default=list)
    if out is not None:
        out.parent.mkdir(parents=True,exist_ok=True)
        with open(out,'x') as fh:fh.write(txt+'\n')
    print('PASS' if rep['PASS'] else 'FAIL',full,err or '')
    return 0 if rep['PASS'] else 1


if __name__=='__main__':sys.exit(main(sys.argv[1:]))
