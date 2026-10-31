"""Lean GTI runner for v0.41.0 (built from scripts/run_tests_0400.py, frozen). Runs each module in its own subprocess
(python -m unittest -v) and writes a JSON report (refuses overwrite). GTI (plan 044) counts only the GATED 044 modules
(test_lowobspolicy17 for the new A16_xf wrapper, test_scripts_044, test_release_0410); the REPORTED modules are frozen earlier
suites run for the record (test_worlds_043, test_scalesearch16_0390 for A16, test_scripts_043). Default output is a scratch path
outside the tree (deviation #146 lesson); the official GTI input is written only with --official
(results/study-044/TEST_SUITE_044.json).
  PYTHONPATH=. python scripts/run_tests_0410.py [--output PATH | --official] [--modules m1 m2 ...]"""
from __future__ import annotations
import argparse,json,os,sys,tempfile,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from scripts.run_tests_0370 import run
OFFICIAL=ROOT/'results/study-044/TEST_SUITE_044.json'
GATED=('test_lowobspolicy17','test_scripts_044','test_release_0410')
REPORTED=('test_worlds_043','test_scalesearch16_0390','test_scripts_043')
MODULES=GATED+REPORTED


def scratch_path():return Path(tempfile.gettempdir())/f'brute_tests_0410_{os.getpid()}_{time.time_ns()}.json'


def main(argv=None):
    ap=argparse.ArgumentParser();g=ap.add_mutually_exclusive_group()
    g.add_argument('--output',default=None);g.add_argument('--official',action='store_true')
    ap.add_argument('--modules',nargs='*',default=list(MODULES));a=ap.parse_args(argv)
    out=OFFICIAL if a.official else Path(a.output) if a.output else scratch_path()
    if out.exists():raise SystemExit(f'refusing to overwrite {out}')
    per={m:run(m) for m in a.modules}
    gated=[m for m in a.modules if m in GATED]
    rep={'schema':'brute.test-suite-044.v1','process':'lean','modules':a.modules,'gated_modules':gated,
         'reported_modules':[m for m in a.modules if m not in GATED],'per_module':per,
         'passed':bool(gated) and all(per[m]['returncode']==0 and per[m]['tests']>0 for m in gated)}
    out.parent.mkdir(parents=True,exist_ok=True);out.write_text(json.dumps(rep,indent=1,sort_keys=True)+'\n')
    print(json.dumps({m:(v['returncode'],v['tests']) for m,v in per.items()}),'passed',rep['passed'],'output',out);return 0 if rep['passed'] else 1


if __name__=='__main__':sys.exit(main())
