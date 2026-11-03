"""Lean GTEST runner for v0.64.0 (new file, built from scripts/run_tests_0630.py, frozen). Each module in its own subprocess
(scripts.run_tests_0370.run). GTEST68 counts the GATED modules: test_scripts_068, test_release_0640 and the frozen certifier tests
test_certify32p, test_certify32s, test_certify20s, test_certify20b. Default output is a scratch path; --official writes
results/study-068/TEST_SUITE_068.json (refuses overwrite).
  PYTHONPATH=. python scripts/run_tests_0640.py [--output PATH | --official]"""
from __future__ import annotations
import argparse,json,os,sys,tempfile,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from scripts.run_tests_0370 import run
OFFICIAL=ROOT/'results/study-068/TEST_SUITE_068.json'
GATED=('test_scripts_068','test_release_0640','test_certify32p','test_certify32s','test_certify20s','test_certify20b')


def main(argv=None):
    ap=argparse.ArgumentParser();g=ap.add_mutually_exclusive_group();g.add_argument('--output');g.add_argument('--official',action='store_true')
    a=ap.parse_args(argv);out=OFFICIAL if a.official else Path(a.output) if a.output else Path(tempfile.gettempdir())/f'brute_tests_0640_{os.getpid()}_{time.time_ns()}.json'
    if out.exists():raise SystemExit(f'refusing to overwrite {out}')
    per={m:run(m) for m in GATED}
    rep={'schema':'brute.test-suite-068.v1','process':'lean','gated_modules':list(GATED),'per_module':per,
         'passed':all(per[m]['returncode']==0 and per[m]['tests']>0 for m in GATED)}
    out.parent.mkdir(parents=True,exist_ok=True);out.write_text(json.dumps(rep,indent=1,sort_keys=True)+'\n')
    print(json.dumps({m:(v['returncode'],v['tests']) for m,v in per.items()}),'passed',rep['passed'],'output',out);return 0 if rep['passed'] else 1


if __name__=='__main__':sys.exit(main())
