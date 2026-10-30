"""Lean GTI runner for v0.24.0 (lean process, as v0.23.0). Runs each v0.24.0 test module
in its own subprocess (python -m unittest -v) and writes results/study-027/TEST_SUITE_027.json (refuses overwrite).
  PYTHONPATH=. python scripts/run_tests_0240.py [--output PATH] [--modules m1 m2 ...]"""
from __future__ import annotations
import argparse,json,os,re,subprocess,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'results/study-027/TEST_SUITE_027.json'
MODULES=('test_scalesearch_0230','test_certify12_0230','test_scripts_027','test_release_0240')


def run(mod,root=ROOT):
    t0=time.time();env={**os.environ,'PYTHONPATH':str(root)}
    p=subprocess.run([sys.executable,'-m','unittest','-v','tests.'+mod],cwd=root,capture_output=True,text=True,env=env,timeout=900)
    res={m.group(1):m.group(2) for m in re.finditer(r'^(test\w+) \(.*?\) \.\.\. (ok|FAIL|ERROR|skipped.*)$',p.stderr,re.M)}
    return {'returncode':p.returncode,'tests':len(res),'results':res,'tail':p.stderr[-600:],'wall_informational':round(time.time()-t0,1)}


def main(argv=None):
    ap=argparse.ArgumentParser();ap.add_argument('--output',default=str(OUT));ap.add_argument('--modules',nargs='*',default=list(MODULES));a=ap.parse_args(argv)
    out=Path(a.output)
    if out.exists():raise SystemExit(f'refusing to overwrite {out}')
    per={m:run(m) for m in a.modules}
    rep={'schema':'brute.test-suite-027.v1','process':'lean','modules':a.modules,'per_module':per,
         'passed':all(v['returncode']==0 and v['tests']>0 for v in per.values())}
    out.parent.mkdir(parents=True,exist_ok=True);out.write_text(json.dumps(rep,indent=1,sort_keys=True)+'\n')
    print(json.dumps({m:(v['returncode'],v['tests']) for m,v in per.items()}),'passed',rep['passed']);return 0 if rep['passed'] else 1


if __name__=='__main__':sys.exit(main())
