"""GTI test isolation runner for study-019 (BRUTE-0170-SEQUENTIAL-MARGIN-019): scripts/run_tests_0160.py (parallel, deviation
#98) with the plan-019 K rules and the D100 fix (dirty_tracked_files parsed with line[3:] on the UNSTRIPPED porcelain
output; run_tests_0160 stripped first, which cut the first character of the first path; reporting only, the
tracked_tree_dirty flag was always right).

Same children as scripts/run_tests_0150.py (frozen, imported for frozen_check / clean_run): every tests/test*.py module
in its OWN fresh interpreter (frozen scripts/run_tests_070.run_child), the plain `unittest discover -s tests` run, and a
clean-tag run of every failing test_release_0X0 module; here up to --workers children run at once (a thread pool of
subprocesses; each child is its own interpreter, so isolation is unchanged). Clause logic as run_tests_0150.verdict plus:
  K_0150 (DECLARED IN ADVANCE, BRUTE_PLAN_018 GTI): test_release_0150.Release0150 version / embeddable API / short verify /
         untampered copy, allowed only if the same test passes on a clean worktree of tag v0.15.0;
  K_0160 (DECLARED IN ADVANCE, BRUTE_PLAN_019 GTI): test_release_0160.Release0160 version / embeddable API / short verify /
         untampered copy, allowed only if the same test passes on a clean worktree of tag v0.16.0;
  K_096  (DECLARED IN ADVANCE, deviation #96): test_scripts_017.Orchestrator017.test_streams (stale frozen literal).
New v0.17.0 tests = tests/test*.py absent from tag v0.16.0. Writes results/study-019/TEST_SUITE_019.json (refuses to overwrite).
"""
from __future__ import annotations
import argparse,glob,json,subprocess,sys,tempfile,threading,time
from concurrent.futures import ThreadPoolExecutor,as_completed
from pathlib import Path
from scripts import run_tests_070 as T
from scripts import run_tests_0150 as P

ROOT=Path(__file__).resolve().parents[1]
PLAN=ROOT/'experiments/BRUTE_PLAN_019.json'
PLAN009=P.PLAN009
OUT=ROOT/'results/study-019/TEST_SUITE_019.json'
K_ALLOWED=dict(P.K_ALLOWED)
K_ALLOWED['0150']={f'test_release_0150.Release0150.{t}' for t in ('test_version_consistent','test_embeddable_api_answers','test_short_verify_passes','test_untampered_copy_passes')}
K_ALLOWED['0160']={f'test_release_0160.Release0160.{t}' for t in ('test_version_consistent','test_embeddable_api_answers','test_short_verify_passes','test_untampered_copy_passes')}
TAGS=dict(P.TAGS,**{'0150':'v0.15.0','0160':'v0.16.0'})
K_096={'test_scripts_017.Orchestrator017.test_streams'}
WORKERS=4
_GIT=threading.Lock()   # git worktree add / remove one at a time (git worktree locks); the child runs OUTSIDE the lock


def _clean(tag,module,python):
    """run_tests_0150.clean_run (frozen) with only the git worktree operations serialized, so clean-tag children run in
    parallel like every other child (the 0150 body, otherwise unchanged)."""
    tmp=Path(tempfile.mkdtemp(prefix=f'{tag}wt-'))/'wt'
    with _GIT:subprocess.run(['git','worktree','add','--detach',str(tmp),tag],cwd=ROOT,check=True,capture_output=True)
    try:
        if not (tmp/'scripts/run_tests_070.py').exists():(tmp/'scripts/run_tests_070.py').write_text((ROOT/'scripts/run_tests_070.py').read_text())
        return T.run_child(module,tmp,python)
    finally:
        with _GIT:subprocess.run(['git','worktree','remove','--force',str(tmp)],cwd=ROOT,capture_output=True)


def new_tests(root=ROOT):
    old=set(subprocess.run(['git','ls-tree','--name-only','v0.16.0','tests/'],cwd=root,capture_output=True,text=True,check=True).stdout.split())
    return tuple(sorted(Path(x).name for x in glob.glob(str(root/'tests/test*.py')) if 'tests/'+Path(x).name not in old))
NEW_TESTS=new_tests()


