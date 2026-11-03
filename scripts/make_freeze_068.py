"""Write experiments/BRUTE_SOURCE_FREEZE_068.json (refuses overwrite): sha256 of the study-068 plan, hand truth, truth check,
adapter, runner, their experiment imports and every file under brute/, plus the brute/ git tree and the Python version.
  PYTHONPATH=. python scripts/make_freeze_068.py"""
import subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from experiments.brute_common import sha,write_new,load,check
OUT=ROOT/'experiments/BRUTE_SOURCE_FREEZE_068.json'
FILES=['experiments/BRUTE_PLAN_068.json','experiments/truth_068.py','docs/research/TRUTH_068.md','results/study-068/TRUTHCHECK.json',
       'scripts/truthcheck_068.py','experiments/targets_068.py','experiments/brute_study_068.py','experiments/worlds_065.py',
       'experiments/worlds_064.py','experiments/worlds_058.py','experiments/brute_common.py','experiments/brute_study_058.py']


def files():return FILES+sorted(str(p.relative_to(ROOT)) for p in (ROOT/'brute').rglob('*.py'))


def tree(rev='HEAD'):return subprocess.run(['git','rev-parse',f'{rev}:brute'],cwd=ROOT,capture_output=True,text=True,check=True).stdout.strip()


def check_freeze():
    fz=load(OUT)
    for rel,d in fz['sha256_files'].items():check(sha(ROOT/rel)==d,'freeze mismatch '+rel)
    return fz


if __name__=='__main__':
    write_new(OUT,{'study':'BRUTE-0640-REALDECODER-068','python':sys.version.split()[0],'brute_tree':tree(),'brute_tree_v0630':tree('v0.63.0'),
                   'sha256_files':{f:sha(ROOT/f) for f in files()}})
    print('wrote',OUT)
