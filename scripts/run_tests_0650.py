"""Lean GTEST runner for v0.65.0 (new file, built from scripts/run_tests_0640.py, frozen). Each module in its own subprocess
(scripts.run_tests_0370.run). GTEST69 counts the GATED modules: the new test_certify32r, test_scripts_069, test_release_keys_0650
(the GTEST68 regression), test_release_0650 and the frozen test_certify20s. The report records the sha256 of every gated test file
(GTEST69 checks they equal the committed files). Run --official ONLY after every test file is final and committed.
Default output is a scratch path; --official writes results/study-069/TEST_SUITE_069.json (refuses overwrite).
  PYTHONPATH=. python scripts/run_tests_0650.py [--output PATH | --official]"""
from __future__ import annotations
import argparse,json,os,subprocess,sys,tempfile,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from scripts.run_tests_0370 import run
from experiments.brute_common import sha
OFFICIAL=ROOT/'results/study-069/TEST_SUITE_069.json'
GATED=('test_certify32r','test_scripts_069','test_release_keys_0650','test_release_0650','test_certify20s')


def main(argv=None):
    ap=argparse.ArgumentParser();g=ap.add_mutually_exclusive_group();g.add_argument('--output');g.add_argument('--official',action='store_true')
    a=ap.parse_args(argv);out=OFFICIAL if a.official else Path(a.output) if a.output else Path(tempfile.gettempdir())/f'brute_tests_0650_{os.getpid()}_{time.time_ns()}.json'
    if out.exists():raise SystemExit(f'refusing to overwrite {out}')
    files={f'tests/{m}.py':sha(ROOT/f'tests/{m}.py') for m in GATED}
    if a.official:
        dirty=subprocess.run(['git','status','--porcelain','--',*files],cwd=ROOT,capture_output=True,text=True).stdout.strip()
        if dirty:raise SystemExit('test files not committed: '+dirty)
    per={m:run(m) for m in GATED}
    rep={'schema':'brute.test-suite-069.v1','process':'lean','gated_modules':list(GATED),'per_module':per,'test_file_sha256':files,
         'head':subprocess.run(['git','rev-parse','HEAD'],cwd=ROOT,capture_output=True,text=True).stdout.strip(),
         'passed':all(per[m]['returncode']==0 and per[m]['tests']>0 for m in GATED)}
    out.parent.mkdir(parents=True,exist_ok=True);out.write_text(json.dumps(rep,indent=1,sort_keys=True)+'\n')
    print(json.dumps({m:(v['returncode'],v['tests']) for m,v in per.items()}),'passed',rep['passed'],'output',out);return 0 if rep['passed'] else 1


if __name__=='__main__':sys.exit(main())