def verdict(mods,plain,frozen,plan,clean=None,new_tests=None):
    clean=clean or {};new_tests=NEW_TESTS if new_tests is None else new_tests
    K=set(json.loads(PLAN009.read_text())['criteria']['GTI_test_isolation']['known_failing_allowed'])
    failing={tid:v for d in mods.values() for tid,v in d['results'].items() if v[0] in ('fail','error')}
    allowed_k=set();rule={}
    for v,A in K_ALLOWED.items():
        rv={t for t in failing if t.startswith(f'test_release_{v}.')};c=clean.get(v)
        ok=bool(rv) and rv<=A and c is not None and all(c['results'].get(t,['missing'])[0]=='ok' for t in rv)
        rule[v]={'failures':sorted(rv),'applied':ok}
        if ok:allowed_k|=rv
    k96=sorted(t for t in failing if t in K_096);rule['096']={'failures':k96,'applied':bool(k96)};allowed_k|=set(k96)
    undeclared=sorted(t for t in failing if t not in K and t not in allowed_k)
    s5={t:v[0] for t,v in mods.get('test_study_005.py',{'results':{}})['results'].items()}
    run_total=sum(d['tests_run'] for d in mods.values());skipped=sorted(t for d in mods.values() for t in d['skipped'])
    new_bad=sorted(t for m in new_tests for t,v in mods.get(m,{'results':{}})['results'].items() if v[0] not in ('ok','skip'))
    missing_new=[m for m in new_tests if m not in mods]
    c={'i_only_declared_failures':not undeclared,
       'ii_test_study_005_six_pass':len(s5)==6 and all(v=='ok' for v in s5.values()),
       'iii_counts_match_plain':run_total==plain['tests_run'] and skipped==sorted(plain['skipped']),
       'iv_frozen_unchanged':not frozen['changed'],
       'v_new_tests_pass':not new_bad and not missing_new}
    return {'clauses':c,'passed':all(c.values()),'undeclared_failures':undeclared,'failing':sorted(failing),
            'test_study_005':s5,'tests_run_per_module_total':run_total,'tests_run_plain':plain['tests_run'],
            'skipped_per_module':skipped,'skipped_plain':sorted(plain['skipped']),'new_tests':list(new_tests),
            'new_test_failures':new_bad,'new_test_modules_missing':missing_new,'k_rules':rule}


def _prev_walls():
    p=ROOT/'results/study-018/TEST_SUITE_018.json'
    if not p.exists():return {}
    return {m:d.get('wall_informational',0) for m,d in json.loads(p.read_text())['per_module'].items()}


def run_all(modules,workers,python=sys.executable,log=print):
    """Per-module children, the plain discover child and the needed clean-tag children on one pool. The plain run and the
    slowest modules are submitted first: longest-processing-time order by the per-module wall recorded in the committed
    study-018 TEST_SUITE_018.json (modules it lacks first; ordering only, results are keyed by module)."""
    mods={};clean={};t0=time.time();prev=_prev_walls()
    modules=sorted(modules,key=lambda m:(-prev.get(m,1e9),m))
    with ThreadPoolExecutor(workers) as ex:
        fp=ex.submit(T.run_child,'test*.py',ROOT,python)
        fm={ex.submit(T.run_child,m,ROOT,python):m for m in modules};fc={}
        for f in as_completed(fm):   # a failing test_release module's clean-tag child is queued as soon as it finishes
            m=fm[f];mods[m]=f.result()
            v=next((v for v in TAGS if m==f'test_release_{v}.py'),None)
            if v and any(r[0] in ('fail','error') for r in mods[m]['results'].values()):fc[v]=ex.submit(_clean,TAGS[v],m,python)
        log(f'modules done {time.time()-t0:.0f} s',flush=True)
        for v in TAGS:clean[v]=fc[v].result() if v in fc else None
        plain=fp.result()
    return {m:mods[m] for m in modules},plain,clean


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--output',default=str(OUT));ap.add_argument('--modules',help='comma list (dev only; not a GTI run)')
    ap.add_argument('--workers',type=int,default=WORKERS)
    a=ap.parse_args();out=Path(a.output)
    if out.exists():raise SystemExit(f'refusing to overwrite {out}')
    plan=json.loads(PLAN.read_text());t0=time.time()
    head=subprocess.run(['git','rev-parse','HEAD'],cwd=ROOT,capture_output=True,text=True).stdout.strip()
    porc=subprocess.run(['git','status','--porcelain','--untracked-files=no'],cwd=ROOT,capture_output=True,text=True).stdout;dirty=porc.strip()
    modules=a.modules.split(',') if a.modules else sorted(Path(x).name for x in glob.glob(str(ROOT/'tests/test*.py')))
    mods,plain,clean=run_all(modules,a.workers);frozen=P.frozen_check()
    V=verdict(mods,plain,frozen,plan,clean)
    rep={'schema':'brute.test-suite.v3','study':plan['study'],'gate':'GTI_test_isolation','python':sys.version.split()[0],
         'executable':sys.executable,'head':head,'tracked_tree_dirty':bool(dirty),'workers':a.workers,
         'dirty_tracked_files':[l[3:] for l in porc.splitlines() if l.strip()],'modules_subset':a.modules,
         'per_module':mods,'plain_discover':plain,'frozen_files':frozen,'clean_tag_runs':clean,
         'verdict':V,'wall_informational':round(time.time()-t0,1)}
    out.parent.mkdir(parents=True,exist_ok=True);out.write_text(json.dumps(rep,indent=1,sort_keys=True)+'\n')
    print(json.dumps({'passed':V['passed'],'clauses':V['clauses'],'undeclared':V['undeclared_failures'],
                      'run':V['tests_run_per_module_total'],'plain':V['tests_run_plain'],'wall':rep['wall_informational']},indent=1))


if __name__=='__main__':main()
