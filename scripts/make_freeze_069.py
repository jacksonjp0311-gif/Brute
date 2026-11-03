"""Write experiments/BRUTE_SOURCE_FREEZE_069.json (refuses overwrite): sha256 of the study-069 plan, hand truth, truth check,
adapter, runner, every experiments/worlds_0*.py (covers the transitive world imports) and every file under brute/, plus the brute/ git tree and the Python version.
  PYTHONPATH=. python scripts/make_freeze_069.py"""
import subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from experiments.brute_common import sha,write_new,load,check
OUT=ROOT/'experiments/BRUTE_SOURCE_FREEZE_069.json'
FILES=['experiments/BRUTE_PLAN_069.json','experiments/truth_069.py','experiments/truth_068.py','docs/research/TRUTH_069.md',
       'results/study-069/TRUTHCHECK.json','scripts/truthcheck_069.py','experiments/targets_069.py','experiments/brute_study_069.py',
       'experiments/worlds_065.py','experiments/worlds_064.py','experiments/worlds_058.py','experiments/brute_common.py']


def files():return FILES+sorted(str(p.relative_to(ROOT)) for p in (ROOT/'experiments').glob('worlds_0*.py') if str(p.relative_to(ROOT)) not in FILES)+sorted(str(p.relative_to(ROOT)) for p in (ROOT/'brute').rglob('*.py'))


def tree(rev='HEAD'):return subprocess.run(['git','rev-parse',f'{rev}:brute'],cwd=ROOT,capture_output=True,text=True,check=True).stdout.strip()


def check_freeze():
    fz=load(OUT)
    for rel,d in fz['sha256_files'].items():check(sha(ROOT/rel)==d,'freeze mismatch '+rel)
    return fz


if __name__=='__main__':
    write_new(OUT,{'study':'BRUTE-0650-RESETDECODER-069','python':sys.version.split()[0],'brute_tree':tree(),'brute_tree_v0640':tree('v0.64.0'),
                   'sha256_files':{f:sha(ROOT/f) for f in files()}})
    print('wrote',OUT)
