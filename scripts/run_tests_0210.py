"""GTI test isolation runner for study-024 (BRUTE-0210-STITCHED-LR-024): scripts/run_tests_0200.py (frozen, imported
unchanged) with the plan-024 rule (GTI carried: "release tooling after run_end").

  K list: run_tests_0200.K_ALLOWED (K_0190 and every earlier declared K) plus ONE new rule, K_0200_113 (DECLARED BEFORE THE
         SOURCE FREEZE, deviation #116): test_release_0200.Release0200.test_short_verify_passes may fail only with the
         known deviation-#113 message ('reference_1 and implementation_0 are the same commit') and only if every test in
         tests/test_release_0200_r1.py passes in the same run. It fails by design (it calls the frozen v0.20.0 verifier) and
         also fails on a clean worktree of tag v0.20.0, so the clean-tag K pattern cannot apply. Any other test_release_0200
         failure stays undeclared.
  clause vi (tooling order): no tests/test_release_0210*.py, scripts/verify_release_0210*.py or
         scripts/make_release_freeze_0210*.py exists in the tree when this runner starts (started at run_start by
         scripts/run_study_024.py; scripts/prerun_check_024.py asserts the same before launch).
New v0.21.0 tests = tests/test*.py absent from tag v0.20.0. Writes results/study-024/TEST_SUITE_024.json (refuses overwrite).
Scheduling order uses the per-module walls of the committed study-023 TEST_SUITE_023.json (ordering only).
"""
from __future__ import annotations
import argparse,glob,json,subprocess,sys,time
from pathlib import Path
from scripts import run_tests_070 as T
from scripts import run_tests_0150 as P
from scripts import run_tests_0190 as Q
from scripts import run_tests_0200 as Z

ROOT=Path(__file__).resolve().parents[1]
PLAN=ROOT/'experiments/BRUTE_PLAN_024.json'
OUT=ROOT/'results/study-024/TEST_SUITE_024.json'
K_ALLOWED=dict(Z.K_ALLOWED)
TAGS=dict(Z.TAGS)
WORKERS=Z.WORKERS
TOOLING_GLOBS=('tests/test_release_0210*.py','scripts/verify_release_0210*.py','scripts/make_release_freeze_0210*.py')


def tooling_present(root=ROOT):
    return sorted(str(Path(p).relative_to(root)) for g in TOOLING_GLOBS for p in glob.glob(str(root/g)))


def new_tests(root=ROOT):
    old=set(subprocess.run(['git','ls-tree','--name-only','v0.20.0','tests/'],cwd=root,capture_output=True,text=True,check=True).stdout.split())
    return tuple(sorted(Path(x).name for x in glob.glob(str(root/'tests/test*.py')) if 'tests/'+Path(x).name not in old))


K_0200_113='test_release_0200.Release0200.test_short_verify_passes'
K_0200_113_MSG='reference_1 and implementation_0 are the same commit'
R1_MODULE='test_release_0200_r1.py'


def k0200_113(mods):
    """True iff the K_0200_113 conditions hold (see the module docstring)."""
    r=next((d['results'].get(K_0200_113) for d in mods.values() if K_0200_113 in d['results']),None)
    if r is None or r[0] not in ('fail','error') or K_0200_113_MSG not in (r[1] if len(r)>1 else ''):return False
    R1=mods.get(R1_MODULE,{'results':{}})['results'];return bool(R1) and all(v[0]=='ok' for v in R1.values())


def verdict(mods,plain,frozen,plan,clean=None,new_tests_=None,tooling=()):
    """run_tests_0200.verdict (frozen K list) with the v0.21.0 new-test set, clause vi on the 0210 tooling and K_0200_113."""
    tooling=tuple(tooling)
    V=Z.verdict(mods,plain,frozen,plan,clean,new_tests=new_tests_ if new_tests_ is not None else new_tests(),tooling=tooling)
    ok=k0200_113(mods);V['k_rules']['0200_113']={'failures':[K_0200_113] if K_0200_113 in V['failing'] else [],'applied':ok}
    if ok:
        V['undeclared_failures']=[t for t in V['undeclared_failures'] if t!=K_0200_113]
        V['clauses']['i_only_declared_failures']=not V['undeclared_failures']
    V['tooling_globs']=list(TOOLING_GLOBS);V['passed']=all(V['clauses'].values());return V


def _prev_walls():
    p=ROOT/'results/study-023/TEST_SUITE_023.json'
    if not p.exists():return {}
    return {m:d.get('wall_informational',0) for m,d in json.loads(p.read_text())['per_module'].items()}


def run_all(modules,workers,python=sys.executable,log=print):
    saved=Z._prev_walls
    try:
        Z._prev_walls=_prev_walls   # ordering only; restored below
        return Z.run_all(modules,workers,python,log)
    finally:Z._prev_walls=saved


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--output',default=str(OUT));ap.add_argument('--modules',help='comma list (dev only; not a GTI run)')
    ap.add_argument('--workers',type=int,default=WORKERS)
    a=ap.parse_args();out=Path(a.output)
    if out.exists():raise SystemExit(f'refusing to overwrite {out}')
    tooling=tooling_present()
    plan=json.loads(PLAN.read_text());t0=time.time()
    head=subprocess.run(['git','rev-parse','HEAD'],cwd=ROOT,capture_output=True,text=True).stdout.strip()
    porc=subprocess.run(['git','status','--porcelain','--untracked-files=no'],cwd=ROOT,capture_output=True,text=True).stdout;dirty=porc.strip()
    modules=a.modules.split(',') if a.modules else sorted(Path(x).name for x in glob.glob(str(ROOT/'tests/test*.py')))
    mods,plain,clean=run_all(modules,a.workers);frozen=P.frozen_check()
    V=verdict(mods,plain,frozen,plan,clean,tooling=tooling)
    rep={'schema':'brute.test-suite.v4','study':plan['study'],'gate':'GTI_test_isolation','python':sys.version.split()[0],
         'executable':sys.executable,'head':head,'tracked_tree_dirty':bool(dirty),'workers':a.workers,
         'dirty_tracked_files':[l[3:] for l in porc.splitlines() if l.strip()],'modules_subset':a.modules,
         'per_module':mods,'plain_discover':plain,'frozen_files':frozen,'clean_tag_runs':clean,
         'verdict':V,'wall_informational':round(time.time()-t0,1)}
    out.parent.mkdir(parents=True,exist_ok=True);out.write_text(json.dumps(rep,indent=1,sort_keys=True)+'\n')
    print(json.dumps({'passed':V['passed'],'clauses':V['clauses'],'undeclared':V['undeclared_failures'],
                      'run':V['tests_run_per_module_total'],'plain':V['tests_run_plain'],'wall':rep['wall_informational']},indent=1))


if __name__=='__main__':main()
