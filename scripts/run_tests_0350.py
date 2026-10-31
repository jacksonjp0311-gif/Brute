"""Lean GTI runner for v0.35.0 (lean process; built from scripts/run_tests_0340.py, frozen). Runs each v0.35.0 test module
in its own subprocess (python -m unittest -v) and writes a JSON report (refuses overwrite).
Deviation #146 (release-verify fix, kept by #148): the DEFAULT output is a fresh scratch path outside the tree
(<tempdir>/brute_tests_0350_<pid>_<time>.json), so a fresh-clone verify run never collides with the tracked, sealed
results/study-038/TEST_SUITE_038.json (run_tests_0320/0330 refused twice in a row on their own). The official GTI input is written
only when asked explicitly:  --output results/study-038/TEST_SUITE_038.json  (or --official).
  PYTHONPATH=. python scripts/run_tests_0350.py [--output PATH | --official] [--modules m1 m2 ...]"""
from __future__ import annotations
import argparse,json,os,re,subprocess,sys,tempfile,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
OFFICIAL=ROOT/'results/study-038/TEST_SUITE_038.json'
MODULES=('test_scalesearch13_0350','test_scalesearch12_0340','test_scalesearch11_0330','test_scalesearch10_0320','test_scalesearch9_0310','test_scalesearch8_0300',
         'test_scalesearch_0230','test_scripts_038','test_release_0350')


def scratch_path():
    """Default output: a new, not yet existing file in the system temp dir (never inside the repository)."""
    return Path(tempfile.gettempdir())/f'brute_tests_0350_{os.getpid()}_{time.time_ns()}.json'


def run(mod,root=ROOT):
    t0=time.time();env={**os.environ,'PYTHONPATH':str(root)}
    p=subprocess.run([sys.executable,'-m','unittest','-v','tests.'+mod],cwd=root,capture_output=True,text=True,env=env,timeout=900)
    res={m.group(1):m.group(2) for m in re.finditer(r'^(test\w+) \(.*?\) \.\.\. (ok|FAIL|ERROR|skipped.*)$',p.stderr,re.M)}
    return {'returncode':p.returncode,'tests':len(res),'results':res,'tail':p.stderr[-600:],'stdout_tail':p.stdout[-1500:],
            'wall_informational':round(time.time()-t0,1)}


def main(argv=None):
    ap=argparse.ArgumentParser();g=ap.add_mutually_exclusive_group()
    g.add_argument('--output',default=None);g.add_argument('--official',action='store_true')
    ap.add_argument('--modules',nargs='*',default=list(MODULES));a=ap.parse_args(argv)
    out=OFFICIAL if a.official else Path(a.output) if a.output else scratch_path()
    if out.exists():raise SystemExit(f'refusing to overwrite {out}')
    per={m:run(m) for m in a.modules}
    rep={'schema':'brute.test-suite-038.v1','process':'lean','modules':a.modules,'per_module':per,
         'passed':all(v['returncode']==0 and v['tests']>0 for v in per.values())}
    out.parent.mkdir(parents=True,exist_ok=True);out.write_text(json.dumps(rep,indent=1,sort_keys=True)+'\n')
    print(json.dumps({m:(v['returncode'],v['tests']) for m,v in per.items()}),'passed',rep['passed'],'output',out);return 0 if rep['passed'] else 1


if __name__=='__main__':sys.exit(main())
