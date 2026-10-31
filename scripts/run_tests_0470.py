"""Lean GTI runner for v0.47.0 (built from scripts/run_tests_0460.py, frozen). Runs each module in its own subprocess
(python -m unittest -v) and writes a JSON report (refuses overwrite). GTI (plan 050) counts only the GATED modules:
test_certify16n (the certify/16n API under test), test_scripts_050, test_release_0470, and the frozen certify/16e, certify/16d,
certify/16 and certify/14 modules test_certify16e, test_certify16d, test_certify16 and test_scalesearch4_0260. REPORTED (run for
the record): test_scripts_049, test_release_0460. The sealed 045 to 050 raw RESULTS must be restored first
(scripts/study04{5..9}_storage.py and study050_storage.py restore). Default output is a scratch path outside the tree; the official
GTI input is written only with --official (results/study-050/TEST_SUITE_050.json).
  PYTHONPATH=. python scripts/run_tests_0470.py [--output PATH | --official] [--modules m1 m2 ...]"""
from __future__ import annotations
import argparse,json,os,sys,tempfile,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from scripts.run_tests_0370 import run
OFFICIAL=ROOT/'results/study-050/TEST_SUITE_050.json'
GATED=('test_certify16n','test_scripts_050','test_release_0470','test_certify16e','test_certify16d','test_certify16','test_scalesearch4_0260')
REPORTED=('test_scripts_049','test_release_0460')
MODULES=GATED+REPORTED


def scratch_path():return Path(tempfile.gettempdir())/f'brute_tests_0470_{os.getpid()}_{time.time_ns()}.json'


def main(argv=None):
    ap=argparse.ArgumentParser();g=ap.add_mutually_exclusive_group()
    g.add_argument('--output',default=None);g.add_argument('--official',action='store_true')
    ap.add_argument('--modules',nargs='*',default=list(MODULES));a=ap.parse_args(argv)
    out=OFFICIAL if a.official else Path(a.output) if a.output else scratch_path()
    if out.exists():raise SystemExit(f'refusing to overwrite {out}')
    per={m:run(m) for m in a.modules}
    gated=[m for m in a.modules if m in GATED]
    rep={'schema':'brute.test-suite-050.v1','process':'lean','modules':a.modules,'gated_modules':gated,
         'reported_modules':[m for m in a.modules if m not in GATED],'per_module':per,
         'passed':bool(gated) and all(per[m]['returncode']==0 and per[m]['tests']>0 for m in gated)}
    out.parent.mkdir(parents=True,exist_ok=True);out.write_text(json.dumps(rep,indent=1,sort_keys=True)+'\n')
    print(json.dumps({m:(v['returncode'],v['tests']) for m,v in per.items()}),'passed',rep['passed'],'output',out);return 0 if rep['passed'] else 1


if __name__=='__main__':sys.exit(main())
