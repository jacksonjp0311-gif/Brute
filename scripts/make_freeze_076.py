"""Write experiments/BRUTE_SOURCE_FREEZE_076.json (refuses overwrite): sha256 of the study-076 plan, the oracle truth (json and reader), the
reset-free adapter, runner, recount, every experiments/worlds_0*.py and every file under brute/, plus the brute/ git tree and Python.
  PYTHONPATH=. python scripts/make_freeze_076.py"""
import subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from experiments.brute_common import sha,write_new,load,check
OUT=ROOT/'experiments/BRUTE_SOURCE_FREEZE_076.json'
FILES=['experiments/BRUTE_PLAN_076.json','experiments/truth_076.json','experiments/truth_076.py','scripts/make_truth_076.py','experiments/targets_076.py',
       'experiments/brute_study_076.py','scripts/recount_076.py','experiments/brute_common.py']


def files():return FILES+sorted(str(p.relative_to(ROOT)) for p in (ROOT/'experiments').glob('worlds_0*.py') if str(p.relative_to(ROOT)) not in FILES)+sorted(str(p.relative_to(ROOT)) for p in (ROOT/'brute').rglob('*.py'))


def tree(rev='HEAD'):return subprocess.run(['git','rev-parse',f'{rev}:brute'],cwd=ROOT,capture_output=True,text=True,check=True).stdout.strip()


def check_freeze():
    fz=load(OUT)
    for rel,d in fz['sha256_files'].items():check(sha(ROOT/rel)==d,'freeze mismatch '+rel)
    return fz


if __name__=='__main__':
    write_new(OUT,{'study':'BRUTE-0710-TIME-076','python':sys.version.split()[0],'brute_tree':tree(),'brute_tree_v0710':tree('v0.71.0'),
                   'sha256_files':{f:sha(ROOT/f) for f in files()}})
    print('wrote',OUT)
