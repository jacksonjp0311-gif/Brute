"""GTI test isolation runner for study-023 (BRUTE-0200-LR-ANYTIME-023): scripts/run_tests_0190.py (frozen, imported unchanged)
with the plan-023 GTI rule: "as study-021 with declared K_0190, plus clause vi".

  K_0190 (DECLARED IN ADVANCE, BRUTE_PLAN_023 GTI): test_release_0190.Release0190 version / embeddable API / short verify /
         untampered copy, allowed only if the same test passes on a clean worktree of tag v0.19.0;
  K_0150 .. K_0180, K_096 and the frozen K list: as run_tests_0190 (study 021).
  clause vi (tooling order, from #107): no tests/test_release_0200*.py and no scripts/verify_release_0200*.py exist in the
         tree when this runner starts (it is started at run_start by scripts/run_study_023.py; the pre-run check
         scripts/prerun_check_023.py asserts the same before launch).
New v0.20.0 tests = tests/test*.py absent from tag v0.19.0. Writes results/study-023/TEST_SUITE_023.json (refuses to overwrite).
Scheduling order uses the per-module walls of the committed study-021 TEST_SUITE_021.json (ordering only).
"""
from __future__ import annotations
import argparse,glob,json,subprocess,sys,time
from concurrent.futures import ThreadPoolExecutor,as_completed
from pathlib import Path
from scripts import run_tests_070 as T
from scripts import run_tests_0150 as P
from scripts import run_tests_0190 as Q

ROOT=Path(__file__).resolve().parents[1]
PLAN=ROOT/'experiments/BRUTE_PLAN_023.json'
OUT=ROOT/'results/study-023/TEST_SUITE_023.json'
K_ALLOWED=dict(Q.K_ALLOWED)
K_ALLOWED['0190']={f'test_release_0190.Release0190.{t}' for t in ('test_version_consistent','test_embeddable_api_answers','test_short_verify_passes','test_untampered_copy_passes')}
TAGS=dict(Q.TAGS,**{'0190':'v0.19.0'})
K_096=set(Q.K_096)
WORKERS=Q.WORKERS
TOOLING_GLOBS=('tests/test_release_0200*.py','scripts/verify_release_0200*.py','scripts/make_release_freeze_0200*.py')


def tooling_present(root=ROOT):
    return sorted(str(Path(p).relative_to(root)) for g in TOOLING_GLOBS for p in glob.glob(str(root/g)))


def new_tests(root=ROOT):
    old=set(subprocess.run(['git','ls-tree','--name-only','v0.19.0','tests/'],cwd=root,capture_output=True,text=True,check=True).stdout.split())
    return tuple(sorted(Path(x).name for x in glob.glob(str(root/'tests/test*.py')) if 'tests/'+Path(x).name not in old))


def verdict(mods,plain,frozen,plan,clean=None,new_tests=None,tooling=()):
    """run_tests_0190.verdict logic with K_0190 added, plus clause vi."""
    saved=Q.K_ALLOWED
    try:
        Q.K_ALLOWED=K_ALLOWED   # the frozen verdict body iterates the module global; restored below
        V=Q.verdict(mods,plain,frozen,plan,clean,new_tests=new_tests if new_tests is not None else new_tests_now())
    finally:Q.K_ALLOWED=saved
    V['clauses']['vi_tooling_order']=not tooling;V['tooling_present_at_start']=list(tooling)
    V['passed']=all(V['clauses'].values());return V


def new_tests_now():return new_tests()


def _prev_walls():
    p=ROOT/'results/study-021/TEST_SUITE_021.json'
    if not p.exists():return {}
    return {m:d.get('wall_informational',0) for m,d in json.loads(p.read_text())['per_module'].items()}


def run_all(modules,workers,python=sys.executable,log=print):
    """run_tests_0190.run_all with TAGS incl. 0190 and the study-021 walls for ordering."""
    mods={};clean={};t0=time.time();prev=_prev_walls()
    modules=sorted(modules,key=lambda m:(-prev.get(m,1e9),m))
    with ThreadPoolExecutor(workers) as ex:
        fp=ex.submit(T.run_child,'test*.py',ROOT,python)
        fm={ex.submit(T.run_child,m,ROOT,python):m for m in modules};fc={}
        for f in as_completed(fm):
            m=fm[f];mods[m]=f.result()
            v=next((v for v in TAGS if m==f'test_release_{v}.py'),None)
            if v and any(r[0] in ('fail','error') for r in mods[m]['results'].values()):fc[v]=ex.submit(Q._clean,TAGS[v],m,python)
        log(f'modules done {time.time()-t0:.0f} s',flush=True)
        for v in TAGS:clean[v]=fc[v].result() if v in fc else None
        plain=fp.result()
    return {m:mods[m] for m in modules},plain,clean


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
